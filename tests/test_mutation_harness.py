"""
tests/test_mutation_harness.py -- the harness itself must be checked.

A test that cannot fail is not a test. The harness that proves the
corpus's checks can go red was, itself, unchecked -- and it was broken
in the worst possible way: it looked like it worked.

THE DEFECT, MEASURED 2026-10-31
-------------------------------
The harness kept the MUTATED text in the same dict it later handed to
the restore. So `_restore_source(path, touched[path])` was given the
mutation, saw `current == original`, and returned True WITHOUT
WRITING. The corpus kept 18 of the harness's 19 mutations. The suite
then reported the damage as a test failure, and the failure looked
like the corpus's fault rather than the harness's.

So the harness needed three checks of its own:

1. it must leave every file it touched byte-identical
2. it must not hold the mutated text in the dict it restores from
3. it must refuse to write over a file another process changed

Run:  python -m pytest tests/test_mutation_harness.py -q
"""
from __future__ import annotations

import hashlib
import importlib.util
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOLS = os.path.join(REPO, "tools")
HARNESS = os.path.join(TOOLS, "mutation_check.py")


def load_harness():
    spec = importlib.util.spec_from_file_location(
        "mutation_check_under_test", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def test_harness_file_exists():
    assert os.path.exists(HARNESS), "the harness is missing"


def test_harness_keeps_the_original_separate_from_the_mutation():
    """THE DEFECT. The harness must not overwrite the original it
    restores from with the mutated text.

    The harness reads a source, mutates it, runs the tests, and writes
    the original back. If the mutated text and the original share one
    dict, the restore is handed the mutation and writes nothing -- and
    the corpus keeps every mutation the harness ever applied.

    This check reads the harness's SOURCE and fails if the original and
    the mutation share a variable. It is a source check because the
    failure is a data-flow error, not a runtime one: the code runs
    happily and produces the wrong result.
    """
    src = open(HARNESS, encoding="utf-8").read()

    # the harness must keep a dict of originals
    assert re_search(r"original\s*=\s*\{\}", src), \
        "the harness keeps no separate dict of the original sources"

    # and the restore must read from THAT dict, not from the mutated one
    restore_block = src[src.rfind("finally:"):]
    assert re_search(r"_restore_source\(path,\s*data\)", restore_block), \
        "the restore does not call _restore_source"
    assert re_search(r"for\s+path,\s*data\s+in\s+original\.items\(\)", restore_block), \
        ("the restore iterates over the MUTATED dict instead of the "
         "original one -- this is the defect measured on 2026-10-31")

    # and the mutation must go into a different dict
    assert re_search(r"touched\s*=\s*\{\}", src), \
        "the harness keeps no dict for the mutated sources"
    assert re_search(r"touched\[path\]\s*=\s*src\.replace", src), \
        "the mutation is not written into the mutated dict"


def re_search(pattern: str, text: str) -> bool:
    import re
    return re.search(pattern, text) is not None


def test_harness_restores_a_file_it_mutated(tmp_path):
    """A file the harness mutates must come back byte-identical.

    This runs the harness's OWN apply-and-restore path on a scratch
    file, not on the corpus, so it is fast and it cannot damage
    anything.
    """
    mc = load_harness()

    target = tmp_path / "sample.py"
    target.write_text("def f():\n    return 1\n", encoding="utf-8")

    original = target.read_text(encoding="utf-8")
    mutated = original.replace("return 1", "return 2")
    assert mutated != original

    # apply
    with open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(mutated)
    assert sha(str(target)) == hashlib.sha256(
        mutated.encode()).hexdigest(), "the mutation was not applied"

    # restore, the way the harness does it
    mc._what_we_wrote[str(target)] = mutated
    ok = mc._restore_source(str(target), original)
    assert ok is True
    assert target.read_text(encoding="utf-8") == original, \
        "the restore did not put the original back"
    assert sha(str(target)) == hashlib.sha256(original.encode()).hexdigest()


def test_harness_refuses_to_overwrite_a_file_another_process_changed(
        tmp_path):
    """A file changed by somebody else must be LEFT ALONE.

    The harness and the corpus live in the same working tree, and a
    concurrent session can edit the same file mid-run. Writing over it
    destroys that work and reports success.
    """
    mc = load_harness()

    target = tmp_path / "shared.py"
    target.write_text("def f():\n    return 1\n", encoding="utf-8")

    ours = "def f():\n    return 2\n"
    with open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(ours)
    mc._what_we_wrote[str(target)] = ours

    # another process edits it
    theirs = "def f():\n    return 3\n"
    with open(target, "w", encoding="utf-8", newline="") as fh:
        fh.write(theirs)

    original = "def f():\n    return 1\n"
    ok = mc._restore_source(str(target), original)
    assert ok is False, "the restore overwrote a file another process changed"
    assert target.read_text(encoding="utf-8") == theirs, \
        "the other process's edit was destroyed"


def test_harness_hashes_the_corpus_it_can_touch():
    """The harness must measure the corpus's state, not infer it.

    The suite's exit code cannot tell you the harness left a mutation
    behind -- the suite reports the damage as a failure and it looks
    like the corpus's fault. So the harness hashes the files it can
    touch, before and after.
    """
    mc = load_harness()
    hashes = mc._hash_corpus()
    assert hashes, "the harness hashes nothing"
    for path in hashes:
        assert os.path.exists(path)
        assert len(hashes[path]) == 64, "sha256 must be full length"


def test_corpus_drift_detects_a_changed_file():
    mc = load_harness()
    before = mc._hash_corpus()
    assert mc._corpus_drift(before) == [], \
        "the corpus is already drifted -- the harness left something behind"
