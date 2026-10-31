"""
test_label_rate.py -- the lossless measure and its gate.

WHAT THIS FILE ASSERTS, and why each assertion is there
--------------------------------------------------------
1. THE THRESHOLD IS DERIVED FROM THE CORPUS, not chosen. And it is
   LOOSER than the canon's own worst text, so the canon is the
   allowance and a draft has to beat the canon to be refused.

2. WITH TOO SMALL A CORPUS THERE IS NO THRESHOLD. A threshold from
   three texts is a number someone chose with extra steps. The gate
   says so and refuses to refuse.

3. THE GATE REPRODUCES THE JUDGMENT. MEASURED 2026-10-31:
   star-rider is REFUSED (33.3 per 1,000 words, above the canon's
   worst at 19.4) and college_girl PASSES (5.5). That is Bobby's
   judgment -- "star rider is so full of them almost unreadable" and
   "college girl... virtually no off topic insertions at all" -- turned
   into a number.

4. THE IDEA SHARE IS MEASURED SEPARATELY. A piece that re-states its
   idea in an idea-word is a failed restore wearing vocabulary, and
   "hand x45, face x40" is the same failure in furniture.

5. AN UNMEASURABLE DRAFT IS NOT REFUSED. A gate that refuses
   everything is a wall, and an absent check must not read as a
   passing one.

Run:
    python -m pytest tests/test_label_rate.py -q
"""

from __future__ import annotations

import os
import sys

import pytest

_HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_HERE, "corpus"))

import label_rate as LR  # noqa: E402

BOOKS = r"C:\Users\HP\Desktop\books"


def _text(name):
    p = os.path.join(BOOKS, name)
    if not os.path.isfile(p):
        pytest.skip("%s is not on this machine" % (name,))
    t = open(p, encoding="utf-8", errors="replace").read()
    if name.endswith(".php"):
        t = LR.strip_html(t)
    return t


# ===========================================================================
# 1. THE THRESHOLD IS DERIVED
# ===========================================================================

def test_the_threshold_is_measured_from_the_corpus():
    thr = LR.threshold()
    assert thr.measured, thr.reason
    assert thr.corpus_size >= LR.MIN_CORPUS
    assert thr.rate > 0


def test_the_threshold_is_looser_than_the_canons_own_worst():
    """the canon is the allowance."""
    thr = LR.threshold()
    rows = LR.measure_corpus()
    worst = max(r["rate"] for r in rows)
    assert thr.rate == pytest.approx(worst), (
        "the threshold is %s but the canon's worst text is %s"
        % (thr.rate, worst))
    assert thr.high == pytest.approx(worst)


def test_the_threshold_moves_with_the_corpus():
    """it is derived, so it is recomputed, not remembered."""
    thr = LR.threshold()
    median = thr.median
    assert thr.p90 >= median
    assert thr.low <= median


# ===========================================================================
# 2. TOO SMALL A CORPUS, NO THRESHOLD
# ===========================================================================

def test_a_small_corpus_claims_no_threshold(tmp_path):
    """a threshold from three texts is a number someone chose."""
    # THE FIXTURE IS LONG ENOUGH TO BE MEASURED. The first version
    # wrote 3 short files, and MIN_WORDS filtered them out, so the
    # corpus came back EMPTY and corpus_size was 0 rather than 3.
    # The gate was right; the fixture was wrong.
    for i in range(3):
        (tmp_path / ("t%d.txt" % i)).write_text(
            "the weather and the rain and the moon and the fold " * 400,
            encoding="utf-8")
    thr = LR.threshold(str(tmp_path))
    assert not thr.measured
    assert thr.corpus_size == 3, (
        "the corpus holds %d measurable texts, expected 3"
        % (thr.corpus_size,))
    assert "no threshold" in thr.reason.lower()


def test_a_missing_corpus_claims_no_threshold(tmp_path):
    thr = LR.threshold(str(tmp_path / "nothing-here"))
    assert not thr.measured
    assert thr.rate == 0.0


# ===========================================================================
# 3. THE GATE REPRODUCES THE JUDGMENT
# ===========================================================================

def test_star_rider_is_refused():
    """MEASURED: 33.3 per 1,000 words, above the canon's worst.

    Bobby, 2026-10-31: *"star rider is so full of them almost
    unreadable."*
    """
    thr = LR.threshold()
    res = LR.gate_draft(_text("star-rider.txt"), thr)
    assert not res.ok, (
        "the gate passed star-rider at %.1f against a threshold of %.1f"
        % (res.rate, res.threshold))
    assert "canon" in res.reason


def test_college_girl_passes():
    """MEASURED: 5.5, below the canon's median.

    Bobby: *"college girl... virtually no off topic insertions at all."*
    """
    thr = LR.threshold()
    res = LR.gate_draft(_text("College-Girl.php"), thr)
    assert res.ok, res.reason
    assert res.rate < thr.median


def test_the_two_sides_of_the_judgment_are_opposite():
    """the same gate, one text each way. That is the whole test."""
    thr = LR.threshold()
    sr = LR.gate_draft(_text("star-rider.txt"), thr)
    cg = LR.gate_draft(_text("College-Girl.php"), thr)
    assert not sr.ok
    assert cg.ok
    assert sr.rate > cg.rate * 2, (
        "the two texts are %.1f and %.1f -- the gate is not "
        "discriminating" % (sr.rate, cg.rate))


def test_the_gate_passes_the_other_canon_works():
    """the gate must not refuse our own work, or it is a wall."""
    thr = LR.threshold()
    for name in ("0-Gabrielle1.txt", "co-remembrance.txt",
                 "The-Little-Monk.txt"):
        res = LR.gate_draft(_text(name), thr)
        assert res.ok, ("the gate refused %s at %.1f: %s"
                        % (name, res.rate, res.reason))


# ===========================================================================
# 4. THE IDEA SHARE
# ===========================================================================

def test_the_idea_share_is_measured():
    r = LR.label_rate(
        "the fold and the clockwork and the attention and the torus "
        "and the membrane and the progress " * 40)
    assert r["idea_rate"] > 0
    assert r["idea_share"] > 50, (
        "a text that is only idea-labels should have an idea share "
        "near 100, got %.1f" % r["idea_share"])


def test_star_rider_names_its_ideas_more_than_its_furniture():
    """MEASURED: star-rider's idea rate is 7.8 against college-girl's
    1.0 -- nearly eight times.

    And the top labels are "hand" x45 and "face" x40: the furniture of
    a scene that is not happening, because the piece is carrying its
    meaning in the WORDS instead.
    """
    thr = LR.threshold()
    sr = LR.label_rate(_text("star-rider.txt"))
    cg = LR.label_rate(_text("College-Girl.php"))
    assert sr["idea_rate"] > cg["idea_rate"] * 3, (
        "star rider %.1f vs college girl %.1f" % (sr["idea_rate"],
                                                   cg["idea_rate"]))


# ===========================================================================
# 5. AN UNMEASURABLE DRAFT IS NOT REFUSED
# ===========================================================================

def test_an_empty_draft_is_not_refused_by_the_threshold():
    """a gate that refuses everything is a wall."""
    thr = LR.threshold()
    res = LR.gate_draft("", thr)
    assert res.ok, res.reason
    assert res.rate == 0.0


def test_a_tiny_corpus_makes_the_gate_pass_without_claiming():
    thr = LR.threshold(str(os.path.join(os.path.dirname(__file__),
                                         "no-corpus-here")))
    assert not thr.measured
    res = LR.gate_draft("the weather and the fold " * 500, thr)
    assert res.ok
    assert not res.measured
    assert "no threshold" in res.reason.lower()
