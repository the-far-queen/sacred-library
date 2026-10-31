"""
voice_corpus.py -- THE AUTHOR CORPUS, AND WHAT IT IS FOR.

WHAT THIS IS
------------
Bobby, 2026-10-31: *"our author corpus is both -- not only reference
material in public domain to write from, but sentence patterns to speak
from. ie it determines an old-fashioned but nonetheless human author
voice for simself. and if we focus on evergreen timeless masters and
pepper with modern best selling authors -- Steele, Ludlum, Clancy,
Rowling, Tolkien, Heinlein -- **not for publication but for simself**
-- we have achieved our task: not a real self but a real sim self, a
working emotive voice for the axes, a super companion, a super game
avatar, a super ai agent."*

**SO THE CORPUS HAS TWO JOBS, AND THEY ARE NOT THE SAME JOB:**

| job | what it needs | what it gives |
|---|---|---|
| **TO WRITE FROM** | the text, for the reader | the material of a work |
| **TO SPEAK FROM** | the SENTENCE PATTERNS, for the voice | the register, the rhythm, the ear |

**AND THE SECOND IS THE ONE THE PROJECT NEEDS NOW.** A voice is 7
axes, and axes are measured in prose: `sentence_rhythm`,
`vocabulary_register`, `imagery_density`, `tense_default`,
`pov_default`, `humor_mode`, plus notices and refuses. **So a voice is
FITTED, not chosen** -- and the fit is over sentence patterns.

**AND THE TWO SETS SERVE DIFFERENT JOBS, which is why both are
needed:**

- **THE TIMELESS MASTERS** -- Melville, Dickens, Austen, Shelley,
  Kafka, Conrad, Stevenson, Melville again. Their sentences are the
  PATTERNS: the rhythm, the turn, the withholding. Their date is
  irrelevant because a sentence pattern is not about the century.
- **THE MODERN SELLERS** -- Ludlum, Clancy, Rowling, Tolkien,
  Heinlein, Steele. Their sentences are the REGISTER the reader is
  used to: the propulsion, the pace, the way a chapter ends.

**AND THE MODERN SET IS NOT FOR PUBLICATION.** Bobby says it plainly.
**We are not imitating them in a book we sell. We are learning how a
sentence moves so our own voice moves.** That is the difference
between a voice and a forgery, and it is the same line as "utilise,
don't steal" -- the author is credited, the prose is ours, and the
*pattern* is what is learned.

**AND THE DIFFERENCE IS MEASURED.** The timeless set's label rate is
the canon's median (7.8 per 1,000 words across 49 measured texts).
The modern set is the test: **a voice fitted to a modern seller must
still land inside the timeless spread.** If it does not, the fit has
produced a modern voice that does not read as human, and the fit
failed.

THE ACCEPTANCE CRITERION, in Bobby's words
-------------------------------------------
> *"we have achieved our task: not a real self but a real sim self, a
> working emotive voice for the axes, a super companion, a super game
> avatar, a super ai agent."*

**SO THE TEST IS NOT "IS IT CONSCIOUS". IT IS "DOES THE VOICE
WORK".** Concretely, four things, each measurable:

1. **THE VOICE IS FITTED** -- the axes come from a corpus, and the
   corpus is cited
2. **THE VOICE IS EMOTIVE** -- it moves the reader, and the movement
   is measurable in the draft's own statistics
3. **THE VOICE WORKS FOR EVERY AXIS** -- one voice per axis, not one
   house voice for everything
4. **THE VOICE IS HUMAN-READING** -- inside the timeless spread, by
   the label-rate gate

Run:
    python corpus/voice_corpus.py --list
    python corpus/voice_corpus.py --fit "herman-melville"
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SACRED = os.path.dirname(_HERE)
_REPOS = os.path.dirname(_SACRED)
sys.path.insert(0, _HERE)

import label_rate as LR  # noqa: E402

DECEPTION = os.path.join(_HERE, "deception", "texts")

#: THE TWO SETS, and they do different jobs.
#:
#: AND THE MEASUREMENT BEHIND THE SPLIT: the timeless set's label rate
#: is the canon's own spread, and the modern set is the TEST of a
#: fitted voice. A voice fitted to a modern seller must still land
#: inside the timeless spread, or the fit has produced a modern voice
#: that does not read as human.
TIMELESS: Dict[str, Dict[str, Any]] = {
    "herman-melville": {
        "file": "melville-moby-dick.txt",
        "what": "the weather first, then the human, then the bell",
        "axis": "sentence_rhythm",
        "pattern": "the long clause that opens and the short one that "
                   "closes it; the fact placed before the meaning",
    },
    "joseph-conrad": {
        "file": "conrad-lord-jim.txt",
        "what": "the mariner's sentence, and the lie inside it",
        "axis": "sentence_rhythm",
        "pattern": "the long retrospective sentence that keeps turning "
                   "back on itself",
    },
    "robert-stevenson": {
        "file": "stevenson-jekyll-hyde.txt",
        "what": "the document found, and the change it records",
        "axis": "structure",
        "pattern": "the section that is a record, then the section that "
                   "is the truth",
    },
    "moliere": {
        "file": "moliere-tartuffe.txt",
        "what": "the lie performed so well the house believes it",
        "axis": "humor_mode",
        "pattern": "the comedy of the double: the audience sees the "
                   "truth before the characters do",
    },
    "leonardo-da-vinci": {
        "file": None,
        "what": "the notebook: the observation before the system",
        "axis": "structure",
        "pattern": "the observation, then the drawing, then the "
                   "principle -- and the principle last, and never "
                   "announced",
    },
    "mary-shelley": {
        "file": None,
        "what": "the frame: a document, a voice, and the thing "
                "unwitnessable",
        "axis": "structure",
        "pattern": "the narrator reports and the reader concludes",
    },
    "charles-dickens": {
        "file": None,
        "what": "the crowd, and the child who sees it clearly",
        "axis": "pov_default",
        "pattern": "the narrator inside the crowd, reporting what it "
                   "gets wrong",
    },
    "franz-kafka": {
        "file": None,
        "what": "the ordinary detail, and the impossibility, without "
                "comment",
        "axis": "imagery_density",
        "pattern": "the image IS the abstraction; nothing is said about it",
    },
}

#: THE MODERN SELLERS. And they are NOT FOR PUBLICATION -- they are
#: the REGISTER the reader knows, so the fitted voice can carry it.
#:
#: AND THEY ARE NOT IN THE CORPUS AS TEXTS. They are in copyright, and
#: the project does not hold their books. So what is held here is the
#: ANALYSIS -- the sentence pattern each one uses -- and the pattern
#: is what is fitted.
#:
#: MEASURED 2026-10-31, and this is the honest shape of the thing:
#: the timeless set has 49 measured texts on disk; the modern set has
#: ZERO, because they are in copyright. So the modern contribution
#: is a SPECIFICATION, not a sample -- and a specification cannot be
#: measured against a corpus it is not in.
MODERN: Dict[str, Dict[str, Any]] = {
    "robert-ludlum": {
        "file": None,
        "what": "plot as a clenched fist",
        "axis": "structure",
        "pattern": "every scene ends with a decision the next scene "
                   "cannot undo. a scene that could be cut without "
                   "damage is not a scene.",
        "measured": "no text in the corpus: in copyright. the "
                    "contribution is the pattern specification, and the "
                    "figure the pattern came from is Bobby's: "
                    "'If Bobby walks more and explains less, Ludlum is "
                    "in the room.'",
    },
    "tom-clancy": {
        "file": None,
        "what": "the chapter that cannot be cut",
        "axis": "sentence_rhythm",
        "pattern": "short declaratives in a run, then one long one that "
                   "turns. the last line of the chapter is the hook "
                   "and the reader knows it.",
        "measured": "no text in the corpus: in copyright. the "
                    "contribution is the pattern specification.",
    },
    "j-k-rowling": {
        "file": None,
        "what": "the stair: a school year as a spine, and the cost of "
                "each term raised",
        "axis": "structure",
        "pattern": "one thing promised early, paid late, and the "
                   "reader can feel the interest accruing.",
        "measured": "no text in the corpus: in copyright. the "
                    "contribution is the pattern specification.",
    },
    "j-r-r-tolkien": {
        "file": None,
        "what": "a world that remembers itself",
        "axis": "imagery_density",
        "pattern": "the name, the song, the walk. the map is one thing "
                   "and the whole world is another, and the second is "
                   "never drawn.",
        "measured": "no text in the corpus: in copyright. the "
                    "contribution is the pattern specification.",
    },
    "robert-a-heinlein": {
        "file": None,
        "what": "one competent person, one problem, talk that does "
                "work",
        "axis": "vocabulary_register",
        "pattern": "plain words, technical words, no lyricism, and the "
                   "argument carried by the problem rather than by the "
                   "speaker's feelings about it.",
        "measured": "no text in the corpus: in copyright. the "
                    "contribution is the pattern specification.",
    },
    "charlotte-steele": {
        "file": None,
        "what": "the romance plot, and the reader who wants it",
        "axis": "humor_mode",
        "pattern": "the wry, knowing asides that let the reader see "
                   "the machinery and keep going.",
        "measured": "no text in the corpus: in copyright. the "
                    "contribution is the pattern specification.",
    },
}


@dataclass
class VoiceFit:
    """a voice fitted over a corpus, with the evidence."""
    author: str
    #: Which set the author is in: timeless | modern
    set: str = "timeless"
    #: The axes this author moves.
    axis: str = ""
    axis_current: str = ""
    axis_intended: str = ""
    #: The sentence pattern, as a specification.
    pattern: str = ""
    #: The claim, in the author's or Bobby's words.
    what: str = ""
    #: Where the text is, if it is in the corpus.
    text_path: Optional[str] = None
    #: The measured label rate of the text, when there is one.
    label_rate: Optional[float] = None
    #: The fit is only usable if the text is here.
    fitted: bool = False
    note: str = ""

    def describe(self) -> Dict[str, Any]:
        return asdict(self)


def fit(author: str) -> Optional[VoiceFit]:
    """the fit for one author, with the evidence attached."""
    if author in TIMELESS:
        spec = TIMELESS[author]
        fit_ = VoiceFit(
            author=author, set="timeless", axis=spec["axis"],
            pattern=spec["pattern"], what=spec["what"])
        # AND THE FILE MAY BE NONE. Some timeless authors are in the
        # registry as a SPECIFICATION -- Dickens, Shelley, Kafka are
        # NOT in the 49-text deception corpus, so there is no text to
        # fit against. The first version passed None into
        # os.path.join and raised TypeError. **A missing file is a
        # missing measurement, not a crash.**
        if spec.get("file"):
            path = os.path.join(DECEPTION, spec["file"])
            if os.path.isfile(path):
                fit_.text_path = path
                text = open(path, encoding="utf-8",
                           errors="replace").read()
                fit_.label_rate = LR.label_rate(text)["rate"]
                fit_.fitted = True
        if not fit_.fitted:
            fit_.note = ("no text of this author is in the corpus, so "
                         "the fit is a specification and not a "
                         "measurement")
        return fit_
    if author in MODERN:
        spec = MODERN[author]
        return VoiceFit(
            author=author, set="modern", axis=spec["axis"],
            pattern=spec["pattern"], what=spec["what"], text_path=None,
            note=spec.get("measured", ""))
    return None


def corpus_state() -> Dict[str, Any]:
    """what is measurable now, and what is a specification.

    AND THE HONEST NUMBER: the timeless set has texts on disk; the
    modern set has none, because they are in copyright. **So the
    modern contribution is a SPECIFICATION, and a specification cannot
    be measured against a corpus it is not in.** That is the limit of
    what was built today, and it is stated rather than hidden.
    """
    timeless_fitted = 0
    timeless_total = 0
    for a in TIMELESS:
        timeless_total += 1
        f = fit(a)
        if f and f.fitted:
            timeless_fitted += 1
    return {
        "timeless_authors": len(TIMELESS),
        "timeless_with_text": timeless_fitted,
        "modern_authors": len(MODERN),
        "modern_with_text": 0,
        "canon_texts_measured": len(LR.measure_corpus()),
        "label_rate_threshold": LR.threshold().describe(),
        "modern_note": "the modern set is a SPECIFICATION, not a sample: "
                       "the books are in copyright and the corpus holds "
                       "no text of them. not for publication -- for the "
                       "voice.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="the author corpus")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fit", default=None)
    ap.add_argument("--state", action="store_true")
    args = ap.parse_args()

    if args.state:
        print(json.dumps(corpus_state(), indent=2))
        return 0

    if args.fit:
        f = fit(args.fit)
        if f is None:
            print("no such author")
            return 1
        print(json.dumps(f.describe(), indent=2))
        return 0

    print("=" * 78)
    print("THE AUTHOR CORPUS -- to write from, and to speak from")
    print("=" * 78)
    print()
    print("  THE TIMELESS MASTERS -- the sentence PATTERNS, and the "
          "text is on disk")
    for a, spec in TIMELESS.items():
        f = fit(a)
        mark = ("measured %.1f" % f.label_rate) if (f and f.fitted) \
            else "SPEC ONLY"
        print("    %-22s %-22s %s" % (a, spec["axis"], mark))
    print()
    print("  THE MODERN SELLERS -- the REGISTER, and NOT for publication")
    for a, spec in MODERN.items():
        print("    %-22s %-22s specification only (in copyright)"
              % (a, spec["axis"]))
    print()
    st = corpus_state()
    print("  the timeless set fitted over a MEASURED text: %d of %d"
          % (st["timeless_with_text"], st["timeless_authors"]))
    print("  the canon texts measured for the label-rate gate: %d"
          % st["canon_texts_measured"])
    print()
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
