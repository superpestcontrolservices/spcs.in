# Super Pest Control Services — Launch Readiness Report

**Audit date:** 17 October 2026  
**Scope:** Read-only review of the local website and read-only HTTP checks of `https://www.superpest.in/`. No deployment, push, Supabase access, enquiry submission, or project-file change was performed during the audit. This report is the only project file created for the audit.

## 1. Verdict

**NO-GO — 0 CRITICAL, 3 HIGH, 6 MEDIUM, 3 LOW findings.** The live site does not match the local release, three required live routes return 404, and the local enquiry configuration is still placeholder/unverified. Resolve the HIGH findings and confirm the live deployment before launch.

### Scope and method

- Enumerated and automatically checked all **574 local HTML files**: 537 indexable pages and 37 legacy `noindex`/meta-refresh redirect pages. Manually inspected **31 representative pages** across home, About, Contact, services, customer types, district and area pages, Blog, Privacy Policy, and Terms.
- Parsed local metadata, links, images, JSON-LD, robots and sitemap; checked location-page similarity with five-word shingles; scanned 1,806 working-tree files for high-confidence secret patterns.
- Made read-only HTTP requests to the live website. The live apex redirects to `www`; sampled live pages returned 200. No form was submitted.
- Hosting is **GitHub Pages**, evidenced by `CNAME`, `.nojekyll`, `_config.yml`, and live response headers.
- **Not verified:** Supabase dashboard/RLS/function state, credentials or customer records; Git history (no `.git` directory and `git` unavailable); repository/deployment commit identity; Lighthouse; full smartphone/browser testing; live Google Business Profile and Search Console status.

## 2. Findings

| ID | Severity | Section | Pages affected (count; examples) | Evidence | Why it matters | Recommended fix | Effort |
|---|---|---|---|---|---|---|---|
| H-01 | HIGH | Indexing / release integrity | **488 local indexable URLs absent from the live sitemap**; examples: `/pest-control-in-pali/`, `/pest-control-in-beawar/`, `/pest-control-in-jaipur/malviya-nagar/` | Local [`sitemap.xml`](./sitemap.xml#L4) has 537 unique page URLs and `lastmod`; live [`sitemap.xml`](https://www.superpest.in/sitemap.xml) returned 49 entries dated 2026-09-06. Local Pali content is newer than the live page. | Search engines are being given a materially incomplete/out-of-date map of the intended release; local changes are not demonstrably deployed. | Publish the reviewed release, regenerate/verify the live sitemap against every intended indexable URL, then resubmit it in Search Console and Bing. Confirm deployed commit and representative changed pages. | Medium |
| H-02 | HIGH | Indexing / trust | **3 live routes return 404**: Privacy Policy, Terms, and Cockroach Control | Read-only HEAD checks: [`/privacy-policy/`](https://www.superpest.in/privacy-policy/), [`/terms-and-conditions/`](https://www.superpest.in/terms-and-conditions/), and [`/services/cockroach-control/`](https://www.superpest.in/services/cockroach-control/) returned HTTP 404. The pages exist locally. | Legal disclosures are unavailable to visitors and crawlers; a linked core service route is broken. | Restore these routes or redirect each to a genuinely equivalent, working page; verify HTTP 200/301 and update the live sitemap. | Small |
| H-03 | HIGH | Security / forms | **1 enquiry form and its shared submission flow**; examples: [`contact/index.html`](./contact/index.html#L252), [`js/security-config.mjs`](./js/security-config.mjs#L1), [`supabase/functions/submit-enquiry/index.ts`](./supabase/functions/submit-enquiry/index.ts#L152) | Local browser config still contains `REPLACE_WITH_ROTATED_SUPABASE_PUBLISHABLE_KEY` and `REPLACE_WITH_CLOUDFLARE_TURNSTILE_SITE_KEY`; the function returns 503 when server secrets are missing. Deployment instructions say the function is not deployed by this change. | Publishing this local state would not establish a working, protected enquiry path. The live form, RLS, SQL policies, and function deployment were not tested and must not be assumed operational. | Set the real publishable/site keys in approved settings, configure function secrets, review/run the provided SQL yourself, deploy the function, then test valid/invalid/rate-limit cases in staging and verify anonymous users cannot read or modify enquiries. | Medium |
| M-01 | MEDIUM | Spam policy / content quality | **109 of 461 nested location pages** occur in **63 pairs at or above 60%** by the stated shingle-containment screen; examples: Khairthal-Tijara/Kishangarh Bas with Jaisalmer/Dhibba Para (68.7%), Sri Ganganagar/Sri Karanpur with Alwar/Ramgarh (67.7%), Kota/Gumanpura with Banswara/Kushalgarh (65.9%). | Example files: [`pest-control-in-khairthal-tijara/kishangarh-bas/index.html`](./pest-control-in-khairthal-tijara/kishangarh-bas/index.html) and [`pest-control-in-jaisalmer/dhibba-para/index.html`](./pest-control-in-jaisalmer/dhibba-para/index.html). The screen excludes shared navigation/header/footer/scripts and compares the overlap of five-word shingles relative to the shorter page. | Reused copy can make location pages look templated or insufficiently distinct. This is a review signal, not proof of a Google policy violation or copied material. | Review the 63 pairs in Appendix C. Keep only genuinely useful local pages; substantiate local details and make each page materially helpful rather than changing place names alone. | Large |
| M-02 | MEDIUM | Trust / reviews | **476 location pages** include the same injected set of 20 five-star testimonials; examples: Jaipur, Pali, and Beawar area pages. The homepage has a separate static testimonial section. | [`js/location-reviews.js`](./js/location-reviews.js#L4) says “backed by real customer experiences”; e.g. named accounts describe precise dates/times, treatments, and complete outcomes. It is loaded by 476 HTML files. | Authenticity, consent, source, rating basis, and accuracy are not verifiable from the website files. If the testimonials are not genuine and authorized, they create significant trust and policy risk. No fake-review conclusion is made here. | Verify each review and permission against original records; remove unsupported claims or replace them with verifiable, consented material. Do not add review structured data unless the displayed content and applicable Google rules support it. | Medium |
| M-03 | MEDIUM | Trust / factual claims | **537 indexable pages** repeat an experience-age inconsistency; **30 district pages** contain a company-certification claim | [`about/index.html`](./about/index.html#L374) says “28 Years”; its footer at [line 414](./about/index.html#L414) says “three decades”. Example certification wording: [`pest-control-in-pali/index.html`](./pest-control-in-pali/index.html#L647) and [`pest-control-in-bundi/index.html`](./pest-control-in-bundi/index.html#L633) say “fully NIPHM and IPCA-certified”. | Conflicting age claims and unsubstantiated certification language can undermine trust and create misleading-advertising risk. The owner’s credentials and exact certification status were not independently verified. | Keep the 28-year figure consistent with the owner-approved date basis; substantiate or narrow company-level certification wording to verifiable staff training/credentials. Review other absolute treatment/safety claims and named testimonial details at the same time. | Small |
| M-04 | MEDIUM | Structured data | **29 FAQ answers across 10 service pages** differ from the exact visible answer text; examples: Bed Bug Eradication, Commercial Fumigation, Termite Control | [`services/bed-bug-eradication/index.html`](./services/bed-bug-eradication/index.html#L50) gives one schema answer; the visible response at [line 529](./services/bed-bug-eradication/index.html#L529) ends “An inspection confirms activity,” rather than “A professional inspection can confirm it.” | Structured data should accurately represent visible page content. Exact-string differences may be harmless paraphrases, but some differences are substantive and need human review. All JSON-LD parsed; no malformed JSON was found. | Align each affected schema answer with its visible answer, or remove FAQ markup for content that is not visibly answered. Re-parse after changes. | Small |
| M-05 | MEDIUM | Security headers | Live sampled pages have HSTS, but **5 other requested protections were absent** | Live `https://www.superpest.in/` response included `Strict-Transport-Security: max-age=31556952`; it did not include CSP, `X-Content-Type-Options`, frame protection, `Referrer-Policy`, or `Permissions-Policy`. [`GITHUB_PAGES_SECURITY_HEADERS.md`](./GITHUB_PAGES_SECURITY_HEADERS.md#L5) documents GitHub Pages’ arbitrary-header limitation. | Missing defense-in-depth leaves fewer browser protections if an injection or framing issue occurs. A CSP meta tag cannot replace all response headers. | Verify GitHub Pages HTTPS enforcement in settings. To add headers, use a supported reverse proxy/CDN or a host with header configuration; stage CSP in report-only mode and account for the many inline scripts before enforcing it. | Medium |
| M-06 | MEDIUM | Local trust / structured data | **9 Service schema nodes** mention Beawar as `areaServed`; examples: Beawar root, Ajmer Road, Beawar City | [`pest-control-in-beawar/index.html`](./pest-control-in-beawar/index.html), [`pest-control-in-beawar/ajmer-road/index.html`](./pest-control-in-beawar/ajmer-road/index.html), and [`pest-control-in-beawar/beawar-city/index.html`](./pest-control-in-beawar/beawar-city/index.html). No Beawar office address/map node was found; these are service-area values, not office assertions. | The requested policy says to hold Beawar public mentions while its Business Profile is unusable. Whether service-area mentions should also be held is an owner decision; profile status was not verified. | Confirm the intended policy and profile status. Do not represent Beawar as an office; remove or retain service-area mentions consistently with the owner’s decision. | Small |
| L-01 | LOW | URL consistency | **Many local references use both apex and `www`**; examples: About Open Graph image and sitemap image URLs | Canonical pages and sitemap `<loc>` entries use `www`; the apex redirects to `www`. [`about/index.html`](./about/index.html#L80) and [`sitemap.xml`](./sitemap.xml#L7) include apex image URLs. No sampled wrong-domain or localhost canonical was found. | The redirect makes this less urgent, but mixed host references complicate canonical consistency and reporting. | Standardize absolute URLs, social image URLs, and schema entity IDs on the chosen canonical host. | Small |
| L-02 | LOW | Content / navigation | **2 indexable pages under 300 visible body words**; one empty Blog anchor | `contact/index.html` is about 90 visible words and `service-location/index.html` about 237; [`blog/index.html`](./blog/index.html#L3349) contains `href="#"`. Word counts exclude shared chrome and are not “unique-word” counts. | The location hub may provide little standalone value; the empty anchor is confusing and does not navigate. Contact-page brevity alone is not a penalty. | Add useful navigation/context to the location hub if it is intended to rank; replace or remove the empty Blog link. | Small |
| L-03 | LOW | UX / accessibility / performance | **4 pages lack a `<main>` landmark**; 1,070 of 1,673 `<img>` elements omit `loading` | Pages without `<main>`: About, Contact, Commercial Pest Control, Residential Pest Control. Sampled images had `alt`, `width`, and `height`; no referenced image exceeded 250 KB. Which un-lazied images are below the fold was not established. | Missing landmarks reduce accessibility. Loading many off-screen images eagerly can affect mobile performance, but the count alone does not prove a user-visible delay. | Add one main landmark on the four pages. Use lazy loading for below-the-fold images and validate representative mobile pages with Lighthouse or equivalent. | Small |

## 3. Blockers and prioritized actions

### Must resolve before launch

1. **Reconcile the live release:** publish the intended local pages and regenerate/verify the live sitemap; confirm that the deployment corresponds to the reviewed source.
2. **Restore the three 404 routes:** Privacy Policy, Terms, and Cockroach Control must return a suitable 200 or a relevant redirect.
3. **Prove the enquiry flow in staging:** replace placeholders, configure server-side secrets, review and run the SQL manually, deploy the Edge Function, and test successful and rejected requests plus anonymous read/update/delete denial. Do not test against production customer data.
4. **Substantiate trust claims:** verify the 20 reviews, 28-year/“three decades” copy, NIPHM/IPCA wording, and strong safety/effectiveness claims before publishing them.

### Quick wins

- Fix the 29 FAQ answer/schema discrepancies.
- Decide the public Beawar service-area policy.
- Remove the empty Blog `href="#"`; normalize host references.
- Ensure below-the-fold images lazy-load and add missing `<main>` landmarks.

### Nice-to-haves

- Review all 63 location-page similarity pairs and remove or improve low-value pages.
- Add response headers through a supported hosting/CDN setup.
- Run multi-page Lighthouse and real-device mobile checks after deployment.

## 4. Pages needing the most work

The first three routes are live 404s. The remaining entries are high-similarity locations flagged for editorial review, not adjudicated duplicate pages.

| Rank | Page | Reason |
|---:|---|---|
| 1 | [`privacy-policy/index.html`](./privacy-policy/index.html) | Live `/privacy-policy/` returns 404. |
| 2 | [`terms-and-conditions/index.html`](./terms-and-conditions/index.html) | Live `/terms-and-conditions/` returns 404. |
| 3 | [`services/cockroach-control/index.html`](./services/cockroach-control/index.html) | Live service route returns 404. |
| 4 | [`contact/index.html`](./contact/index.html) | Form configuration is placeholder locally; submission/backend is unverified; about 90 visible words. |
| 5 | [`service-location/index.html`](./service-location/index.html) | About 237 visible words; confirm that the hub gives enough useful navigation/context. |
| 6 | [`pest-control-in-khairthal-tijara/kishangarh-bas/index.html`](./pest-control-in-khairthal-tijara/kishangarh-bas/index.html) | 68.7% pair with Jaisalmer/Dhibba Para. |
| 7 | [`pest-control-in-jaisalmer/dhibba-para/index.html`](./pest-control-in-jaisalmer/dhibba-para/index.html) | 68.7% pair with Khairthal-Tijara/Kishangarh Bas. |
| 8 | [`pest-control-in-sri-ganganagar/sri-karanpur/index.html`](./pest-control-in-sri-ganganagar/sri-karanpur/index.html) | 67.7% pair with Alwar/Ramgarh. |
| 9 | [`pest-control-in-alwar/ramgarh/index.html`](./pest-control-in-alwar/ramgarh/index.html) | 67.7% pair with Sri Ganganagar/Sri Karanpur. |
| 10 | [`pest-control-in-kota/gumanpura/index.html`](./pest-control-in-kota/gumanpura/index.html) | 65.9% pair with Banswara/Kushalgarh. |
| 11 | [`pest-control-in-banswara/kushalgarh/index.html`](./pest-control-in-banswara/kushalgarh/index.html) | 65.9% pair with Kota/Gumanpura. |
| 12 | [`pest-control-in-dholpur/rajakhera/index.html`](./pest-control-in-dholpur/rajakhera/index.html) | 65.6% pair with Deeg/Pahari. |
| 13 | [`pest-control-in-deeg/pahari/index.html`](./pest-control-in-deeg/pahari/index.html) | 65.6% pair with Dholpur/Rajakhera. |
| 14 | [`pest-control-in-tonk/tonk-city/index.html`](./pest-control-in-tonk/tonk-city/index.html) | 65.3% pair with Dungarpur/Galiyakot. |
| 15 | [`pest-control-in-dungarpur/galiyakot/index.html`](./pest-control-in-dungarpur/galiyakot/index.html) | 65.3% pair with Tonk/Tonk City. |
| 16 | [`pest-control-in-karauli/todabhim/index.html`](./pest-control-in-karauli/todabhim/index.html) | 65.2% pair with Chittorgarh/Gangrar. |
| 17 | [`pest-control-in-chittorgarh/gangrar/index.html`](./pest-control-in-chittorgarh/gangrar/index.html) | 65.2% pair with Karauli/Todabhim. |
| 18 | [`pest-control-in-bhilwara/gangapur-road/index.html`](./pest-control-in-bhilwara/gangapur-road/index.html) | 64.9% pair with Ajmer/Civil Lines. |
| 19 | [`pest-control-in-ajmer/civil-lines/index.html`](./pest-control-in-ajmer/civil-lines/index.html) | 64.9% pair with Bhilwara/Gangapur Road. |
| 20 | [`pest-control-in-chittorgarh/bapu-nagar/index.html`](./pest-control-in-chittorgarh/bapu-nagar/index.html) | 64.7% pair with Ajmer/Hathi Bhata. |

## 5. Not verified

- **Git history and branches:** no `.git` metadata was present and `git` was unavailable. The full history, commit timeline, branch state, and whether deployed files differ from Git cannot be established.
- **Supabase:** no project/dashboard/API access was used. Production RLS, table grants, existing enquiry exposure, Edge Function deployment, rate-limit RPC, logs, user list, backups, and actual form delivery are not verified.
- **Third-party/account security:** credential rotation, 2FA, GitHub collaborators/tokens/actions/webhooks, hosting access, DNS/registrar, email, Cloudflare, and Google account security require owner review.
- **Customer data:** no customer records were identified by the working-tree secret/file scan, but the live Supabase database and all external backups were not inspected.
- **Live deployment identity:** the domain is GitHub Pages, but the deployed commit/build source and deployment workflow were not accessible.
- **Testimonials, certificates, local facts, office/working hours, ownership/consent, and safety claims:** source files cannot prove their truth. Owner records and official documents are needed.
- **Google Business Profile and Search Console:** profile status, manual actions, security issues, index coverage, sitemap processing, and actual search results were not accessed.
- **Lighthouse and mobile:** no Lighthouse run was available. Only one local page was visually inspected at a 904×676 viewport; no representative smartphone/browser matrix, tap-target, contrast, or screen-reader test was performed.
- **Below-the-fold image loading:** 1,070 images have no explicit `loading` attribute, but their viewport positions were not measured.
- **Keyword density, all-page hidden/off-screen rendering, full copy originality against competitors, every external destination, live click-to-call/WhatsApp/email behavior, and all local climatic/industry claims:** not conclusively verified.
- **Legal review:** this technical audit does not determine compliance with India’s DPDP Act 2023 or applicable CERT-In directions.

## 6. Manual launch checklist

These are owner actions and are **not marked as passed**:

1. **Domain and HTTPS:** verify DNS and certificate status; confirm apex-to-`www` HTTPS redirection and enforce-HTTPS settings. Add both relevant domain variants to Google Search Console, submit the sitemap there and in Bing Webmaster Tools, and inspect representative URLs.
2. **Google Business Profile:** verify the Jaipur office listing is complete and consistent with the site. Check the other profile’s current status and re-verification. Keep Beawar office claims/maps/profile mentions on hold until that profile is reinstated; decide separately whether service-area references should remain.
3. **Accounts and keys:** rotate any key that was ever exposed; enable 2FA for GitHub, hosting, Supabase, registrar, email, Google, and Cloudflare if used. Review access, collaborators, deploy keys/tokens, Actions secrets, webhooks, app authorizations, deploy hooks, team members, and environment variables.
4. **Supabase review:** inspect Auth users and remove only accounts you confirm are unauthorized; check API logs, table changes/rows, storage buckets, Edge Functions, database roles, RLS and grants. Disable public sign-ups if they are not needed. Confirm no anonymous enquiry read/update/delete access. Do not delete user data as part of this audit.
5. **GitHub security:** enable secret scanning with push protection and Dependabot alerts; review Actions and branch protection on `main` (pull request required; prevent force-push). Review the full repository history with an authorized workstation before deciding whether history rewriting is necessary.
6. **Backups and recovery:** export Supabase data and keep an offline copy; keep an offline repository/site backup and document a tested rollback procedure.
7. **Search and legal:** review Search Console Security Issues and Manual Actions; if hacked content was flagged and has been removed, request review. If personal data may have been exposed, consult an India-qualified lawyer/security professional about DPDP Act 2023 obligations and applicable CERT-In reporting directions.
8. **Release strategy:** publish in controlled batches (for example, by district). Between batches, monitor Search Console Pages/Security reports, crawl errors, 404s, sitemap processing, form delivery, uptime, and real searches for at least a week.
9. **First-week operations:** test enquiry arrival using an authorized staging or controlled test, verify uptime and live redirects, watch crawl/indexing coverage, and confirm a visitor can reach legal pages and contact the business.
10. **Claims and content:** retain source/permission evidence for testimonials and photos; verify credentials, service areas, business details, hours, and all treatment/safety claims before making them public.

## Appendix A — Automated check outputs

### Indexing, URLs, internal links

- Local HTML: **574 total** = 537 indexable and 37 legacy pages with `noindex, follow` plus immediate meta refresh. These 37 are excluded from the local sitemap.
- `robots.txt` allows crawling and references the `www` sitemap ([`robots.txt`](./robots.txt#L4)).
- Local sitemap: **537 unique URLs**, each with `lastmod`; all correspond to a local indexable HTML file. Local internal-link checks found **0 broken internal links**, **0 case-mismatch paths**, **0 orphan indexable pages**, and maximum click depth **3**.
- Live sitemap: **49 URLs** versus 537 locally. The live sitemap date observed was 2026-09-06; sampled local sitemap dates were 2026-10-17.
- Live response checks: apex → `www` 301; sampled home/About/Contact/Pali/Jaipur routes 200; Privacy Policy, Terms, and Cockroach Control 404; an arbitrary unknown path returned 404.
- No localhost, loopback, `file://`, or staging-domain canonical was identified in the local page scan. Apex/`www` references are mixed in image/social/schema URLs; canonical `<link>` values use `www`.
- No empty-PIN badge was found. One empty `href="#"` is present in the Blog listing.
- A custom local `404.html` was not found. The tested unknown live path returned 404, but custom error-page rendering was not verified.
- Special filenames include image assets whose spaces are percent-encoded in URLs; checked local links resolved. No route case mismatch was found.

### Page metadata and content

- On 537 indexable pages: exactly **one H1 each**, one canonical, a `lang` attribute, viewport, Open Graph title/description, and Twitter card were present. Titles and descriptions were unique. The normalized title scan found none over 60 characters; no description over 160 characters was found.
- Visible body count below 300 words: Contact (about 90) and Service Location (about 237). This is a word count, not a count of unique words.
- **35 HTML TODO comments** request owner-approved photos or verified local examples; they are not visible page placeholders. No visible lorem ipsum, `example.com`, `your-domain`, `undefined`, `NaN`, or `XXXX` placeholder was identified.
- `location-reviews.js` is referenced by 476 HTML pages. Its rendered review content is dynamically inserted; it is absent from the source HTML until the script runs.
- No confirmed hacked-content injection, suspicious encoded blob, redirect script, or unrelated injected link was identified in the sampled/source scan. The earlier compromise timeline cannot be established without Git history and hosting logs.

### Structured data

- **537 JSON-LD blocks parsed; 0 JSON syntax errors.** The 37 redirect stubs have no JSON-LD.
- FAQPage markup occurs on **485 pages** with **2,593 FAQ entities**. The exact visible-answer comparison found **29 answer-text differences across 10 service pages**; FAQ questions matched. Differences can be paraphrases, so the listed pages require human review.
- No `Review` or `AggregateRating` JSON-LD was found. The local business entity consistently uses an apex-host `@id`, while canonical pages use `www`.
- Beawar appeared in `areaServed` on 9 Service nodes. No Beawar office address or map node was found.

### Security, forms, dependencies, and hosting

- **Secrets scan:** 1,806 working-tree files; no high-confidence service-role/secret-key/JWT/private-key match and no `.env` file found. The browser config contains placeholders, not actual key material. No secret value is reproduced here.
- **History scan:** not performed; there is no `.git` directory and `git` is unavailable. Rotation/history-rewrite need cannot be concluded.
- **Enquiry flow in local source:** client-side trimming, validation/length caps, honeypot, minimum 3-second completion time, Turnstile, and generic `textContent` status are present. Browser code calls the Edge Function; server-side code validates, verifies Turnstile, rate-limits, inserts with `Prefer: return=minimal`, and returns no enquiry row. No browser enquiry `select`, `update`, or `delete` was found. Actual live behavior and Supabase RLS remain unverified.
- **Other APIs:** browser-side Cloudflare Turnstile widget/API loading; enquiry POST to the Supabase Edge Function. The Edge Function calls the rate-limit RPC and inserts an enquiry server-side. No separate admin/scheduler app was identified in the local tree; other consumers of the same Supabase project are not verifiable.
- **Script scan:** 583 inline script blocks in HTML; 0 inline event-handler attributes; 0 direct external script or stylesheet URLs in HTML; 0 SRI attributes. Turnstile is dynamically loaded from Cloudflare by the form module. No npm/package lockfile was found, so `npm audit` does not apply.
- GitHub Pages does not support arbitrary response headers through `_headers`, `.htaccess`, or site HTML. Live HSTS was present; CSP, `X-Content-Type-Options`, frame protection, `Referrer-Policy`, and `Permissions-Policy` were absent.
- Read-only HEAD checks found the following internal artifacts **not served** (404): `SECURITY_REPORT.md`, `SECURITY_AUDIT.md`, `MANUAL_STEPS.md`, `supabase/security.sql`, the Edge Function source, `SEO_CONTENT_TOPIC_AUDIT.csv`, `AI_READINESS_REPORT.md`, `seo-audit-report/ISSUES.csv`, and `/tests/`. This is limited to those paths and the current live deployment.
- No analytics/pixel script was identified in the inspected HTML. The Privacy Policy text and actual deployed third-party use were not fully reconciled; consent obligations depend on actual tracking.

### Images, accessibility, and mobile

- **1,673 `<img>` elements**: 0 missing `alt`, 0 missing `width`/`height`; 1,070 have no explicit `loading` attribute. No referenced local image exceeded 250 KB. File formats were mixed; not every image was proven to be WebP.
- 3,515 `_blank` links checked had `noopener noreferrer`.
- Four sampled source pages have no `<main>` landmark: About, Contact, Commercial Pest Control, and Residential Pest Control.
- No direct inline event-handler attributes were found. Form status messages use `textContent`; the `insertAdjacentHTML` use in location reviews injects a static hard-coded review template, not form input.
- Lighthouse, contrast, tap-target, screen-reader, and comprehensive small-screen tests were not available/performed.

## Appendix B — Security scan limitations

The working-tree scan found no high-confidence exposed secret. Public project identifiers and configuration placeholders are not secret credentials and are intentionally not reproduced. The full Git-history scan, GitHub secret-scanning status, external repositories/apps, Supabase dashboard, private storage, backups, and production logs were unavailable. A clean current-tree scan therefore does **not** establish that a previously exposed key was rotated or that no historic secret exists.

## Appendix C — Highest location-page overlap pairs

Screening method: for each of 461 nested location pages, tokenize visible `<main>` text, build sets of five-word shingles, and calculate `intersection / size of the smaller set`. This is a containment screen, not a standard plagiarism score. Results at/above 60% are listed; manually review context before deciding whether pages should change or be removed.

| Similarity | Page A | Page B |
|---:|---|---|
| 68.7% | `pest-control-in-khairthal-tijara/kishangarh-bas/index.html` | `pest-control-in-jaisalmer/dhibba-para/index.html` |
| 67.7% | `pest-control-in-sri-ganganagar/sri-karanpur/index.html` | `pest-control-in-alwar/ramgarh/index.html` |
| 65.9% | `pest-control-in-kota/gumanpura/index.html` | `pest-control-in-banswara/kushalgarh/index.html` |
| 65.6% | `pest-control-in-dholpur/rajakhera/index.html` | `pest-control-in-deeg/pahari/index.html` |
| 65.3% | `pest-control-in-tonk/tonk-city/index.html` | `pest-control-in-dungarpur/galiyakot/index.html` |
| 65.2% | `pest-control-in-karauli/todabhim/index.html` | `pest-control-in-chittorgarh/gangrar/index.html` |
| 64.9% | `pest-control-in-bhilwara/gangapur-road/index.html` | `pest-control-in-ajmer/civil-lines/index.html` |
| 64.7% | `pest-control-in-chittorgarh/bapu-nagar/index.html` | `pest-control-in-ajmer/hathi-bhata/index.html` |
| 64.7% | `pest-control-in-sri-ganganagar/raisinghnagar/index.html` | `pest-control-in-sikar/sri-madhopur/index.html` |
| 64.0% | `pest-control-in-jhunjhunu/rajota/index.html` | `pest-control-in-dholpur/nh-44-area/index.html` |
| 63.9% | `pest-control-in-udaipur/hiran-magri/index.html` | `pest-control-in-ajmer/civil-lines/index.html` |
| 63.7% | `pest-control-in-udaipur/bhuwana/index.html` | `pest-control-in-deeg/deeg-city/index.html` |
| 63.6% | `pest-control-in-bhilwara/azad-nagar/index.html` | `pest-control-in-barmer/baytu/index.html` |
| 63.6% | `pest-control-in-alwar/jai-marg/index.html` | `pest-control-in-alwar/kathumar/index.html` |
| 63.6% | `pest-control-in-jodhpur/luni/index.html` | `pest-control-in-bundi/bundi-city/index.html` |
| 63.5% | `pest-control-in-sri-ganganagar/raisinghnagar/index.html` | `pest-control-in-pali/sadri/index.html` |
| 63.4% | `pest-control-in-churu/sardarshahar/index.html` | `pest-control-in-bundi/keshoraipatan/index.html` |
| 63.3% | `pest-control-in-udaipur/panchsheel-market/index.html` | `pest-control-in-banswara/udaipur-road/index.html` |
| 63.3% | `pest-control-in-rajsamand/rajsamand-city/index.html` | `pest-control-in-jhalawar/manohar-thana/index.html` |
| 63.0% | `pest-control-in-tonk/tonk-city/index.html` | `pest-control-in-baran/chhipabarod/index.html` |
| 62.8% | `pest-control-in-bhilwara/mandal/index.html` | `pest-control-in-bhilwara/pur-road/index.html` |
| 62.8% | `pest-control-in-sirohi/sarupganj/index.html` | `pest-control-in-barmer/chohtan/index.html` |
| 62.7% | `pest-control-in-bhilwara/raipur/index.html` | `pest-control-in-beawar/bijainagar/index.html` |
| 62.2% | `pest-control-in-kotputli-behror/viratnagar/index.html` | `pest-control-in-alwar/jai-marg/index.html` |
| 62.2% | `pest-control-in-tonk/dooni/index.html` | `pest-control-in-tonk/newai/index.html` |
| 62.1% | `pest-control-in-dungarpur/chikhli/index.html` | `pest-control-in-ajmer/ajmer-city/index.html` |
| 61.9% | `pest-control-in-rajsamand/kankroli/index.html` | `pest-control-in-alwar/rajgarh/index.html` |
| 61.9% | `pest-control-in-nagaur/merta-city/index.html` | `pest-control-in-baran/chhipabarod/index.html` |
| 61.7% | `pest-control-in-jaisalmer/sam/index.html` | `pest-control-in-dausa/ramgarh-pachwara/index.html` |
| 61.6% | `pest-control-in-phalodi/jodhpur-road/index.html` | `pest-control-in-khairthal-tijara/kishangarh-bas/index.html` |
| 61.6% | `pest-control-in-jodhpur/bhopalgarh/index.html` | `pest-control-in-chittorgarh/rawatbhata/index.html` |
| 61.6% | `pest-control-in-rajsamand/amet/index.html` | `pest-control-in-beawar/beawar-city/index.html` |
| 61.6% | `pest-control-in-dausa/baswa/index.html` | `pest-control-in-bhilwara/pur-road/index.html` |
| 61.6% | `pest-control-in-dungarpur/galiyakot/index.html` | `pest-control-in-alwar/ramgarh/index.html` |
| 61.5% | `pest-control-in-tonk/station-road/index.html` | `pest-control-in-bhilwara/azad-nagar/index.html` |
| 61.5% | `pest-control-in-khairthal-tijara/tijara-city/index.html` | `pest-control-in-jhunjhunu/nawalgarh/index.html` |
| 61.4% | `pest-control-in-pali/rohat/index.html` | `pest-control-in-bhilwara/bhilwara-city/index.html` |
| 61.4% | `pest-control-in-jaipur/kalgiri-road/index.html` | `pest-control-in-hanumangarh/hanumangarh-junction/index.html` |
| 61.3% | `pest-control-in-pali/sojat-road/index.html` | `pest-control-in-beawar/masuda/index.html` |
| 61.1% | `pest-control-in-khairthal-tijara/khairthal-city/index.html` | `pest-control-in-bikaner/bikaner-city/index.html` |
| 61.0% | `pest-control-in-nagaur/parbatsar-road/index.html` | `pest-control-in-jaipur/muhana/index.html` |
| 61.0% | `pest-control-in-jalore/sayla/index.html` | `pest-control-in-bhilwara/riico-industrial-area/index.html` |
| 60.9% | `pest-control-in-sikar/neem-ka-thana/index.html` | `pest-control-in-banswara/anandpuri/index.html` |
| 60.9% | `pest-control-in-kotputli-behror/kotputli-city/index.html` | `pest-control-in-banswara/anandpuri/index.html` |
| 60.9% | `pest-control-in-chittorgarh/begun/index.html` | `pest-control-in-bikaner/kolayat/index.html` |
| 60.7% | `pest-control-in-sawai-madhopur/bamanwas/index.html` | `pest-control-in-bhilwara/pur-road/index.html` |
| 60.7% | `pest-control-in-salumbar/kherwara-salumber/index.html` | `pest-control-in-pali/bali/index.html` |
| 60.7% | `pest-control-in-pali/bali/index.html` | `pest-control-in-jaipur/jawahar-nagar/index.html` |
| 60.6% | `pest-control-in-jhalawar/manohar-thana/index.html` | `pest-control-in-bikaner/dungargarh/index.html` |
| 60.5% | `pest-control-in-jaipur/barhmohanpura/index.html` | `pest-control-in-jaipur/sirsi-road/index.html` |
| 60.5% | `pest-control-in-sirohi/abu-road-industrial-area/index.html` | `pest-control-in-jaipur/kalwar/index.html` |
| 60.5% | `pest-control-in-udaipur/celebration-mall-area/index.html` | `pest-control-in-jalore/sanchore/index.html` |
| 60.4% | `pest-control-in-hanumangarh/tibbi/index.html` | `pest-control-in-alwar/govindgarh/index.html` |
| 60.4% | `pest-control-in-dausa/lalsot/index.html` | `pest-control-in-baran/atru/index.html` |
| 60.2% | `pest-control-in-dausa/mahwa-road/index.html` | `pest-control-in-churu/nai-sarak/index.html` |
| 60.2% | `pest-control-in-kota/itawa/index.html` | `pest-control-in-ajmer/nasirabad/index.html` |
| 60.2% | `pest-control-in-dholpur/sepau/index.html` | `pest-control-in-balotra/sindhari/index.html` |
| 60.2% | `pest-control-in-phalodi/jodhpur-road/index.html` | `pest-control-in-jaipur/officers-campus/index.html` |
| 60.2% | `pest-control-in-udaipur/nathdwara-road/index.html` | `pest-control-in-tonk/station-road/index.html` |
| 60.1% | `pest-control-in-jodhpur/mandore/index.html` | `pest-control-in-dausa/lalsot/index.html` |
| 60.1% | `pest-control-in-jaipur/kishan-pole-bazaar/index.html` | `pest-control-in-deeg/weir/index.html` |
| 60.1% | `pest-control-in-jalore/jaswantpura/index.html` | `pest-control-in-jaisalmer/pokaran/index.html` |
| 60.0% | `pest-control-in-sri-ganganagar/suratgarh/index.html` | `pest-control-in-churu/taranagar-rural/index.html` |

Three additional district-root pairs scored at least 60% by the same screen: Nagaur/Tonk (61.9%), Pali/Tonk (61.4%), and Tonk/Udaipur (60.9%).
