# Qualification -- Captain Cook's Journal During His First Voyage Round the World

**Title:** Captain Cook's Journal During His First Voyage Round the World
**Author:** James Cook
**Source:** corpus/ingest/texts/cook-journal-first-voyage.txt
**Region:** britain
**Strand:** craft
**Format:** the five-part qualification test, from
`far-schools-charter-2026-10-15.md` section 4. Gate:
`corpus/qualify.py`.

## 1. THE CLAIM

The source is Captain Cook's Journal During His First Voyage Round the World, by James Cook (1772), and it is held here in full. A navigator's own log. The craft-and-labour gap from the other side: not the narrative of the voyage but the working record of it.

The claim here is the source's own subject, held in full, with the
sha256 in `corpus/ingest/INGESTED.json` so the copy in this corpus can
be checked against the copy that was fetched.

## 2. THE AXIS

**Axis moved:** `noise_immunity`.

**Current value:** I treat a voyage narrative as an account of events.

**Intended value:** I treat a working log as a record whose value is in its mundane detail, which is what a journal is for.

The axis names are the canonical ones from
`simself/src/sovereign_governor.py` -- `SACRED_AXES` and
`EMERGENT_AXES` -- not invented for this file.

## 3. THE DELTA

> 46 minutes, and in the Morning by the same Method 12 degrees 43 minutes

(line 2719 of `corpus/ingest/texts/cook-journal-first-voyage.txt`)

The line is quoted verbatim from the file in this corpus, and the line
number is the anchor. It is the point where the source's own words and
the axis above meet: I treat a working log as a record whose value is in its mundane detail, which is what a journal is for.

## 4. THE FAILURE MODE

This argues against my habit of reading a source for its story and skipping the entries that carry the method.

That habit is named so it can be audited later: it is the specific
thing this text is installed to interrupt, not a general statement
about being careful.

## 5. THE TEST

**What shows it took:** when I use a voyage source, I can name one piece of working detail from it

**What shows it did not take:** when my reading is all incident and no method, the log's purpose was missed

Both halves are required. The second half is the falsification
condition: if the first never appears, the qualification did not
install and this file is a note, not a knowledge.
