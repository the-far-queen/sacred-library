# Verified source manifest — far-law

Every entry was checked by fetching it on the date shown. Where a source
could not be reached, it is recorded as **UNVERIFIED** with the failure
mode — a plausible URL that returns a maintenance page is worse than no
URL, because it looks verified.

Last checked: **2026-10-06**

---

## SAFE — US government works

US federal statutes, the Constitution, and federal court opinions are
works of the US government and are in the public domain. That is the
strongest legal position available in this repo: no attribution
required, no NC clause, no share-alike.

### Status of the primary access routes on 2026-10-06

| Route | Result | Note |
|---|---|---|
| `https://uscode.house.gov/` | HTTP 200 but **page is "Site is currently under maintenance"** | Returns 200 with an error body. **Treat as DOWN.** Do not cite as verified until the maintenance banner clears. |
| `https://www.govinfo.gov/` | HTTP 200 | Site reachable. |
| `https://www.govinfo.gov/bulkdata/USCODE/2023` | **HTTP 404** after redirect | The bulk US Code path does not currently resolve. |
| `https://api.govinfo.gov/collections/USCODE` | HTTP 401 `API_KEY_MISSING` | govinfo API requires a **free** key (sign up at govinfo.gov/api-signup). Once registered, this is the correct machine route for bulk statute data. |
| `https://www.courtlistener.com/` | HTTP 403 | Bot-wall, not absence. CourtListener/RECAP is the right source for federal opinions; access needs a browser or their API. |
| `https://constitution.congress.gov/` | HTTP 403 | Cloudflare bot-wall, not absence. |

**Rule for this repo: a source whose HTTP status is 200 but whose body
is a maintenance or error page is NOT verified.** Check the body, not
the status code. This is the same failure class as a fabricated
citation — it looks fine until you read it.

---

## SAFE — public.resource.org (verified reachable)

**Public.Resource.Org** (Carl Malamud) — verified HTTP 200 on
2026-10-06. Bulk public-domain legal and government data.

| Resource | URL |
|---|---|
| root | `https://law.resource.org/` |
| US Code (public) | `https://law.resource.org/pub/us/code/` |
| Court cases | `https://public.resource.org/court_cases.html` |
| Court cases (govinfo archive) | `https://public.resource.org/uscourts.gov/index.html` |
| federal archive collection | `https://archive.org/details/govlaw` |

These mirror US federal material as public domain. **UNVERIFIED in
detail:** whether every individual file carries an explicit public
domain determination, and the freshness of the US Code mirror. Check a
file's own header before citing it.

---

## NOT SAFE — copyrighted

| Work | Holder | Status |
|---|---|---|
| **Black's Law Dictionary**, all editions | Thomson Reuters | **NOT public domain.** No edition is free to redistribute. Verified via Wikipedia's edition history and Thomson Reuters' publication record. |
| Restatement of the Law | American Law Institute | NOT public domain; ALI sells it and does not license it freely. |
| Yale Law School casebooks | Yale University Press | NOT public domain. |
| Harvard, Stanford, and other law school casebooks | various | NOT public domain. |

### On Black's Law Dictionary specifically

It is the standard term dictionary for American law and Bobby named it
as the model for term definitions. It cannot be copied into this repo.

The 1919 **second edition** is digitized on archive.org, but its metadata
is **self-contradictory**: four Internet Archive copies of the same 1910
2nd edition declare *different* licenses (two carry the Public Domain Mark,
one carries CC BY-NC-ND 4.0, one declares none). The scan itself is a Google
Books copy whose front matter adds non-commercial and no-automated-querying
conditions. **Verdict: NOT SAFE. Do not copy any Black's text into this
repo**, however old the edition.

**The 2nd edition is still useful as a research pointer** — for which terms
existed historically and which old-English/civil-law terms modern sources
drop. Point at it; never vendor it.

The correct pattern for this repo: define a term in our own words, cite
a **public-domain** authority for the definition (a statute, a rule, a
public-domain case), and record that source. Black's is the *shape* of
the entry, not the *text*.

---

## OPEN-ACCESS LAW SCHOOL MATERIAL

| Source | License | Verdict |
|---|---|---|
| Harvard Law School **H2O** (`opencasebook.org`) | **CC BY-NC-SA 3.0** | NC + SA bind. Free to read, but a derived work cannot be relicensed MIT. Link and index; do not copy wholesale into MIT content. |
| Stanford **OpenLaw** / CodeX Stanford | — | **`openlaw.stanford.edu` does not resolve** (DNS failure). Not reachable; do not plan around it. |
| MIT OpenCourseWare law courses | **CC BY-NC-SA 4.0** | Same NC + SA bind as H2O. **NOT SAFE** to copy. |
| University casebooks on **Open Textbook Library** | **per title** — verified: CC BY-SA *or* CC BY-NC-SA | CC BY-SA titles are usable in a self-contained SA subdirectory; CC BY-NC-SA titles are not. Check per title. |
| **Caselaw Access Project** (`case.law`) data + metadata | **CC0 1.0** (verified `case.law/terms`, effective 2024-03-13) | **SAFE.** No conditions; attribution is a request, not a requirement. |
| **OpenStax** | no Law subject exists; blanket CC BY-NC-SA | **n/a.** `openstax.org/subjects/law` renders empty; subject list has no law. Drop from plan. |

**H2O being NC-SA is the important one.** It looks like an unrestricted
legal resource and is not usable in MIT-licensed derivative content
without inheriting NC-SA. **MIT OCW is identical** — CC BY-NC-SA 4.0.

**The best licence in this repo is CC0 1.0** (CAP data). It is the only
material here with no conditions at all.

---

## CAVEAT ON YALE DIVISIONS

The far-law taxonomy uses Yale Law School's academic divisions as its
section structure. This is an *organizational* choice — the division
names describe coverage areas. It does not imply Yale endorses,
sponsors, or contributes to this repo. No Yale material is reproduced
here; only the names of subject areas, which are not copyrightable.

---

## PENDING — not yet verified

| Candidate | What to check |
|---|---|
| govinfo API with free key | register, then verify bulk US Code + federal court opinion endpoints |
| uscode.house.gov | re-check when maintenance clears; this is the authoritative US Code |
| Cornell LII (law.cornell.edu) | reachable (verified 200 on a US Code page); LII is its own copyrighted compilation — check its terms before copying. Its `/terms-of-use` and `/about` both returned **404**, so the licence text was not located. |
| case.law / Caselaw Access Project | **RESOLVED.** Data + metadata = CC0 1.0 (SAFE). API sunset 2024-09-05 — `api.case.law` now serves HTML, not JSON. Use `static.case.law` bulk instead. |
| ALI permissions page | `ali.org/permissions/` 404 — Restatement licensing NOT verified against a primary source. Substance (not free) is not in doubt; licence text is. |
