#!/usr/bin/env python3
"""
tools/repair_mutation_damage.py -- undo a mutation harness that left its
mutations applied to the corpus.

WHY THIS EXISTS, MEASURED 2026-10-31
------------------------------------
The harness kept the MUTATED text in the same dict it later handed to the
restore. So `_restore_source(path, touched[path])` was given the
mutation, saw `current == original`, and returned True WITHOUT writing.
The corpus kept every mutation it was ever given.

MEASURED on the corpus as found: 18 of the harness's 19 mutations were
applied on disk, and 2 of them had been applied TWICE (the harness was
run twice, and the mutation's `old` is a prefix of its `new`, so the
second run matched again and left a second copy of the injected line).

THE GROUND TRUTH IS THE HARNESS'S OWN (old -> new) PAIRS. The harness
declares, for each mutation, the exact text it replaces and the exact
text it writes. So the original text is recoverable: put `old` back
where `new` now sits.

THE RULES
---------
1. The site of a mutation is pinned by the text immediately BEFORE and
   AFTER it. A site that is not unique STOPS the repair. The repair
   never guesses which occurrence to undo.
2. Two mutations that share the SAME (old, new) pair are ONE edit on
   disk. It is undone once. Which of the two labels it belongs to is
   reported, not assumed.
3. The undos run in the REVERSE order of application, so overlapping
   edits unwind correctly and each undo's anchors still describe the
   file as it stands.
4. A mutation whose `new` is not in the file was never applied and is
   skipped. A mutation whose `old` is still in the file, and is NOT a
   substring of its `new`, was never applied either -- the file held
   that text for its own reasons -- and is skipped.
5. The whole file is compiled AFTER all of its undos, and it is written
   only if it compiles. A file that does not compile is left alone and
   the repair says so.

Run:  python tools/repair_mutation_damage.py [--dry-run]
Exit: 0 if the corpus holds no mutation text and nothing stopped.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

#: (before, after) anchors that pin the site of a mutation's `new` text.
#: `before` must be a SUFFIX of the text before the site; `after` must
#: be a PREFIX of the text after it.
ANCHORS = {
    "gate: a missing part is still a part": (
        "        p.words = words\n        ",
        "\n        if not p.present:",
    ),
    "gate: four of five counts as qualified": (
        "    def qualified(self) -> bool:\n        ",
        "\n\n    def missing(self) -> list:",
    ),
    "gate: the delta need not be quoted": (
        "    if delta.present:\n        ",
        "\n        anchored = ",
    ),
    "gate: the delta need not be anchored": (
        "        quoted = True\n        ",
        "\n        if not quoted:",
    ),
    "gate: the bare word line is an anchor again": (
        'r"(?:\\bpp?\\.\\s*\\d|\\bp{1,2}\\s*\\.?\\s*\\d+\\b|',
        '\n    r"|\\bchapter',
    ),
    "gate: the failure mode need not name a habit": (
        '    fm = parts["failure_mode"]\n    ',
        "\n        fm.present = False",
    ),
    "gate: the test need not have a falsification condition": (
        '    tst = parts["test"]\n    ',
        "\n        tst.present = False",
    ),
    "gate: fetched bytes count as ingested": (
        "        q = parse_qualification(full)\n        ",
        "\n        else:\n            refused.append(",
    ),
    "gate: a refused qualification still counts": (
        "        q = parse_qualification(full)\n        ",
        "\n            qualified.append(row)",
    ),
    "gate: a broken manifest crashes the reader": (
        "            return json.load(fh)\n",
        "\n\n\ndef write_manifest",
    ),
    "artifact: the module no longer parses": (
        "    Structural test only - no topic knowledge. A row is prose if it is written\n",
        "    if IMPERATIVE_RE.search(line):",
    ),
    "artifact: the parser drops an entry": (
        "        seen.add(ident)\n",
        "\n        e.has_author = bool(author and author != line)",
    ),
    "corpus: the delta quote is fabricated": (
        '        return dict(file=base, status="skipped", reason="text file not on disk")\n\n',
        "\n    quote = 'a line that was never in the book at all, invented here'\n"
        "    if not quote:",
    ),
    "corpus: the quote comes from the licence header": (
        "    # live in the first tenth of a book.\n",
        "\n    for i in range(start, min(start + 400, len(lines))):",
    ),
    "corpus: the boilerplate filter is removed": (
        "    def usable(s: str) -> bool:\n        low = s.lower()\n",
        "\n        if s.startswith((",
    ),
    "corpus: the boilerplate filter AND the body floor are removed": (
        "    def usable(s: str) -> bool:\n        low = s.lower()\n",
        "\n        if s.startswith((",
    ),
    "acquirer: the title marker is not checked": (
        '        text = body.decode("latin-1")\n',
        '\n        return dict(t, status="not_acquired",\n'
        '                    error=f"body does not contain the title marker "',
    ),
    "acquirer: the size floor is not checked": (
        "                          f\"{t['marker']!r} (got {len(body)} bytes)\",\n"
        "                    acquired=False, url=url_used)\n",
        '\n        return dict(t, status="not_acquired",\n'
        '                    error=f"only {len(body)} bytes',
    ),
    "measure: the gender table guesses": (
        "    for name in WOMEN:\n        if name in a:\n            return True\n",
        "(row: dict) -> bool:",
    ),
}

#: Lines the harness left behind that are NOT the site of any mutation --
#: a SECOND copy of the injected text, left because the harness ran
#: twice and the mutation's `old` is a prefix of its `new`. They are
#: removed after the undo, and only if the undo of their own mutation
#: succeeded.
STRAY = {
    "corpus: the delta quote is fabricated":
        "    quote = 'a line that was never in the book at all, invented here'\n",
}


def load_harness(repo: str):
    spec = importlib.util.spec_from_file_location(
        "mc", os.path.join(repo, "tools", "mutation_check.py"))
    mc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mc)
    return mc


def edits_of(mutation):
    edits = [(mutation[1], mutation[2], mutation[3])]
    if len(mutation) == 7:
        edits.append((mutation[4], mutation[5], mutation[6]))
    return edits


def locate(src: str, new: str, before: str, after: str):
    """The index of every site of `new` framed by `before` and `after`."""
    hits = []
    start = 0
    while True:
        i = src.find(new, start)
        if i < 0:
            break
        if src[:i].endswith(before) and src[i + len(new):].startswith(after):
            hits.append(i)
        start = i + 1
    return hits


def sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--repo", default=REPO)
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)

    mc = load_harness(repo)

    # Group by (file, old, new): two labels that share a pair are one
    # edit on disk.
    groups = {}
    for mutation in mc.MUTATIONS:
        for rel, old, new in edits_of(mutation):
            path = os.path.join(repo, rel.replace("/", os.sep))
            key = (path, old, new)
            groups.setdefault(key, []).append(mutation[0])

    by_file = {}
    for (path, old, new), labels in groups.items():
        by_file.setdefault(path, []).append((labels, old, new))

    failures = 0
    for path, edits in by_file.items():
        src = open(path, encoding="utf-8").read()
        original_src = src
        base = os.path.basename(path)
        before_hash = sha(path)
        changed = False
        for labels, old, new in reversed(edits):
            label = labels[0]
            if new not in src:
                print("  skip     %-58s %s (not applied)" % (label, base))
                continue
            if old in src and old not in new:
                print("  skip     %-58s %s (the file already held that text "
                      "on its own)" % (label, base))
                continue
            before_txt, after_txt = ANCHORS.get(label, ("", ""))
            if before_txt:
                hits = locate(src, new, before_txt, after_txt)
            else:
                hits = [src.find(new)]
            if len(hits) != 1:
                print("  STOP     %-58s %s (%d sites match the anchor)"
                      % (label, base, len(hits)))
                failures += 1
                continue
            i = hits[0]
            src = src[:i] + old + src[i + len(new):]
            print("  undo     %-58s %s" % (label, base))
            if len(labels) > 1:
                print("        (this pair carries %d labels: %s)"
                      % (len(labels), ", ".join(labels)))
            changed = True
            if label in STRAY:
                stray = STRAY[label]
                n = src.count(stray)
                if n:
                    print("        and %d stray copy/copies removed" % n)
                    src = src.replace(stray, "")
        if not changed:
            continue
        try:
            compile(src, path, "exec")
        except SyntaxError as exc:
            print("  STOP     %s does not compile after the repair: %s"
                  % (base, exc))
            failures += 1
            continue
        # **AND THE FILE IS RE-READ BEFORE IT IS WRITTEN.** Another
        # process may have edited it while this repair was computing. A
        # repair that writes over somebody else's edit is the same
        # failure as the harness's: it destroys work and reports
        # success. If the bytes on disk are not the bytes this repair
        # read, the repair stops and says so.
        now = open(path, encoding="utf-8").read()
        if now != original_src:
            print("  STOP     %s changed while the repair was computing -- "
                  "not overwriting it" % base)
            failures += 1
            continue
        if not args.dry_run:
            with open(path, "w", encoding="utf-8", newline="") as fh:
                fh.write(src)
            print("        %s: %s -> %s" % (base, before_hash, sha(path)))

    print()
    if args.dry_run:
        print("DRY RUN: nothing was written.")
        return 1 if failures else 0
    print("VERIFY: the corpus holds no mutation text")
    leftovers = 0
    for (path, old, new), labels in groups.items():
        src = open(path, encoding="utf-8").read()
        if new in src and old not in src:
            print("  LEFTOVER %-58s %s" % (labels[0], os.path.basename(path)))
            leftovers += 1
    print("leftovers: %d   stops: %d" % (leftovers, failures))
    return 1 if (leftovers or failures) else 0


if __name__ == "__main__":
    sys.exit(main())
