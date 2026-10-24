"""
cite.py — the law-school citation schema, compiler, and gate.

The gate is the repo. Everything else is content that has to pass it.

Design rule: a document that cannot name its jurisdiction and its source
is refused. That single rule is what keeps an AI-written legal corpus
from filling up with plausible-sounding fabrication.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any, Dict, List, Optional

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIVISIONS_DIR = os.path.join(REPO, "divisions")

# ---------------------------------------------------------------------------
# the taxonomy: Yale Law School academic divisions
# ---------------------------------------------------------------------------
DIVISIONS = [
    "constitutional",
    "criminal",
    "corporate",
    "environmental",
    "health",
    "intellectual-property",
    "legislation-policy",
    "litigation",
    "tax",
    "commercial",
    "international",
    "labor",
    "clinical",
]

JURISDICTIONS = [
    "us-federal",
    "us-state-ny", "us-state-ca", "us-state-tx", "us-state-fl",
    "us-state-il", "us-state-ma", "us-state-pa", "us-state-de",
    "uk", "eu", "international", "other",
]

LICENSES = ["public-domain", "cc-by", "cc-by-sa", "cc-by-nc-sa", "other"]

# license ranking: a document may never claim a MORE permissive license
# than its source carries. higher rank = more permissive.
LICENSE_RANK = {
    "public-domain": 4,
    "cc-by": 3,
    "cc-by-sa": 2,
    "cc-by-nc-sa": 1,
    "other": 0,
}

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# A source URL that returns HTTP 200 is not automatically verified.
# uscode.house.gov served 200 with a "Site is currently under
# maintenance" body on 2026-10-06. A page that looks fine until you
# read it is the same failure class as a fabricated citation.
MAINTENANCE_MARKERS = (
    "currently under maintenance",
    "site is temporarily unavailable",
    "temporarily unavailable",
    "service unavailable",
)


@dataclass
class Citation:
    """a single authority reference."""
    reporter: str = ""          # e.g. "410 U.S. 113"
    pin_cite: str = ""          # e.g. "125-26"
    source_url: str = ""        # where the text actually came from
    court: str = ""
    year: Optional[int] = None

    def is_empty(self) -> bool:
        return not (self.reporter or self.source_url)


@dataclass
class Document:
    """anything that enters the repo passes through here."""
    kind: str                    # opinion | statute | term | contract | brief
    title: str
    jurisdiction: str = ""
    division: str = ""
    doc_date: str = ""           # ISO-8601
    license: str = ""
    citation: Citation = field(default_factory=Citation)
    body: str = ""
    extra: Dict[str, Any] = field(default_factory=dict)

    def doc_id(self) -> str:
        """deterministic id from the load-bearing axes, not from the body.
        Two documents with the same jurisdiction/court/date/reporter are
        the same document even if someone reformats the text."""
        parts = [
            self.kind, self.jurisdiction, self.citation.court,
            self.doc_date, self.citation.reporter, self.title,
        ]
        h = hashlib.sha256("|".join(p or "" for p in parts).encode("utf-8"))
        return f"{self.kind}-{h.hexdigest()[:12]}"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["doc_id"] = self.doc_id()
        return d


@dataclass
class Verdict:
    allow: bool
    reasons: List[str] = field(default_factory=list)
    doc_id: str = ""

    @classmethod
    def of(cls, allow: bool, reasons: List[str], doc_id: str = "") -> "Verdict":
        return cls(allow=allow, reasons=reasons, doc_id=doc_id)

    def __str__(self) -> str:
        state = "ALLOW" if self.allow else "DENY"
        return f"{state} {self.doc_id} {self.reasons}"


# ---------------------------------------------------------------------------
# compile
# ---------------------------------------------------------------------------

def compile_doc(kind: str, title: str, **kw) -> Document:
    """build a document. citation may be passed as a dict or a Citation."""
    cit = kw.pop("citation", None)
    if isinstance(cit, dict):
        cit = Citation(**cit)
    elif cit is None:
        cit = Citation()
    return Document(kind=kind, title=title, citation=cit, **kw)


# ---------------------------------------------------------------------------
# gate
# ---------------------------------------------------------------------------

def _divisions_on_disk() -> List[str]:
    if not os.path.isdir(DIVISIONS_DIR):
        return []
    return sorted(
        d for d in os.listdir(DIVISIONS_DIR)
        if os.path.isdir(os.path.join(DIVISIONS_DIR, d))
    )


def looks_like_maintenance(body: str) -> bool:
    """HTTP 200 with an error body is not a working source.

    Offline check: the caller fetches, passes the body here. Kept pure so
    it is testable without network.
    """
    if not body:
        return False
    low = body.lower()
    return any(m in low for m in MAINTENANCE_MARKERS)


def gate(doc: Document, on_disk: Optional[List[str]] = None) -> Verdict:
    """refuse anything that cannot name where it came from."""
    r: List[str] = []
    did = doc.doc_id()

    # 1. jurisdiction required
    if not doc.jurisdiction:
        r.append("no_jurisdiction")
    elif doc.jurisdiction not in JURISDICTIONS:
        r.append(f"unknown_jurisdiction:{doc.jurisdiction}")

    # 2. a source: either a reporter cite or a real URL
    if doc.citation.is_empty():
        r.append("no_citation")
    elif doc.citation.reporter and not doc.citation.source_url:
        # A reporter cite with nowhere to check it is exactly the shape a
        # hallucinated citation takes: it looks right and cannot be verified.
        r.append("unverifiable_cite")

    # 3. opinions need a pin-cite — an unpinned cite is not citable
    if doc.kind == "opinion" and not doc.citation.pin_cite:
        r.append("no_pin_cite")

    # 4. division must exist on disk (if the repo has been scaffolded)
    disk = on_disk if on_disk is not None else _divisions_on_disk()
    if disk:
        if not doc.division:
            r.append("no_division")
        elif doc.division not in disk:
            r.append(f"unknown_division:{doc.division}")

    # 5. license recorded, never blank
    if not doc.license:
        r.append("no_license")
    elif doc.license not in LICENSES:
        r.append(f"unknown_license:{doc.license}")

    # 6. date must parse
    if doc.doc_date:
        if not ISO_DATE.match(doc.doc_date):
            r.append(f"bad_date:{doc.doc_date}")
        else:
            try:
                date.fromisoformat(doc.doc_date)
            except ValueError:
                r.append(f"bad_date:{doc.doc_date}")

    # 7. no claiming a license more permissive than the source
    claimed = doc.extra.get("source_license")
    if claimed and doc.license in LICENSE_RANK and claimed in LICENSE_RANK:
        if LICENSE_RANK[doc.license] > LICENSE_RANK[claimed]:
            r.append(f"license_upgrade:{claimed}->{doc.license}")

    return Verdict.of(not r, r, did)


# ---------------------------------------------------------------------------
# terms
# ---------------------------------------------------------------------------

@dataclass
class Term:
    """a defined legal term. the Black's-Law-Dictionary-shaped object, sourced."""
    term: str
    division: str
    definition: str
    citation: str = ""
    source: str = ""
    license: str = ""
    see_also: List[str] = field(default_factory=list)

    def term_id(self) -> str:
        h = hashlib.sha256(
            f"{self.term}|{self.division}".lower().encode("utf-8")
        ).hexdigest()
        return f"term-{h[:12]}"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["term_id"] = self.term_id()
        return d


def gate_term(t: Term) -> Verdict:
    r: List[str] = []
    if not t.term.strip():
        r.append("no_term")
    if not t.definition.strip():
        r.append("no_definition")
    if not t.source:
        r.append("no_source")
    if not t.license:
        r.append("no_license")
    return Verdict.of(not r, r, t.term_id())


def load_terms(division: str) -> List[Term]:
    """load terms/<division>.json if present."""
    path = os.path.join(DIVISIONS_DIR, division, "terms.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out = []
    for d in raw if isinstance(raw, list) else raw.get("terms", []):
        d = dict(d)
        d.pop("term_id", None)
        out.append(Term(**d))
    return out


def save_terms(division: str, terms: List[Term]) -> str:
    d = os.path.join(DIVISIONS_DIR, division)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "terms.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump([t.to_dict() for t in terms], f, indent=2, ensure_ascii=False)
    return path


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

def _main(argv: List[str]) -> int:
    if not argv:
        print(__doc__)
        print("usage: cite.py gate <file.json> | cite.py list | cite.py init")
        return 1
    cmd = argv[0]

    if cmd == "list":
        print("divisions:")
        for d in _divisions_on_disk():
            n = len(load_terms(d))
            print(f"  {d:24s} {n:5d} terms")
        return 0

    if cmd == "init":
        os.makedirs(DIVISIONS_DIR, exist_ok=True)
        for d in DIVISIONS:
            sub = os.path.join(DIVISIONS_DIR, d)
            os.makedirs(os.path.join(sub, "sources"), exist_ok=True)
            os.makedirs(os.path.join(sub, "cases"), exist_ok=True)
            readme = os.path.join(sub, "README.md")
            if not os.path.exists(readme):
                with open(readme, "w", encoding="utf-8") as f:
                    f.write(f"# {d}\n\nDivision of the far-law taxonomy. "
                            "Terms live in `terms.json`, primary text in "
                            "`cases/`, open textbooks in `sources/`.\n")
        print(f"initialized {len(DIVISIONS)} divisions under {DIVISIONS_DIR}")
        return 0

    if cmd == "gate":
        if len(argv) < 2:
            print("gate: need a file")
            return 1
        with open(argv[1], encoding="utf-8") as f:
            raw = json.load(f)
        raw.pop("doc_id", None)
        cit = raw.pop("citation", {}) or {}
        doc = Document(citation=Citation(**cit), **raw)
        v = gate(doc)
        print(v)
        return 0 if v.allow else 2

    print(f"unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
