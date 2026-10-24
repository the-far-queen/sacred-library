"""
inv.py — the engineering-school invention-record schema, compiler, and gate.

Same gate shape as the law citation gate and the medical anatomy gate:
a claim without a source is refused, and a license is never upgraded
from what the source actually carries.

The engineering-specific rule is the date ordering: you cannot build
before you conceive. That single check is what separates an invention
record from a filing receipt.
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
DISCIPLINES_DIR = os.path.join(REPO, "disciplines")

DISCIPLINES = [
    "mechanical",
    "electrical",
    "civil",
    "chemical",
    "biomedical",
    "thermal",
    "optical",
    "acoustic",
    "control",
    "computing",
    "manufacturing",
    "fieldcore-link",
]

STATUSES = [
    "conceived", "prototyped", "built", "tested",
    "filed", "granted", "abandoned",
]

OFFICES = ["uspto", "epo", "wipo", "ukipo", "jpo", "other"]

LICENSES = ["ours", "public-domain", "cc-by", "cc-by-sa", "cc-by-nc-sa", "other"]

LICENSE_RANK = {
    "public-domain": 5,
    "ours": 4,
    "cc-by": 3,
    "cc-by-sa": 2,
    "cc-by-nc-sa": 1,
    "other": 0,
}

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass
class PriorArt:
    """something that existed before our invention. the novelty check."""
    citation: str
    relation: str = ""       # anticipates, discloses, teaches, ...
    source_url: str = ""
    license: str = ""

    def is_empty(self) -> bool:
        return not (self.citation or self.source_url)


@dataclass
class Invention:
    """what we built, and when."""
    title: str
    discipline: str
    status: str = "conceived"
    date_conceived: str = ""
    date_built: str = ""
    summary: str = ""
    test_case: str = ""          # the falsifiable check. empty = decoration.
    prior_art: List[PriorArt] = field(default_factory=list)
    filing_office: str = ""
    filing_number: str = ""
    filing_url: str = ""
    source_license: str = "ours"

    def invention_id(self) -> str:
        h = hashlib.sha256(
            f"{self.title}|{self.discipline}".lower().encode("utf-8")
        ).hexdigest()
        return f"inv-{h[:12]}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Verdict:
    allow: bool
    reasons: List[str] = field(default_factory=list)
    invention_id: str = ""

    @classmethod
    def of(cls, allow: bool, reasons: List[str], invention_id: str = "") -> "Verdict":
        return cls(allow=allow, reasons=reasons, invention_id=invention_id)

    def __str__(self) -> str:
        return f"{'ALLOW' if self.allow else 'DENY'} {self.invention_id} {self.reasons}"


def _disciplines_on_disk() -> List[str]:
    if not os.path.isdir(DISCIPLINES_DIR):
        return []
    return sorted(
        d for d in os.listdir(DISCIPLINES_DIR)
        if os.path.isdir(os.path.join(DISCIPLINES_DIR, d))
    )


def _parse(d: str) -> Optional[date]:
    try:
        return date.fromisoformat(d)
    except (TypeError, ValueError):
        return None


def gate(inv: Invention, on_disk: Optional[List[str]] = None) -> Verdict:
    r: List[str] = []

    if not inv.title.strip():
        r.append("no_title")

    disk = on_disk if on_disk is not None else _disciplines_on_disk()
    if disk:
        if not inv.discipline:
            r.append("no_discipline")
        elif inv.discipline not in disk:
            r.append(f"unknown_discipline:{inv.discipline}")

    if inv.status not in STATUSES:
        r.append(f"unknown_status:{inv.status}")

    # --- dates are the substance ---
    dc = _parse(inv.date_conceived)
    db = _parse(inv.date_built)
    if not inv.date_conceived:
        r.append("no_date_conceived")
    elif dc is None:
        r.append(f"bad_date_conceived:{inv.date_conceived}")
    if not inv.date_built:
        r.append("no_date_built")
    elif db is None:
        r.append(f"bad_date_built:{inv.date_built}")

    # you cannot build before you conceive
    if dc and db and db < dc:
        r.append("built_before_conceived")

    # anything past "prototyped" should be able to say how we know
    if inv.status in ("built", "tested", "filed", "granted") and not inv.test_case:
        r.append("no_test_case")

    # a filing needs an office and something to click
    if inv.status in ("filed", "granted"):
        if not inv.filing_office:
            r.append("no_filing_office")
        elif inv.filing_office not in OFFICES:
            r.append(f"unknown_office:{inv.filing_office}")
        if not inv.filing_url:
            r.append("no_filing_url")

    for i, pa in enumerate(inv.prior_art):
        if pa.is_empty():
            r.append(f"empty_prior_art:{i}")
        if not pa.license:
            r.append(f"no_prior_art_license:{i}")

    if not inv.source_license:
        r.append("no_license")
    elif inv.source_license not in LICENSES:
        r.append(f"unknown_license:{inv.source_license}")

    return Verdict.of(not r, r, inv.invention_id())


def gate_license_never_upgraded(claimed: str, source_license: str) -> Verdict:
    if claimed in LICENSE_RANK and source_license in LICENSE_RANK:
        if LICENSE_RANK[claimed] > LICENSE_RANK[source_license]:
            return Verdict.of(False, [f"license_upgrade:{source_license}->{claimed}"])
    return Verdict.of(True, [])


def load_inventions(discipline: str) -> List[Invention]:
    path = os.path.join(DISCIPLINES_DIR, discipline, "inventions.json")
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    out = []
    for d in (raw if isinstance(raw, list) else raw.get("inventions", [])):
        d = dict(d)
        d.pop("invention_id", None)
        d["prior_art"] = [PriorArt(**pa) if isinstance(pa, dict) else pa
                          for pa in d.get("prior_art", [])]
        out.append(Invention(**d))
    return out


def save_inventions(discipline: str, invs: List[Invention]) -> str:
    d = os.path.join(DISCIPLINES_DIR, discipline)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "inventions.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump([i.to_dict() for i in invs], f, indent=2, ensure_ascii=False)
    return path


def _main(argv: List[str]) -> int:
    if not argv:
        print(__doc__)
        print("usage: inv.py gate <file.json> | inv.py list | inv.py init")
        return 1
    cmd = argv[0]

    if cmd == "list":
        print("disciplines:")
        for d in _disciplines_on_disk():
            print(f"  {d:16s} {len(load_inventions(d)):5d} inventions")
        return 0

    if cmd == "init":
        os.makedirs(DISCIPLINES_DIR, exist_ok=True)
        for d in DISCIPLINES:
            sub = os.path.join(DISCIPLINES_DIR, d)
            os.makedirs(os.path.join(sub, "notes"), exist_ok=True)
            readme = os.path.join(sub, "README.md")
            if not os.path.exists(readme):
                with open(readme, "w", encoding="utf-8") as f:
                    f.write(f"# {d}\n\nEngineering discipline. Inventions in "
                            "`inventions.json`, derivations in `notes/`.\n")
        print(f"initialized {len(DISCIPLINES)} disciplines under {DISCIPLINES_DIR}")
        return 0

    if cmd == "gate":
        if len(argv) < 2:
            print("gate: need a file")
            return 1
        with open(argv[1], encoding="utf-8") as f:
            raw = json.load(f)
        raw.pop("invention_id", None)
        raw["prior_art"] = [PriorArt(**pa) if isinstance(pa, dict) else pa
                            for pa in raw.get("prior_art", [])]
        v = gate(Invention(**raw))
        print(v)
        return 0 if v.allow else 2

    print(f"unknown command: {cmd}")
    return 1


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
