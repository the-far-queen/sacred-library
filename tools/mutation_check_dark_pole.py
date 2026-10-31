"""
tools/mutation_check_dark_pole.py -- prove the dark-pole checks can fail.

CENTRAL-RULES rule 7: "A test that cannot fail is not a test." Every
bug this project has ever shipped was behind green output.

So: eight mutations of the CORPUS, each of which must make the test
suite go RED. If a mutation stays green, the check that should have
caught it does not exist, and the mutation is reported as SURVIVED.

The mutations are the ones a real strip would make:
  1. the licence header is left in           -> the boilerplate check
  2. the licence footer is left in           -> the boilerplate check
  3. the book's first division is eaten      -> the structure check
  4. the book's last division is eaten       -> the structure check
  5. a split word is left split              -> the word check
  6. the 1984 appendix is eaten               -> the appendix check
  7. the 2020 postface is left in            -> the postface check
  8. the manifest lies about the byte count  -> the receipt check

WHY THE MUTATIONS ARE APPLIED TO THE FILES, not to the builder's source:
a mutation applied to source has to find an exact string in it, and
when the source is edited the mutation silently stops applying -- which
is what the first version of this file did. It reported "0 of 8
mutations went RED" for eight mutations that never ran, and that is a
worse failure than a missing check, because it LOOKS like a result.

A mutation that corrupts a BUILT FILE cannot silently fail to apply,
and it tests the same thing: the checks on the corpus. Each mutation
runs in a scratch tree, so the real corpus is never touched.

Run:  python tools/mutation_check_dark_pole.py
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, List, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
BUILDER_REL = os.path.join("corpus", "dark-pole", "build_dark_pole.py")
TEST_REL = os.path.join("tests", "test_dark_pole.py")
TEXTS_REL = os.path.join("corpus", "dark-pole")
RAW_REL = os.path.join("corpus", "dark-pole", "_raw")
MANIFEST_REL = os.path.join("corpus", "dark-pole", "ACQUIRED.json")


def _read(path: str) -> str:
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


# ==========================================================================
# the mutations
# ==========================================================================

def m_licence_header(tree: str) -> str:
    """Put the licence header back at the top of Paradise Lost."""
    p = os.path.join(tree, TEXTS_REL, "milton-paradise-lost.txt")
    raw = _read(os.path.join(tree, RAW_REL, "pg20.txt"))
    head = raw[:raw.find("*** START OF THE PROJECT GUTENBERG EBOOK")]
    _write(p, head + _read(p))
    return "the licence header is back in Paradise Lost"


def m_licence_footer(tree: str) -> str:
    """Put the licence footer back at the end of The White Devil."""
    p = os.path.join(tree, TEXTS_REL, "webster-white-devil.txt")
    raw = _read(os.path.join(tree, RAW_REL, "pg12915.txt"))
    tail = raw[raw.find("*** END OF THE PROJECT GUTENBERG EBOOK"):]
    _write(p, _read(p) + tail)
    return "the licence footer is back in The White Devil"


def m_first_division(tree: str) -> str:
    """Eat Paradise Lost's first book heading."""
    p = os.path.join(tree, TEXTS_REL, "milton-paradise-lost.txt")
    t = _read(p)
    t2 = re.sub(r"(?m)^\s*BOOK\s+I\.\s*$", "", t, count=1)
    assert t2 != t, "the first division was not found"
    _write(p, t2)
    return "Paradise Lost lost its first book heading"


def m_last_division(tree: str) -> str:
    """Eat The White Devil's last act heading."""
    p = os.path.join(tree, TEXTS_REL, "webster-white-devil.txt")
    t = _read(p)
    t2 = re.sub(r"(?m)^\s*ACT\s+V\s*$", "", t, count=1)
    assert t2 != t, "the last division was not found"
    _write(p, t2)
    return "The White Devil lost its fifth act heading"


def m_split_word(tree: str) -> str:
    """Leave a word split across a line."""
    p = os.path.join(tree, TEXTS_REL, "milton-paradise-lost.txt")
    t = _read(p)
    t2 = t.replace("The World was all before them",
                   "The World was all before\n  them", 1)
    assert t2 != t, "the phrase was not found"
    _write(p, t2)
    return "Paradise Lost has a word split across a line"


def m_appendix(tree: str) -> str:
    """Eat the 1984 appendix."""
    p = os.path.join(tree, TEXTS_REL, "orwell-nineteen-eighty-four.txt")
    t = _read(p)
    i = t.find("APPENDIX")
    assert i > 0, "the appendix was not found"
    _write(p, t[:i])
    return "1984 lost its Newspeak appendix"


def m_postface(tree: str) -> str:
    """Leave the 2020 postface in the 1984 text."""
    p = os.path.join(tree, TEXTS_REL, "orwell-nineteen-eighty-four.txt")
    raw = _read(os.path.join(tree, RAW_REL, "p_raw.txt"))
    post = raw.find("Orwell in Early 20th")
    assert post > 0, "the postface was not found in the raw fetch"
    _write(p, _read(p) + raw[post:post + 3000])
    return "1984 carries the 2020 postface"


def m_manifest_lies(tree: str) -> str:
    """The manifest's byte count does not match the file."""
    p = os.path.join(tree, MANIFEST_REL)
    rows = json.loads(_read(p))
    hit = False
    for r in rows:
        if r["file"].endswith("milton-paradise-lost.txt"):
            r["bytes"] = int(r["bytes"]) + 1
            hit = True
            break
    assert hit, "the manifest row was not found"
    _write(p, json.dumps(rows, indent=2, ensure_ascii=False) + "\n")
    return "the manifest's byte count does not match the file"


def m_git_attribute_removed(tree: str) -> str:
    """Take the -text attribute off the corpus texts.

    With core.autocrlf=true on this machine, that means git would
    rewrite the texts' line endings on checkout and the manifest's
    sha256 would stop matching the file. This is the defect that was
    actually present before the .gitattributes was extended.
    """
    p = os.path.join(tree, ".gitattributes")
    t = _read(p)
    t2 = t.replace("corpus/dark-pole/*.txt -text\n", "")
    assert t2 != t, "the dark-pole rule was not found"
    _write(p, t2)
    return "the corpus texts lost their -text git attribute"


MUTATIONS: List[Tuple[str, Callable[[str], str]]] = [
    ("the licence header is left in", m_licence_header),
    ("the licence footer is left in", m_licence_footer),
    ("the book's first division is eaten", m_first_division),
    ("the book's last division is eaten", m_last_division),
    ("a split word is left split", m_split_word),
    ("the 1984 appendix is eaten", m_appendix),
    ("the 2020 postface is left in", m_postface),
    ("the manifest lies about the byte count", m_manifest_lies),
    ("the corpus texts lose the -text attribute", m_git_attribute_removed),
]


# ==========================================================================
# the harness
# ==========================================================================

def make_tree() -> str:
    """A scratch copy of the corpus, the test and the raw fetches."""
    tree = tempfile.mkdtemp(prefix="dp_mut_")
    for rel in (BUILDER_REL, TEST_REL, MANIFEST_REL, ".gitattributes"):
        src = os.path.join(REPO, rel)
        dst = os.path.join(tree, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
    # the raw fetches
    raw_dst = os.path.join(tree, RAW_REL)
    os.makedirs(raw_dst, exist_ok=True)
    for name in os.listdir(os.path.join(REPO, RAW_REL)):
        shutil.copy2(os.path.join(REPO, RAW_REL, name),
                     os.path.join(raw_dst, name))
    # the built texts, which sit beside the manifest
    for name in os.listdir(os.path.join(REPO, TEXTS_REL)):
        if name.endswith(".txt"):
            shutil.copy2(os.path.join(REPO, TEXTS_REL, name),
                         os.path.join(tree, TEXTS_REL, name))
    # `git check-attr` reads the attributes from the working tree, so the
    # scratch tree needs to be a repository of its own.
    subprocess.run(["git", "init", "-q"], cwd=tree, capture_output=True,
                   timeout=120)
    return tree


def run_tests(tree: str) -> Tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", TEST_REL, "-q", "--no-header",
         "-p", "no:cacheprovider"],
        cwd=tree, capture_output=True, text=True, timeout=600)
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    print("=" * 78)
    print("THE MUTATION CHECK: each mutation must make the suite go RED")
    print("=" * 78)
    print()

    # the unmutated tree must be GREEN, or the whole check means nothing
    tree = make_tree()
    try:
        rc, out = run_tests(tree)
        if rc != 0:
            print("  THE UNMUTATED CORPUS IS ALREADY RED. THE CHECK IS VOID.")
            print(out[-2000:])
            return 1
        lines = [l for l in out.strip().splitlines() if l.strip()]
        print("  the unmutated corpus is GREEN (%s)" % (lines[-1] if lines else "?"))
    finally:
        shutil.rmtree(tree, ignore_errors=True)
    print()

    results = []
    for name, mutate in MUTATIONS:
        tree = make_tree()
        try:
            try:
                mutate(tree)
            except AssertionError as exc:
                print("  %-42s COULD NOT APPLY: %s" % (name, exc))
                results.append((name, "NOT-APPLIED"))
                continue
            rc, out = run_tests(tree)
            lines = [l for l in out.strip().splitlines() if l.strip()]
            tail = lines[-1] if lines else ""
            if rc != 0:
                print("  %-42s RED   %s" % (name, tail))
                results.append((name, "RED"))
            else:
                print("  %-42s GREEN -- SURVIVED. THE CHECK IS MISSING." % name)
                results.append((name, "SURVIVED"))
        finally:
            shutil.rmtree(tree, ignore_errors=True)

    print()
    print("=" * 78)
    survived = [r for r in results if r[1] != "RED"]
    print("  %d of %d mutations went RED"
          % (len(results) - len(survived), len(results)))
    for name, kind in survived:
        print("    NOT CAUGHT: %s (%s)" % (name, kind))
    print("=" * 78)
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
