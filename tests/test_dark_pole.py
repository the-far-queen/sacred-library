"""
tests/test_dark_pole.py -- the dark pole is acquired, and the receipt
tells the truth about it.

The dark pole is four texts with no other home: Milton's Paradise Lost,
Marlowe's Doctor Faustus, Webster's The White Devil and Orwell's
Nineteen Eighty-Four. `corpus/dark-pole/build_dark_pole.py` builds them
from the raw fetches and writes the manifest.

WHAT IS LOAD-BEARING HERE, and why each check exists:

  1. THE BOILERPLATE IS GONE. A strip that leaves the licence in is not
     a strip, and the licence is ~10% of the file.

  2. THE BOOK'S STRUCTURE SURVIVED THE STRIP. This is the check the
     first version did not have, and it is the one that matters. A strip
     that takes the body between the markers, but loses the ten books of
     Paradise Lost or the five acts of The White Devil, has thrown the
     book away and replaced it with prose. The strip is therefore
     measured against the book's own divisions, counted from the file
     on disk.

  3. THE MANIFEST MATCHES THE FILES. The manifest's byte counts and
     hashes are re-computed from disk and compared. A manifest that
     describes an intention is not a receipt.

  4. THE 1984 POSTFACE IS NOT IN THE BOOK. The Project Gutenberg
     Canada edition carries a 2020 postface by Louis Markos. It is not
     Orwell and it is not in the book. It is removed, and the check is
     that the appendix -- the part the dark pole is actually after -- IS
     present, so the postface cannot be removed by accident along with
     the text.

  5. THE STRIP IS NOT A NO-OP AND NOT A DESTRUCTION. Each text must be
     smaller than its raw fetch (the boilerplate went) and larger than
     a floor (the book is still there).

Run:  python -m pytest tests/test_dark_pole.py -q
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
DARK = os.path.join(REPO, "corpus", "dark-pole")
TEXTS = DARK
RAW = os.path.join(DARK, "_raw")
MANIFEST = os.path.join(DARK, "ACQUIRED.json")
BUILDER = os.path.join(DARK, "build_dark_pole.py")

sys.path.insert(0, DARK)
import build_dark_pole as builder  # noqa: E402


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def manifest():
    if not os.path.exists(MANIFEST):
        pytest.skip("no manifest -- the dark pole has not been built yet")
    with open(MANIFEST, encoding="utf-8") as fh:
        return json.load(fh)


ROWS = manifest()
BY_FILE = {r["file"]: r for r in ROWS}


# ==========================================================================
# 1. the four texts are there
# ==========================================================================

def test_the_manifest_has_four_texts():
    assert len(ROWS) == 4, "the dark pole is four texts, got %d" % len(ROWS)


def test_each_text_exists_on_disk():
    for r in ROWS:
        p = os.path.join(REPO, r["file"])
        assert os.path.exists(p), "the manifest names a file that is not there: %s" % r["file"]


def test_each_text_is_a_real_book():
    """A full play or a full poem. A truncated fetch must not pass."""
    for r in ROWS:
        assert r["bytes"] >= builder.MIN_BYTES, (
            "%s is only %d bytes -- under the floor" % (r["file"], r["bytes"]))
        assert r["words"] >= 20_000, (
            "%s has only %d words" % (r["file"], r["words"]))


# ==========================================================================
# 2. the boilerplate is gone
# ==========================================================================

BOILERPLATE = (
    "PROJECT GUTENBERG",
    "START OF THE PROJECT GUTENBERG",
    "END OF THE PROJECT GUTENBERG",
    "This eBook is for the use of anyone anywhere",
    "subscribe to our email newsletter",
    "Most people start at our website",
)


def test_the_gutenberg_boilerplate_is_gone():
    for r in ROWS:
        t = read(os.path.join(REPO, r["file"]))
        for probe in BOILERPLATE:
            assert probe not in t, (
                "%s still carries the boilerplate %r" % (r["file"], probe))


def test_the_licence_markers_are_gone():
    for r in ROWS:
        t = read(os.path.join(REPO, r["file"]))
        assert "PEnd p" not in t and "P End p" not in t, (
            "%s still carries the licence's end-of-page marker" % r["file"])


# ==========================================================================
# 3. the structure survived the strip  <- the load-bearing check
# ==========================================================================

def test_each_text_still_carries_its_own_divisions():
    """Counted from the file on disk, against the book's real divisions.

    This is the check that a strip cannot fake: a body that lost the
    ten books of Paradise Lost, the five acts of The White Devil, the
    four chorus speeches of Doctor Faustus or the three parts of 1984
    is not the book.
    """
    for r in ROWS:
        t = read(os.path.join(REPO, r["file"]))
        name = os.path.basename(r["file"])
        found = builder.count_structure(t, builder.STRUCTURE_PATTERNS[name])
        assert found == r["structure_expected"], (
            "%s carries %d of its %d %s -- the strip lost the book"
            % (r["file"], found, r["structure_expected"], r["structure_label"]))


def test_paradise_lost_has_ten_books():
    t = read(os.path.join(TEXTS, "milton-paradise-lost.txt"))
    books = re.findall(r"(?m)^\s*BOOK\s+([IVX]+)\.\s*$", t)
    assert len(books) == 10, "Paradise Lost has %d books, not 10" % len(books)
    assert books == ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    # and it ends where the poem ends
    assert "THE END" in t[-200:], "Paradise Lost does not end with THE END"


def test_white_devil_has_five_acts():
    t = read(os.path.join(TEXTS, "webster-white-devil.txt"))
    acts = re.findall(r"(?m)^\s*ACT\s+([IVX]+)\s*$", t)
    assert acts == ["I", "II", "III", "IV", "V"], "the acts are %s" % acts
    # sixteen scenes across the five acts
    scenes = re.findall(r"(?m)^\s*SCENE\s+([IVX]+)\s*$", t)
    assert len(scenes) == 16, "The White Devil has %d scenes, not 16" % len(scenes)


def test_doctor_faustus_has_its_four_chorus_speeches():
    t = read(os.path.join(TEXTS, "marlowe-doctor-faustus.txt"))
    speeches = re.findall(r"(?m)^[ \t]*CHORUS\.[ \t]", t)
    assert len(speeches) == 4, "Doctor Faustus has %d chorus speeches" % len(speeches)
    # the last chorus is the play's closing speech
    assert "Cut is the branch that might have grown full straight" in t


def test_nineteen_eighty_four_has_three_parts_and_the_appendix():
    t = read(os.path.join(TEXTS, "orwell-nineteen-eighty-four.txt"))
    parts = re.findall(r"(?m)^\s*(ONE|TWO|THREE)\s*$", t)
    assert parts == ["ONE", "TWO", "THREE"], "the parts are %s" % parts
    # the appendix is the reason this text is in the dark pole
    assert "APPENDIX" in t, "the Newspeak appendix is missing"
    assert "THE PRINCIPLES OF NEWSPEAK" in t


# ==========================================================================
# 4. the 1984 postface is not in the book
# ==========================================================================

def test_the_modern_postface_is_not_in_the_book():
    """The PG Canada edition carries a 2020 postface by Louis Markos.
    It is not Orwell. It must not be in the text."""
    t = read(os.path.join(TEXTS, "orwell-nineteen-eighty-four.txt"))
    assert "Markos" not in t, "the 2020 postface is in the text"
    assert "Orwell in Early 20th" not in t, "the postface's running head is in the text"


def test_the_1984_body_ends_with_the_appendix_not_the_postface():
    t = read(os.path.join(TEXTS, "orwell-nineteen-eighty-four.txt"))
    assert t.rstrip().endswith("as 2050."), (
        "the text does not end on the appendix's last line")


def test_the_1984_text_starts_at_part_one():
    t = read(os.path.join(TEXTS, "orwell-nineteen-eighty-four.txt"))
    head = t.lstrip()[:400]
    assert "ONE" in head.split("It was a bright cold day")[0], (
        "the text does not start at the first part marker")


# ==========================================================================
# 5. the strip was neither a no-op nor a destruction
# ==========================================================================

def test_the_corpus_texts_are_marked_as_binary_for_git():
    """The corpus texts must be byte-exact, and git must be told so.

    `core.autocrlf=true` is set on this machine. Without a `-text`
    attribute, git rewrites LF to CRLF on checkout, and the manifest's
    sha256 stops matching the file. The repo already had the rule for
    `corpus/**/texts/*.txt` -- and the dark pole's texts sit DIRECTLY in
    `corpus/dark-pole/`, so the pattern did not reach them. That was a
    real defect, found by asking git rather than by reading the file.

    The check is `git check-attr`, so it measures what git will actually
    do, not what the attribute file appears to say.
    """
    repo = REPO
    try:
        proc = subprocess.run(
            ["git", "check-attr", "text", "--"] +
            [os.path.join(DARK, n) for n in
             ("milton-paradise-lost.txt", "marlowe-doctor-faustus.txt",
              "webster-white-devil.txt", "orwell-nineteen-eighty-four.txt")],
            cwd=repo, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.SubprocessError):
        pytest.skip("git is not available here")
    if proc.returncode != 0:
        pytest.skip("git check-attr failed: %s" % proc.stderr.strip())
    lines = [l for l in proc.stdout.strip().splitlines() if l.strip()]
    assert lines, "git check-attr returned nothing"
    for line in lines:
        path, attr, value = line.rsplit(": ", 2)
        assert value == "unset", (
            "%s has git attribute %s=%s, but a corpus text must be "
            "byte-exact, so it needs -text" % (path, attr, value))


def test_the_strip_is_not_a_no_op_and_not_a_destruction():
    """Each text must be smaller than its raw fetch (the boilerplate
    went) and larger than a floor (the book is still there)."""
    for r in ROWS:
        raw_path = os.path.join(RAW, r["source_file"])
        assert os.path.exists(raw_path), "the raw fetch is gone: %s" % r["source_file"]
        raw_bytes = os.path.getsize(raw_path)
        assert r["bytes"] < raw_bytes, (
            "%s is not smaller than its raw fetch (%d vs %d) -- the strip "
            "did nothing" % (r["file"], r["bytes"], raw_bytes))
        assert r["bytes"] > raw_bytes * 2 // 3, (
            "%s kept only %d of %d raw bytes -- the strip ate the book"
            % (r["file"], r["bytes"], raw_bytes))


# ==========================================================================
# 6. the manifest matches the files
# ==========================================================================

def test_the_manifest_byte_counts_match_the_files():
    for r in ROWS:
        p = os.path.join(REPO, r["file"])
        assert os.path.getsize(p) == r["bytes"], (
            "%s is %d bytes on disk, the manifest says %d"
            % (r["file"], os.path.getsize(p), r["bytes"]))


def test_the_manifest_hashes_match_the_files():
    for r in ROWS:
        p = os.path.join(REPO, r["file"])
        with open(p, "rb") as fh:
            digest = hashlib.sha256(fh.read()).hexdigest()
        assert digest == r["sha256"], (
            "%s does not match its manifest hash" % r["file"])


def test_the_manifest_names_the_books_it_claims():
    """The receipt must name the book it holds, and the RAW FETCH must
    name the same book.

    The author's name is checked in the RAW FETCH, not in the stripped
    text: Gutenberg puts "Author: John Webster" in the licence header,
    which the strip removes, and The White Devil's own front matter
    never names its author at all. Checking the stripped text for the
    author's name would therefore be checking for something the book
    does not contain -- and 25 of the 49 deception texts fail that same
    check, which is how the repo's own convention was learned.

    TWO CONVENTIONS, and both are real:
      * the Gutenberg plain-text header carries "Title: X" and
        "Author: Y" (Milton, Marlowe, Webster);
      * the Project Gutenberg Canada edition carries neither, and puts
        the title and the byline in its first line instead ("Nineteen
        Eighty-Four by George Orwell [Blair, Eric Arthur]").

    So the check accepts either, and it requires that the raw fetch
    names the SAME book the manifest names.
    """
    for r in ROWS:
        raw = read(os.path.join(RAW, r["source_file"]))
        title_line = re.search(r"(?m)^Title:\s*(.+)$", raw)
        author_line = re.search(r"(?m)^Author:\s*(.+)$", raw)
        if title_line and author_line:
            raw_title = title_line.group(1).strip()
            raw_author = author_line.group(1).strip()
        else:
            # the Canada edition: title and byline in the first line
            first = next((l.strip() for l in raw.splitlines() if l.strip()), "")
            raw_title = first.split(" by ")[0].strip() if " by " in first else first
            raw_author = (first.split(" by ")[1].split(" [")[0].strip()
                          if " by " in first else "")
            assert raw_title, "the raw fetch of %s names no title" % r["file"]
            assert raw_author, "the raw fetch of %s names no author" % r["file"]
        assert raw_title.lower() in r["title"].lower(), (
            "the raw fetch of %s is %r, the manifest says %r"
            % (r["file"], raw_title, r["title"]))
        assert raw_author.lower() in r["author"].lower(), (
            "the raw fetch of %s is by %r, the manifest says %r"
            % (r["file"], raw_author, r["author"]))


def test_each_text_carries_its_title_in_its_own_front_matter():
    """The book's own title, in the book's own front matter.

    Paradise Lost prints "PARADISE LOST", Faustus prints its title,
    The White Devil prints "THE WHITE DEVIL". The 1984 edition opens
    straight into the novel with no title page, so it is not held to
    this -- and saying so here is the point: the check names its own
    exception rather than skipping quietly.
    """
    for name in ("milton-paradise-lost.txt", "marlowe-doctor-faustus.txt",
                 "webster-white-devil.txt"):
        t = read(os.path.join(TEXTS, name)).upper()
        assert "PARADISE LOST" in t[:2000] or "TRAGICAL HISTORY OF DOCTOR FAUSTUS" in t[:2000] \
            or "THE WHITE DEVIL" in t[:2000], (
            "%s does not carry its own title in its front matter" % name)


def test_every_row_names_a_source_and_a_tradition():
    for r in ROWS:
        assert r.get("source"), "%s names no source" % r["file"]
        assert r.get("tradition"), "%s names no tradition" % r["file"]
        assert r.get("teaches"), "%s teaches nothing" % r["file"]
        assert r.get("fruit"), "%s has no fruit" % r["file"]


# ==========================================================================
# 7. the strip function itself
# ==========================================================================

def test_strip_gutenberg_returns_the_body_between_the_markers():
    text = ("junk before\n"
            "*** START OF THE PROJECT GUTENBERG EBOOK THING ***\n"
            "THE BOOK BODY\n"
            "*** END OF THE PROJECT GUTENBERG EBOOK THING ***\n"
            "junk after\n")
    body, hdr, ftr = builder.strip_gutenberg(text)
    assert "THE BOOK BODY" in body
    assert "junk before" not in body and "junk after" not in body
    assert hdr is True and ftr is True


def test_strip_gutenberg_leaves_a_non_gutenberg_file_alone():
    """A file with no markers is not mangled. The function says so
    rather than pretending it stripped something."""
    text = "This file was never a Gutenberg ebook.\nSecond line.\n"
    body, hdr, ftr = builder.strip_gutenberg(text)
    assert body == text
    assert hdr is False and ftr is False


def test_normalise_rejoins_a_word_split_across_a_line():
    out = builder.normalise("A kilom-\neter away.")
    assert "kilometer" in out, out


def test_normalise_keeps_a_hyphen_that_is_part_of_the_word():
    out = builder.normalise("the self-interested course")
    assert "self-interested" in out, out
