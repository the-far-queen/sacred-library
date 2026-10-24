"""
test_inv.py — E1..E10 gate tests for the engineering invention gate.

The load-bearing one is E5: you cannot build before you conceive. That
is the whole point of keeping conceived and built dates separate — a
filing receipt alone tells you nothing about how much clock was left.

COLLECTION FIX 2026-10-24. These functions were named t_E1_* ... and pytest
collected ZERO of them — the suite read as "no tests" rather than "10
passing checks". They are now named test_E1_* .. test_E10_*, keeping the
same IDs, and the count is verifiable: pytest must report 10 collected.

Run:  python tests/test_inv.py
"""

from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "tools"))

from inv import (  # noqa: E402
    Invention, PriorArt, DISCIPLINES, STATUSES, OFFICES, LICENSES,
    gate, gate_license_never_upgraded,
)

DISK = list(DISCIPLINES)


def good_inv(**over):
    base = dict(
        title="Single-axis resonator mount",
        discipline="acoustic",
        status="built",
        date_conceived="2026-09-01",
        date_built="2026-10-01",
        summary="mounts a 137 Hz resonator rigidly without parasitic modes",
        test_case="measured first mode = 137 Hz +/- 0.5",
    )
    base.update(over)
    return Invention(**base)


def test_E1_repro_id():
    a = good_inv()
    b = good_inv()
    assert a.invention_id() == b.invention_id()
    c = good_inv(title="Something else")
    assert a.invention_id() != c.invention_id()
    print("E1: ok (deterministic invention id)")


def test_E2_title_required():
    v = gate(good_inv(title="  "), DISK)
    assert not v.allow
    assert "no_title" in v.reasons
    print("E2: ok (title required)")


def test_E3_discipline_valid():
    v = gate(good_inv(discipline="aether-manufacture"), DISK)
    assert not v.allow
    assert any(x.startswith("unknown_discipline") for x in v.reasons)
    print(f"E3: ok (fake discipline refused: {v.reasons})")


def test_E4_dates_required():
    v = gate(good_inv(date_conceived="", date_built=""), DISK)
    assert not v.allow
    assert "no_date_conceived" in v.reasons
    assert "no_date_built" in v.reasons
    v2 = gate(good_inv(date_conceived="autumn 2026"), DISK)
    assert not v2.allow
    assert any(x.startswith("bad_date_conceived") for x in v2.reasons)
    print(f"E4: ok (dates required: {v2.reasons})")


def test_E5_cannot_build_before_conceive():
    """THE test."""
    v = gate(good_inv(date_conceived="2026-10-01", date_built="2026-09-01"), DISK)
    assert not v.allow, "built-before-conceived was ALLOWED"
    assert "built_before_conceived" in v.reasons, v.reasons
    print("E5: ok (build date cannot precede conception)")


def test_E6_test_case_required_once_built():
    """past 'prototyped', you must say how we know."""
    v = gate(good_inv(test_case=""), DISK)
    assert not v.allow
    assert "no_test_case" in v.reasons, v.reasons
    ok = gate(good_inv(status="conceived", test_case=""), DISK)
    assert ok.allow, f"conception wrongly required a test: {ok.reasons}"
    print("E6: ok (test case required once built)")


def test_E7_filing_needs_office_and_url():
    v = gate(good_inv(status="filed", filing_office="", filing_url=""), DISK)
    assert not v.allow
    assert "no_filing_office" in v.reasons
    assert "no_filing_url" in v.reasons
    v2 = gate(good_inv(status="filed", filing_office="moon-patent-office",
                       filing_url="https://x.example/1"), DISK)
    assert not v2.allow
    assert any(x.startswith("unknown_office") for x in v2.reasons)
    print(f"E7: ok (filing requires a real office: {v2.reasons})")


def test_E8_status_valid():
    for s in STATUSES:
        v = gate(good_inv(status=s), DISK)
        assert "unknown_status" not in v.reasons, f"{s} rejected"
    v = gate(good_inv(status="nearly-done"), DISK)
    assert not v.allow
    print("E8: ok (status on the list)")


def test_E9_license_never_upgraded():
    v = gate_license_never_upgraded("public-domain", "cc-by-nc-sa")
    assert not v.allow, "NC-SA upgraded to public-domain"
    # 'ours' is our own material; narrowing to cc-by-nc-sa is allowed
    v2 = gate_license_never_upgraded("cc-by-nc-sa", "ours")
    assert v2.allow
    print(f"E9: ok (no license upgrade: {v.reasons})")


def test_E10_taxonomy_complete():
    assert len(DISCIPLINES) == len(set(DISCIPLINES))
    for d in DISCIPLINES:
        assert d in DISK, f"{d} declared but not scaffolded"
    for core in ("mechanical", "electrical", "biomedical", "computing"):
        assert core in DISCIPLINES
    print(f"E10: ok ({len(DISCIPLINES)} disciplines declared and scaffolded)")


def main():
    test_E1_repro_id()
    test_E2_title_required()
    test_E3_discipline_valid()
    test_E4_dates_required()
    test_E5_cannot_build_before_conceive()
    test_E6_test_case_required_once_built()
    test_E7_filing_needs_office_and_url()
    test_E8_status_valid()
    test_E9_license_never_upgraded()
    test_E10_taxonomy_complete()
    print("\nALL ENGINEERING GATE TESTS PASS (E1..E10)")


if __name__ == "__main__":
    main()
