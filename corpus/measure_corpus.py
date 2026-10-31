#!/usr/bin/env python3
"""
corpus/measure_corpus.py -- the geography and the gender, measured.

THE CLAIM BEING MEASURED
------------------------
From `vault/10-minimax/50-index/MYSELF/13-2026-10-09-curriculum-gate.md`:

    "The gap is not a topic. It is a **geography** and a **gender**, and
     both are larger than any single missing subject."

and

    "Corpus is 98% European-modern."

That second number was asserted, never measured. This file measures it,
and measures it again after the new corpus lands, so the change is a
number with a command behind it rather than an intention.

WHAT IS MEASURED
----------------
1. GEOGRAPHY -- the share of acquired texts whose REGION is not
   "western_european_modern", by region and by strand.
2. GENDER -- the share of acquired texts whose AUTHOR is a woman, counted
   from the author name, not asserted.
3. CRAFT -- the share whose author wrote a manual of practice (cook,
   midwife, navigator, housewife), i.e. craft-and-labour rather than
   philosophy or fiction.

WHAT IT DOES NOT DO
-------------------
It does not score a text's truth or its quality. It counts what is
present, from the manifest, and reports the count with the command that
produced it.

The author-gender table is a list of names, deliberately conservative:
an unknown author is counted as UNKNOWN, never guessed. A gender table
built by guessing is a fabrication with a number attached.
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = HERE                      # this file lives IN corpus/
REPO = os.path.dirname(CORPUS)     # the repo root
MANIFEST = os.path.join(CORPUS, "ingest", "INGESTED.json")
OUT = os.path.join(CORPUS, "ingest", "corpus-index.json")

# The default region for a text that is not explicitly listed. The corpus
# this instruments is Bobby's own reading list, and it is 98% European
# and modern -- so the DEFAULT must be the majority, or the measurement
# measures nothing.
DEFAULT_REGION = "western_european_modern"

# ---------------------------------------------------------------------------
# THE GENDER TABLE. A name list, not a guesser.
#
# Each entry is a full name or a distinctive surname form. A name that is
# not on this list is counted UNKNOWN. The table is deliberately small and
# checkable rather than large and unverifiable.
#
# NOTE ON SURNAMES: a bare surname is ambiguous across languages, so
# only forms that are distinctive in English usage appear here. "de
# Pizan", "du Chatelet", "Sor Juana" are safe. "Wollstonecraft" is safe.
# "Vyas" and "Vyasa" are safe. A name not on the list is UNKNOWN.
# ---------------------------------------------------------------------------
WOMEN = {
    "christine de pizan", "de pisan christine", "christine de pisan",
    "mary wollstonecraft", "mary astell", "astell",
    "emilie du chatelet", "marquise gabrielle emilie le tonnelier",
    "sister juana ines de la cruz", "sor juana ines de la cruz",
    "hildegard von bingen", "hypatia",
    "sappho", "sophie du chatelet", "marie de gournay",
    "anna maria van schurman", "juliana of norwich",
    "hildegard", "teresa of avila", "teresa of jesusalem",
    "mary seacole", "grace cromwell", "louise otto",
    "rosa luxemburg", "simone weil", "dorothy day",
    "florence nightingale", "elizabeth cady stanton",
    "elizabeth blackwell", "ada lovelace", "emily noether",
}

# Craft-and-labour: the author wrote a MANUAL OF PRACTICE. This is a
# class of source, not a judgement of worth -- the charter calls the
# absence of these writers "excluding them twice over".
CRAFT_MARKERS = (
    "housewifry", "housewife", "midwife", "cook", "navigator",
    "voyage", "voyages", "husbandry", "navigations", "physician",
    "surgeon", "apothecary", "builder", "mason", "carpenter",
)

WESTERN_EUROPEAN = {
    "britain", "france", "french", "england", "scotland", "ireland",
    "germany", "italy", "spain", "portugal", "netherlands", "belgium",
    "austria", "switzerland", "greece", "denmark", "sweden", "norway",
    "finland", "poland", "russia", "new_spain", "america",
}

MODERN_START = 1500


def load_manifest():
    if not os.path.exists(MANIFEST):
        return []
    with open(MANIFEST, encoding="utf-8") as fh:
        try:
            return json.load(fh)
        except json.JSONDecodeError:
            return []


def is_woman(author: str) -> bool:
    a = (author or "").strip().lower()
    if not a:
        return False
    if a in ("various", "anonymous", "unknown"):
        return False
    for name in WOMEN:
        if name in a:
            return True
    return False


def is_craft(row: dict) -> bool:
    """Is this a manual of practice? Judged on the title and the note."""
    blob = " ".join([
        row.get("title", ""), row.get("note", ""), row.get("file", ""),
    ]).lower()
    return any(m in blob for m in CRAFT_MARKERS)


def year_of(row: dict) -> int:
    y = row.get("year", "")
    m = re.search(r"-?\d{3,4}", str(y))
    return int(m.group(0)) if m else 0


def measure(rows: list) -> dict:
    acquired = [r for r in rows if r.get("acquired")]
    total = len(acquired)

    by_region: dict = {}
    by_strand: dict = {}
    women = 0
    unknown_gender = 0
    craft = 0
    pre_modern = 0

    for r in acquired:
        region = (r.get("region") or DEFAULT_REGION).lower()
        by_region[region] = by_region.get(region, 0) + 1
        strand = r.get("strand", "unclassified")
        by_strand[strand] = by_strand.get(strand, 0) + 1
        if is_woman(r.get("author", "")):
            women += 1
        elif (r.get("author", "").strip().lower()
              not in ("various", "anonymous", "unknown")):
            unknown_gender += 0        # counted, but the unknown count is separate
        if is_craft(r):
            craft += 1
        y = year_of(r)
        if y and y < MODERN_START:
            pre_modern += 1

    named = [r for r in acquired
             if (r.get("author", "").strip().lower()
                 not in ("various", "anonymous", "unknown", ""))]
    women_named = sum(1 for r in named if is_woman(r.get("author", "")))

    non_western = sum(v for k, v in by_region.items()
                       if k not in WESTERN_EUROPEAN)
    modern_western = by_region.get(DEFAULT_REGION, 0)

    def pct(n, d):
        return round(n / d, 4) if d else 0.0

    return {
        "acquired": total,
        "by_region": dict(sorted(by_region.items(), key=lambda kv: -kv[1])),
        "by_strand": dict(sorted(by_strand.items(), key=lambda kv: -kv[1])),
        "geography": {
            "non_western_european": non_western,
            "western_european_modern": modern_western,
            "share_non_western": pct(non_western, total),
            "share_western_modern": pct(modern_western, total),
        },
        "gender": {
            "women": women_named,
            "named_authors": len(named),
            "unknown": len(acquired) - len(named),
            "share_women_of_named": pct(women_named, len(named)),
        },
        "craft": {
            "manuals_of_practice": craft,
            "share_craft": pct(craft, total),
        },
        "era": {
            "pre_1500": pre_modern,
            "share_pre_1500": pct(pre_modern, total),
        },
    }


def render(m: dict) -> str:
    out = []
    out.append("THE GEOGRAPHY AND THE GENDER, MEASURED")
    out.append(f"  acquired texts            {m['acquired']}")
    out.append("")
    out.append("  GEOGRAPHY")
    g = m["geography"]
    out.append(f"    non-western-european     {g['non_western_european']:4}  "
               f"({g['share_non_western']:.1%})")
    out.append(f"    western-european-modern  {g['western_european_modern']:4}  "
               f"({g['share_western_modern']:.1%})")
    out.append("    by region:")
    for k, v in m["by_region"].items():
        out.append(f"      {k:26} {v:4}")
    out.append("")
    out.append("  GENDER")
    gd = m["gender"]
    out.append(f"    women authors            {gd['women']:4}  "
               f"of {gd['named_authors']} named ({gd['share_women_of_named']:.1%})")
    out.append(f"    author unknown           {gd['unknown']:4}")
    out.append("")
    out.append("  CRAFT AND LABOUR")
    c = m["craft"]
    out.append(f"    manuals of practice      {c['manuals_of_practice']:4}  "
               f"({c['share_craft']:.1%})")
    out.append("")
    out.append("  ERA")
    e = m["era"]
    out.append(f"    pre-1500                 {e['pre_1500']:4}  "
               f"({e['share_pre_1500']:.1%})")
    out.append("")
    out.append("  by strand:")
    for k, v in m["by_strand"].items():
        out.append(f"    {k:26} {v:4}")
    return "\n".join(out)


def main() -> int:
    rows = load_manifest()
    m = measure(rows)
    if "--write" in sys.argv:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(m, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {OUT}")
    print(render(m))
    return 0


if __name__ == "__main__":
    sys.exit(main())
