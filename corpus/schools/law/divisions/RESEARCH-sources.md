# Public-domain legal sources & open-access law textbooks — research report

**Purpose:** source legal term definitions and open-access law textbooks for
far-law's pipeline. Every URL below was fetched on **2026-10-06** unless marked
UNVERIFIED. Read the body, not the status code: two of the most important
routes (`uscode.house.gov`, `opencasebook.org`) return HTTP 200 with an error
or block page.

**Headline:** the strongest legal position in this repo is US government
works — public domain, no attribution, no NC clause, no share-alike. Everything
dictionary-shaped is copyrighted. Everything open-textbook-shaped is
NC or SA-constrained. **Neither is MIT-safe as copied text.**

---

## Master table

| # | Source | Exact URL | License | Redistribute in MIT repo? | Access | Status |
|---|---|---|---|---|---|---|
| 1 | US Code (OLRC) | `https://uscode.house.gov/` | US gov work → public domain | **YES** | browse / XML+txt zips | **DOWN** — HTTP 200 but body = "Site is currently under maintenance" |
| 2 | US Code on GovInfo | `https://www.govinfo.gov/app/collection/USCODE` | US gov work → public domain | **YES** | `content/pkg/USCODE-<year>-title<N>/html/*.htm` | VERIFIED 200; browser render confirmed |
| 3 | GovInfo Bulk Data | `https://www.govinfo.gov/bulkdata/` | US gov work → public domain | **YES** | directory + XML zips | VERIFIED; `/bulkdata/CFR/<year>` resolves |
| 4 | GovInfo Public Domain Notice | `https://www.govinfo.gov/about` | — | — | — | VERIFIED, quoted below |
| 5 | GovInfo developer/API | `https://www.govinfo.gov/about/developers` | — | — | `api.govinfo.gov` needs free key | VERIFIED 200 |
| 6 | Federal court opinions (GovInfo) | `https://www.govinfo.gov/app/collection/USCOURTS-opinions` | US gov work → public domain | **YES** | `content/pkg/USCOURTS-<court>-<year>/html/*.htm` | VERIFIED 200 on content path |
| 7 | U.S. Reports / Supreme Court | `https://www.supremecourt.gov/opinions/USReports.aspx` | US gov work → public domain | **YES** | bound volumes + opinions | VERIFIED 200 |
| 8 | Federal Judicial Center IDB | `https://www.fjc.gov/history/opinions` | US gov work → public domain | **YES** | `https://www.fjc.gov/history/opinions/txt` | VERIFIED 200 |
| 9 | Caselaw Access Project (case.law) | `https://case.law/terms/` | **CC0 1.0** on data+metadata; site text CC BY-SA 4.0 | **YES** (data) | static bulk only | VERIFIED |
| 10 | CAP static bulk | `https://static.case.law/` | CC0 1.0 | **YES** | per-reporter `<vol>.zip/.tar/.tar.csv/.pdf` | VERIFIED |
| 11 | CourtListener / RECAP | `https://www.courtlistener.com/` | opinions = public domain; site terms govern | **YES** (opinions) | REST v4 + S3 bulk CSVs | **403 to curl** — bot-wall, not absence |
| 12 | CourtListener bulk data | `https://www.courtlistener.com/help/api/bulk-data/` | — | (opinions only) | S3 `bulk-data/*.csv.bz2` | VERIFIED 200 |
| 13 | eCFR API | `https://www.ecfr.gov/api/versioner/v1/titles.json` | US gov work → public domain | **YES** | JSON, no key | VERIFIED 200, live JSON |
| 14 | **Black's Law Dictionary, any edition** | publisher = Thomson Reuters | **All rights reserved** | **NO** | paid subscription | VERIFIED via edition record |
| 15 | Black's 2nd ed. (1910) @ Internet Archive | `https://archive.org/details/blacks-law-dictionary-2nd-edition-1910` | **CONFLICTING metadata** | **NO — treat as blocked** | free download | VERIFIED conflict, see §1 |
| 16 | Black's 2nd ed. @ other IA item | `https://archive.org/details/blacks_law_second_edition` | Public Domain Mark 1.0 | **NO — treat as blocked** | free download | VERIFIED conflict |
| 17 | Harvard H2O Open Casebooks | `https://opencasebook.org/` | **CC BY-NC-SA 3.0** | **NO** (NC + SA) | free to read | VERIFIED |
| 18 | MIT OpenCourseWare | `https://ocw.mit.edu/terms/` | **CC BY-NC-SA 4.0** | **NO** (NC + SA) | free | VERIFIED |
| 19 | Open Textbook Library — law | `https://open.umn.edu/opentextbooks/subjects/law` | **per title**: CC BY-SA *or* CC BY-NC-SA | per title | free | VERIFIED per title |
| 20 | OpenStax | `https://openstax.org/subjects/law` | CC BY-NC-SA 4.0 | n/a | n/a | **NO LAW SUBJECT EXISTS** |
| 21 | Restatement of the Law | American Law Institute | All rights reserved | **NO** | paid | UNVERIFIED (see §1) |
| 22 | Stanford OpenLaw | `https://openlaw.stanford.edu` | — | — | — | **DOES NOT RESOLVE** (DNS) |
| 23 | Harvard H2O (legacy host) | `https://h2o.harvard.edu` | — | — | — | **DOES NOT RESOLVE** (DNS) |
| 24 | law.resource.org | `https://law.resource.org/` | public-domain mirror | verify per file | browse | VERIFIED 200 (thin page) |

---

## 1. Black's Law Dictionary — the honest answer

**No edition is free to redistribute. There is no CC-licensed edition. This
is unambiguous.**

### Edition record (VERIFIED, Wikipedia `Black's Law Dictionary`)

Henry Campbell Black authored the first two editions. Publisher is
**West (Thomson Reuters)**. The **current edition is the 12th (2024)** — note
this corrects the common "9th edition (2019)" framing in the task brief.

```
1891 (1st)   1910 (2nd)   1933 (3rd)   1951 (4th)   1968 (4thR)
1979 (5th)   1990 (6th)   1999 (7th)   2004 (8th)   2009 (9th)
2014 (10th)  2019 (11th)  2024 (12th)
```

All modern editions sit inside copyright (life + 70 / 95 years). **Verdict:
NOT SAFE.**

### The 1910 second edition — a real conflict, not a clean answer

Four Internet Archive copies of the same 1910 2nd edition carry
**mutually contradictory** license metadata. This is the decisive evidence
that "it's on archive.org" is not a clearance:

| IA identifier | Declared licenseurl |
|---|---|
| `blacks-law-dictionary-2nd-edition-1910` | `https://creativecommons.org/licenses/by-nc-nd/4.0/` |
| `blacks_law_second_edition` | `http://creativecommons.org/publicdomain/mark/1.0/` |
| `BlacksLaw2dEd` | `http://creativecommons.org/publicdomain/mark/1.0/` |
| `blacks-law-dictionary-bss.org` | *(none)* |

**Why the conflict is not resolvable in our favour.** I downloaded the full
7.1 MB OCR text of the 1910 edition and read the front matter. The scan is a
**Google Books** digitization whose embedded front matter states the term
"has expired and the book to enter the public domain" — but that same
front matter is Google's boilerplate plus these conditions:

- "Make non-commercial use of the files"
- "Refrain from automated querying"
- "Do not assume that just because we believe that the book is in the public
  domain for users in the United States, that the work is also in the public
  domain for users in other countries."
- The IA item hosting that Google scan is tagged **BY-NC-ND 4.0**.

So the only artifact that asserts public domain is a **Google assertion
attached to a scan Google obtained**, and the item actually carrying it is
NC-ND. Under US law the 1910 work itself is very likely public domain today
(author Henry Campbell Black died 1927; 1927 + 70 = 1997, plus the pre-1978
28+28 renewal structure). **But "the underlying work is probably PD in the
US" is not the same as "this file is licensed for redistribution,"** and this
repo's gate exists precisely to stop that leap.

**Verdict: NOT SAFE. Do not copy any Black's text into far-law.**

**The correct pattern** (already recorded in AGENTS.md, reaffirmed): Black's
is the *shape* of a term entry, never the *text*. Define terms in our own
words and cite a public-domain authority — a statute section, a court rule, a
federal opinion from CAP/CourtListener. The 1910 edition is still useful as a
*research pointer* for which terms existed historically and which old-English
and civil-law terms are missing from modern sources.

### Verified US copyright duration (U.S. Copyright Office, Circular 1)

Downloaded `https://www.copyright.gov/circs/circ01.pdf` and extracted the text:

> "In general, for works created on or after January 1, 1978, the term of
> copyright is the life of the author plus seventy years after the author's
> death."

> "For works created before January 1, 1978, that were not published or
> registered as of that date, the law, however, provides that in no case would
> the term have expired before December 31, 2002, and if the work was published
> on or before that date, the term will not expire before December 31, 2047."

This is why every pre-1978 dictionary edition needs individual analysis, and
why the 1910 edition's renewal status is the crux.

### Restatement of the Law — UNVERIFIED

I did **not** find a fetchable authoritative ALI licensing page
(`https://www.ali.org/permissions/` returned 404; a targeted search returned
no usable result). The operative fact — that ALI copyright and sells the
Restatements, and that they carry no free license — is not in doubt and is
consistent with AGENTS.md, but **I am flagging it UNVERIFIED against a
primary source rather than asserting a license text I did not read.**
Verdict on the substance: **NOT SAFE.**

### CC-licensed derivative of Black's? None found

No authoritative source publishes CC-licensed derivative content of Black's.
The claim in the task brief to check for "CC-licensed derivative content"
did not turn up anything. Black's is licensed only through commercial
subscription. **Negative finding, stated as such.**

---

## 2. Public-domain US legal material — the strong result

### GovInfo's own notice (VERIFIED, `https://www.govinfo.gov/about`)

> "In general, GovInfo documents fall under Title 17, Section 105, United
> States Code, which provides that: Copyright protection under this title is
> not available for any work of the United States Government, but the United
> States Government is not precluded from receiving and holding copyrights
> transferred to it by assignment, bequest, or otherwise."

> "By virtue of the foregoing, public documents can generally be reprinted
> without legal restriction. However, Government publications may contain
> copyrighted material which was used with permission of the copyright owner.
> Publication in a Government document does not authorize any use or
> appropriation of such copyright material without the consent of the owner."

The caveat in that second paragraph is load-bearing: **third-party material
reprinted inside a government document is still protected.** This is exactly
where commercial headnotes, ALI Restatement quotations, and West's editorial
annotations get smuggled in.

### ⚠️ `uscode.house.gov` IS CURRENTLY DOWN

Every path I tried returns **HTTP 200 with a "Site is currently under
maintenance" body**:

- `https://uscode.house.gov/`
- `https://uscode.house.gov/statutes.shtml`
- `https://uscode.house.gov/download/releasepoints.htm`
- XML zip `.../xml_usc04@119-15.zip` → **403**
- txt zip `.../txt_usc04@119-15.zip` → **403**

Confirmed via both curl and a real browser (JS-rendered page shows the same
banner). **Do not cite uscode.house.gov as a verified route today.** Re-check
before relying on it. Use GovInfo in the meantime.

### Working verified machine routes (all no-key)

```
# US Code, per-title HTML — VERIFIED 200
https://www.govinfo.gov/content/pkg/USCODE-2023-title17/html/USCODE-2023-title17-part1.htm

# Federal Register — VERIFIED 200
https://www.govinfo.gov/content/pkg/FR-2024-01-01/html/2024-00001.htm

# Federal court opinions — VERIFIED 200
https://www.govinfo.gov/content/pkg/USCOURTS-dcsupreme-2023/html/USCOURTS-dcsupreme-2023-1.htm
```

Bulk directories that resolve (from the live `/bulkdata` index):
`BILLS BILLSTATUS BILLSUM CBD CFR COMPS ECFR FR GOVMAN HMAN PAI PLAW PPP
SCD STATUTE`. Note `/bulkdata/USCODE` is **404** — the US Code is served via
`/app/collection/USCODE` + `content/pkg`, not the bulk tree.

GovInfo API needs a **free** key: `https://api.govinfo.gov/collections/USCODE`
returns 403 `API_KEY_MISSING`. Free signup at `govinfo.gov/api-signup`.

### eCFR — VERIFIED live, no key

`https://www.ecfr.gov/api/versioner/v1/titles.json` returned real JSON with all
50 CFR titles, current as of 2026-10-02. Free and unrestricted.

### Caselaw Access Project — CC0 1.0, and the API *is* actually dead

**Terms (VERIFIED, `https://case.law/terms/`, effective March 13 2024):**

> "Harvard makes the caselaw data and metadata on this site (the 'Caselaw
> Data') available for public use under the CC0 1.0 Public Domain Designation"

> "Other than the Caselaw Data, the text of this site is licensed CC BY-SA
> 4.0." — site source code is MIT.

> "Although Harvard does not impose any legally binding conditions on access to
> the Metadata, Harvard requests that you act in accordance with the following
> Community Norms" — attribute Harvard/CAP, and republish improvements on the
> same terms. **Requested, not required.**

**This is the best licence in the entire report: CC0 1.0.** Data can be
redistributed with no conditions at all.

**The API sunset is real — verified, not assumed.** The task brief asked me to
check this. `https://api.case.law/v1/cases/?full_case=true` returns **HTTP 200
but serves an HTML documentation page, not JSON**. Any code hitting the old
CAP API will appear to succeed and silently ingest markup. CAP announced the
API and search sunset for **September 5, 2024**.

**What still works — the static bulk tree (VERIFIED):**

```
https://static.case.law/VolumesMetadata.json     # 40,622 volumes
https://static.case.law/ReportersMetadata.json    # 401 reporters
https://static.case.law/JurisdictionsMetadata.json
https://static.case.law/<reporter>/<vol>.zip
https://static.case.law/<reporter>/<vol>.tar
https://static.case.law/<reporter>/<vol>.tar.csv
https://static.case.law/<reporter>/<vol>.pdf
https://static.case.law/<reporter>/<vol>.tar.sha256
```

Confirmed by listing `https://static.case.law/a2d/` in a browser: per-volume
rows with Zip/PDF/Tar/Tar.csv/Tar.sha256 links, and both a zip and tar.csv
returned 200 on HEAD. Note the earlier-intuitive `a2d/1.json` is **404** —
per-volume files are numbered by actual volume, not by index.

### CourtListener / RECAP

- `https://www.courtlistener.com/` → **403 to curl** (bot-wall, not absence);
  `/api/rest/v4/` and `/api/rest/v4/search/?q=test&type=o` both returned 200,
  so the REST API is reachable.
- `https://www.courtlistener.com/terms/` → 403 via curl **and** via browser
  (CloudFront block). I read the terms page through the earlier 200 fetch and
  found the operative sentence: *"while judicial opinions, motions, and other
  filings are generally in the public domain, other court filings may contain
  third-party copyrighted works, such as books and articles, that may retain
  copyright protection."*
- Bulk data doc VERIFIED: files are PostgreSQL `COPY TO` CSVs, UTF-8 with header
  row, snapshots not deltas, regenerated quarterly, streamed to S3 at
  `https://com-courtlistener-storage.s3-us-west-2.amazonaws.com/`.
  I listed the bucket and confirmed real objects:
  `bulk-data/citation-map-2024-08-31.csv.bz2` and similar.

**Verdict: opinions SAFE (public domain).** Do not treat RECAP *filings*
generally as safe — the site's own terms carve out third-party works.

---

## 3. Open-access law textbooks

### ⚠️ Harvard H2O is CC BY-**NC**-SA — the key finding

Two independent H2O pages confirm it:

`https://opencasebook.org/pages/about/`:
> "H2O allows professors to develop, remix, and collaborate on digital course
> materials under a Creative Commons Attribution-Noncommercial-Share Alike 3.0
> License"

`https://opencasebook.org/pages/terms-of-service/`:
> "you also agree to allow H2O to license your Content under the Creative
> Commons Attribution-Noncommercial-Share Alike 3.0 License"

> "H2O makes some of its source code related to the H2O Services available
> under the GNU Affero General Public License."

**Verdict: NOT SAFE to copy into MIT-licensed content.** Two independent
constraints: **NC** (kills commercial use) and **SA** (forces relicensing of
derivatives, which directly contradicts far-law's MIT repo). You may *link
and index* H2O casebooks; you may not vendor their text. Note the live
platform is `opencasebook.org`; the legacy host `h2o.harvard.edu` **does not
resolve**, and `about.opencasebook.org` is behind a Cloudflare challenge.

### MIT OpenCourseWare is also CC BY-NC-SA 4.0

From `https://ocw.mit.edu/terms/`:
> "Creative Commons License / Attribution-NonCommercial-ShareAlike 4.0
> International (CC BY-NC-SA 4.0)"

MIT's own summary states "Non-commercial use means that users may not sell,
profit from, or commercialize OCW materials or works derived from them."
Same verdict: **NOT SAFE** to copy; safe to cite and link.

**Real law courses do exist** (the `?d=Law` filter on the search page is
ignored by the JS app and silently returns all 2587 courses — use
`?q=law&type=course`). Verified course pages, e.g.
`https://ocw.mit.edu/courses/6-912-introduction-to-copyright-law-january-iap-2006/`
(Keith Winstein, topic "Legal Studies", CC BY-NC-SA 4.0 footer). Others:
`21a-219-law-and-society`, `24-235j-philosophy-of-law`,
`11-368-environmental-justice-law-and-policy`,
`15-615-law-for-the-entrepreneur-and-manager`,
`15-649-the-law-of-mergers-and-acquisitions`,
`21h-225j-gender-and-the-law-in-u-s-history`,
`10-805j-technology-law-and-the-working-environment`,
`6-805-ethics-and-the-law-on-the-electronic-frontier`.

### Open Textbook Library — license is **per title**, and I checked each

`https://open.umn.edu/opentextbooks/subjects/law` lists 10 law titles. Verified
"Conditions of Use" for each of these:

| Title | Conditions of Use | MIT-safe? |
|---|---|---|
| Introduction to Basic Legal Citation | **CC BY-SA** | Yes — but **SA** forces relicensing |
| United States Copyright Law | **CC BY-SA** | Yes — but SA forces relicensing |
| United States Trademark Law | **CC BY-SA** | Yes — but SA forces relicensing |
| Introduction to Criminal Law | CC BY-NC-SA | **NO** |
| Land Use | CC BY-NC-SA | **NO** |
| Federal Rules of Appellate Procedure | CC BY-NC-SA | **NO** |
| Contract Doctrine (vol 1 & 2), Criminal Law, Legal/Ethical Environment of Business | not individually checked | check before use |

This is the one open-textbook route with **no NC clause on some titles**, which
makes it the best candidate for far-law — but CC BY-SA still means a derived
work must be SA. Under an MIT repo the clean options are: vendor the text into
a subdirectory under its own CC BY-SA license with clear attribution, or link
only.

### ❌ OpenStax has NO Law subject

The premise in the task brief does not hold. `https://openstax.org/subjects/law`
returns HTTP 200 but renders an **empty page** — no books, no category listing.
The full subject list at `https://openstax.org/subjects/view-all` is:
business, college-success, computer-science, humanities, math, nursing, science,
social-sciences. **No law.**

Only adjacent coverage exists: *Business Law and Ethics* under
`/subjects/business#Business Law and Ethics`, plus *Introduction to Business*.
Also note OpenStax's blanket license is
"Creative Commons Attribution-NonCommerical-ShareAlike 4.0" — NC + SA, so
**NOT SAFE** to copy regardless.

### Dead ends — recorded so nobody re-checks them

- `https://h2o.harvard.edu` — DNS does not resolve
- `https://openlaw.stanford.edu` — DNS does not resolve
- `https://legisworks.org` — DNS does not resolve
- `https://sylt.cc` — connection timeout
- `https://law.justia.com` — 403
- `https://about.opencasebook.org` — Cloudflare bot challenge
- `law.libretexts.org` — returned a resolver error page on both curl attempts
- `pressbooks.directory/subjects/law` — 404 (no law subject)

**No CC-licensed copy of Black's exists anywhere on these.**

---

## 4. Yale Law School areas of study — VERIFIED, exact published names

Fetched `https://law.yale.edu/studying-law-yale/areas-study` (HTTP 200, full
nav + body). Yale publishes these under **"Areas of Interest"** — note that is
the heading on the page, not "divisions." The 12 names, verbatim:

1. **Constitutional Law**
2. **Corporate & Commercial Law**
3. **Criminal Justice**
4. **Environmental Law**
5. **Human Rights Law**
6. **International Law**
7. **Law & Economics**
8. **Law & Health**
9. **Law Teaching**
10. **Legal History**
11. **Public Interest Law**
12. **Technology & Media Law**

### Mismatch with far-law's current `divisions/`

The repo has 13 directories. Comparing:

| far-law directory | Maps to published Yale area? |
|---|---|
| `constitutional/` | Constitutional Law ✅ |
| `corporate/` | Corporate & Commercial Law ✅ (but `commercial/` also claims it) |
| `criminal/` | Criminal Justice ✅ |
| `environmental/` | Environmental Law ✅ |
| `health/` | Law & Health ✅ |
| `intellectual-property/` | **no direct Yale area** ❌ |
| `legislation-policy/` | **no direct Yale area** ❌ |
| `litigation/` | **no direct Yale area** ❌ |
| `tax/` | **no direct Yale area** ❌ |
| `commercial/` | **overlaps `corporate/`** ⚠️ |
| `international/` | International Law ✅ |
| `labor/` | **no direct Yale area** ❌ |
| `clinical/` | ~Public Interest Law ✅ (approx.) |

**Four repo divisions the brief expected — Intellectual Property, Legislation &
Policy, Litigation, Tax — are not Yale areas.** IP sits inside Yale's
Technology & Media Law / Information Society Project; litigation and tax are
covered by faculty without a named area; labor has no named area either.

**Recommendation:** the repo's taxonomy is defensible as an *editorial*
taxonomy, but AGENTS.md currently says it is "organized by Yale Law School's
academic divisions" — that sentence is **inaccurate as written**. Either
(a) relabel to "a taxonomy informed by, and extending, Yale's published areas
of interest," or (b) publish a mapping file so the divergence is explicit and
defensible. Subject-area *names* are not copyrightable, so (b) is legally fine.

---

## Recommended ingest order for far-law

| Priority | Source | License | Action |
|---|---|---|---|
| 1 | GovInfo US Code (`content/pkg/USCODE-*`) | public domain | ingest freely; the spine of `Statute` packets |
| 2 | CAP `static.case.law` (`*.tar.csv`, 40,622 vols) | **CC0 1.0** | ingest freely; the spine of `Opinion` packets |
| 3 | GovInfo federal court opinions (`USCOURTS-*`) | public domain | ingest freely; official federal opinions |
| 4 | CourtListener bulk CSVs (S3) | opinions public domain | ingest; primary source for RECAP + non-CAP cases |
| 5 | eCFR API | public domain | ingest; regulations |
| 6 | Open Textbook Library CC BY-SA titles | CC BY-SA | link + index; vendor only in a self-contained SA subdirectory |
| 7 | Black's 1910 (2nd ed.) | contested | **do not ingest**; research pointer only |
| 8 | H2O, MIT OCW, LibreTexts | CC BY-NC-SA | **link only, never copy** |
| 9 | OpenStax | no law subject | drop from plan |

## Rules this report adds to AGENTS.md

1. **A 200 with an error body is not verified.** `uscode.house.gov` proves it.
2. **CC0 beats every licence here.** CAP data is the only material with no
   conditions at all — attribution is a *request*, not a requirement.
3. **Government publication ≠ public domain.** GovInfo's own notice warns that
   third-party material reprinted inside government documents stays protected.
   Screen for Restatement/West headnote content.
4. **NC and SA each independently break MIT.** MIT permits relicensing and
   commercial use; CC BY-NC-SA forbids both. H2O, MIT OCW, and OpenStax all
   fail on this.
5. **CC BY-SA is a usable escape hatch** — vendor into its own subdirectory
   under its own licence rather than mixing it into MIT content.
6. **Library metadata is not a license.** Conflicting IA metadata on the same
   1910 edition is the proof.