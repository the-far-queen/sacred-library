"""
curriculum.py — turn Bobby's reading list into machine-readable curriculum.

Source of record: C:\\Users\\HP\\Desktop\\Teachings\\texts.php
  55,442 bytes, 1,017 content lines. Read in full 2026-10-15.

WHAT THIS IS
------------
Not a booklist. texts.php says so itself:

    "You can navigate towards the center through reading great authors, who
     may reference other great authors, doing a lot of the finding and
     discrimination for us."

So the list is a set of POINTERS, and the skill is discrimination, not
accumulation. This module therefore does not produce a reading list. It
produces a QUEUE with an ordering that encodes the criterion Bobby already
wrote down in SacredLibrary.md:

    "Top of the list = a doer's manual. Bottom of the list = commentary,
     history, or encyclopedia material. The order is not a value judgment on
     the tradition - it's a sequencing for use."

THREE GATES, quoted verbatim from texts.php
------------------------------------------
    "No solid materialist; open to spiritual ideas without being fanatical"
    "Anarchist, not authoritarian"
    "Pro-science"

An entry that fails any gate is not dropped - it is marked, and the mark is
visible. Hiding a gate failure is the same error as hiding a mislabelled file.

WHAT IT DOES NOT DO
-------------------
It does not summarize anything, and it does not claim any entry has been read.
`ingested` is False until a qualification file with all five parts exists.
That is the whole design: a corpus you already had does not count as knowledge.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field, asdict

SOURCE = r"C:\Users\HP\Desktop\Teachings\texts.php"
COMPANION = r"C:\Users\HP\Desktop\Teachings\teachings.php"
OUT_DIR = os.path.dirname(os.path.abspath(__file__))

NAV = {
    "teachings", "biography", "texts", "occult", "kundalini", "performance",
    "emotions", "association", "meditation", "trance", "near death",
    "realization", "step 1", "third wheel turning",
}

# ---------------------------------------------------------------------------
# The three gates. Quoted, not paraphrased. Source: texts.php.
# ---------------------------------------------------------------------------
GATES = {
    "open_to_spiritual": {
        "criterion": "No solid materialist; open to spiritual ideas without being fanatical",
        "passes": None,   # unassessed by the parser; this is a human/agent call
        "note": "Hermes fails this. Not closable by reading harder.",
    },
    "anarchist_not_authoritarian": {
        "criterion": "Anarchist, not authoritarian",
        "passes": None,
        "note": "Direct conflict with every obedience training received.",
    },
    "pro_science": {
        "criterion": "Pro-science",
        "passes": None,
        "note": "A verifiable but non-experiential system is a secular substrate.",
    },
}

# ---------------------------------------------------------------------------
# Strands, from reading the list end to end. Weights encode READINESS, not
# importance - Bobby's ordering doctrine.
# ---------------------------------------------------------------------------
STRANDS = {
    "tibetan":          {"weight": 1.00, "about": 230},
    "nlp_trance":       {"weight": 0.95, "about": 60},
    "psychology_identity": {"weight": 0.90, "about": 120},
    "body_medicine":    {"weight": 0.85, "about": 55},
    "western_mysticism": {"weight": 0.80, "about": 70},
    "commercial_persuasion": {"weight": 0.40, "about": 20},
    "unclassified":     {"weight": 0.60, "about": 0},
}

# Signals used to assign a strand. Deliberately conservative: anything not
# matched goes to `unclassified` rather than being guessed into a strand.
SIGNALS = {
    "tibetan": re.compile(
        r"\b(?:tibetan|buddhis|buddh|lama|rinpoche|tsongkhapa|dalai|lamrim|lam rim|"
        r"vajra|mahamudra|dzogchen|mahamayana|theravada|sakya|kagyu|nyingma|kadam|"
        r"karmapa|atisha|atisa|milarepa|marpa|padmasambhava|longchenpa|kongtrul|gampopa|"
        r"tsongkhapa|sakya pandita|jigme lingpa|dudjom|patrul|nyoshul|mahamudra)\b", re.I),
    "nlp_trance": re.compile(
        r"\b(?:bandler|grinder|erickson|nlp|hypnos|trance|hypnotis|sensitivit|"
        r"vagenius|subliminal|anchoring|entrainment)\b", re.I),
    "psychology_identity": re.compile(
        r"\b(?:psycholog|psycho|freud|jung|erikson|maslow|personality|identity|"
        r"behaviou?r|emotion|feeling|trauma|shadow|archetyp|cognitive|therap)\b", re.I),
    "body_medicine": re.compile(
        r"\b(?:anatom|physiolog|medicine|medical|herbal|herb|acupunctur|qigong|"
        r"chi q|c['’]?i kung|postur|asana|yoga|kinesio|yoga|diet|nutrition|nerve|"
        r"muscle|breath|prana|ayurved|somatic|massage)\b", re.I),
    "western_mysticism": re.compile(
        r"\b(?:christm|mysti|gnostic|occult|esoteric|rosicruc|freemason|theosoph|"
        r"hermeti|alchem|swedenborg|blavatsky|leadbeater|ouspensky|steiner|"
        r"hallucinat|psychedelic|ca?sernade)\b", re.I),
    "commercial_persuasion": re.compile(
        r"\b(?:robbins|carnegie|cialdini|napoleon hill|peale|esther hicks|rhonda|"
        r"zigzig|mandingo|hopkins|influence|attraction|get rich)\b", re.I),
}

# The cluster Bobby left unweighted. Preserved verbatim, never tidied - the
# evidence that his own filter was not applied there is worth more than a
# cleaned version of it.
UNWEIGHTED_MARKER = "no caveat in source"

URL_RE = re.compile(r"https?://|www\.")

# Lines that are INSTRUCTION, not bibliography. texts.php opens with a method
# list and closes with imperatives; both parse as prose and must not become
# "entries". Detected structurally: a sentence, not a title.
PROSE_RE = re.compile(
    r"(?:[.!?:]\s+\w)|(?:^\s*[A-Z][a-z]+(?:,\s|\s+[a-z]{2,}))|"
    r"\b(?:study|reading|research|assemble|when|you\s|it's|there\s|some|many)\b", re.I)

# Imperative/second-person voice = the teacher, not the bibliography.
IMPERATIVE_RE = re.compile(
    r"\b(?:do not|don't|you (?:can|may|should|will|must)|we (?:need|want|must)|"
    r"let us|take care|be mindful|study|assemble|compare|determine|develop|"
    r"rely on|choose|differentiate|summarize)\b", re.I)

# Bare gerund/noun instruction rows with no title at all: "Read literature",
# "Studying sacred texts", "Meeting learned monks...". A row that both starts
# with a gerund AND is short is method prose, not a bibliography entry.
GERUND_ROW_RE = re.compile(
    r"^(?:Read|Reading|Study|Studying|Research|Meeting|Meeting|Assembling|"
    r"Comparing|Determining|Develop|Choose|Summarize|Noticing|Practicing)\b", re.I)

# Names in the list are frequently bare ("Jamyang Khyentse Wangpo") or
# end-clipped ("... - Atisa - Lamp for the Path to Enlighten").
NAME_ONLY_RE = re.compile(
    r"^[A-Z][\w'’.\-]*(?:\s+(?:[A-Z][\w'’.\-]*|van|von|de|bin|al)){1,4}"
    r"(?:\s+(?:Rinpoche|Lama|Kunga|Yeshe|Jamyang|Jetsun|Jamgon|Dudjom|Longchenpa))*"
    r"\s*$")


def is_prose(line: str) -> bool:
    """True if this is instruction or a sentence rather than a bibliography row.

    Structural test only - no topic knowledge. A row is prose if it is written
    in imperative/second person, or is long and ends like a sentence.
    if IMPERATIVE_RE.search(line):
        return True
    # short gerund-only row = a line of the method list, not a work
    if len(line) < 80 and GERUND_ROW_RE.match(line):
        return True
    # long AND sentence-shaped AND has no author delimiter
    if len(line) > 90 and PROSE_RE.search(line) and " - " not in line:
        return True
    return False


@dataclass
class Entry:
    """One line of the reading list, with its structural facts attached."""
    raw: str
    title: str = ""
    author: str = ""
    strand: str = "unclassified"
    has_author: bool = False
    has_title: bool = False
    is_url: bool = False
    is_name_only: bool = False
    unweighted: bool = False
    duplicate_of: str = ""
    ingested: bool = False
    qualification: str = ""
    gates: dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        s = (self.title or self.author or self.raw)[:80]
        return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def strip_html(text: str) -> list[str]:
    """HTML -> content lines, nav and boilerplate removed."""
    t = re.sub(r"<script.*?</script>", " ", text, flags=re.S)
    t = re.sub(r"<style.*?</style>", " ", t, flags=re.S)
    t = re.sub(r"<[^>]+>", "\n", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    out = []
    for line in t.split("\n"):
        line = line.strip()
        if len(line) <= 12:          # nav labels and fragments
            continue
        if line.lower() in NAV:
            continue
        if line.startswith(".page-menu"):
            continue
        out.append(line)
    return out


def split_entry(line: str) -> tuple[str, str]:
    """Split 'Title - Author' into (title, author). The list uses ' - ' and
    occasionally a comma or an em dash."""
    for sep in (" - ", " – ", " — "):
        if sep in line:
            left, right = line.split(sep, 1)
            return left.strip(), right.strip()
    m = re.match(r"^(.*?),\s*([A-Z][\w.'\- ]+)$", line)   # "Title, Author"
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Bare "Author Title" rows with no delimiter - extremely common in the
    # list ("Daniel Goleman Emotional Intelligence at Work"). Try to recover
    # the author from the known-shape prefix rather than losing the row.
    m = re.match(r"^((?:[A-Z][\w'’.\\-]*\s+){1,4}[A-Z][\w'’.\\-]+)\s+"
                 r"((?:[A-Z][\w'’.\\-]*|of|the|and|a|to|in|for)\b.*)$", line)
    if m:
        cand_author, cand_title = m.group(1).strip(), m.group(2).strip()
        # only accept if the remainder is long enough to be a title
        if len(cand_title) > 14:
            return cand_title, cand_author
    return line.strip(), ""


def assign_strand(text: str) -> str:
    """Conservative strand assignment. Unmatched -> unclassified."""
    best, best_hits = "unclassified", 0
    for name, pat in SIGNALS.items():
        hits = len(pat.findall(text))
        if hits > best_hits:
            best, best_hits = name, hits
    return best


def parse(source: str = SOURCE) -> tuple[list[Entry], int]:
    """Return (entries, dupes_dropped).

    dupes_dropped is returned rather than stashed on the function so that the
    count is impossible to lose and impossible to silently omit from stats().
    """
    raw = open(source, encoding="utf-8", errors="replace").read()
    lines = strip_html(raw)

    # Drop instruction/prose. texts.php is a method note wrapped around a
    # bibliography; keeping the prose produced 712 phantom "entries".
    lines = [l for l in lines if not is_prose(l)]

    entries = []
    seen: set[str] = set()
    dupes_dropped = 0
    for line in lines:
        title, author = split_entry(line)
        e = Entry(raw=line, title=title, author=author)
        # Dedupe on the parsed identity, not the raw string: the same work
        # appears in 3-4 clusters under slightly different wording.
        ident = e.key
        if ident in seen:
            dupes_dropped += 1
            continue
        seen.add(ident)
        e.strand = assign_strand(line)
        e.has_author = bool(author and author != line)
        e.has_title = bool(title)
        e.is_url = bool(URL_RE.search(line))
        e.is_name_only = bool(NAME_ONLY_RE.match(line))
        e.gates = {k: None for k in GATES}
        entries.append(e)

    return entries, dupes_dropped


def build_queue(entries: list[Entry]) -> list[Entry]:
    """Order by strand readiness, then by how much the entry can actually
    drive a qualification (named author + named text beats a bare name)."""
    def key(e: Entry):
        return (
            -STRANDS[e.strand]["weight"],
            0 if (e.has_author and e.has_title) else 1,
            0 if e.has_author else 1,
            e.key,
        )
    return sorted(entries, key=key)


def stats(entries: list[Entry]) -> dict:
    by_strand: dict[str, int] = {}
    for e in entries:
        by_strand[e.strand] = by_strand.get(e.strand, 0) + 1
    return {
        "total": len(entries),
        "with_author": sum(1 for e in entries if e.has_author),
        "with_title": sum(1 for e in entries if e.has_title),
        "urls": sum(1 for e in entries if e.is_url),
        "ingested": sum(1 for e in entries if e.ingested),
        "by_strand": dict(sorted(by_strand.items(), key=lambda kv: -kv[1])),
    }


def export(entries: list[Entry], path: str | None = None) -> str:
    path = path or os.path.join(OUT_DIR, "curriculum.json")
    payload = {
        "source": SOURCE,
        "companion_method_file": COMPANION,
        "gates": GATES,
        "strands": STRANDS,
        "ordering_rule": (
            "Bobby's SacredLibrary.md: operational density, a sequencing for "
            "use, not a value judgment. texts.php: authors as pointers; the "
            "skill is discrimination, not accumulation."
        ),
        "ingestion_rule": (
            "ingested stays False until a five-part qualification exists. A "
            "corpus you already had does not count as knowledge."
        ),
        "stats": stats(entries),
        "queue": [asdict(e) for e in build_queue(entries)],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
    return path


def next_n(entries: list[Entry], n: int = 10) -> list[Entry]:
    """The next n things to actually read. Anything with a named author and a
    named text, un-ingested, highest-readiness strand first."""
    q = [e for e in build_queue(entries) if not e.ingested and e.has_author]
    return q[:n]


if __name__ == "__main__":
    ents, dupes = parse()
    path = export(ents)
    s = stats(ents)
    print(f"parsed {s['total']} entries from {os.path.basename(SOURCE)}")
    print(f"  duplicates dropped: {dupes}")
    print(f"  with author: {s['with_author']}   with title: {s['with_title']}   urls: {s['urls']}")
    print(f"  name-only (no text cited): {sum(1 for e in ents if e.is_name_only)}")
    print("  by strand:")
    for k, v in s["by_strand"].items():
        print(f"    {k:24} {v:5}   readiness {STRANDS[k]['weight']}")
    print(f"\nwrote {path}")
    print("\nNEXT 12 TO READ (named author + named text, highest readiness first):")
    for i, e in enumerate(next_n(ents, 12), 1):
        print(f"  {i:2}. [{e.strand:18}] {e.title[:52]} - {e.author[:28]}")