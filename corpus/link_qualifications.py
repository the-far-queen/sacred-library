#!/usr/bin/env python3
"""
corpus/link_qualifications.py -- point the manifest at its qualifications.

`fetch_corpus.py` writes the receipt with an empty `qualification` field,
because at fetch time no qualification exists yet. `write_qualifications.py`
writes the qualifications. This step joins the two, so the gate in
`corpus/qualify.py` can read the manifest and find the qualification for
each acquired text.

The join is by FILE NAME, and it is checked: a manifest row whose
qualification file is not on disk is reported, not silently linked to a
path that does not exist.

Run:  python corpus/link_qualifications.py
"""
from __future__ import annotations

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = HERE
MANIFEST = os.path.join(CORPUS, "ingest", "INGESTED.json")
QUAL_DIR = os.path.join(CORPUS, "ingest", "qualifications")


def main() -> int:
    if not os.path.exists(MANIFEST):
        print("no manifest:", MANIFEST)
        return 1
    with open(MANIFEST, encoding="utf-8") as fh:
        rows = json.load(fh)

    linked = 0
    missing = []
    for row in rows:
        if not row.get("acquired"):
            continue
        base = os.path.basename(row.get("file", ""))
        if not base:
            continue
        cand = os.path.join(QUAL_DIR, base.replace(".txt", ".md"))
        if os.path.exists(cand):
            row["qualification"] = os.path.join(
                "corpus", "ingest", "qualifications",
                base.replace(".txt", ".md")).replace("\\", "/")
            linked += 1
        else:
            missing.append(base)

    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
        fh.write("\n")

    print(f"linked {linked} qualification(s)")
    if missing:
        print(f"MISSING qualification files ({len(missing)}):")
        for m in missing:
            print(f"  {m}")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
