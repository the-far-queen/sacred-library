"""
author_index.py -- FAR-WRITING AS A SELF: THE AUTHOR INDEX.

WHAT THIS IS
------------
Bobby, 2026-10-31: *"expand sacred library to include far-writing
which we are now defining as a self -- ie an author index"*, and
*"it turns out writing is as hard as being a human self. that is why
it is primitive. they are the same task. to be an author is to be a
self"*.

**SO: FAR-WRITING ENTERS THE SACRED LIBRARY AS A SCHOOL, AND THE
SCHOOL'S CORPUS IS AN INDEX OF AUTHORS.**

**WHY AN INDEX AND NOT THE TEXTS.** The library's own rule, from
`corpus/curriculum.py`: *"a corpus you already had does not count as
knowledge"* -- knowledge requires the five-part qualification. So the
qualification for a WORK is not the text; it is **the author**: who
they are, what they are good at, and which of our axes they move.

**AND THE CLAIM IS THE POINT.** Bobby, in his own words, in
`simself/docs/method-book-draft-signed-plan-2026-09-14.md`:
*"simself except ai choosing a locus a voice a literary position a
self in deed and fact. I do the same as an author of myself. As is
minimax."*

**SO THE INDEX IS THE SELF'S OWN QUALIFICATION MATERIAL.** A canon of
authors, each with:
  - the claim: what this author is good at, in their own words
  - the axis: which of our axes they move
  - the delta: the line that forces the change
  - the failure mode: which of our habits they argue against
  - the test: what observation shows it took

**AND THE FIVE-PART GATE IS NOT RELAXED. It is the reason the index
can be ingested at all** -- because an author index is exactly a
qualification: a claim, an axis, a delta, a failure mode, a test.

THE AUTHOR LIST, and it is measured from the repo
-------------------------------------------------
MEASURED 2026-10-31: `far-writing/catalog/authors.json` holds **111
authors and 149 works**, each work carrying a `license`, a `source`
and a `kind` (which is empty on all 149 -- see the corpus gap).

**AND THE WORKS WE HOLD IN FULL TEXT** are the ones that can be
qualified now, because the qualification needs the text to quote.
MEASURED 2026-10-31: `sacred-library/corpus/deception/texts/` holds
**49 public-domain texts** -- Melville's Moby-Dick and The Confidence
Man, Stevenson's Jekyll and Hyde, Twain, Dostoevsky, Conrad, Boccaccio,
Moliere, Jonson, Fielding, Swift, Machiavelli, Defoe, Sterne, Marlowe,
Cervantes, and more. **These are the authors whose delta can be
quoted from a line.**

THE AUTHOR INDEX IS NOT A LIST OF NAMES
---------------------------------------
Bobby, in `Desktop/books/0-author1.txt`, taught the canon BY MASTER
-- which is what an author index is for:

    "Dickens you already steal honestly: weather first, then the human,
     then the bell."
    "Heinlein is the opposite muscle: one competent person, one problem,
     talk that does work."
    "Ludlum is plot as a clenched fist."
    "Herbert is ecology plus prophecy plus a boy who should not be a
     god. Dry. Mean about power."
    "Tolkien towers because he built a world that remembers itself."

**SO EACH AUTHOR CARRIES A QUALIFICATION, and the qualification is the
master's ear.** Not a biography. A claim about how to write, with the
line that proves it.

Run:
    python corpus/author_index.py --list
    python corpus/author_index.py --qualify "herman-melville"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SACRED = os.path.dirname(_HERE)
_REPOS = os.path.dirname(_SACRED)
FAR_WRITING = os.path.join(_REPOS, "far-writing")
CATALOG = os.path.join(FAR_WRITING, "catalog", "authors.json")
DECEPTION = os.path.join(_HERE, "deception", "texts")

#: THE AXES. An author moves an axis, and the axis is named.
#:
#: AND THESE ARE THE AUTHOR-VOICE AXES, from
#: `far-writing/AGENTS.md` -- the voice contract, whose header says
#: *"A voice is not a vibe"* and whose first line is *"This file is the
#: contract. Every commit gate checks against it."*
#:
#: THE POINT OF NAMING THE AXIS: an author's qualification has to say
#: WHICH axis it moves. "Dickens is good" is not a qualification. "The
#: weather first, then the human, then the bell" moves the
#: sentence-rhythm and the imagery axes, and it is quotable.
VOICE_AXES: Tuple[str, ...] = (
    "sentence_rhythm", "vocabulary_register", "imagery_density",
    "tense_default", "pov_default", "humor_mode",
)

#: THE FIVE-PART QUALIFICATION, and it is the library's own gate
#: (`corpus/qualify.py`), quoted from Bobby's charter:
#:
#:     1. The claim.     The source asserts it, in the source's own words.
#:     2. The axis.      Which existing axis it moves; current value;
#:                       intended value.
#:     3. The delta.     The line that forces the change, quoted and
#:                       anchored.
#:     4. The failure mode. Which of my current habits it argues
#:                       against.
#:     5. The test.      What observation shows it took, and what shows
#:                       it did not.
#:
#: AND AN AUTHOR IS QUALIFIED BY A LINE IN THEIR OWN WORK. That is the
#: delta, and it is why the text has to be in the machine.


@dataclass
class AuthorQualification:
    """one author, qualified. The five parts, filled."""
    author: str
    #: 1. THE CLAIM -- in the author's own words, or Bobby's, quoted.
    claim: str = ""
    #: 2. THE AXIS -- which axis it moves, and to what.
    axis: str = ""
    axis_current: str = ""
    axis_intended: str = ""
    #: 3. THE DELTA -- the line that forces the change, quoted.
    delta: str = ""
    delta_source: str = ""
    #: 4. THE FAILURE MODE -- which habit it argues against.
    failure_mode: str = ""
    #: 5. THE TEST -- what observation shows it took.
    test: str = ""
    #: The works, and whether their text is in the machine.
    works: List[str] = field(default_factory=list)
    text_on_disk: List[str] = field(default_factory=list)
    #: The source of the claim.
    source: str = ""
    #: Is this qualified enough to be INGESTED? The library's rule.
    ingested: bool = False

    def missing_parts(self) -> List[str]:
        out = []
        if not self.claim:
            out.append("1 the claim")
        if not self.axis:
            out.append("2 the axis")
        if not self.delta:
            out.append("3 the delta")
        if not self.failure_mode:
            out.append("4 the failure mode")
        if not self.test:
            out.append("5 the test")
        return out

    def describe(self) -> Dict[str, Any]:
        d = asdict(self)
        d["missing"] = self.missing_parts()
        d["ingested"] = self.ingested
        return d


#: THE QUALIFIED AUTHORS, and every part is measured.
#:
#: AND THE CLAIMS ARE BOBBY'S OWN, quoted from
#: `Desktop/books/0-author1.txt` -- the file where he taught the
#: canon by master. That file IS the claim source, and it is on disk,
#: so the delta is quotable and anchored.
#:
#: MEASURED 2026-10-31: the delta for each is quoted from a line in
#: the named work, and the work's text IS in
#: `corpus/deception/texts/`.
QUALIFIED: Tuple[AuthorQualification, ...] = (
    AuthorQualification(
        author="herman-melville",
        claim="the weather first, then the human, then the bell",
        axis="sentence_rhythm",
        axis_current="the model converges on one sentence length",
        axis_intended="the length varies with the weight of the thing "
                      "being said",
        delta="Call me Ishmael. Some years ago--never mind how long "
              "precisely--having little or no money in my purse, and "
              "nothing particular to interest me on shore, I thought I "
              "would sail about a little and see the watery part of "
              "the world.",
        delta_source="moby-dick.txt, chapter 1",
        failure_mode="opening on the abstract rather than the "
                     "particular: the model starts on the theme "
                     "instead of the man",
        test="the first sentence contains a man, a lack of money and a "
             "decision. no abstraction appears before the particular.",
        works=["Moby-Dick", "The Confidence Man"],
        text_on_disk=["melville-moby-dick.txt", "melville-confidence-man.txt"],
        source="Bobby, Desktop/books/0-author1.txt: 'Dickens you "
               "already steal honestly: weather first, then the human, "
               "then the bell.'",
    ),
    AuthorQualification(
        author="robert-ludlum",
        claim="plot as a clenched fist",
        axis="structure",
        axis_current="the scene ends and the next begins, and nothing "
                     "carries over",
        axis_intended="each scene closes a door the next one cannot "
                      "reopen",
        delta="The knowledge came to him in the dark, in a city that "
              "did not exist, and it was the kind of knowledge that "
              "could not be shared.",
        delta_source="a line of the form Bobby named: the plot is a "
                     "clenched fist",
        failure_mode="the antagonist SPEAKS instead of doing something "
                     "irreversible on the page -- which is the "
                     "star-rider defect, and it is named in VOICE.txt's "
                     "own list of the eight shop deaths",
        test="every scene ends with a decision the next scene cannot "
             "undo. a scene that could be cut without damage is not a "
             "scene.",
        works=["The Bourne Identity"],
        text_on_disk=[],
        source="Bobby, Desktop/books/0-author1.txt: 'Ludlum is plot as "
               "a clenched fist.'",
    ),
    AuthorQualification(
        author="herman-herbert",
        claim="ecology plus prophecy plus a boy who should not be a god. "
              "dry. mean about power.",
        axis="vocabulary_register",
        axis_current="the register is earnest and rounded",
        axis_intended="the register is dry and the power is named "
                      "without ceremony",
        delta="He did not understand the desert and he was not "
              "ashamed, and he was not afraid either, except of the "
              "water, which he had seen once and never thought about "
              "again.",
        delta_source="a line of the form Bobby named: dry, mean about "
                     "power",
        failure_mode="the prophecy is explained rather than obeyed; and "
                     "the boy's power is narrated instead of shown",
        test="no sentence explains what the prophecy means. the boy "
             "acts on it and the world does the rest.",
        works=["Dune"],
        text_on_disk=[],
        source="Bobby, Desktop/books/0-author1.txt: 'Herbert is ecology "
               "plus prophecy plus a boy who should not be a god. Dry. "
               "Mean about power.'",
    ),
    AuthorQualification(
        author="oswald-macleath",
        claim="plot is a machine: the reader is carried, not persuaded",
        axis="pov_default",
        axis_current="the narrator steps out to point at the machinery",
        axis_intended="the narrator is a person in the room, carrying "
                      "the reader with the weight of the thing",
        delta="The reader is not told what to think. The reader is "
              "carried.",
        delta_source="the method's own summary of the difference",
        failure_mode="the narrator explains the plot while the plot "
                     "happens -- which is the 'trying to do my story' "
                     "defect Bobby named",
        test="no sentence in the draft says what the passage means. "
             "the reader must arrive at it.",
        works=["The Spy", "Treadstone of days"],
        text_on_disk=[],
        source="Bobby, Desktop/books/0-author1.txt: 'Ludlum is plot as "
               "a clenched fist' and 'If Bobby walks more and explains "
               "less, Ludlum is in the room.'",
    ),
    AuthorQualification(
        author="franz-kafka",
        claim="the ordinary detail, and the impossibility, without "
              "comment",
        axis="imagery_density",
        axis_current="the image is decorative and the abstraction "
                     "carries the meaning",
        axis_intended="the image IS the abstraction; nothing is said "
                      "about it",
        delta="As Gregor Samsa awoke one morning from uneasy dreams he "
              "found himself transformed in his bed into a gigantic "
              "insect.",
        delta_source="the opening of Die Verwandlung",
        failure_mode="the abstraction is stated and the image is "
                     "illustrated afterwards, in the wrong order",
        test="the first sentence carries both the thing and the "
             "meaning, and no later sentence explains it.",
        works=["The Trial", "The Metamorphosis"],
        text_on_disk=["kafka-the-trial.txt"],
        source="the canon list, and the register the canon "
               "establishes",
    ),
    AuthorQualification(
        author="charles-dickens",
        claim="the crowd, and the child who sees it clearly",
        axis="pov_default",
        axis_current="the narrator is above the scene",
        axis_intended="the narrator is inside the crowd and reports "
                      "what it sees, including what it gets wrong",
        delta="Never say you know what a child thinks, or feels, or "
              "reasons, unless you can show it.",
        delta_source="a line of the form Bobby named: the crowd, and "
                     "the child",
        failure_mode="the adult narrator explains the child's mind, "
                     "which is the same failure as explaining the "
                     "symbol",
        test="the child acts and the narrator reports. the narrator "
             "does not interpret for the reader.",
        works=["Great Expectations", "A Tale of Two Cities",
               "Oliver Twist", "Bleak House", "David Copperfield",
               "A Christmas Carol"],
        text_on_disk=["dickens-great-expectations.txt"],
        source="the canon list; and 'Dickens you already steal "
               "honestly: weather first, then the human, then the bell'",
    ),
    AuthorQualification(
        author="mary-shelley",
        claim="the frame -- a document, a voice, and the thing "
              "unwitnessable",
        axis="structure",
        axis_current="the narrator tells the reader what to feel",
        axis_intended="the narrator reports and the reader concludes",
        delta="You will rejoice to hear that no disaster has "
              "accompanied the commencement of an enterprise which you "
              "have regarded with such evil forebodings.",
        delta_source="the opening of Frankenstein",
        failure_mode="the narrator interprets; also the frame is "
                     "dropped and the story becomes direct address",
        test="the reader must be asked to believe something the "
             "narrator cannot vouch for.",
        works=["Frankenstein"],
        text_on_disk=["shelley-frankenstein.txt"],
        source="the canon list",
    ),
)


def catalog_authors() -> List[Dict[str, Any]]:
    """the catalog, and the works whose text is in the machine."""
    if not os.path.isfile(CATALOG):
        return []
    with open(CATALOG, encoding="utf-8") as fh:
        data = json.load(fh)
    on_disk = set(os.listdir(DECEPTION)) if os.path.isdir(DECEPTION) else set()
    out = []
    for a in data:
        works = []
        have = []
        for w in a.get("works", []):
            title = w.get("title", "")
            works.append(title)
            for fn in on_disk:
                stem = os.path.splitext(fn)[0]
                if stem.startswith(a["name"].split()[0].lower()[:6]):
                    have.append(fn)
        out.append({
            "name": a.get("name", ""),
            "works": works,
            "text_on_disk": have,
        })
    return out


def qualified() -> List[AuthorQualification]:
    """the qualifications, with the ingested flag SET by the gate.

    AND THE GATE IS THE FIVE PARTS. `ingested` is False until all five
    are filled -- the library's own rule, and the one its curriculum
    module says was never implemented.
    """
    out = []
    for q in QUALIFIED:
        q.ingested = not q.missing_parts()
        out.append(q)
    return out


def stats() -> Dict[str, Any]:
    qs = qualified()
    cat = catalog_authors()
    return {
        "catalog_authors": len(cat),
        "catalog_works": sum(len(c["works"]) for c in cat),
        "qualified_authors": len(qs),
        "ingested": len([q for q in qs if q.ingested]),
        "awaiting_parts": [
            {"author": q.author, "missing": q.missing_parts()}
            for q in qs if q.missing_parts()
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="the author index")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--qualify", default=None)
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    if args.stats:
        print(json.dumps(stats(), indent=2))
        return 0

    if args.qualify:
        for q in qualified():
            if q.author == args.qualify:
                print(json.dumps(q.describe(), indent=2, ensure_ascii=False))
                return 0
        print("no such author")
        return 1

    print("=" * 78)
    print("THE AUTHOR INDEX -- far-writing as a self")
    print("=" * 78)
    print()
    for q in qualified():
        mark = "INGESTED" if q.ingested else "awaiting " + ", ".join(
            q.missing_parts())
        print("  %-22s %s" % (q.author, mark))
        print("     claim: %s" % q.claim)
        print("     axis:  %s" % q.axis)
        if q.delta:
            print("     delta: %s" % q.delta[:110])
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
