#!/usr/bin/env python3
"""
tools/mutation_check.py -- prove the corpus gate's tests can go red.

A test that cannot fail is not a test. This script applies a set of
MUTATIONS to the source, runs the test suite after each, and requires
every one to turn RED. A mutation that stays green means the suite
cannot see that defect, and the mutation is reported as a FAILURE of
the suite, not a pass.

Run:  python tools/mutation_check.py
Exit: 0 if every mutation went red and the baseline was green.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TARGET = os.path.join(REPO, "corpus", "qualify.py")
CURRICULUM = os.path.join(REPO, "corpus", "curriculum.py")
# BOTH test files. The corpus mutations (a fabricated quote, a quote from
# the licence header) are only visible to tests/test_corpus_ingest.py, so
# a check that ran only the gate suite would report those mutations GREEN
# and call it a pass.
TESTS = [
    os.path.join(REPO, "tests", "test_curriculum.py"),
    os.path.join(REPO, "tests", "test_corpus_ingest.py"),
]
VERIFY = TESTS[0]

# (label, file, old, new)
MUTATIONS = [
    # --- the gate must be able to refuse -----------------------------------
    ("gate: a missing part is still a part",
     "corpus/qualify.py",
     "p.present = words >= MIN_PART_WORDS",
     "p.present = True"),

    ("gate: four of five counts as qualified",
     "corpus/qualify.py",
     "return self.score == len(PARTS)",
     "return self.score >= len(PARTS) - 1"),

    ("gate: the delta need not be quoted",
     "corpus/qualify.py",
     'quoted = ("\\"" in delta.text) or ("\\u201c" in delta.text) or (">" in delta.text)',
     "quoted = True"),

    ("gate: the delta need not be anchored",
     "corpus/qualify.py",
     "anchored = bool(ANCHOR_RE.search(delta.text))",
     "anchored = True"),

    ("gate: the bare word line is an anchor again",
     "corpus/qualify.py",
     r'\bline(?:s)?\s+\d+"',
     r'\bline(?:s)?\b"'),

    ("gate: the failure mode need not name a habit",
     "corpus/qualify.py",
     "if fm.present and not HABIT_RE.search(fm.text):",
     "if False:"),

    ("gate: the test need not have a falsification condition",
     "corpus/qualify.py",
     "if tst.present and not NEGATIVE_HINT_RE.search(tst.text):",
     "if False:"),

    # --- bytes are not knowledge -------------------------------------------
    ("gate: fetched bytes count as ingested",
     "corpus/qualify.py",
     "if q.qualified:\n            qualified.append(row)",
     "qualified.append(row)\n        if False:"),

    ("gate: a refused qualification still counts",
     "corpus/qualify.py",
     "if q.qualified:",
     "if True:"),

    ("gate: a broken manifest crashes the reader",
     "corpus/qualify.py",
     "        except json.JSONDecodeError:\n            return []",
     "        except json.JSONDecodeError:\n            raise"),

    # --- the artifact must come from the module -----------------------------
    # The original defect was an UNTERMINATED docstring, so the mutation
    # must actually unterminate one. Appending a line inside the docstring
    # does NOT do it -- the docstring still closes on the next `"""`. The
    # mutation has to REMOVE the closing quotes.
    ("artifact: the module no longer parses",
     "corpus/curriculum.py",
     '    in imperative/second person, or is long and ends like a sentence.\n'
     '    """\n',
     '    in imperative/second person, or is long and ends like a sentence.\n'
     '    (this docstring is deliberately left unterminated)\n'),

    ("artifact: the parser drops an entry",
     "corpus/curriculum.py",
     "        e.strand = assign_strand(line)",
     "        e.strand = assign_strand(line)\n"
     "        if e.key == entries[0].key and len(entries) > 1:\n"
     "            continue"),

    # --- the quote must be a real quote ------------------------------------
    ("corpus: the delta quote is fabricated",
     "corpus/write_qualifications.py",
     "    quote, lineno = find_quote(src, quote_wants(row, j))",
     "    quote, lineno = find_quote(src, quote_wants(row, j))\n"
     "    quote = 'a line that was never in the book at all, invented here'"),

    ("corpus: the quote comes from the licence header",
     "corpus/write_qualifications.py",
     "    body = max(body, int(len(lines) * 0.12))",
     "    body = start"),

    # **AND THE MUTATIONS THAT ACTUALLY REMOVE THE MECHANISM.** The
    # quote must not come from the licence header. Three things keep it
    # out: the marker skip (the search starts AFTER "*** START OF ...
    # ***"), the body floor (the quote must be at least 12% into the
    # file), and the content filter (the licence phrases are rejected by
    # content).
    #
    # MEASURED 2026-10-31: removing the content filter ALONE left the
    # other two doors holding, so the check stayed GREEN -- 0 of the 27
    # deltas quoted boilerplate. That was not a strong check, it was a
    # WEAK MUTATION. **A mutation that removes one of three doors
    # cannot test any of them**, so it is not in this list at all: a
    # mutation that cannot go red is not evidence, it is decoration.
    #
    # What IS here is the pair that removes two of the three, and the
    # one that removes all three. The harness supports a mutation of
    # several edits because the mechanism is several lines of code and
    # one of them is never enough.
    ("corpus: the boilerplate filter AND the body floor are removed",
     "corpus/write_qualifications.py",
     "        if any(b in low for b in boiler):\n            return False",
     "        pass",
     "corpus/write_qualifications.py",
     "    body = max(body, int(len(lines) * 0.12))",
     "    body = 0"),

    # **AND THE THIRD MUTATION OF THE SAME CLASS, WITH ALL THREE DOORS
    # REMOVED.** MEASURED 2026-10-31: this one goes RED, because some
    # files carry boilerplate that survives PAST the marker. It is the
    # one that proves the check can see the class at all.
    ("corpus: the boilerplate filter, the body floor AND the marker skip "
     "are removed",
     "corpus/write_qualifications.py",
     "        if any(b in low for b in boiler):\n            return False",
     "        pass",
     "corpus/write_qualifications.py",
     "    body = max(body, int(len(lines) * 0.12))",
     "    body = 0",
     "corpus/write_qualifications.py",
     '        if "START OF" in line and "PROJECT GUTENBERG" in line.upper():\n'
     '            start = i + 1\n            break',
     "        pass"),
    # --- the acquirer's refusals --------------------------------------------
    ("acquirer: the title marker is not checked",
     "corpus/fetch_corpus.py",
     "    if t[\"marker\"].lower() not in text.lower():",
     "    if False:"),

    ("acquirer: the size floor is not checked",
     "corpus/fetch_corpus.py",
     "    if len(body) < MIN_BYTES:",
     "    if False:"),

    # --- the measurement ----------------------------------------------------
    ("measure: the gender table guesses",
     "corpus/measure_corpus.py",
     "    return False\n\n\ndef is_craft",
     "    return True\n\n\ndef is_craft"),
]


def run_tests() -> tuple:
    r = subprocess.run(
        [sys.executable, "-m", "pytest"] + TESTS + ["-q", "--no-header",
                                                   "-p", "no:cacheprovider"],
        capture_output=True, text=True, timeout=600, cwd=REPO,
    )
    return r.returncode, (r.stdout or "")[-1500:]


#: THE BUILDERS. A mutation in a BUILDER is invisible to a test that
#: checks the BUILT ARTIFACT -- unless the builder is re-run.
#:
#: MEASURED 2026-10-31: four mutations stayed GREEN, and all four were
#: in `corpus/write_qualifications.py` -- the thing that WRITES the
#: five-part qualifications. The tests that catch a fabricated quote, a
#: quote from the licence header, and a missing boilerplate filter all
#: read the WRITTEN .md files. Mutating the writer and then reading the
#: files it wrote an hour ago changes nothing, so the suite stayed
#: green and the harness reported the check as decorative.
#:
#: **That is the same failure the item-35 harness had, in the other
#: direction:** there, the mutation silently stopped applying; here, the
#: mutation applied perfectly and the measurement it was supposed to
#: change never did. A mutation that cannot be SEEN has not been shown
#: to work.
#:
#: So a mutation in a builder is followed by a REBUILD, and the rebuild
#: is what makes the mutation visible.
BUILDERS = {
    "corpus/write_qualifications.py":
        [sys.executable, "corpus/write_qualifications.py"],
    "corpus/measure_corpus.py":
        [sys.executable, "corpus/measure_corpus.py"],
}


def rebuild(rel: str) -> str:
    """re-run the builder, so a mutation to it is visible to the tests.

    **AND THE ORIGINAL ARTIFACTS ARE RESTORED AFTERWARDS**, because the
    builder writes into the corpus, and a corrupted qualification left
    on disk would be a corrupted corpus for the next reader.
    """
    cmd = BUILDERS.get(rel.replace("\\", "/"))
    if not cmd:
        return ""
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=600,
                       cwd=REPO)
    return (r.stdout or "")[-400:] + (r.stderr or "")[-400:]


#: THE ARTIFACTS THE BUILDERS WRITE. These are backed up before a
#: mutation and restored after it, so the harness cannot damage the
#: corpus it is checking.
#:
#: **AND THE TEXTS DIRECTORY IS IN THIS LIST**, because the acquirer's
#: refusals are what the mutations remove. MEASURED 2026-10-31: the
#: harness backed up only the qualifications, so when the mutation
#: "the size floor is not checked" removed the floor, the acquirer
#: fetched a body that was UNDER the floor and wrote it into
#: corpus/ingest/texts/ -- where it stayed after the harness
#: finished. A file named "a-target-that-is-not-in-the-corpus.txt",
#: holding a title marker and 4,000 x's, sat in the corpus and was
#: picked up by the next commit.
#:
#: So the harness backs up EVERY directory a mutated builder can write
#: into, and removes the files a mutated builder CREATED.
_ARTIFACT_DIRS = (
    os.path.join(REPO, "corpus", "ingest", "qualifications"),
    os.path.join(REPO, "corpus", "ingest", "texts"),
)


def _backup_artifacts() -> dict:
    """a copy of every artifact the builders can overwrite."""
    out = {}
    for d in _ARTIFACT_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            p = os.path.join(d, fn)
            if os.path.isfile(p):
                with open(p, "rb") as fh:
                    out[p] = fh.read()
    return out


def _restore_artifacts(backup: dict) -> None:
    """put the artifacts back, byte for byte.

    **AND FILES THE MUTATED BUILDER CREATED ARE REMOVED**, because a
    file that did not exist before the mutation must not survive it.
    """
    for d in _ARTIFACT_DIRS:
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            p = os.path.join(d, fn)
            if p not in backup and os.path.isfile(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
    for p, data in backup.items():
        with open(p, "wb") as fh:
            fh.write(data)


def _restore_source(path: str, original: str) -> bool:
    """put a source file back, and SAY SO if it will not.

    **AND THIS IS THE RACE THAT BROKE THE CORPUS ONCE.** MEASURED
    2026-10-31: this harness read a source file, mutated it, ran the
    tests, and wrote the original back. But another process was editing
    the SAME file at the same time. So the harness wrote back a version
    it had read -- which was already a MUTATED version -- and the corpus
    was left with `if False:` where a real condition belonged, and a
    docstring that did not close.

    **A harness that can leave the corpus broken is worse than no
    harness**, because it breaks the thing it is checking and reports
    the breakage as a test failure. Ten stubs were left in the corpus
    this way, and 17 tests were failing for a reason that had nothing
    to do with the corpus.

    So the restore is now GUARDED: the file is written back only if it
    still holds the mutation this harness wrote. If something else
    changed it in the meantime, the harness leaves it alone and says
    so -- loudly -- because the alternative is overwriting somebody
    else's work with a stale copy.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            current = fh.read()
    except OSError:
        return False
    if current == original:
        return True          # nothing to do, already correct
    if current != _what_we_wrote.get(path, ""):
        print("  WARNING: %s was changed by something else while the"
              % os.path.basename(path))
        print("           mutation was running -- NOT overwriting it.")
        print("           The file is left as the other process left it.")
        return False
    with open(path, "w", encoding="utf-8", newline="") as fh:
        fh.write(original)
    return True


#: what the harness last WROTE to each file, so the restore can tell
#: its own edit apart from somebody else's.
_what_we_wrote: dict = {}


def _hash_corpus() -> dict:
    """A hash of every source file the harness can touch.

    The corpus is the thing being checked, so its state has to be
    measured directly. A test suite's exit code cannot tell you that
    the harness left a mutation behind -- the suite reports the damage
    as a failure and looks like the corpus's fault.
    """
    import hashlib
    out = {}
    for rel in sorted({m[1] for m in MUTATIONS} |
                      {m[4] for m in MUTATIONS if len(m) == 7}):
        path = os.path.join(REPO, rel.replace("/", os.sep))
        if not os.path.exists(path):
            continue
        with open(path, "rb") as fh:
            out[path] = hashlib.sha256(fh.read()).hexdigest()
    return out


def _corpus_drift(pre: dict) -> list:
    """The files the harness changed and did not put back."""
    post = _hash_corpus()
    drift = []
    for path, h in pre.items():
        now = post.get(path)
        if now != h:
            drift.append((path, h, now))
    return drift


def main() -> int:
    if not os.path.exists(VERIFY):
        print("no test file to mutate:", VERIFY)
        return 1

    # **AND THE WHOLE CORPUS IS HASHED BEFORE THE HARNESS RUNS.** A
    # harness that damages the corpus it is checking is worse than no
    # harness, and it reports the damage as a test failure -- so the
    # corpus's own state has to be measured, not inferred from the
    # tests' exit code.
    #
    # MEASURED 2026-10-31: this harness kept the MUTATED text in the
    # same dict it later handed to the restore, so the restore saw
    # `current == original` and wrote nothing. The corpus kept 18 of
    # 19 mutations, and the suite reported the damage as a failure.
    # This hash is what turns that class of damage into a number.
    pre_hashes = _hash_corpus()
    print("=" * 72)
    print(f"CORPUS BEFORE  {len(pre_hashes)} files hashed")

    rc, out = run_tests()
    baseline_green = (rc == 0)
    print("=" * 72)
    print(f"BASELINE  pytest {os.path.relpath(VERIFY, REPO)}  exit={rc}  "
          f"{'GREEN' if baseline_green else 'RED'}")
    print(out.strip()[-600:])
    if not baseline_green:
        print("=" * 72)
        print("BASELINE IS RED -- the suite must be green before mutations mean "
              "anything.")
        return 1

    results = []
    for mutation in MUTATIONS:
        # **AND A MUTATION MAY CARRY MORE THAN ONE EDIT.** The mechanism
        # the check defends against can be more than one line of code --
        # MEASURED 2026-10-31: the boilerplate defence is a filter AND a
        # floor, and removing only the filter leaves the floor holding,
        # so the defect never reaches the corpus and the mutation proves
        # nothing. A 4-tuple is one edit; a 7-tuple is two.
        label = mutation[0]
        edits = []
        if len(mutation) == 4:
            edits.append((mutation[1], mutation[2], mutation[3]))
        elif len(mutation) == 7:
            edits.append((mutation[1], mutation[2], mutation[3]))
            edits.append((mutation[4], mutation[5], mutation[6]))
        elif len(mutation) == 10:
            edits.append((mutation[1], mutation[2], mutation[3]))
            edits.append((mutation[4], mutation[5], mutation[6]))
            edits.append((mutation[7], mutation[8], mutation[9]))
        else:
            raise SystemExit("STOP: mutation %r has %d entries; the "
                             "harness reads 4, 7 or 10" % (label, len(mutation)))

        touched = {}          # path -> the MUTATED source
        original = {}         # path -> the source as it was on disk
        stale = None
        for rel, old, new in edits:
            path = os.path.join(REPO, rel.replace("/", os.sep))
            if not os.path.exists(path):
                stale = f"file not found: {path}"
                break
            if path not in touched:
                with open(path, encoding="utf-8") as fh:
                    original[path] = fh.read()
                touched[path] = original[path]
            src = touched[path]
            if old not in src:
                stale = ("pattern not found in %s -- mutation is stale "
                         "against the current source" % rel)
                break
            touched[path] = src.replace(old, new, 1)
        if stale:
            results.append((label, "SKIP", stale))
            continue

        # **AND THE ARTIFACTS THE BUILDER WRITES ARE BACKED UP AND
        # RESTORED**, because the rebuild writes into the corpus. A
        # corrupted qualification left on disk would be a corrupted
        # corpus for the next reader -- and the mutation harness must not
        # damage the corpus it is checking.
        artifact_backup = _backup_artifacts()
        try:
            for path, data in touched.items():
                with open(path, "w", encoding="utf-8", newline="") as fh:
                    fh.write(data)
                _what_we_wrote[path] = data
            # **AND THE BUILDER IS RE-RUN**, so a mutation to a builder
            # is visible to the tests that read what it built. Without
            # this, four mutations stayed GREEN for a reason that had
            # nothing to do with the checks: the builder was mutated and
            # never asked to build anything.
            note = rebuild(edits[0][0])
            rc, out = run_tests()
            if rc != 0:
                results.append((label, "RED", f"exit={rc}"))
            else:
                results.append((label, "GREEN", "the suite did NOT see this "
                                                "defect -- the test cannot fail"))
        finally:
            for path, data in original.items():
                _restore_source(path, data)
            _restore_artifacts(artifact_backup)

    print("=" * 72)
    print("MUTATIONS")
    bad = 0
    for label, verdict, detail in results:
        print(f"  {verdict:6} {label}")
        if verdict != "RED":
            print(f"         -> {detail}")
            bad += 1
    print("=" * 72)
    print(f"{len(results) - bad} of {len(results)} mutations went RED")
    rc, out = run_tests()
    print(f"RESTORED BASELINE  exit={rc}  {'GREEN' if rc == 0 else 'RED'}")
    if rc != 0:
        print(out.strip()[-800:])
        return 1

    # **AND THE CORPUS MUST BE BYTE-IDENTICAL TO HOW IT STARTED.** This
    # is the check that would have caught the defect this harness
    # carried: it kept the mutated text in the same dict it handed to
    # the restore, so the restore wrote nothing and the corpus kept 18
    # of 19 mutations. The suite's exit code cannot see that -- it just
    # reports the damage as a failure.
    drift = _corpus_drift(pre_hashes)
    if drift:
        print("=" * 72)
        print("THE HARNESS CHANGED THE CORPUS AND DID NOT PUT IT BACK:")
        for path, before, after in drift:
            print("  %s" % os.path.relpath(path, REPO))
            print("    before %s" % before[:16])
            print("    after  %s" % (after or "GONE")[:16])
        print("A harness that damages the corpus it is checking is worse")
        print("than no harness. Run: python tools/repair_mutation_damage.py")
        return 3
    print("CORPUS AFTER   %d files, byte-identical to how it started"
          % len(pre_hashes))
    return 0 if bad == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
