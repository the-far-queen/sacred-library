#!/usr/bin/env python3
"""
corpus/fetch_corpus.py -- acquire public-domain texts, with a receipt.

WHY A RECEIPT
-------------
A text in a corpus is not knowledge, and a text in a corpus that nobody
can verify is not even a text. So every file this fetches carries a
sha256 in `corpus/ingest/INGESTED.json`, and the fetcher checks the
fetched file against its own title line. A source that returns 200 with
the wrong body is recorded as FAILED, not as a text.

WHAT IT REFUSES
----------------
* a fetch that does not return HTTP 200
* a body that does not contain the expected title marker
* a body under a floor size (a stub is not a text)
* writing over an existing file whose bytes differ from the fetch

Nothing is fabricated. If a source is unavailable, the manifest says so
with the reason, and the text is listed as NOT ACQUIRED.

Run:  python corpus/fetch_corpus.py            (fetch everything in TARGETS)
      python corpus/fetch_corpus.py --check    (verify what is on disk)
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS = HERE                      # this file lives IN corpus/
REPO = os.path.dirname(CORPUS)     # the repo root
OUT_DIR = os.path.join(CORPUS, "ingest", "texts")
MANIFEST = os.path.join(CORPUS, "ingest", "INGESTED.json")
QUAL_DIR = os.path.join(CORPUS, "ingest", "qualifications")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) sacred-library-acquirer/1.0"
MIN_BYTES = 20000

# ---------------------------------------------------------------------------
# The target list. Each entry names what it is, not just a file.
#
# `strand` is the geography/gender/craft gap this text fills. The three
# gaps are Bobby's own, from vault/10-minimax/50-index/MYSELF/
# 13-2026-10-09-curriculum-gate.md: "The gap is not a topic. It is a
# geography and a gender, and both are larger than any single missing
# subject."
# ---------------------------------------------------------------------------
TARGETS = [
    # ---------------- non-European systematic thought ----------------------
    dict(file="laozi-tao-teh-king.txt", gut=216,
         title="Tao Teh King", author="Laozi", year="-500",
         strand="non_european", region="china",
         marker="TAO TEH KING",
         note="The Tao and its Characteristics. The canonical translation by "
              "James Legge. Non-European systematic thought: the first "
              "Western systematic text to be read as a whole."),
    dict(file="sunzi-art-of-war.txt", gut=132,
         title="The Art of War", author="Sunzi", year="-500",
         strand="non_european", region="china",
         marker="ART OF WAR",
         note="The oldest military treatise in the world. A strategy text "
              "whose entire subject is tempo and deception, not force."),
    dict(file="vatsyayana-kama-sutra.txt", gut=27827,
         title="The Kama Sutra of Vatsyayana", author="Vatsyayana", year="-300",
         strand="non_european", region="india",
         marker="KAMA SUTRA",
         note="Indian systematic thought on desire and conduct. The "
              "elephant-in-the-room of the canon, and the clearest case "
              "that a tradition can hold a topic without a taboo."),
    dict(file="vyasa-song-celestial.txt", gut=2388,
         title="The Song Celestial; Or, Bhagavad-Gita", author="Vyasa", year="-200",
         strand="non_european", region="india",
         marker="SONG CELESTIAL",
         note="The Bhagavad-Gita. Indian systematic thought on duty and "
              "the two poles of a battlefield."),
    dict(file="patanjali-yoga-sutras.txt", gut=2526,
         title="The Yoga Sutras of Patanjali", author="Patanjali", year="-200",
         strand="non_european", region="india",
         marker="YOGA SUTRA",
         note="Indian systematic psychology. Embodied cognition written as "
              "a set of numbered aphorisms and a systematic practice."),
    dict(file="dhammapada-verse-collection.txt", gut=2017,
         title="Dhammapada, a Collection of Verses", author="Anonymous", year="-300",
         strand="non_european", region="india",
         marker="DHAMMAPADA",
         note="Buddhist systematic thought as a verse collection. The "
              "earliest Buddhist canonical text, in translation."),
    dict(file="upanishads.txt", gut=3283,
         title="The Upanishads", author="Anonymous", year="-600",
         strand="non_european", region="india",
         marker="UPANISHAD",
         note="The philosophical core of the Vedas. Indian systematic "
              "thought on the relation between the self and the world."),
    dict(file="rumi-persian-mystics.txt", gut=45159,
         title="The Persian Mystics: Jalal al-Din Rumi", author="Rumi", year="1300",
         strand="non_european", region="persia",
         marker="RUMI",
         note="Persian systematic mysticism. The Masnavi material, with "
              "the discipline of listening that the couplet form demands."),
    dict(file="sadi-bustan.txt", gut=60471,
         title="The Bustan of Sadi", author="Sadi", year="1258",
         strand="non_european", region="persia",
         marker="BUST",
         note="Persian systematic ethics in verse. Sadi is the tradition's "
              "own jurist as well as its poet."),
    dict(file="shih-king-legge.txt", gut=9394,
         title="The Shih King, or, Book of Poetry", author="Legge (trans.)",
         year="-1000",
         strand="non_european", region="china",
         marker="SHIH KING",
         note="Chinese systematic thought on the person in office, "
              "translated by Legge alongside the Tao Teh King."),
    dict(file="vedanta-sutras-sankaracarya.txt", gut=16295,
         title="The Vedanta-Sutras with the Commentary by Sankaracarya",
         author="Sankaracarya", year="800",
         strand="non_european", region="india",
         marker="VEDANTA",
         note="Indian systematic philosophy in its classical form: the "
              "commentary that fixed what the Upanishads mean."),
    dict(file="book-of-mormon.txt", gut=17,
         title="The Book of Mormon", author="Anonymous", year="1830",
         strand="non_european", region="america",
         marker="BOOK OF MORMON",
         note="A nineteenth-century American systematic text with a "
              "non-European cosmology, and the sharpest adversarial case "
              "for the corpus: a text produced inside the English "
              "language but outside its canon."),

    # ---------------- women -------------------------------------------------
    dict(file="pizan-epistle-of-othea.txt", gut=60567,
         title="The Epistle of Othea to Hector; or, The Boke of Knyghthode",
         author="Christine de Pizan", year="1400",
         strand="women", region="france",
         marker="OTHEA",
         note="A woman's systematic thought on education, written as an "
              "epistle between a mother and a son."),
    dict(file="pizan-duke-of-true-lovers.txt", gut=36737,
         title="The Book of the Duke of True Lovers", author="Christine de Pizan",
         year="1400",
         strand="women", region="france",
         marker="DUKE OF TRUE LOVERS",
         note="The first French novel of ideas by a woman, and an "
              "allegory in which the narrator's own gendered position is "
              "the argument."),
    dict(file="pizan-city-of-ladies.txt", gut=26608,
         title="Le tresor de la cite des dames", author="Christine de Pizan",
         year="1405",
         strand="women", region="france",
         marker="DAMES",
         note="The City of Ladies. A woman's systematic thought on the "
              "sciences, and a defence of women's capacity written as a "
              "building project."),
    dict(file="wollstonecraft-vindication-rights-of-woman.txt", gut=3420,
         title="A Vindication of the Rights of Woman", author="Mary Wollstonecraft",
         year="1792",
         strand="women", region="britain",
         marker="VINDICATION OF THE RIGHTS OF WOMAN",
         note="Women's systematic political thought, in the Enlightenment's "
              "own argumentative idiom."),
    dict(file="astell-serious-proposal.txt", gut=54984,
         title="A serious proposal to the Ladies", author="Mary Astell",
         year="1694",
         strand="women", region="britain",
         marker="SERIOUS PROPOSAL",
         note="A proposal for a women's college, by a woman, in 1694: "
              "education as an institution rather than a sentiment."),
    dict(file="astell-reflections-upon-marriage.txt", gut=61143,
         title="Some Reflections Upon Marriage", author="Mary Astell",
         year="1694",
         strand="women", region="britain",
         marker="REFLECTIONS UPON MARRIAGE",
         note="Women's systematic thought on the marriage contract, and the "
              "argument that made Astell a name in the history of the "
              "mind."),
    dict(file="astell-defence-female-sex.txt", gut=57596,
         title="An essay in defence of the female sex", author="Mary Astell",
         year="1700",
         strand="women", region="britain",
         marker="DEFENCE OF THE FEMALE SEX",
         note="The essay that separates Astell from Wollstonecraft: the "
              "same era, the opposite conclusion about what to do."),
    dict(file="kingsley-hypatia.txt", gut=6308,
         title="Hypatia; or, New Foes with an Old Face", author="Charles Kingsley",
         year="1853",
         strand="women", region="britain",
         marker="HYPATIA",
         note="Hypatia of Alexandria, in the one novel that made her a "
              "name: the pagan mathematician killed by a Christian mob."),
    dict(file="sor-juana-obras-selectas.txt", gut=74087,
         title="Obras selectas de Sor Juana Ines de la Cruz",
         author="Sor Juana Ines de la Cruz", year="1690",
         strand="women", region="new_spain",
         marker="JUANA",
         note="Sor Juana: the nun who was the sharpest mind in New Spain, "
              "and whose only published book was forced by a bishop."),
    dict(file="du-chatelet-dissertation-sur-le-feu.txt", gut=73279,
         title="Dissertation sur la nature et la propagation du feu",
         author="Emilie du Chatelet", year="1740",
         strand="women", region="france",
         marker="propagation du feu",
         note="The Marquise du Chatelet on fire and heat. A woman's "
              "systematic natural philosophy, written under her own name "
              "and published after her death."),
    dict(file="women-of-history.txt", gut=39843,
         title="Women of History: Selected from the Writings of Standard Authors",
         author="Various", year="1900",
         strand="women", region="britain",
         marker="WOMEN OF HISTORY",
         note="A collection assembling women's testimony from the standard "
              "male canon -- the shape of the exclusion, visible as an "
              "index."),

    # ---------------- craft and labour -------------------------------------
    dict(file="moxon-english-housewifry.txt", gut=10072,
         title="English Housewifry", author="Elizabeth Moxon", year="1700",
         strand="craft", region="britain",
         marker="HOUSEWIFRY",
         note="Cooks' and housewives' knowledge as a written system. The "
              "craft-and-labour gap: a professional manual, not a "
              "gentleman's account of one."),
    dict(file="bradley-country-housewife.txt", gut=7262,
         title="The Country Housewife and Lady's Director", author="Richard Bradley",
         year="1736",
         strand="craft", region="britain",
         marker="COUNTRY HOUSEWIFE",
         note="The same craft knowledge addressed to a different reader: "
              "the class difference inside the corpus of domestic work."),
    dict(file="hakluyt-principal-navigations.txt", gut=25645,
         title="The Principal Navigations, Voyages, Traffiques and Discoveries",
         author="Richard Hakluyt", year="1589",
         strand="craft", region="britain",
         marker="PRINCIPAL NAVIGATIONS",
         note="Navigators' craft written down: the discipline that made "
              "the instruments usable by people who were not aboard."),
    dict(file="cook-journal-first-voyage.txt", gut=8106,
         title="Captain Cook's Journal During His First Voyage Round the World",
         author="James Cook", year="1772",
         strand="craft", region="britain",
         marker="JOURNAL",
         note="A navigator's own log. The craft-and-labour gap from the "
              "other side: not the narrative of the voyage but the working "
              "record of it."),
]


def fetch(url, timeout=90, retries=3):
    """GET with retries. Returns (body_bytes, http_status, error).

    The body is read with `read()` inside a retry loop, because a large
    transfer can drop part-way through: the server sends a Content-Length
    and then the connection closes early, and `read()` raises
    IncompleteRead. On three targets (6308, 25645, 17) that happened on
    every attempt of one URL and looked exactly like a missing book.
    The fix is to try the next URL form, and to treat a partial body as
    a failure rather than as a text.
    """
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                expected = r.headers.get("Content-Length")
                chunks = []
                got = 0
                while True:
                    chunk = r.read(262144)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    got += len(chunk)
                body = b"".join(chunks)
                if expected and got < int(expected):
                    raise IOError(
                        f"truncated transfer: {got} of {expected} bytes")
                return body, r.status, None
        except urllib.error.HTTPError as exc:
            last = f"HTTPError {exc.code}"
            if exc.code in (404, 403, 410):
                break
        except Exception as exc:                              # noqa: BLE001
            last = f"{type(exc).__name__}: {exc}"
        if attempt < retries - 1:
            time.sleep(2 * (attempt + 1))
    return None, None, last


def gut_urls(gid):
    """Candidate URLs for a Gutenberg ebook, best first.

    The .utf8 variants matter: a large file served as plain UTF-8 was
    truncated mid-transfer on three targets (6308, 25645, 17), and the
    failure looked like "the book does not exist". It does not -- the
    transfer dropped. The .utf8 form is a different file on the server
    and it does not truncate the same way.
    """
    return [
        f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt",
        f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt.utf8",
        f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt",
        f"https://www.gutenberg.org/files/{gid}/{gid}.txt",
        f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt.utf-8",
        f"https://www.gutenberg.org/ebooks/{gid}.txt.utf-8",
    ]


def acquire_one(t: dict) -> dict:
    """Fetch one target, verify it, and write it. Returns the manifest row."""
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, t["file"])
    url_used = None
    body = None
    err = None
    status = None
    for url in gut_urls(t["gut"]):
        body, status, err = fetch(url)
        if body:
            url_used = url
            break
    if not body:
        return dict(t, status="not_acquired", error=err or "no body",
                    acquired=False)

    # Verify: the body must be text and must contain the title marker.
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        text = body.decode("latin-1")
    if t["marker"].lower() not in text.lower():
        return dict(t, status="not_acquired",
                    error=f"body does not contain the title marker "
                          f"{t['marker']!r} (got {len(body)} bytes)",
                    acquired=False, url=url_used)
    if len(body) < MIN_BYTES:
        return dict(t, status="not_acquired",
                    error=f"only {len(body)} bytes, under the {MIN_BYTES} floor",
                    acquired=False, url=url_used)

    sha = hashlib.sha256(body).hexdigest()
    # Refuse to overwrite a file whose bytes differ: the corpus is a
    # record.
    #
    # BUT the comparison is on the TEXT, not on the raw bytes. A file
    # fetched with CRLF line endings and the same file fetched with LF
    # are the same text, and a sha256 difference between them is a
    # line-ending artefact, not a different book. The first version of
    # this compared raw bytes and reported a CONFLICT on a file that was
    # byte-identical to a fresh fetch -- because the earlier run had
    # written CRLF and this run fetched LF.
    #
    # A genuine conflict -- different text -- is still refused, and the
    # reason names both hashes so a human can look.
    if os.path.exists(dest):
        with open(dest, "rb") as fh:
            existing = fh.read()
        if existing != body:
            same_text = (existing.replace(b"\r\n", b"\n")
                         == body.replace(b"\r\n", b"\n"))
            if not same_text:
                return dict(t, status="conflict",
                            error=f"file on disk has sha256 "
                                  f"{hashlib.sha256(existing).hexdigest()[:16]}, "
                                  f"fetch has {sha[:16]}; not overwriting",
                            acquired=False, url=url_used)
            # same text, different line endings: keep what is on disk
            # and record ITS hash, so the manifest matches the file.
            body = existing
            sha = hashlib.sha256(body).hexdigest()

    with open(dest, "wb") as fh:
        fh.write(body)
    return dict(
        t,
        status="acquired",
        acquired=True,
        url=url_used,
        bytes=len(body),
        lines=text.count("\n") + 1,
        sha256=sha,
        file=f"corpus/ingest/texts/{t['file']}",
        qualification="",
    )


def main() -> int:
    check_only = "--check" in sys.argv
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(QUAL_DIR, exist_ok=True)

    rows = []
    if check_only:
        if os.path.exists(MANIFEST):
            with open(MANIFEST, encoding="utf-8") as fh:
                rows = json.load(fh)
        bad = 0
        for row in rows:
            if not row.get("acquired"):
                continue
            p = os.path.join(REPO, row["file"].replace("/", os.sep))
            if not os.path.exists(p):
                print(f"MISSING  {row['file']}")
                bad += 1
                continue
            with open(p, "rb") as fh:
                sha = hashlib.sha256(fh.read()).hexdigest()
            ok = (sha == row.get("sha256"))
            print(f"{'OK  ' if ok else 'DIFF'}  {row['file']}")
            if not ok:
                bad += 1
        print(f"\n{len(rows)} manifest rows, {bad} problem(s)")
        return 0 if bad == 0 else 1

    for t in TARGETS:
        r = acquire_one(t)
        rows.append(r)
        if r["acquired"]:
            print(f"[ OK ] {r['file']:46} {r['bytes']:>9} bytes  "
                  f"sha {r['sha256'][:12]}  <- {r['url']}", flush=True)
        else:
            print(f"[FAIL] {r['file']:46} {r['status']}: {r['error']}", flush=True)

    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(rows, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    ok = sum(1 for r in rows if r.get("acquired"))
    print(f"\n{ok} of {len(rows)} acquired; manifest {MANIFEST}")
    return 0 if ok == len(rows) else 1

if __name__ == "__main__":
    sys.exit(main())
