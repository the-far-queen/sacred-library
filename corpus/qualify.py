"""
corpus/qualify.py -- the five-part qualification gate, and the ingestion
manifest it reads.

WHY THIS FILE EXISTS
--------------------
`corpus/curriculum.py` says, in its own docstring:

    "`ingested` is False until a qualification file with all five parts
     exists. That is the whole design: a corpus you already had does not
     count as knowledge."

and in `export()`:

    "ingestion_rule": "ingested stays False until a five-part qualification
                       exists. A corpus you already had does not count as
                       knowledge."

**Neither of those rules was implemented.** `Entry.ingested` was a field
nobody ever set, `qualification` was a field nobody ever filled, and
`stats()["ingested"]` was therefore a hard-coded 0 that read like a
measurement. A corpus you already had DID count as knowledge, because
the gate was prose.

The five parts come from Bobby's charter, `far-schools-charter-2026-10-15.md`
section 4, quoted:

    1. The claim.     The source asserts it, in the source's own words.
    2. The axis.      Which existing axis it moves; current value;
                       intended value.
    3. The delta.     The line that forces the change, quoted and anchored.
    4. The failure mode. Which of my current habits it argues against,
                       named so it can be audited later.
    5. The test.      What observation shows it took, and what shows it
                       didn't.

    "Four of five is a note."

THE GATE
---------
A qualification file is refused unless all five parts are present and
non-trivial. The refusal reasons are named, because "Four of five is a
note" is only useful if the reader can see WHICH part is missing.

This is the same shape as the two gates already in this repo -- the law
citation gate (`corpus/schools/law/tools/cite.py`) and the engineering
invention gate (`corpus/schools/engineering/tools/inv.py`): a schema, a
compiler, and a gate that can say no.

WHAT IT DOES NOT DO
-------------------
It does not decide whether a claim is TRUE. It checks that the claim is
PRESENT, QUOTED, ANCHORED, and that the qualification names a failure
mode and a test. Truth is a separate instrument and this gate is not it.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS = os.path.join(REPO, "corpus")
# The receipt lives in corpus/ingest/, beside the texts it describes.
# The first version of this looked for INGESTED.json at the corpus root,
# found nothing, and reported "fetched 0" -- a gate that reads zero
# because it is looking in the wrong place reads exactly like a gate
# that has found nothing.
INGEST_DIR = os.path.join(CORPUS, "ingest")

# The five parts, in the charter's order. The key is the markdown heading
# a qualification file uses; the value is what the part must carry.
PARTS = {
    "claim":        "the source asserts it, in the source's own words",
    "axis":         "which existing axis it moves; current value; intended value",
    "delta":        "the line that forces the change, quoted and anchored",
    "failure_mode": "which of my current habits it argues against, named",
    "test":         "what observation shows it took, and what shows it didn't",
}

# A part is not present if it is empty, or if it is only a heading with
# nothing under it. The floor is deliberately low -- this gate checks
# STRUCTURE, not quality of thought. Quality is a human or agent call and
# pretending otherwise is how a gate becomes decoration.
MIN_PART_WORDS = 8

# A quote must be anchored: a location inside the source, not just a
# string in quotation marks. Page, line, chapter, section, or a URL
# fragment -- any of these count.
#
# The bare words "line" and "section" do NOT count. They are ordinary
# English: "the line that forces the change" is prose, not a location.
# The first version of this regex accepted them, so an unanchored delta
# was accepted -- the gate said green on a quote with no location in it.
# A location must carry a NUMBER, or be a numbered reference.
ANCHOR_RE = re.compile(
    r"(?:\bpp?\.\s*\d|\bp{1,2}\s*\.?\s*\d+\b|\bline(?:s)?\s+\d+"
    r"|\bchapter\b|\bchap\.\s*\d|\bverse\s+\d|\bfolio\b|\bitem\s+\d"
    r"|\bentry\s+\d|\bsection\s+\d|\bvol(?:ume)?\.?\s+\d"
    r"|\bfolio\s+\d|\bhttps?://\S+#\S+|\#\w+|\bpp?\.\s*\d+\b)",
    re.I,
)

# A failure mode has to NAME a habit. A file that says "the failure mode is
# failing" has not named one.
HABIT_RE = re.compile(
    r"(?:\bI\b|\bmy\b|\bhabit\b|\btendency\b|\bdefault\b|\bI keep\b|\bI tend\b|"
    r"\bmyself\b|\bour\b|\bwe\b)",
    re.I,
)

# A test has to be OBSERVABLE. Two halves: what shows it took, and what
# shows it didn't. The charter says "and what shows it didn't", so a test
# with only the positive half is incomplete.
NEGATIVE_HINT_RE = re.compile(
    r"(?:\bnot\b|\bfalsif\w+|\bno\b|\bfail\w+|\bunless\b|\bwould not\b|"
    r"\bdoes not\b|\babsent\b|\bmissing\b|\bwould show\b|\bshould not\b)",
    re.I,
)


@dataclass
class Part:
    """One of the five parts, as it was found in the file."""
    name: str
    text: str = ""
    words: int = 0
    present: bool = False
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.present


@dataclass
class Qualification:
    """A qualification file, parsed. The gate reads this."""
    path: str = ""
    title: str = ""
    author: str = ""
    source_file: str = ""
    parts: dict = field(default_factory=dict)   # name -> Part
    extra: dict = field(default_factory=dict)

    @property
    def score(self) -> int:
        return sum(1 for p in self.parts.values() if p.ok)

    @property
    def qualified(self) -> bool:
        return self.score == len(PARTS)

    def missing(self) -> list:
        return [name for name, p in self.parts.items() if not p.ok]

    def why_not(self) -> list:
        """The reasons it is not qualified, named. Empty when it is."""
        out = []
        for name in PARTS:
            p = self.parts.get(name)
            if p is None or not p.ok:
                out.append(f"{name}: {PARTS[name]}"
                           + (f" ({p.reason})" if p and p.reason else ""))
        return out


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s*(.+?)\s*$", re.M)

# The heading text a part can be announced by. Longest first so that
# "failure mode" wins over "failure".
PART_ALIASES = {
    "claim":        ("the claim", "claim"),
    "axis":         ("the axis", "axis"),
    "delta":        ("the delta", "delta"),
    "failure_mode": ("the failure mode", "failure mode", "failure mode this argues against",
                     "failure-mode"),
    "test":         ("the test", "test"),
}


def _heading_key(text: str) -> str:
    """Map a heading to one of the five part names, or '' if it is not one."""
    t = text.strip().lower().rstrip(":").strip()
    # strip a leading numeral like "1." or "1)" -- the charter numbers them
    t = re.sub(r"^\d+\s*[.)]\s*", "", t)
    # strip markdown emphasis
    t = t.strip("*_` ")
    for name, aliases in PART_ALIASES.items():
        for a in aliases:
            if t == a or t.startswith(a + " ") or t.startswith(a + ":"):
                return name
    return ""


def parse_qualification(path: str) -> Qualification:
    """Parse a qualification markdown file into the five parts.

    A part is the text BETWEEN its heading and the next heading. A part
    with a heading and no body is a heading, not a part.
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()

    # locate every heading and its body
    marks = []
    for m in HEADING_RE.finditer(raw):
        marks.append((m.start(), m.end(), m.group(1)))
    # add a sentinel for the body after the last heading
    marks.append((len(raw), len(raw), ""))

    parts = {name: Part(name=name) for name in PARTS}
    for i in range(len(marks) - 1):
        start, hend, head_text = marks[i]
        body_start = hend
        body_end = marks[i + 1][0]
        body = raw[body_start:body_end]
        key = _heading_key(head_text)
        if not key:
            continue
        # If a part is announced twice, the FIRST wins and the later one is
        # ignored -- but the body is merged, because a charter-style file
        # sometimes continues the part under a sub-heading.
        p = parts[key]
        text = (p.text + "\n" + body).strip() if p.text else body.strip()
        words = len(text.split())
        p.text = text
        p.words = words
        p.present = words >= MIN_PART_WORDS
        if not p.present:
            p.reason = (f"only {words} word(s) under the heading"
                        if words else "heading present with no body")
        else:
            p.reason = ""

    # The delta must be QUOTED and ANCHORED. A delta that is a paraphrase
    # is not a delta: the charter says "quoted and anchored".
    delta = parts["delta"]
    if delta.present:
        quoted = ("\"" in delta.text) or ("\u201c" in delta.text) or (">" in delta.text)
        anchored = bool(ANCHOR_RE.search(delta.text))
        if not quoted:
            delta.present = False
            delta.reason = "no quoted line in the delta"
        elif not anchored:
            delta.present = False
            delta.reason = "the quote carries no anchor (page/line/chapter/section)"

    # The failure mode must NAME a habit.
    fm = parts["failure_mode"]
    if fm.present and not HABIT_RE.search(fm.text):
        fm.present = False
        fm.reason = "no habit named"

    # The test must have BOTH halves.
    tst = parts["test"]
    if tst.present and not NEGATIVE_HINT_RE.search(tst.text):
        tst.present = False
        tst.reason = "no falsification condition (what shows it did NOT take)"

    q = Qualification(path=path, parts=parts)

    # header fields, if present
    def grab(label: str) -> str:
        m = re.search(r"^\s*(?:\*\*)?%s(?:\*\*)?\s*[:\-]\s*(.+?)\s*$" % label,
                      raw, re.M | re.I)
        return m.group(1).strip() if m else ""

    q.title = grab("Title")
    q.author = grab("Author")
    q.source_file = grab("Source")
    return q


# --------------------------------------------------------------------------
# The manifest: which qualification belongs to which source text
# --------------------------------------------------------------------------
MANIFEST_NAME = "INGESTED.json"


def manifest_path(root: str = CORPUS) -> str:
    """Where the receipt lives.

    The default root is corpus/ingest/, which is where fetch_corpus.py
    writes it and where link_qualifications.py updates it. A caller that
    passes a DIFFERENT root (a test's tmp_path) gets the manifest in
    that root, so the tests keep working against a temporary directory.
    """
    if os.path.abspath(root) == os.path.abspath(CORPUS):
        return os.path.join(INGEST_DIR, MANIFEST_NAME)
    return os.path.join(root, MANIFEST_NAME)


def load_manifest(root: str = CORPUS) -> list:
    p = manifest_path(root)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return []


def write_manifest(rows: list, root: str = CORPUS) -> str:
    p = manifest_path(root)
    with open(p, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return p


def resolve_qualification(qp: str, root: str = CORPUS) -> str:
    """Turn a manifest's qualification path into a real path on disk.

    The manifest stores REPO-RELATIVE paths ("corpus/ingest/
    qualifications/x.md"), because that is what a reader of the manifest
    needs -- the path works from the repo root, which is where the
    manifest is committed.

    The first version joined that path against `root`, which is
    corpus/, and so looked for corpus/corpus/ingest/... The file was
    there; the LOOKUP was wrong. The gate reported "fetched 27,
    qualified 0" and every one of the 27 was counted as "fetched, not
    qualified" -- which reads exactly like a corpus of bytes with no
    knowledge in it. It was a path bug.

    So: try the REPO root, then `root`, then the raw path. The first
    one that exists wins, and if none exists the raw path is returned so
    the caller reports it as missing.
    """
    if os.path.isabs(qp):
        return qp
    candidates = [
        os.path.join(REPO, qp),
        os.path.join(root, qp),
        qp,
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def ingest_state(root: str = CORPUS) -> dict:
    """Which source texts are ingested, and on what evidence.

    An entry is ingested when its qualification file EXISTS and the gate
    accepts it. The manifest alone does not make a text ingested: the
    manifest records what was fetched, and the qualification file is what
    makes it knowledge. A text with bytes but no qualification is
    `fetched_not_qualified` -- present, and explicitly not yet knowledge.

    This is the rule `curriculum.py` promised and did not implement.
    """
    rows = load_manifest(root)
    qualified, fetched_only, refused = [], [], []
    for row in rows:
        qp = row.get("qualification")
        if not qp:
            fetched_only.append(row)
            continue
        full = resolve_qualification(qp, root)
        if not os.path.exists(full):
            fetched_only.append(row)
            continue
        q = parse_qualification(full)
        if q.qualified:
            qualified.append(row)
        else:
            refused.append({"row": row, "missing": q.missing(),
                            "why": q.why_not()})
    return {
        "fetched": len(rows),
        "qualified": len(qualified),
        "fetched_not_qualified": len(fetched_only),
        "refused": len(refused),
        "refused_detail": refused,
    }


def render_report(state: dict) -> str:
    lines = []
    lines.append("THE FIVE-PART QUALIFICATION GATE")
    lines.append(f"  fetched                 {state['fetched']}")
    lines.append(f"  qualified (5 of 5)      {state['qualified']}")
    lines.append(f"  fetched, NOT qualified  {state['fetched_not_qualified']}")
    lines.append(f"  refused (qualification) {state['refused']}")
    for r in state.get("refused_detail", []):
        f = r["row"].get("file", "?")
        lines.append(f"    REFUSED {f}: missing {', '.join(r['missing'])}")
    return "\n".join(lines)


if __name__ == "__main__":
    st = ingest_state()
    print(render_report(st))
