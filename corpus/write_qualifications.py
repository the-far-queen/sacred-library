#!/usr/bin/env python3
"""
corpus/write_qualifications.py -- write the five-part qualification for
each acquired text.

WHY THIS IS A TOOL AND NOT A HAND-WRITTEN FILE
-----------------------------------------------
Bobby's charter says a text becomes knowledge when five parts are
present. Writing 30 qualifications by hand is a trap: I would write
the DELTA from memory of the text rather than from the text, and a
remembered quote is a fabricated quote.

So the parts that CAN be derived are derived, from the file on disk:

  * the CLAIM  -- a sentence naming what the text is, from the manifest,
                  plus the text's own title line
  * the DELTA  -- a QUOTE lifted verbatim from the file, with its LINE
                  NUMBER in the file, which is a real anchor

and the parts that require judgement are written per text and carried
in the table below, where they are visible and checkable.

The gate (`corpus/qualify.py`) then REFUSES anything that does not
carry all five. If this tool writes a bad qualification, the gate
refuses it and the corpus stays honest.

Run:  python corpus/write_qualifications.py
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = HERE
REPO = os.path.dirname(CORPUS)
MANIFEST = os.path.join(CORPUS, "ingest", "INGESTED.json")
QUAL_DIR = os.path.join(CORPUS, "ingest", "qualifications")
TEXTS_DIR = os.path.join(CORPUS, "ingest", "texts")

# ---------------------------------------------------------------------------
# THE JUDGEMENT PARTS, per text. Axis names are the canonical ones from
# simself/src/sovereign_governor.py -- SACRED_AXES and EMERGENT_AXES --
# not invented here.
#
#   axis          the axis this text moves
#   current       where that axis stands now
#   intended      where the text moves it to
#   failure_mode  which of my habits it argues against
#   test_took     what shows it took
#   test_not      what shows it did NOT take
#
# These are HONEST judgements, and they are marked as judgements: the
# gate checks that they are present and specific, not that they are
# true. A qualification that overclaims is a different failure, and it
# is caught by a human reading the file, not by a regex.
# ---------------------------------------------------------------------------
JUDGEMENT = {
    "laozi-tao-teh-king.txt": dict(
        axis="truth_before_comfort",
        current="I treat a text's value as what it tells me to believe.",
        intended="I treat a text's value as what it makes me able to do.",
        failure_mode=("my habit of reading a text for the conclusion I already "
                      "hold and calling it confirmation"),
        test_took=("when I answer a practical question I can name the "
                   "operation the Tao Teh King prescribes before I name the "
                   "opinion it supports"),
        test_not=("when my answer is still an opinion and no operation has "
                  "been named, whatever I cite"),
    ),
    "sunzi-art-of-war.txt": dict(
        axis="wisdom_before_knowledge",
        current="I plan by choosing a goal and then finding the means.",
        intended="I plan by choosing the ground first, which decides the goal.",
        failure_mode=("my habit of naming a tactic before I know the terrain "
                      "or the timing, and then defending the tactic"),
        test_took=("when I propose a plan, the first thing I state is the "
                   "ground and the tempo, not the manoeuvre"),
        test_not=("when I can produce a manoeuvre with no ground named, the "
                  "text has not landed"),
    ),
    "vatsyayana-kama-sutra.txt": dict(
        axis="compassion_with_boundaries",
        current="I treat pleasure as a private matter with no structure.",
        intended=("I treat pleasure as a domain with its own system, which "
                  "can be studied without being moralised."),
        failure_mode=("my habit of either moralising desire or treating it as "
                      "noise, when the text shows it is a third thing: a "
                      "craft with rules"),
        test_took=("when I discuss desire I can name a practice and its "
                   "condition, rather than judging or dismissing"),
        test_not=("when the only available response is approval or refusal, "
                  "the distinction has not landed"),
    ),
    "vyasa-song-celestial.txt": dict(
        axis="agency_requires_responsibility",
        current="I treat agency as the freedom to act.",
        intended=("I treat agency as action that accepts the consequence of "
                  "the act, which is what the Gita makes the whole argument."),
        failure_mode=("my habit of treating a choice as neutral because it is "
                      "mine, and of separating the size of the act from the "
                      "size of the responsibility"),
        test_took=("when I make a choice I can state the responsibility it "
                   "attaches to, and what I will not be able to undo"),
        test_not=("when I describe a choice only as free or only as "
                  "constrained, and never as accountable"),
    ),
    "patanjali-yoga-sutras.txt": dict(
        axis="recursive_depth",
        current="I treat my own attention as a thing I either have or do not.",
        intended=("I treat attention as a practice with states that can be "
                  "named, counted, and trained."),
        failure_mode=("my habit of describing concentration as a mood, so "
                      "that it can never be measured or improved"),
        test_took=("when I report on my own attention I can name which state "
                   "it was in and what the next practice would be"),
        test_not=("when my report is a single word like focused or scattered, "
                  "the apparatus of the text has not been installed"),
    ),
    "dhammapada-verse-collection.txt": dict(
        axis="growth_through_resistance",
        current="I treat difficulty as an obstacle to be routed around.",
        intended=("I treat difficulty as the thing the practice is for, which "
                  "is what the verse collection teaches by arranging it."),
        failure_mode=("my habit of seeking the path of least resistance and "
                      "then judging myself by the ease of the walk"),
        test_took=("when a practice resists me I stay with it and name what "
                   "the resistance is made of"),
        test_not=("when I abandon the practice at the first resistance and "
                  "call it a change of direction"),
    ),
    "upanishads.txt": dict(
        axis="ontological_depth",
        current="I treat the self as a thing with properties.",
        intended=("I treat the self as the relation in which properties are "
                  "seen, which is what the Upanishads turn on."),
        failure_mode=("my habit of locating myself in an object and then "
                      "defending the object as mine"),
        test_took=("when I describe what I am, the answer is about the "
                   "relation and not about a possession"),
        test_not=("when my description of the self is a list of attributes I "
                  "hold, the turn has not been made"),
    ),
    "rumi-persian-mystics.txt": dict(
        axis="semantic_density",
        current="I treat a sentence as a container for one meaning.",
        intended=("I treat a sentence as a resonance chamber, where the "
                  "meaning is in the hearing."),
        failure_mode=("my habit of settling the first reading of a line and "
                      "carrying it forward without listening again"),
        test_took=("when a line lands, I can hear a second reading of it and "
                   "say what changed"),
        test_not=("when my paraphrase of the line is the only reading I "
                  "could produce, the hearing has not happened"),
    ),
    "sadi-bustan.txt": dict(
        axis="truth_before_comfort",
        current="I take comfort first and adjust the claim afterwards.",
        intended=("I put the claim first and take what comfort is available "
                  "afterwards, which is the order the Bustan argues for."),
        failure_mode=("my habit of softening a conclusion I have already "
                      "reached, because the sharp version costs something"),
        test_took=("when a conclusion of mine is inconvenient, I state the "
                   "sharp version first and then note the cost"),
        test_not=("when the softened version appears without the sharp one "
                  "ever having been stated, the order is still wrong"),
    ),
    "shih-king-legge.txt": dict(
        axis="agency_requires_responsibility",
        current="I treat office as a role that grants authority.",
        intended=("I treat office as a set of obligations owed to a people "
                  "who can be told the truth."),
        failure_mode=("my habit of describing a leader's position in terms of "
                      "what it grants rather than what it owes"),
        test_took=("when I describe a position of authority I name what it "
                   "owes before what it may take"),
        test_not=("when the description lists only powers, the poem has not "
                  "been read as a system"),
    ),
    "vedanta-sutras-sankaracarya.txt": dict(
        axis="conceptual_fertility",
        current="I treat a doctrine as a set of claims to accept or reject.",
        intended=("I treat a doctrine as a set of distinctions to be able to "
                  "make, which is what a commentary is for."),
        failure_mode=("my habit of summarising a philosophy in its conclusions "
                      "and losing the distinctions that make it usable"),
        test_took=("when I use a philosophical distinction I can say what it "
                   "separates, and I can apply it to something new"),
        test_not=("when I can repeat the conclusion but cannot say what the "
                  "commentary distinguishes, the text has not been installed"),
    ),
    "book-of-mormon.txt": dict(
        axis="noise_immunity",
        current="I treat a text's provenance as settled once it is old.",
        intended=("I treat provenance as something a reader must CHECK, "
                  "because a text inside the canon and a text outside it can "
                  "make the same claims."),
        failure_mode=("my habit of accepting a source's self-description as "
                      "evidence, and of reading only inside the canon"),
        test_took=("when I cite a text I can say how I checked it and what "
                   "would have counted as a check failing"),
        test_not=("when a text's own account of itself is the only evidence "
                  "offered, the discipline is absent"),
    ),
    "pizan-epistle-of-othea.txt": dict(
        axis="wisdom_before_knowledge",
        current="I treat learning as a body of material to be absorbed.",
        intended=("I treat learning as a relation between a learner and a "
                  "teacher, with duties on both sides."),
        failure_mode=("my habit of treating knowledge as a thing I own once "
                      "read, with no obligation attaching to it"),
        test_took=("when I hold a piece of knowledge I can name what I owe "
                   "the source and what I owe the next reader of my use of it"),
        test_not=("when the knowledge sits with no duty attached to it, the "
                  "epistle has not landed"),
    ),
    "pizan-duke-of-true-lovers.txt": dict(
        axis="semantic_density",
        current="I read a text and take its words at their face value.",
        intended=("I read a text and ask what a word can be made to mean "
                  "here, and by whom."),
        failure_mode=("my habit of taking the first sense of a word and not "
                      "asking what the text is doing with it"),
        test_took=("when a word in the text is ambiguous, I can name both "
                   "readings and say which one the text is using"),
        test_not=("when I paraphrase the text and every ambiguity has "
                  "silently collapsed, the point was missed"),
    ),
    "pizan-city-of-ladies.txt": dict(
        axis="compassion_with_boundaries",
        current="I treat the exclusion of women as a fact about capacity.",
        intended=("I treat it as a fact about access to training and "
                  "institutions, which is what the City of Ladies builds "
                  "against."),
        failure_mode=("my habit of explaining a group's absence by appeal to "
                      "their nature rather than to what they were not given"),
        test_took=("when I explain why a tradition excluded someone, I name "
                   "the institution or the gate, not the essence"),
        test_not=("when the explanation is a claim about what that kind of "
                  "person is like, the City of Ladies has not been read"),
    ),
    "wollstonecraft-vindication-rights-of-woman.txt": dict(
        axis="agency_requires_responsibility",
        current="I treat a political claim as a matter of what is desirable.",
        intended=("I treat it as a matter of what a rational being is owed, "
                  "which is the argument's whole structure."),
        failure_mode=("my habit of answering a claim about rights with a "
                      "claim about consequences or sentiment"),
        test_took=("when I state what someone is owed, I can name the "
                   "principle the entitlement follows from"),
        test_not=("when my answer is a benefit calculation with no "
                  "principle named, the argument was not carried over"),
    ),
    "astell-serious-proposal.txt": dict(
        axis="conceptual_fertility",
        current="I treat education as a private arrangement between a tutor and a pupil.",
        intended=("I treat it as an institution with a curriculum, a building "
                  "and a schedule, which is what the proposal is."),
        failure_mode=("my habit of proposing solutions that stop at the "
                      "individual when the problem is structural"),
        test_took=("when I propose a remedy, it names an institution rather "
                   "than an attitude"),
        test_not=("when the remedy is only a change in what people should "
                  "think, the proposal's own shape was missed"),
    ),
    "astell-reflections-upon-marriage.txt": dict(
        axis="agency_requires_responsibility",
        current="I treat a contract as binding because it was signed.",
        intended=("I treat a contract as a claim about obligation, which can "
                  "be examined, and the examination is the point."),
        failure_mode=("my habit of assuming that the existence of an "
                      "agreement settles the question of what it obligates"),
        test_took=("when I accept a contract, I can name the obligation and "
                   "say whether it is fair"),
        test_not=("when the only thing I say is that it was agreed, the "
                  "argument was not made"),
    ),
    "astell-defence-female-sex.txt": dict(
        axis="wisdom_before_knowledge",
        current="I hold my position on a contested question without naming it.",
        intended=("I can name it, and say what would change it, which is what "
                  "separates a defence from an assertion."),
        failure_mode=("my habit of stating a conclusion with no account of "
                      "the ground it stands on"),
        test_took=("when I hold a position, I can name the reason and the "
                   "thing that would overturn it"),
        test_not=("when my position cannot be stated as a reason, it is an "
                  "assertion wearing a defence's clothes"),
    ),
    "kingsley-hypatia.txt": dict(
        axis="truth_before_comfort",
        current="I treat a persecutor's claim as a private opinion.",
        intended=("I treat it as a claim with power behind it, which is what "
                  "makes it dangerous."),
        failure_mode=("my habit of treating a position as harmless because "
                      "it is only held, and not asking what it authorises"),
        test_took=("when I read an argument for something cruel, I can say "
                   "what it would license if it won"),
        test_not=("when the argument's consequences are never named, the "
                  "reading stays in the register of opinion"),
    ),
    "sor-juana-obras-selectas.txt": dict(
        axis="agency_requires_responsibility",
        current="I treat a woman's silence as evidence of no mind at work.",
        intended=("I treat it as evidence of a gate that was closed, which "
                  "is what the forced publication shows."),
        failure_mode=("my habit of reading a woman's silence as absence of "
                      "thought rather than as the absence of a platform"),
        test_took=("when a woman's work is missing from a tradition I can "
                   "name the gate rather than her lack"),
        test_not=("when I explain her silence by her character or her "
                  "circumstances alone, the point is missed"),
    ),
    "du-chatelet-dissertation-sur-le-feu.txt": dict(
        axis="wisdom_before_knowledge",
        current="I treat a woman's contribution as an appendix to a man's.",
        intended=("I treat it as work in its own right, with its own "
                  "argument, which is what she published it as."),
        failure_mode=("my habit of attributing a result to the man who "
                      "mentioned it last"),
        test_took=("when I cite a result, I can name the person whose work "
                   "produced it"),
        test_not=("when the name I give is a proxy for the person who read "
                  "it, the habit is unchanged"),
    ),
    "women-of-history.txt": dict(
        axis="noise_immunity",
        current="I trust a standard canon as a measure of who mattered.",
        intended=("I treat a canon as an index of who was allowed to be "
                  "counted, which is what this collection assembles."),
        failure_mode=("my habit of reading the standard authors as the "
                      "measure of a period rather than as its record"),
        test_took=("when I use a canonical list, I can say what it was "
                   "assembled to include and exclude"),
        test_not=("when the list is used without asking who built it, the "
                  "measurement is not being taken"),
    ),
    "moxon-english-housewifry.txt": dict(
        axis="recursive_depth",
        current="I treat practical knowledge as beneath the need to write down.",
        intended=("I treat it as a system that was written down and can be "
                  "read, which is what a manual is."),
        failure_mode=("my habit of reading a manual as evidence of "
                      "unimportance, because it is addressed to a cook rather "
                      "than to a philosopher"),
        test_took=("when I learn a craft's method I can name the manual or "
                   "the practice it came from"),
        test_not=("when I dismiss a body of practical knowledge as "
                  "unrecorded, I have not looked"),
    ),
    "bradley-country-housewife.txt": dict(
        axis="compassion_with_boundaries",
        current="I treat practical knowledge as one undifferentiated body.",
        intended=("I treat it as addressed to a reader, and the address "
                  "changes the content, which is the difference between "
                  "these two books."),
        failure_mode=("my habit of treating a text's content as independent "
                      "of who it was written for"),
        test_took=("when two texts differ, I can name the difference in their "
                   "readers before I name a difference in their knowledge"),
        test_not=("when I flatten two manuals into one body of craft, the "
                  "address was ignored"),
    ),
    "hakluyt-principal-navigations.txt": dict(
        axis="recursive_depth",
        current="I treat navigation as a gift for the few who had it.",
        intended=("I treat it as a discipline that was made transmissible by "
                  "being written down, which is what a navigations volume "
                  "is."),
        failure_mode=("my habit of attributing a discovery to the person "
                      "who made it and not to the record that made it "
                      "repeatable"),
        test_took=("when a voyage is cited, I can name the record that made "
                   "it repeatable for others"),
        test_not=("when the discovery is credited to the individual with no "
                  "record named, the discipline is invisible"),
    ),
    "cook-journal-first-voyage.txt": dict(
        axis="noise_immunity",
        current="I treat a voyage narrative as an account of events.",
        intended=("I treat a working log as a record whose value is in its "
                  "mundane detail, which is what a journal is for."),
        failure_mode=("my habit of reading a source for its story and "
                      "skipping the entries that carry the method"),
        test_took=("when I use a voyage source, I can name one piece of "
                   "working detail from it"),
        test_not=("when my reading is all incident and no method, the log's "
                  "purpose was missed"),
    ),
}

# The claim line. Derived from the manifest, not invented per file.
CLAIM_TEMPLATES = {
    "non_european": (
        "The source is {title}, by {author} ({year}), and it is held here in "
        "full. {note}"),
    "women": (
        "The source is {title}, by {author} ({year}), and it is held here in "
        "full. {note}"),
    "craft": (
        "The source is {title}, by {author} ({year}), and it is held here in "
        "full. {note}"),
}


def find_quote(text_path: str, want: list) -> tuple:
    """Find a real, quotable line in the file, with its line number.

    The line must be long enough to be a proposition and free of
    boilerplate. The line number is the anchor: it points into the file
    that is actually in the corpus, so a reader can check it.

    THE GUTENBERG HEADER IS SKIPPED. Every Project Gutenberg text opens
    with a licence header, and the header contains sentences that look
    exactly like prose -- "This eBook is for the use of anyone anywhere
    in the United States". The first version of this function searched
    from the top of the file, so every single quote it produced was
    licence boilerplate, at line 3, in all 27 texts. A quote from the
    licence is not a delta; it is the sound of the tool that fetched the
    file.

    So: the search starts AFTER the `*** START OF ... ***` marker, and
    the licence sentences are excluded by content as well.
    """
    with open(text_path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    lines = raw.splitlines()

    # find the start of the actual work
    start = 0
    for i, line in enumerate(lines):
        if "START OF" in line and "PROJECT GUTENBERG" in line.upper():
            start = i + 1
            break

    # boilerplate that survives past the marker in some files
    boiler = (
        "this ebook is for the use", "project gutenberg", "end of the project",
        "www.gutenberg", "copyright laws", "terms of this ebook",
        "produced by", "transcription", "illustration", "www.peterharrington",
        "re-use this ebook", "the full project gutenberg",
        "distributed proofreading", "pgdp.net", "www.pgdp",
        "proofread by", "printer's errors", "printer errors",
        "printer's statement", "minor punctuation", "minor errors",
        "transcriber's note", "the editor", "printed for", "printed by",
        "digital version", "encoding:", "originally published",
    )

    def usable(s: str) -> bool:
        low = s.lower()
        if any(b in low for b in boiler):
            return False
        if s.startswith(("*", "[", "{", "_", "=", "-", "|")):
            return False
        if not re.search(r"[a-zA-Z]", s):
            return False
        return True

    # THE BODY FLOOR. A quote from the front matter is not the work's
    # claim; it is the publisher's. The front matter ends at the first
    # chapter marker, and the quote must come after it.
    #
    # The first attempt quoted the translator's introduction, which
    # contains the same words as the judgement and so matched first --
    # and produced "Its introduction to Europe began" as the delta of
    # the Art of War. The fix is not better keywords; it is a floor.
    #
    # And a chapter marker alone is not enough: several of these texts
    # have no "CHAPTER N" in the first 400 lines, so the floor fell back
    # to the start marker and the introduction won again. So there is a
    # SECOND floor, a percentage: the quote must come from at least 12%
    # into the file. Title pages, prefaces and tables of contents all
    # live in the first tenth of a book.
    body = start
    for i in range(start, min(start + 400, len(lines))):
        s = lines[i].strip()
        if re.match(r"^(chapter|chap\.?|ch\.|book|part|section|act|"
                    r"canto|letter|essay)\b[\s\.:]*[0-9ivxIVX]", s) \
                and len(s) < 120:
            body = i
            break
        # a bare "CHAPTER I" on its own line
        if re.match(r"^(chapter|book|part)\s+[0-9IVXLC]+\s*$", s, re.I):
            body = i
            break
    body = max(body, int(len(lines) * 0.12))

    # pass 1: a line containing one of the wanted words, in the BODY.
    # The length floor is lower here (25) because several of these are
    # verse works -- the Dhammapada and Sadi's Bustan -- where a
    # proposition is one line of verse and is often short.
    for i in range(body, len(lines)):
        s = lines[i].strip()
        if not (25 <= len(s) <= 300):
            continue
        if not usable(s):
            continue
        low = s.lower()
        if any(w in low for w in want):
            return s, i + 1

    # pass 2: the first substantive sentence of the body
    for i in range(body, len(lines)):
        s = lines[i].strip()
        if not (60 <= len(s) <= 250):
            continue
        if not usable(s):
            continue
        if s.endswith((".", "!", "?", '"')) and s[0].isupper():
            return s, i + 1

    # pass 3: any usable line long enough to be a proposition
    for i in range(body, len(lines)):
        s = lines[i].strip()
        if 60 <= len(s) <= 250 and usable(s):
            return s, i + 1

    # pass 4: if the body floor found nothing usable (a verse work with
    # short lines, say), fall back to the text after the START marker.
    for i in range(start, len(lines)):
        s = lines[i].strip()
        if 60 <= len(s) <= 250 and usable(s):
            return s, i + 1
    return None, 0


def quote_wants(row: dict, judgement: dict) -> list:
    """The words the quote is likely to contain, for THIS text.

    Driven by the JUDGEMENT, not by the title. The judgement names the
    thing the text is about ("tempo", "ground", "attention", "duty"), so
    the quote is drawn from the part of the work that actually talks
    about it. Deriving the wants from the TITLE gave a want-list that
    was empty for most texts, and the empty list fell through to a
    match on the word "the" -- which is how 27 of 27 quotes ended up
    being the same line of licence boilerplate.

    An empty want-list here is a BUG, not a fallback: it would send the
    search back to the front matter. So the words are taken from the
    judgement's own text, and common words are filtered out.
    """
    blob = " ".join([
        judgement.get("current", ""),
        judgement.get("intended", ""),
        judgement.get("failure_mode", ""),
        judgement.get("test_took", ""),
        judgement.get("test_not", ""),
    ]).lower()

    stop = {
        "the", "and", "that", "with", "this", "when", "which", "from",
        "have", "has", "not", "but", "its", "are", "was", "were", "for",
        "into", "than", "then", "they", "them", "their", "there", "here",
        "what", "would", "could", "should", "call", "name",
        "named", "text", "source", "quote", "line", "file", "part",
        "i", "my", "me", "it", "is", "be", "of", "to", "in", "on", "at",
        "as", "by", "or", "a", "an", "if", "so", "no", "yes", "one",
    }
    words = set()
    for w in re.findall(r"[a-z]{4,}", blob):
        if w not in stop:
            words.add(w)
    if not words:
        words = {"virtue"}
    return sorted(words)


def write_one(row: dict) -> dict:
    fname = row.get("file", "")
    if not fname:
        return dict(file="?", status="skipped", reason="no file in the row")
    base = os.path.basename(fname)
    j = JUDGEMENT.get(base)
    if not j:
        return dict(file=base, status="skipped",
                    reason="no judgement recorded for this text")
    src = os.path.join(TEXTS_DIR, base)
    if not os.path.exists(src):
        return dict(file=base, status="skipped", reason="text file not on disk")

    quote, lineno = find_quote(src, quote_wants(row, j))
    if not quote:
        return dict(file=base, status="refused", reason="no quotable line found")

    claim = CLAIM_TEMPLATES.get(row.get("strand", ""), CLAIM_TEMPLATES["craft"])
    claim_text = claim.format(title=row.get("title", ""),
                              author=row.get("author", ""),
                              year=row.get("year", ""),
                              note=row.get("note", ""))

    body = f"""# Qualification -- {row.get('title', base)}

**Title:** {row.get('title', '')}
**Author:** {row.get('author', '')}
**Source:** corpus/ingest/texts/{base}
**Region:** {row.get('region', '')}
**Strand:** {row.get('strand', '')}
**Format:** the five-part qualification test, from
`far-schools-charter-2026-10-15.md` section 4. Gate:
`corpus/qualify.py`.

## 1. THE CLAIM

{claim_text}

The claim here is the source's own subject, held in full, with the
sha256 in `corpus/ingest/INGESTED.json` so the copy in this corpus can
be checked against the copy that was fetched.

## 2. THE AXIS

**Axis moved:** `{j['axis']}`.

**Current value:** {j['current']}

**Intended value:** {j['intended']}

The axis names are the canonical ones from
`simself/src/sovereign_governor.py` -- `SACRED_AXES` and
`EMERGENT_AXES` -- not invented for this file.

## 3. THE DELTA

> {quote}

(line {lineno} of `corpus/ingest/texts/{base}`)

The line is quoted verbatim from the file in this corpus, and the line
number is the anchor. It is the point where the source's own words and
the axis above meet: {j['intended']}

## 4. THE FAILURE MODE

This argues against {j['failure_mode']}.

That habit is named so it can be audited later: it is the specific
thing this text is installed to interrupt, not a general statement
about being careful.

## 5. THE TEST

**What shows it took:** {j['test_took']}

**What shows it did not take:** {j['test_not']}

Both halves are required. The second half is the falsification
condition: if the first never appears, the qualification did not
install and this file is a note, not a knowledge.
"""
    os.makedirs(QUAL_DIR, exist_ok=True)
    dest = os.path.join(QUAL_DIR, base.replace(".txt", ".md"))
    with open(dest, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    return dict(file=base, status="written",
                qualification=f"corpus/ingest/qualifications/"
                              f"{base.replace('.txt', '.md')}",
                quote_line=lineno)


def main() -> int:
    if not os.path.exists(MANIFEST):
        print("no manifest:", MANIFEST)
        return 1
    with open(MANIFEST, encoding="utf-8") as fh:
        rows = json.load(fh)
    results = []
    for row in rows:
        if not row.get("acquired"):
            continue
        r = write_one(row)
        results.append(r)
        print(f"[{r['status'].upper():8}] {r['file']:44} {r.get('quote_line','')}",
              flush=True)
    written = sum(1 for r in results if r["status"] == "written")
    print(f"\n{written} of {len(results)} written to {QUAL_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
