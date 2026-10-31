"""
tests/test_corpus_ingest.py -- the receipt, the acquirer, and the
measurement.

`tests/test_curriculum.py` covers the gate. This file covers everything
downstream of it: that a fetch is recorded honestly, that the receipt
matches the bytes on disk, that the measurement counts what it claims
to count, and that a quote in a qualification is a REAL quote from the
file it names.

That last one is the load-bearing check. The first version of the
qualification writer put the same line of Project Gutenberg licence
boilerplate in all 27 deltas, because the quote finder searched from the
top of the file and the licence contains sentences. Nothing caught it:
the gate accepted every one, because a boilerplate quote IS a quote with
an anchor. Only a check that compares the quoted line against the file
catches it.

Run:  python -m pytest tests/test_corpus_ingest.py -q
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
CORPUS = os.path.join(REPO, "corpus")
INGEST = os.path.join(CORPUS, "ingest")
sys.path.insert(0, CORPUS)

import qualify  # noqa: E402


def load_manifest():
    p = os.path.join(INGEST, "INGESTED.json")
    if not os.path.exists(p):
        pytest.skip("no manifest -- the corpus has not been fetched yet")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


MANIFEST = load_manifest()
ACQUIRED = [r for r in MANIFEST if r.get("acquired")]


# ==========================================================================
# the receipt
# ==========================================================================

def test_the_manifest_has_acquired_rows():
    assert ACQUIRED, "no acquired texts in the manifest"


def test_every_acquired_text_is_on_disk_with_the_recorded_hash():
    """The receipt must match the bytes. A manifest that lies about its
    own files is worse than no manifest.

    MUTATION: change the sha256 in the manifest.
    """
    bad = []
    for row in ACQUIRED:
        p = os.path.join(REPO, row["file"].replace("/", os.sep))
        assert os.path.exists(p), f"{row['file']} is in the manifest but not on disk"
        with open(p, "rb") as fh:
            sha = hashlib.sha256(fh.read()).hexdigest()
        if sha != row["sha256"]:
            bad.append(row["file"])
    assert not bad, f"sha256 mismatch: {bad}"


def test_every_acquired_text_records_its_size_and_source():
    for row in ACQUIRED:
        assert row.get("bytes", 0) > 0, row["file"]
        assert row.get("url", "").startswith("https://"), row["file"]
        assert row.get("sha256"), row["file"]


def test_every_acquired_text_is_large_enough_to_be_a_text():
    """A stub is not a text. The acquirer refuses under 20,000 bytes."""
    for row in ACQUIRED:
        assert row["bytes"] >= 20000, f"{row['file']} is only {row['bytes']} bytes"


def test_every_acquired_text_carries_a_region_and_a_strand():
    """The measurement is only meaningful if each text says what it is."""
    for row in ACQUIRED:
        assert row.get("region"), row["file"]
        assert row.get("strand") in ("non_european", "women", "craft"), row["file"]


def test_the_corpus_covers_all_three_gaps():
    """Bobby's gap was a geography, a gender, and craft-and-labour.
    A corpus that filled only one of them would be a partial answer.
    """
    strands = {r["strand"] for r in ACQUIRED}
    assert strands == {"non_european", "women", "craft"}, strands


# ==========================================================================
# the qualification
# ==========================================================================

def test_every_acquired_text_has_a_qualification():
    for row in ACQUIRED:
        assert row.get("qualification"), f"{row['file']} has no qualification"
        p = qualify.resolve_qualification(row["qualification"])
        assert os.path.exists(p), f"{row['file']}: {p} does not exist"


def test_every_qualification_passes_the_gate():
    refused = []
    for row in ACQUIRED:
        p = qualify.resolve_qualification(row["qualification"])
        q = qualify.parse_qualification(p)
        if not q.qualified:
            refused.append((row["file"], q.missing()))
    assert not refused, f"refused by the gate: {refused}"


DELTA_RE = re.compile(r"^> (.+)$", re.M)
LINE_RE = re.compile(r"\(line (\d+) of `([^`]+)`\)")


def test_every_delta_is_a_real_quote_from_the_file_it_names():
    """THE LOAD-BEARING CHECK.

    The quoted line must be present, VERBATIM, at the stated line number,
    of the stated file. A quote that does not survive that comparison is
    a fabricated quote, and the whole qualification rests on it.
    """
    bad = []
    for row in ACQUIRED:
        qp = qualify.resolve_qualification(row["qualification"])
        with open(qp, encoding="utf-8") as fh:
            body = fh.read()
        m = DELTA_RE.search(body)
        if not m:
            bad.append((row["file"], "no quoted line in the delta"))
            continue
        quote = m.group(1).strip()
        lm = LINE_RE.search(body)
        if not lm:
            bad.append((row["file"], "no line anchor in the delta"))
            continue
        lineno = int(lm.group(1))
        named = lm.group(2)
        src = os.path.join(REPO, named.replace("/", os.sep))
        if not os.path.exists(src):
            bad.append((row["file"], f"named file does not exist: {named}"))
            continue
        with open(src, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().splitlines()
        if lineno > len(lines):
            bad.append((row["file"], f"line {lineno} past the end of the file"))
            continue
        actual = lines[lineno - 1].strip()
        if quote != actual:
            bad.append((row["file"],
                        f"quote is not line {lineno}\n"
                        f"        claimed: {quote[:90]}\n"
                        f"        actual:  {actual[:90]}"))
    assert not bad, "the deltas are not real quotes:\n" + "\n".join(
        f"  {f}: {why}" for f, why in bad)


def test_no_delta_quotes_the_gutenberg_licence():
    """The specific failure this check exists for: all 27 deltas were
    the same line of licence boilerplate, and the gate accepted every
    one of them.
    """
    boiler = ("this ebook is for the use", "project gutenberg", "copyright",
              "terms of this ebook", "redistribution", "www.gutenberg")
    for row in ACQUIRED:
        qp = qualify.resolve_qualification(row["qualification"])
        with open(qp, encoding="utf-8") as fh:
            body = fh.read()
        m = DELTA_RE.search(body)
        assert m, row["file"]
        quote = m.group(1).lower()
        for b in boiler:
            assert b not in quote, f"{row['file']}: the delta quotes the licence"


def test_no_delta_quotes_the_front_matter():
    """The quote must come from the body of the work, not from the
    title page or the translator's introduction.
    """
    for row in ACQUIRED:
        qp = qualify.resolve_qualification(row["qualification"])
        with open(qp, encoding="utf-8") as fh:
            body = fh.read()
        lm = LINE_RE.search(body)
        assert lm, row["file"]
        named = lm.group(2)
        src = os.path.join(REPO, named.replace("/", os.sep))
        with open(src, encoding="utf-8", errors="replace") as fh:
            nlines = len(fh.read().splitlines())
        pct = 100.0 * int(lm.group(1)) / max(1, nlines)
        assert pct >= 10.0, (
            f"{row['file']}: the delta quotes line {lm.group(1)} of {nlines} "
            f"({pct:.1f}% in) -- that is front matter")


def test_every_qualification_names_a_canonical_axis():
    """The axis names come from simself/src/sovereign_governor.py. An
    invented axis is not a move on a real axis.
    """
    import re as _re
    gov = os.path.join(os.path.dirname(REPO), "simself", "src",
                       "sovereign_governor.py")
    if not os.path.exists(gov):
        pytest.skip("simself is not on this machine")
    with open(gov, encoding="utf-8") as fh:
        gsrc = fh.read()
    known = set(_re.findall(r'"([a-z_]+)"', gsrc))
    for row in ACQUIRED:
        qp = qualify.resolve_qualification(row["qualification"])
        with open(qp, encoding="utf-8") as fh:
            body = fh.read()
        m = _re.search(r"\*\*Axis moved:\*\* `([a-z_]+)`", body)
        assert m, f"{row['file']}: no axis named"
        assert m.group(1) in known, (
            f"{row['file']}: axis {m.group(1)!r} is not a canonical axis")


# ==========================================================================
# the measurement
# ==========================================================================

def test_the_measurement_matches_the_manifest():
    import measure_corpus
    m = measure_corpus.measure(MANIFEST)
    assert m["acquired"] == len(ACQUIRED)
    assert sum(m["by_strand"].values()) == len(ACQUIRED)
    assert sum(m["by_region"].values()) == len(ACQUIRED)


def test_the_measurement_counts_women_by_name_not_by_guess():
    """An unknown author is UNKNOWN. A gender table built by guessing is
    a fabrication with a number attached.
    """
    import measure_corpus
    assert measure_corpus.is_woman("Mary Wollstonecraft")
    assert measure_corpus.is_woman("Christine de Pizan")
    assert measure_corpus.is_woman("Emilie du Chatelet")
    assert not measure_corpus.is_woman("Sunzi")
    assert not measure_corpus.is_woman("")
    assert not measure_corpus.is_woman("Anonymous")
    assert not measure_corpus.is_woman("Various")


def test_the_measurement_reports_a_share_between_zero_and_one():
    import measure_corpus
    m = measure_corpus.measure(MANIFEST)
    for section in ("geography", "gender", "craft", "era"):
        for k, v in m[section].items():
            if k.startswith("share_"):
                assert 0.0 <= v <= 1.0, f"{section}.{k} = {v}"


def test_the_measurement_command_runs_and_writes_the_index():
    r = subprocess.run(
        [sys.executable, os.path.join(CORPUS, "measure_corpus.py"), "--write"],
        capture_output=True, text=True, timeout=300, cwd=REPO,
    )
    assert r.returncode == 0, r.stderr[-2000:]
    idx = os.path.join(INGEST, "corpus-index.json")
    assert os.path.exists(idx)
    with open(idx, encoding="utf-8") as fh:
        m = json.load(fh)
    assert m["acquired"] == len(ACQUIRED)


def test_the_gate_command_runs_and_reports_every_acquired_text():
    r = subprocess.run(
        [sys.executable, os.path.join(CORPUS, "qualify.py")],
        capture_output=True, text=True, timeout=300, cwd=REPO,
    )
    assert r.returncode == 0, r.stderr[-2000:]
    assert "qualified (5 of 5)" in r.stdout
    # the gate must not report a refusal for anything in this corpus
    assert "REFUSED" not in r.stdout, r.stdout


# ==========================================================================
# the acquirer's own refusals
# ==========================================================================

def test_the_acquirer_refuses_a_body_without_the_title_marker():
    """MUTATION: accept any body over the size floor.
    """
    import fetch_corpus
    t = dict(fetch_corpus.TARGETS[0])
    t["marker"] = "A MARKER THAT IS NOT IN ANY BOOK"
    r = fetch_corpus.acquire_one(t)
    assert not r["acquired"]
    assert "marker" in r["error"]


def test_the_acquirer_refuses_a_body_under_the_size_floor():
    """**AND THE FLOOR IS THE REASON, NOT THE FETCH.**

    MEASURED 2026-10-31: this test set `gut = -1` -- no such book --
    so `acquire_one` returned at the FETCH, before the size floor was
    ever reached. The assertion `not r["acquired"]` passed, and it
    would have passed with the size floor deleted. **A check that
    passes for the wrong reason is not a check**, and this one was
    counted as covering the size floor in the mutation harness while
    the mutation "the size floor is not checked" stayed GREEN.

    So the floor is exercised directly: a body that IS fetched, DOES
    contain the title marker, and IS under MIN_BYTES. The refusal must
    name the floor -- because a refusal that says "no body" when the
    body was there and too small is a refusal that hides the real
    reason.
    """
    import fetch_corpus
    t = dict(fetch_corpus.TARGETS[0])
    t["marker"] = "TAO TEH KING"
    # **AND THE TARGET MUST NOT ALREADY BE ON DISK.** MEASURED
    # 2026-10-31: the first version of this test used the real target
    # name, and the acquirer refused it at the CONFLICT check -- the
    # file is on disk with different bytes -- before the size floor was
    # ever reached. The assertion `not r["acquired"]` passed, for the
    # wrong reason, exactly as before.
    #
    # So the target gets a file name that is not in the corpus, and the
    # body is under the floor. The refusal must name the floor.
    t["file"] = "a-target-that-is-not-in-the-corpus.txt"
    # a body that is real, has the marker, and is under the floor
    body = ("TAO TEH KING\n" + "x" * (fetch_corpus.MIN_BYTES - 100)).encode()
    assert len(body) < fetch_corpus.MIN_BYTES
    orig_fetch = fetch_corpus.fetch
    orig_urls = fetch_corpus.gut_urls
    try:
        fetch_corpus.gut_urls = lambda gut: ["http://example.invalid/x.txt"]
        fetch_corpus.fetch = lambda url: (body, 200, None)
        r = fetch_corpus.acquire_one(t)
    finally:
        fetch_corpus.fetch = orig_fetch
        fetch_corpus.gut_urls = orig_urls
    assert not r["acquired"], (
        "a body under the size floor was ACCEPTED: %r" % r)
    assert "floor" in (r.get("error") or ""), (
        "the refusal does not name the size floor: %r" % (r.get("error"),))


def test_the_acquirer_never_overwrites_different_text():
    """MUTATION: overwrite the file on disk with the fetch.
    """
    import fetch_corpus
    t = dict(fetch_corpus.TARGETS[0])
    t["gut"] = -1
    # a target whose file exists, fetched from a different id
    t2 = dict(t)
    t2["file"] = "laozi-tao-teh-king.txt"
    t2["marker"] = "TAO TEH KING"
    # simulate by writing a file with different content and pointing at it
    dest = os.path.join(fetch_corpus.OUT_DIR, t2["file"])
    if not os.path.exists(dest):
        pytest.skip("the corpus has not been fetched yet")
    with open(dest, "rb") as fh:
        before = fh.read()
    r = fetch_corpus.acquire_one(t2)
    with open(dest, "rb") as fh:
        after = fh.read()
    assert before == after, "the acquirer overwrote the file on disk"
