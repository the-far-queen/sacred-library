# corpus/ingest -- the geography and the gender, acquired

**Built 2026-10-29 by Hermes.** This directory holds the material that
fills the two gaps Bobby's own corpus has, per
`vault/10-minimax/50-index/MYSELF/13-2026-10-09-curriculum-gate.md`:

> "The gap is not a topic. It is a **geography** and a **gender**, and
>  both are larger than any single missing subject."

and a third: craft and labour.

## What is here

| path | what |
|---|---|
| `texts/*.txt` | the public-domain source texts, byte-exact as fetched |
| `INGESTED.json` | the receipt: one row per target, with the sha256, the URL, the byte count, and the qualification path |
| `qualifications/*.md` | the five-part qualification for each text |
| `corpus-index.json` | the measurement: the geography, the gender, the craft share |

## THE RULE THIS DIRECTORY ENFORCES

> "A corpus you already had does not count as knowledge."

That sentence is in `corpus/curriculum.py`'s own docstring, and it was
**not implemented** until now: `Entry.ingested` was a field nobody set,
and `stats()["ingested"]` was a hard-coded 0 that read like a
measurement. So the rule is now a gate, in `corpus/qualify.py`:

* a text is **fetched** when its bytes are on disk with a matching sha256
* a text is **qualified** when its qualification carries all five parts
  and the gate accepts it
* a text with bytes and no qualification is **fetched, not qualified** --
  present, and explicitly not yet knowledge

## THE FIVE PARTS

From `far-schools-charter-2026-10-15.md` section 4, quoted:

1. **The claim.** The source asserts it, in the source's own words.
2. **The axis.** Which existing axis it moves; current value; intended value.
3. **The delta.** The line that forces the change, quoted and anchored.
4. **The failure mode.** Which of my current habits it argues against,
   named so it can be audited later.
5. **The test.** What observation shows it took, and what shows it didn't.

> "Four of five is a note."

The gate refuses anything short of five, and names which part is
missing. The delta must be **quoted and anchored** -- a paraphrase is not
a delta, and a quote with no location in the source is not anchored. The
failure mode must **name a habit**. The test must carry **both** halves.

The axis names in the qualifications are the canonical ones from
`simself/src/sovereign_governor.py` (`SACRED_AXES`, `EMERGENT_AXES`) --
not invented for this corpus.

## THE COMMANDS

    python corpus/fetch_corpus.py            # acquire; writes the receipt
    python corpus/fetch_corpus.py --check    # verify the sha256 of what is on disk
    python corpus/write_qualifications.py    # write the five-part qualification
    python corpus/qualify.py                 # the gate's report
    python corpus/measure_corpus.py --write  # the geography/gender measurement
    python -m pytest tests/test_curriculum.py -q
    python tools/mutation_check.py

## WHAT THE ACQUIRER REFUSES

* a fetch that does not return HTTP 200
* a body that does not contain the text's own title marker -- this caught
  two real errors (the markers for Sadi's *Bustan* and de Pizan's *City
  of Ladies* did not account for the diacritics and the French spelling)
* a body under 20,000 bytes: a stub is not a text
* a truncated transfer: the body is read in full and compared against
  the server's Content-Length, because a dropped connection once looked
  exactly like a missing book
* overwriting a file whose TEXT differs from the fetch (a line-ending
  difference is the same text and is not a conflict)

Nothing is fabricated. A source that cannot be reached is recorded with
the reason and counted as **not acquired**.

## WHAT THE QUALIFICATIONS ARE NOT

The claim and the delta are **derived from the file in this corpus** --
the delta is a line quoted verbatim with its line number in the file, so
a reader can check it. The axis, the failure mode and the test are
**judgements**, and they are marked as judgements. The gate checks that
they are present and specific; it does not check that they are true.
A qualification that overclaims is caught by a reader, not by a regex.
