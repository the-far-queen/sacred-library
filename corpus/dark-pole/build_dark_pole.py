"""
corpus/dark-pole/build_dark_pole.py -- BUILD THE DARK POLE, FROM THE RAW
FETCHES, WITH EVERY DECISION MEASURED.

WHAT THIS DOES
--------------
The four dark-pole texts (Milton, Marlowe, Webster, Orwell) were fetched
raw into `corpus/dark-pole/_raw/`. This file turns the raw fetches into
the corpus: four named text files, with the Project Gutenberg boilerplate
stripped, and an `ACQUIRED.json` manifest that records exactly what each
file is and where it came from.

WHY THE STRIP MATTERS
---------------------
The deception library (49 texts) keeps its books' own front matter and
drops only the licence boilerplate. The same rule is applied here, and it
is a rule with a measurement: after stripping, a text must still carry its
BOOK's structure -- Paradise Lost's ten books, The White Devil's five
acts, Faustus's scenes, and 1984's three parts and its appendix. A strip
that loses the structure has thrown away the book.

THE FOUR TEXTS, AND WHERE EACH CAME FROM
-----------------------------------------
    milton-paradise-lost.txt   PG #20    Paradise Lost (1667)
    marlowe-doctor-faustus.txt  PG #811   Doctor Faustus, the 1616 quarto
    webster-white-devil.txt     PG #12915 The White Devil (c.1612)
    orwell-nineteen-eighty-four.txt
                                PG Canada #949  (Project Gutenberg's own
                                catalog carries no plain-text 1984; the
                                Canadian edition is public domain)

Run:
    python corpus/dark-pole/build_dark_pole.py
    python corpus/dark-pole/build_dark_pole.py --check
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = os.path.dirname(HERE)          # .../sacred-library/corpus
REPO = os.path.dirname(CORPUS)          # .../sacred-library
RAW = os.path.join(HERE, "_raw")
#: The texts sit DIRECTLY in corpus/dark-pole/, because that is the
#: layout the item's verify command reads:
#:     ls corpus/dark-pole/*.txt && cat corpus/dark-pole/ACQUIRED.json
TEXTS = HERE
MANIFEST = os.path.join(HERE, "ACQUIRED.json")

#: The smallest a book may be and still be a book. Every one of these
#: texts is a full play or a full poem; a truncated fetch must not pass.
MIN_BYTES = 60_000


# ==========================================================================
# THE STRIP
# ==========================================================================

def strip_gutenberg(text: str) -> Tuple[str, bool, bool]:
    """Return (body, had_header, had_footer).

    Project Gutenberg wraps every ebook in a licence header and footer.
    The header ends at `*** START OF THE PROJECT GUTENBERG EBOOK ... ***`
    and the footer begins at `*** END OF THE PROJECT GUTENBERG EBOOK ... ***`.

    A body that carries NEITHER marker is returned unchanged, with both
    flags False. That is the honest answer: this file is not a Gutenberg
    plain-text edition and no boilerplate was removed from it. A strip
    that silently mangles such a file would be worse than no strip.
    """
    m = re.search(
        r"\*\*\* ?START OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*\*\*\*",
        text)
    e = re.search(
        r"\*\*\* ?END OF (?:THE|THIS) PROJECT GUTENBERG EBOOK[^\n]*\*\*\*",
        text)
    if m and e and e.start() > m.end():
        return text[m.end():e.start()], True, True
    return text, bool(m), bool(e)


def normalise(body: str) -> str:
    """Clean the body, keeping the book's words.

    Removed: the licence's remaining furniture (the `* * * * *` separator
    and the `PEnd p` marker), carriage returns, and trailing whitespace.

    NOT removed: the book's own front matter (the title page, the
    dramatis personae, the editor's note). The deception library keeps
    those, so the dark pole keeps them too -- and the Faustus editor's
    note is itself evidence about which quarto the text is.

    Hyphenation across a line break is REJOINED, because a word split by
    the book's line-wrapping is one word. A hyphen that is part of the
    word itself (`telescreen`, `self-interested`) is untouched, because
    the join only fires across a line break.
    """
    body = body.replace("\r\n", "\n").replace("\r", "\n")
    body = body.replace("\f", "\n")
    # a word broken across a line: "kilome-\nter" -> "kilometer"
    body = re.sub(r"([A-Za-z])-\n([a-z])", r"\1\2", body)
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    # the licence's own markers, which sit inside the book body
    body = re.sub(r"(?m)^\s*P\s*End\s+p\s*$", "", body)
    body = re.sub(r"(?m)^\s*\*\s*\*\s*\*\s*\*\s*\*\s*$", "", body)
    body = body.strip() + "\n"
    return body


# ==========================================================================
# THE 1984 EDITION
# ==========================================================================
#
# The Project Gutenberg catalog carries no plain-text Nineteen
# Eighty-Four -- the searches return nothing for "Nineteen Eighty-Four"
# and "1984 orwell" ("No records found."). The copy the raw fetch
# produced is the Project Gutenberg Canada edition #949, which is public
# domain under Canadian copyright law.
#
# That edition has three layers: the novel, the APPENDIX (The Principles
# of Newspeak -- the part the dark pole is actually after, because it is a
# language designed so that a thought cannot be had), and a 2020
# POSTFACE by Louis Markos, which is not Orwell and is not the book.
#
# The postface is removed. The appendix is kept. The boundary is found,
# not guessed: the postface begins at the running head that carries its
# title.

POSTFACE_MARK = "Orwell in Early 20th"
NOVEL_OPEN = "It was a bright cold day in April"


def derive_1984(raw: str) -> Tuple[str, Dict[str, Any]]:
    """Derive the 1984 body from the PG Canada edition.

    The body starts at the novel's first PART marker -- "ONE" -- not at
    the first sentence, because the part marker is part of the book's
    structure and the file's own table of contents has no line that is
    just "ONE", so the two cannot be confused.

    Returns (body, facts) where facts records what was found and where.
    """
    facts: Dict[str, Any] = {}
    # the part marker, immediately followed by the novel's first sentence
    m = re.search(r"(?m)^ONE\s*\n" + re.escape(NOVEL_OPEN), raw)
    if not m:
        raise ValueError("the novel's first part marker is not in the file")
    start = m.start()
    facts["novel_opens_at"] = start
    facts["part_marker"] = "ONE"

    # The appendix ends where the modern postface begins. The postface is
    # introduced by a running head carrying its title, which is the first
    # place that title appears AFTER the novel.
    after = start + len(NOVEL_OPEN)
    post = raw.find(POSTFACE_MARK, after)
    facts["postface_at"] = post
    if post < 0:
        raise ValueError("the postface marker is not in the file")

    body = raw[start:post]
    # the licence's trailing furniture, which sits at the end of the
    # appendix, before the postface's running head
    body = re.sub(r"(?m)^\s*P\s*End\s+p\s*$", "", body)
    body = re.sub(r"(?m)^\s*\*\s*\*\s*\*\s*\*\s*\*\s*$", "", body)
    body = body.replace("\f", "\n")
    body = re.sub(r"(?m)^\s*\d{1,3}\s*$", "", body)          # page numbers
    body = re.sub(r"(?m)^\s*19 8 4\s*$", "", body)            # the running head
    body = re.sub(r"([A-Za-z])-\n([a-z])", r"\1\2", body)     # split words
    body = re.sub(r"[ \t]+\n", "\n", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    body = body.strip() + "\n"
    facts["postface_removed"] = True
    return body, facts


# ==========================================================================
# THE FOUR TEXTS
# ==========================================================================

TARGETS: List[Dict[str, Any]] = [
    dict(
        file="milton-paradise-lost.txt",
        raw="pg20.txt",
        title="Paradise Lost",
        author="John Milton",
        year="1667",
        source="https://www.gutenberg.org/cache/epub/20/pg20.txt",
        source_id="PG #20",
        tradition="the_rebel_angel",
        teaches="the rebel angel's argument, which is sophisticated and "
                "loses -- and the losing is the point",
        fruit="Satan's address to the fallen host is the most persuasive "
              "piece of rhetoric in English arguing that the self-"
              "interested course is the right one. He is right about "
              "everything except the one thing, and the poem's whole "
              "weight is on that exception.",
        structure=("10 books", r"(?m)^\s*BOOK\s+([IVX]+)\.\s*$", 10),
    ),
    dict(
        file="marlowe-doctor-faustus.txt",
        raw="faustus_811.txt",
        title="The Tragical History of Doctor Faustus",
        author="Christopher Marlowe",
        year="1616 quarto (text) / 1588-92 (play)",
        source="https://www.gutenberg.org/cache/epub/811/pg811.txt",
        source_id="PG #811",
        tradition="the_bargain",
        teaches="the same bargain as Goethe's Faust, earlier and colder -- "
                "and the difference in what the devil asks for",
        fruit="the cost is not given at the start, it is taken in "
              "instalments: Faustus gives up one thing at a time and "
              "believes each piece is a gain. The play's twenty-four "
              "years are the instalment plan.",
        structure=("4 chorus speeches", r"(?m)^[ \t]*CHORUS\.[ \t]", 4),
    ),
    dict(
        file="webster-white-devil.txt",
        raw="pg12915.txt",
        title="The White Devil",
        author="John Webster",
        year="c.1612",
        source="https://www.gutenberg.org/cache/epub/12915/pg12915.txt",
        source_id="PG #12915",
        tradition="the_adversary_who_wins",
        teaches="every social advantage the infernal one lacks: the most "
                "successful devil of the Renaissance stage",
        fruit="the White Devil is the one who does not need a disguise "
              "and does not need a prohibition. He is the adversary who "
              "wins on his own terms, which is the case a gate keyed on "
              "suspicion will not catch.",
        structure=("5 acts", r"(?m)^\s*ACT\s+([IVX]+)\s*$", 5),
    ),
    dict(
        file="orwell-nineteen-eighty-four.txt",
        raw="p_raw.txt",
        title="Nineteen Eighty-Four",
        author="George Orwell",
        year="1949",
        source="Project Gutenberg Canada #949 "
               "(https://www.gutenberg.org/ebooks/949)",
        source_id="PG Canada #949",
        tradition="the_language_that_forbids",
        teaches="the Newspeak appendix -- a language designed so that a "
                "thought cannot be had: a lie that cannot be stated even "
                "by itself",
        fruit="the appendix is the densest statement of the whole "
              "project: a vocabulary whose second principle is that "
              "nothing exists that cannot be said, and a second "
              "principle that makes the first one true.",
        structure=("3 parts + appendix",
                   r"(?m)^\s*(ONE|TWO|THREE)\s*$", 3),
    ),
]


# ==========================================================================
# THE MEASUREMENT
# ==========================================================================

def count_structure(body: str, pattern: str) -> int:
    return len(re.findall(pattern, body))


#: The structure each text must still carry after the strip, by file
#: name. Derived from TARGETS so there is ONE place that says what a
#: book's divisions are, and the builder and the test cannot disagree.
STRUCTURE_PATTERNS: Dict[str, str] = {
    str(t["file"]): str(t["structure"][1]) for t in TARGETS
}
STRUCTURE_EXPECTED: Dict[str, int] = {
    str(t["file"]): int(t["structure"][2]) for t in TARGETS
}
STRUCTURE_LABELS: Dict[str, str] = {
    str(t["file"]): str(t["structure"][0]) for t in TARGETS
}


def check_structure(body: str, spec) -> Tuple[str, int, int]:
    """Return (label, found, expected)."""
    label, pattern, expected = spec
    return label, count_structure(body, pattern), expected


def write_text(dest: str, body: str) -> None:
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)


def build() -> List[Dict[str, Any]]:
    os.makedirs(TEXTS, exist_ok=True)
    rows: List[Dict[str, Any]] = []
    for t in TARGETS:
        raw_path = os.path.join(RAW, str(t["raw"]))
        with open(raw_path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()

        if t["file"].startswith("orwell-"):
            body, facts = derive_1984(raw)
            had_hdr, had_ftr = False, False
        else:
            body, had_hdr, had_ftr = strip_gutenberg(raw)
            facts = {}

        body = normalise(body)

        dest = os.path.join(TEXTS, str(t["file"]))
        write_text(dest, body)
        with open(dest, "rb") as fh:
            data = fh.read()

        label, found, expected = check_structure(body, t["structure"])
        row = dict(t)
        row.pop("structure")
        row.pop("raw")
        row.update(
            file="corpus/dark-pole/" + str(t["file"]),
            source_file=str(t["raw"]),
            bytes=len(data),
            lines=body.count("\n"),
            words=len(body.split()),
            sha256=hashlib.sha256(data).hexdigest(),
            gut_header_removed=had_hdr,
            gut_footer_removed=had_ftr,
            structure_label=label,
            structure_found=found,
            structure_expected=expected,
            facts=facts,
        )
        rows.append(row)
    return rows


def check() -> List[Dict[str, Any]]:
    """Re-read what is on disk and re-measure it. The manifest must
    describe the FILES, not the intentions."""
    rows: List[Dict[str, Any]] = []
    for t in TARGETS:
        dest = os.path.join(TEXTS, str(t["file"]))
        if not os.path.exists(dest):
            rows.append(dict(file=str(t["file"]), present=False))
            continue
        with open(dest, encoding="utf-8", errors="replace") as fh:
            body = fh.read()
        with open(dest, "rb") as fh:
            data = fh.read()
        label, found, expected = check_structure(body, t["structure"])
        rows.append(dict(
            file=str(t["file"]),
            present=True,
            bytes=len(data),
            lines=body.count("\n"),
            words=len(body.split()),
            sha256=hashlib.sha256(data).hexdigest(),
            structure_label=label,
            structure_found=found,
            structure_expected=expected,
        ))
    return rows


def main() -> int:
    if "--check" in sys.argv:
        rows = check()
        print("THE DARK POLE, AS IT IS ON DISK")
        print("=" * 78)
        bad = 0
        for r in rows:
            if not r.get("present"):
                print("  MISSING: %s" % r["file"])
                bad += 1
                continue
            ok = (r["structure_found"] == r["structure_expected"]
                  and int(r["bytes"]) >= MIN_BYTES)
            if not ok:
                bad += 1
            print("  %-36s %8d bytes %7d words  %-20s %d/%d  %s"
                  % (r["file"], r["bytes"], r["words"], r["structure_label"],
                     r["structure_found"], r["structure_expected"],
                     "OK" if ok else "NOT OK"))
        print()
        print("  %d of %d texts are present and carry their structure"
              % (len(rows) - bad, len(rows)))
        return 1 if bad else 0

    rows = build()
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=2, ensure_ascii=False)
        fh.write("\n")

    print("BUILT %d texts" % len(rows))
    print("=" * 78)
    for r in rows:
        print("  %-36s %8d bytes %7d words  %-20s %d/%d"
              % (os.path.basename(str(r["file"])), r["bytes"], r["words"],
                 r["structure_label"], r["structure_found"],
                 r["structure_expected"]))
    print()
    print("  manifest: %s (%d bytes)" % (MANIFEST, os.path.getsize(MANIFEST)))
    print()
    print("=" * 78)
    print("  Run: python corpus/dark-pole/build_dark_pole.py")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
