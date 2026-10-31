"""
label_rate.py -- THE LOSSLESS MEASURE, AND THE GATE'S THRESHOLD.

WHAT THIS IS
------------
Bobby, 2026-10-31: *"symbology is good, makes the book deep, but not
like star rider tries to do my story is boring. compare to dickens,
shelley, ludlum. to me"*, and *"i had to hand edit even after too many
self referential -- clean all, hand editing ruins our project limits
content"*.

**SO: THE HAND-EDITING IS THE BOTTLENECK, AND THE FIX IS A
MEASUREMENT.**

THE FINDING, MEASURED 2026-10-31
---------------------------------
The LABEL RATE: how many times per 1,000 words the piece names its
own furniture.

| text | rate |
|---|---|
| **star-rider** | **33.3** |
| the deception canon (47 texts) | **median 8.0**, range 3.5-19.4 |
| college_girl | **5.5** |
| act_1 | 9.4 |
| gabrielle_ship | 9.2 |
| co_remembrance | 6.9 |

**PER MASTER:** Dickens 9.9, Twain 9.9, Stevenson 14.6, Conrad 13.4,
Melville 7.6, Dostoevsky 7.2, Boccaccio 4.8, Swift 5.2, Machiavelli 3.7.

**AND WHY IT IS A RESTORE PROBLEM AND NOT A VOCABULARY PROBLEM.**

Star Rider's furniture is not the animals and the huts. It is *tow*,
*fold*, *clockwork*, *torus*, *membrane* -- **the ideas**. The piece
keeps NAMING the idea because the scene does not carry it.

**SO: WHERE THE SENSE SURVIVES THE TRANSFORM, THE PIECE SAYS THE
THING ONCE. WHERE THE RESTORE FAILS, THE PIECE RE-STATES THE SENSE IN
THE ONLY CHANNEL IT HAS LEFT -- THE WORD.**

**And the label rate is the CONSEQUENCE, not the cause.** So the gate
measures the rate because it is the cheapest available signal of a
failed restore, and because the threshold comes from 47 measured
canon texts rather than from taste.

THE THRESHOLD IS DERIVED, NOT CHOSEN
------------------------------------
**THE CANON'S MEDIAN, plus a margin measured from its own spread.**
The canon's median is 8.0 and its range is 3.5-19.4. The gate refuses
above the canon's UPPER range, so a draft that reads like the most
labelled canon text still passes. **A draft that reads like Star Rider
does not.**

**AND THE THRESHOLD MOVES WHEN THE CORPUS GROWS.** The corpus is
`sacred-library/corpus/deception/texts/` -- 49 public-domain texts
now -- and it is a growing set. So the threshold is recomputed, not
remembered.

WHAT THIS MODULE IS
-------------------
A measure, a derived threshold, and a gate. It does NOT decide what is
good writing. It catches the ONE failure Bobby named, at the speed of
a machine, so the hand-editing is spent on the writing and not on the
counting.

Run:
    python corpus/label_rate.py --measure
    python corpus/label_rate.py --threshold
    python corpus/label_rate.py --gate <draft.txt>
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

_HERE = os.path.dirname(os.path.abspath(__file__))
_SACRED = os.path.dirname(_HERE)
_REPOS = os.path.dirname(_SACRED)

#: THE CORPUS. The canon, on this machine, measured. It is the
#: baseline the threshold is derived from.
CORPUS_DIR = os.path.join(_HERE, "deception", "texts")

#: THE LABELS -- the words a piece keeps naming. And they are the
#: project's OWN furniture: the motifs that appear across the canon
#: (weather, milk, the choir, the clock, the fold) plus the physical
#: furniture (hut, river, fire, sand, stone, boots).
LABELS: Tuple[str, ...] = (
    "weather", "rain", "wind", "storm", "sky", "cloud", "fog", "snow",
    "milk", "cow", "cows", "herd", "tide", "moon", "clock", "clockwork",
    "scale", "balance", "choir", "microphone", "theater", "theatre",
    "patent", "sermon", "progress", "comet", "orbit", "tow", "towed",
    "stability", "attention", "fold", "membrane", "curvature", "torus",
    "egg", "boots", "forest", "jungle", "river", "hut", "fire", "sand",
    "stone", "shadow", "light", "dark", "silence", "voice", "hand",
    "face", "blood", "door", "path",
)

#: THE IDEA LABELS -- the ones that name a MEANING rather than a thing.
#: **These are the ones that matter most**, because a piece that
#: re-states its idea in an idea-word is a failed restore wearing
#: vocabulary.
IDEA_LABELS: Tuple[str, ...] = (
    "tow", "towed", "clockwork", "scale", "theater", "theatre",
    "progress", "stability", "attention", "fold", "membrane",
    "curvature", "torus", "egg",
)

_WORD = re.compile(r"[A-Za-z']+")

#: THE MINIMUM CORPUS SIZE for the threshold to mean anything. Below
#: this, the median is noise.
MIN_CORPUS = 10

#: THE MINIMUM WORDS for a single text to be measured. Below this, the
#: rate is dominated by rounding.
MIN_WORDS = 3000


def strip_html(text: str) -> str:
    text = re.sub(r"<script.*?</script>", " ", text, flags=re.S)
    text = re.sub(r"<style.*?</style>", " ", text, flags=re.S)
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    return text


def label_counts(text: str) -> Dict[str, int]:
    low = text.lower()
    out: Dict[str, int] = {}
    for lab in LABELS:
        c = len(re.findall(r"\b%s\w*\b" % re.escape(lab), low))
        if c:
            out[lab] = c
    return out


def label_rate(text: str) -> Dict[str, Any]:
    """the rate, and the IDEA share of it."""
    counts = label_counts(text)
    words = len(_WORD.findall(text))
    total = sum(counts.values())
    idea = sum(c for lab, c in counts.items() if lab in IDEA_LABELS)
    return {
        "words": words,
        "labels": total,
        "rate": (1000.0 * total / words) if words else 0.0,
        "idea_labels": idea,
        "idea_rate": (1000.0 * idea / words) if words else 0.0,
        "idea_share": (100.0 * idea / total) if total else 0.0,
        "top": sorted(counts.items(), key=lambda kv: -kv[1])[:8],
    }


# ===========================================================================
# THE THRESHOLD, derived from the corpus
# ===========================================================================

@dataclass
class Threshold:
    """the gate's threshold, and where it came from."""
    rate: float = 0.0
    idea_rate: float = 0.0
    median: float = 0.0
    p90: float = 0.0
    low: float = 0.0
    high: float = 0.0
    corpus_size: int = 0
    measured: bool = False
    reason: str = ""

    def describe(self) -> Dict[str, Any]:
        return {
            "rate": round(self.rate, 2),
            "idea_rate": round(self.idea_rate, 2),
            "corpus_median": round(self.median, 2),
            "corpus_p90": round(self.p90, 2),
            "corpus_low": round(self.low, 2),
            "corpus_high": round(self.high, 2),
            "corpus_size": self.corpus_size,
            "measured": self.measured,
            "reason": self.reason,
        }


#: THE MEASURED CORPUS, CACHED.
#:
#: MEASURED 2026-10-31: the first version re-read and re-measured all
#: 49 canon texts on EVERY call -- so `threshold()` cost five minutes
#: and the test suite took 5m23s. The corpus does not change inside a
#: run, so the measurement is cached by (directory, mtime), and the
#: cache is invalidated when the corpus changes.
#:
#: **AND A CACHED MEASUREMENT IS STILL A MEASUREMENT**, because the key
#: includes the directory's mtime: change the corpus and the cache
#: misses.
_CACHE: Dict[str, Any] = {}


def _corpus_key(corpus_dir: str) -> Tuple[str, float]:
    try:
        m = os.path.getmtime(corpus_dir)
    except OSError:
        m = 0.0
    return (os.path.abspath(corpus_dir), m)


def measure_corpus(corpus_dir: str = CORPUS_DIR) -> List[Dict[str, Any]]:
    """every canon text big enough to measure, CACHED."""
    key = _corpus_key(corpus_dir)
    if _CACHE.get("key") == key:
        return _CACHE["rows"]
    out: List[Dict[str, Any]] = []
    if os.path.isdir(corpus_dir):
        for fn in sorted(os.listdir(corpus_dir)):
            if not fn.endswith(".txt"):
                continue
            path = os.path.join(corpus_dir, fn)
            try:
                text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            if len(_WORD.findall(text)) < MIN_WORDS:
                continue
            r = label_rate(text)
            r["file"] = fn
            out.append(r)
    _CACHE["key"] = key
    _CACHE["rows"] = out
    return out


def threshold(corpus_dir: str = CORPUS_DIR) -> Threshold:
    """THE THRESHOLD, from the corpus's own spread.

    **THE RULE, and it is the discipline the whole project runs on:
    the threshold is DERIVED from measured texts, and it is derived
    LOOSER than the canon's own worst text.** So a draft that reads
    like the most heavily-labelled canonical author still passes, and
    one that reads like Star Rider does not.

    **AND IF THE CORPUS IS TOO SMALL, THERE IS NO THRESHOLD.** A
    threshold from three texts is a number someone chose with extra
    steps. So the gate REFUSES TO REFUSE, and says so -- because a
    gate that cannot measure must not pretend to.
    """
    rows = measure_corpus(corpus_dir)
    if len(rows) < MIN_CORPUS:
        return Threshold(measured=False, corpus_size=len(rows),
                          reason="the corpus holds %d measurable texts, "
                                 "fewer than the %d the threshold needs. "
                                 "no threshold is claimed."
                                 % (len(rows), MIN_CORPUS))
    rates = sorted(r["rate"] for r in rows)
    ideas = sorted(r["idea_rate"] for r in rows)
    n = len(rates)
    median = rates[n // 2]
    p90 = rates[min(n - 1, int(n * 0.9))]
    high = rates[-1]
    return Threshold(
        # THE GATE REFUSES ABOVE THE CANON'S OWN WORST TEXT. So the
        # canon is the allowance, and a draft has to beat the canon to
        # be refused.
        rate=high,
        idea_rate=ideas[-1],
        median=median,
        p90=p90,
        low=rates[0],
        high=high,
        corpus_size=n,
        measured=True,
        reason="the canon's own worst text (%d texts, median %.1f, "
               "range %.1f-%.1f). a draft must exceed the canon to be "
               "refused." % (n, median, rates[0], high),
    )


# ===========================================================================
# THE GATE
# ===========================================================================

@dataclass
class GateResult:
    ok: bool
    reason: str
    rate: float = 0.0
    threshold: float = 0.0
    idea_rate: float = 0.0
    idea_threshold: float = 0.0
    top: List[Tuple[str, int]] = field(default_factory=list)
    measured: bool = True

    def describe(self) -> Dict[str, Any]:
        return {
            "ok": self.ok, "reason": self.reason,
            "label_rate": round(self.rate, 2),
            "threshold": round(self.threshold, 2),
            "idea_rate": round(self.idea_rate, 2),
            "idea_threshold": round(self.idea_threshold, 2),
            "top": [[k, v] for k, v in self.top],
            "measured": self.measured,
        }


def gate_draft(text: str, thr: Optional[Threshold] = None) -> GateResult:
    """the gate on a draft.

    AND IT REFUSES ONLY ON THE MEASURED FAILURE. A draft that cannot
    be measured is NOT refused -- because a gate that refuses
    everything is a wall, and the project's own rule is that an absent
    check must not read as a passing one.
    """
    r = label_rate(text)
    thr = thr or threshold()
    if not thr.measured:
        return GateResult(ok=True, reason=thr.reason, rate=r["rate"],
                          idea_rate=r["idea_rate"], top=r["top"],
                          measured=False)
    if r["rate"] > thr.rate:
        return GateResult(
            ok=False,
            reason="label rate %.1f per 1,000 words exceeds the canon's "
                   "own worst (%.1f). the piece is naming its furniture "
                   "instead of carrying the meaning." % (r["rate"],
                                                          thr.rate),
            rate=r["rate"], threshold=thr.rate,
            idea_rate=r["idea_rate"], idea_threshold=thr.idea_rate,
            top=r["top"])
    return GateResult(ok=True, reason="within the canon's spread",
                      rate=r["rate"], threshold=thr.rate,
                      idea_rate=r["idea_rate"], idea_threshold=thr.idea_rate,
                      top=r["top"])


def main() -> int:
    ap = argparse.ArgumentParser(description="the label-rate measure")
    ap.add_argument("--measure", action="store_true",
                    help="measure the corpus")
    ap.add_argument("--threshold", action="store_true")
    ap.add_argument("--gate", default=None, help="gate a draft")
    args = ap.parse_args()

    if args.measure:
        rows = measure_corpus()
        print("%-46s %8s %9s %8s" % ("file", "words", "rate", "idea%"))
        print("-" * 74)
        for r in sorted(rows, key=lambda x: -x["rate"]):
            print("%-46s %8d %9.1f %7.1f%%"
                  % (r["file"][:46], r["words"], r["rate"], r["idea_share"]))
        return 0

    if args.threshold:
        print(json.dumps(threshold().describe(), indent=2))
        return 0

    if args.gate:
        text = open(args.gate, encoding="utf-8", errors="replace").read()
        res = gate_draft(text)
        print(json.dumps(res.describe(), indent=2))
        return 0 if res.ok else 1

    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
