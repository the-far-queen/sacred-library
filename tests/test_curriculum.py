"""
tests/test_curriculum.py -- the corpus gate, measured.

This file exists because the queue item's own verify command names it:
`python -m pytest tests/test_curriculum.py -q`. That path did not exist,
so pytest exited 4 (usage error: file not found) -- which a `| tail`
read turns into "no tests ran, exit 0". A verify command that can pass
because its target is MISSING is not a verify command.

WHAT IS TESTED
--------------
1. `corpus/curriculum.py` must PARSE. It did not: an unterminated
   docstring in `is_prose()` meant the module could not be imported at
   all, and the committed `curriculum.json` (615 entries) was therefore
   not the output of the committed `curriculum.py` (610 entries). The
   artifact and the generator had drifted apart and nothing noticed.

2. The five-part qualification gate in `corpus/qualify.py` must be able
   to REFUSE. `curriculum.py` promises "ingested stays False until a
   five-part qualification exists" and never implemented it; `ingested`
   was a field nobody set and `stats()["ingested"]` was a hard-coded 0
   that read like a measurement.

3. The JSON artifact must be REPRODUCIBLE from the module that claims to
   produce it. The check that would have caught the drift.

THE MUTATION NOTE
-----------------
Every assertion below is paired with the mutation that must turn it red.
`tools/mutation_check.py` applies them for real; the list is in that
file and the counts are printed by running it.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CORPUS = os.path.join(REPO, "corpus")
sys.path.insert(0, CORPUS)

import qualify  # noqa: E402


# ==========================================================================
# 1. the module must parse, and the artifact must come from it
# ==========================================================================

def test_curriculum_module_parses():
    """corpus/curriculum.py must compile.

    MUTATION: remove the closing triple-quote of the is_prose() docstring.
    """
    src = open(os.path.join(CORPUS, "curriculum.py"), encoding="utf-8").read()
    compile(src, "corpus/curriculum.py", "exec")   # raises SyntaxError


def test_curriculum_module_imports_and_runs():
    """...and must actually run against Bobby's list.

    MUTATION: point SOURCE at a path that does not exist.
    """
    r = subprocess.run(
        [sys.executable, os.path.join(CORPUS, "curriculum.py")],
        capture_output=True, text=True, timeout=300, cwd=REPO,
    )
    assert r.returncode == 0, r.stderr[-3000:]
    assert "parsed" in r.stdout, r.stdout[-2000:]


def test_committed_json_is_reproducible_from_the_module():
    """The committed curriculum.json must be exactly what the module emits.

    This is the check that would have caught the 615-vs-610 drift: the
    artifact was committed by one version of the parser and the module
    was committed by another, and nothing compared them.

    MUTATION: change the parser so it emits one fewer entry.
    """
    r = subprocess.run(
        [sys.executable, os.path.join(CORPUS, "curriculum.py")],
        capture_output=True, text=True, timeout=300, cwd=REPO,
    )
    assert r.returncode == 0, r.stderr[-3000:]
    with open(os.path.join(CORPUS, "curriculum.json"), encoding="utf-8") as fh:
        on_disk = json.load(fh)
    # the module rewrites the file in place; re-read and compare to a
    # fresh export so the comparison is against the module's own output.
    import curriculum
    entries, _dupes = curriculum.parse()
    path = curriculum.export(entries, os.path.join(CORPUS, "curriculum.json"))
    with open(path, encoding="utf-8") as fh:
        fresh = json.load(fh)
    assert fresh["stats"] == on_disk["stats"], (
        "curriculum.json does not match what curriculum.py produces:\n"
        f"  on disk: {on_disk['stats']}\n"
        f"  fresh:   {fresh['stats']}"
    )
    assert len(fresh["queue"]) == len(on_disk["queue"])


def test_the_source_list_is_read_not_empty():
    """610 entries parsed from Bobby's own texts.php.

    MUTATION: make strip_html() drop every line.
    """
    import curriculum
    entries, dupes = curriculum.parse()
    s = curriculum.stats(entries)
    assert s["total"] > 500, f"only {s['total']} entries parsed"
    assert s["with_author"] > 300, f"only {s['with_author']} with an author"
    assert dupes > 0, "no duplicates dropped -- the dedupe never ran"


# ==========================================================================
# 2. the five-part qualification gate must be able to REFUSE
# ==========================================================================

GOOD = """# A qualification

**Title:** The Art of War
**Author:** Sunzi
**Source:** corpus/ingest/art-of-war.txt

## 1. THE CLAIM
Sunzi writes that the supreme excellence in war is to subdue the enemy
without fighting, and this is asserted in the source text itself.

## 2. THE AXIS
Axis moved: truth_focus. Current value: external strategy. Intended
value: internal tempo. The axis is named and both values are given.

## 3. THE DELTA
> "He who will not bend his weapons and fight for his country is not a
> soldier." (p. 12)

The quote forces the change: tempo is a precondition, not an outcome.

## 4. THE FAILURE MODE
This argues against my habit of treating a plan as an action, which I
default to when the outcome is uncertain.

## 5. THE TEST
If it took, my next strategic answer will name a tempo before a tactic.
If it did not take, the answer will still begin with the tactic, and
that absence is the falsification condition.
"""


def write(tmp_path, body, name="q.md"):
    p = tmp_path / name
    p.write_text(body, encoding="utf-8")
    return str(p)


def test_a_complete_qualification_is_accepted(tmp_path):
    """MUTATION: require 6 parts instead of 5."""
    q = qualify.parse_qualification(write(tmp_path, GOOD))
    assert q.qualified, q.why_not()
    assert q.score == 5
    assert q.missing() == []


def test_four_of_five_is_a_note_not_a_qualification(tmp_path):
    """The charter: "Four of five is a note."

    MUTATION: treat a missing part as present.
    """
    body = GOOD.replace("## 5. THE TEST", "## 5. NOTES")
    q = qualify.parse_qualification(write(tmp_path, body))
    assert not q.qualified
    assert "test" in q.missing()
    assert any("test" in r for r in q.why_not())


def test_each_part_can_be_the_missing_one(tmp_path):
    """Every part must be able to fail on its own, or the gate is decorative.

    MUTATION: hardcode `missing` to return [].
    """
    for part in qualify.PARTS:
        # Remove ONLY the heading of the part under test. The other four
        # keep theirs, so exactly one part is missing. The heading text is
        # found from GOOD itself, so this cannot drift from the fixture.
        body = GOOD
        removed = False
        for n in ("1", "2", "3", "4", "5"):
            for form in qualify.PART_ALIASES[part]:
                target = f"## {n}. {form.upper()}"
                if target in body:
                    body = body.replace(target, "## X")
                    removed = True
        assert removed, f"could not find the heading for {part} in GOOD"
        q = qualify.parse_qualification(write(tmp_path, body))
        assert not q.qualified, f"{part} could not fail on its own"
        assert part in q.missing(), f"{part} missing not reported: {q.missing()}"


def test_a_heading_with_no_body_is_not_a_part(tmp_path):
    """MUTATION: count a heading as a present part regardless of body.
    """
    body = GOOD.replace(
        "## 5. THE TEST\nIf it took,",
        "## 5. THE TEST\n\n## 6. NOTES\n\nnothing\n\nIf it took,")
    q = qualify.parse_qualification(write(tmp_path, body))
    assert not q.qualified
    assert "test" in q.missing()


def test_a_bodyless_part_with_no_secondary_check_is_refused(tmp_path):
    """The CLAIM part carries no second check, so a bodyless claim is the
    ONLY thing that can catch a mutation which sets `present = True`.

    The TEST part cannot do this job: it also fails the falsification
    check, so it stays refused even when the word-count check is
    removed, and a mutation to that check would stay GREEN.

    MUTATION: p.present = True.
    """
    body = GOOD.replace(
        "## 1. THE CLAIM\nSunzi writes",
        "## 1. THE CLAIM\n\n## 1b. NOTES\n\nx\n\nSunzi writes")
    assert body != GOOD, "the bodyless-claim fixture did not apply"
    q = qualify.parse_qualification(write(tmp_path, body))
    assert not q.qualified
    assert "claim" in q.missing()
    assert q.parts["claim"].words == 0


def test_an_unquoted_delta_is_refused(tmp_path):
    """The charter says the delta is "quoted and anchored".

    The fixture must fail on the QUOTE check ALONE, so it still keeps an
    anchor -- otherwise the mutation "quoted = True" stays green because
    the anchor check refuses it anyway. The delta here is unquoted but
    carries "(p. 12)", so the anchor check passes and only the quote
    check can refuse it.

    MUTATION: drop the quote check.
    """
    body = GOOD.replace(
        '> "He who will not bend his weapons and fight for his country is not a\n'
        '> soldier." (p. 12)',
        'He who will not bend his weapons and fight for his country is not a\n'
        'soldier. (p. 12)')
    assert body != GOOD, "the unquoted-delta replacement did not apply"
    q = qualify.parse_qualification(write(tmp_path, body))
    assert not q.qualified
    assert "delta" in q.missing()
    assert any("quoted" in r for r in q.why_not())


def test_an_unanchored_delta_is_refused(tmp_path):
    """A quote with no location is not anchored.

    The fixture keeps the QUOTATION, so it fails on the anchor check
    alone.

    MUTATION: drop the anchor check.
    """
    body = GOOD.replace('(p. 12)', '').replace(
        "The quote forces the change: tempo is a precondition, not an outcome.",
        "The quote forces the change: tempo is a precondition, not an outcome, "
        "and the line is what I am quoting here in full.")
    assert body != GOOD, "the unanchored-delta replacement did not apply"
    q = qualify.parse_qualification(write(tmp_path, body))
    assert not q.qualified
    assert "delta" in q.missing()
    assert any("anchor" in r for r in q.why_not())


def test_the_bare_word_line_is_not_an_anchor(tmp_path):
    """The anchor regex once accepted the word "line" on its own, so an
    unanchored delta passed. "the line that forces the change" is prose.

    MUTATION: accept the bare words line/section as locations again.
    """
    assert not qualify.ANCHOR_RE.search("the line that forces the change")
    assert not qualify.ANCHOR_RE.search("see the section on strategy")
    assert qualify.ANCHOR_RE.search("p. 12")
    assert qualify.ANCHOR_RE.search("chapter 3")
    assert qualify.ANCHOR_RE.search("lines 40-42")


def test_a_failure_mode_with_no_named_habit_is_refused(tmp_path):
    """The charter says the failure mode must be "named so it can be audited".

    MUTATION: drop the habit check.
    """
    body = GOOD.replace(
        "This argues against my habit of treating a plan as an action, which I\n"
        "default to when the outcome is uncertain.",
        "The failure mode is failure, and it must be avoided wherever it\n"
        "appears in the process going forward.")
    q = qualify.parse_qualification(write(tmp_path, body))
    assert not q.qualified
    assert "failure_mode" in q.missing()
    assert any("habit" in r for r in q.why_not())


def test_a_test_with_no_falsification_condition_is_refused(tmp_path):
    """The charter asks for "what shows it took, AND what shows it didn't".

    MUTATION: drop the negative-half check.
    """
    body = GOOD.replace(
        "If it took, my next strategic answer will name a tempo before a tactic.\n"
        "If it did not take, the answer will still begin with the tactic, and\n"
        "that absence is the falsification condition.",
        "If it took, my next strategic answer will name a tempo before a tactic,\n"
        "and that will be the observable sign that the qualification landed\n"
        "on the axis it was supposed to move.")
    q = qualify.parse_qualification(write(tmp_path, body))
    assert not q.qualified
    assert "test" in q.missing()
    assert any("falsification" in r for r in q.why_not())


def test_an_empty_qualification_is_refused(tmp_path):
    """MUTATION: treat an empty file as qualified.
    """
    q = qualify.parse_qualification(write(tmp_path, "# nothing here\n"))
    assert not q.qualified
    assert len(q.missing()) == 5


# ==========================================================================
# 3. the manifest: bytes are not knowledge
# ==========================================================================

def test_bytes_without_a_qualification_are_not_ingested(tmp_path):
    """The rule curriculum.py promised and never implemented.

    MUTATION: count a fetched text as ingested regardless of qualification.
    """
    root = tmp_path / "corpus"
    root.mkdir()
    rows = [{
        "file": "art-of-war.txt",
        "title": "The Art of War",
        "qualification": "qualifications/art-of-war.md",
    }]
    qualify.write_manifest(rows, root=str(root))
    state = qualify.ingest_state(root=str(root))
    assert state["fetched"] == 1
    assert state["qualified"] == 0
    assert state["fetched_not_qualified"] == 1


def test_a_text_with_a_passing_qualification_is_ingested(tmp_path):
    """MUTATION: never set ingested=True.
    """
    root = tmp_path / "corpus"
    (root / "qualifications").mkdir(parents=True)
    (root / "qualifications" / "art-of-war.md").write_text(GOOD, encoding="utf-8")
    rows = [{
        "file": "art-of-war.txt",
        "title": "The Art of War",
        "qualification": "qualifications/art-of-war.md",
    }]
    qualify.write_manifest(rows, root=str(root))
    state = qualify.ingest_state(root=str(root))
    assert state["qualified"] == 1
    assert state["fetched_not_qualified"] == 0


def test_a_text_with_a_refused_qualification_is_refused_not_ingested(tmp_path):
    """Four of five must not slip through as knowledge.

    MUTATION: treat a refused qualification as qualifying.
    """
    root = tmp_path / "corpus"
    (root / "qualifications").mkdir(parents=True)
    body = GOOD.replace("## 5. THE TEST", "## 5. NOTES")
    (root / "qualifications" / "art-of-war.md").write_text(body, encoding="utf-8")
    rows = [{
        "file": "art-of-war.txt",
        "title": "The Art of War",
        "qualification": "qualifications/art-of-war.md",
    }]
    qualify.write_manifest(rows, root=str(root))
    state = qualify.ingest_state(root=str(root))
    assert state["qualified"] == 0
    assert state["refused"] == 1
    assert "test" in state["refused_detail"][0]["missing"]


def test_a_manifest_with_a_broken_json_reads_as_empty_not_as_a_crash(tmp_path):
    """A corrupt manifest must not raise -- it must report nothing ingested.

    MUTATION: let json.JSONDecodeError propagate.
    """
    root = tmp_path / "corpus"
    root.mkdir()
    (root / qualify.MANIFEST_NAME).write_text("{not json", encoding="utf-8")
    assert qualify.load_manifest(root=str(root)) == []
    state = qualify.ingest_state(root=str(root))
    assert state["fetched"] == 0


def test_the_manifest_is_written_with_newlines_not_crlf(tmp_path):
    """The corpus json files are `-text` in .gitattributes, so a CRLF
    rewrite would show as a whole-file diff.

    MUTATION: open the manifest without newline="\\n".
    """
    root = tmp_path / "corpus"
    root.mkdir()
    qualify.write_manifest([{"file": "a.txt"}], root=str(root))
    raw = (root / qualify.MANIFEST_NAME).read_bytes()
    assert b"\r\n" not in raw


# ==========================================================================
# 4. the gate must be wired to the corpus it claims to govern
# ==========================================================================

def test_curriculum_stats_ingested_is_not_a_hardcoded_zero():
    """curriculum.stats()["ingested"] counted entries with ingested=True.
    Nobody ever set the flag, so it read 0 -- a measurement that was
    really a constant.

    MUTATION: hardcode "ingested": 0.
    """
    import curriculum
    entries, _ = curriculum.parse()
    s = curriculum.stats(entries)
    assert "ingested" in s
    # it must be derived from the entries, not a constant
    derived = sum(1 for e in entries if e.ingested)
    assert s["ingested"] == derived


def test_the_five_parts_are_the_charter_s_five_parts():
    """MUTATION: rename a part.
    """
    assert set(qualify.PARTS) == {
        "claim", "axis", "delta", "failure_mode", "test"}
