# AI Search Readiness Audit — Super Pest Control Services

**Audit date:** 2026-10-17  
**Scope:** Local project files (all 574 HTML pages) plus read-only requests to the public site. The audit pass itself was read-only; the owner later requested fixes, recorded below. No external API keys or authenticated APIs were used.

## Verdict and scores

**Overall verdict: Not AI-friendly yet — 60/100.**

| Section | Score | Basis |
|---|---:|---|
| A. Crawl access | 4/10 | robots.txt is permissive and HTTPS works, but the live sitemap is much smaller than the local sitemap and multiple locally present URLs return public 404s. |
| B. Content without JavaScript | 8/10 | Sampled content is in static HTML; the main content does not appear to depend on JavaScript. |
| C. Answer-ready content | 4/10 | Local area pages have substantial measured textual similarity, some key landing pages are short, and the blog has no article pages. |
| D. Entity and trust signals | 4/10 | Two AI-facing files claim a Beawar office despite the requested Jaipur-only office policy; the “30 years” experience claim conflicts with the confirmed 2001 founding year. |
| E. Structured data | 7/10 | JSON-LD parses and useful types are present, but six FAQ questions do not appear visibly on their pages, and some pages lack canonical/social metadata. |
| F. Internal linking | 9/10 | All audited district/area relationships are reciprocal, all indexable pages are reachable within three internal-link steps, and no weak-anchor phrases were detected by the phrase check. |
| G. Technical quality | 6/10 | Images are WebP with alt text and dimensions, but few are lazy-loaded and the live site is missing several security headers. |
| H. Local/off-site readiness | Not scored | These facts require access to business listings and webmaster accounts; they were not verified and are excluded from the score. |

**Scoring method:** A–G are equally weighted technical/content sections; 42/70 normalizes to 60/100. This is an evidence-based audit estimate, not a search-engine score. Section H is intentionally unscored rather than guessed.

### Post-audit local remediation — 2026-10-17

The scores and findings below are the original audit baseline. Subsequent working-tree-only changes changed the company-age copy to 28 years across all 537 indexable pages and updated the generators. The owner has since confirmed the founding year as 2001, so the correct experience claim in 2026 is 25 years; the 28-year copy and generators still need correction. Other working-tree-only changes removed the Beawar office/address claims from the AI-facing files and future generated service-area schema; completed missing canonical and social-preview metadata (filling incomplete Open Graph/Twitter fields on 49 indexable pages); aligned the six FAQ schema mismatches; lazy-loaded below-the-fold images while leaving each page's first three image tags unchanged; and updated all 537 sitemap `lastmod` values. These source changes have **not** been deployed. The live sitemap mismatch, sampled public 404s, hosting-level response-header limits, and facts requiring external account access remain unresolved until deployment or owner action. Area-page similarity flags are not rewritten with invented locality facts.

## Findings

| ID | Severity | Section | Page(s) affected (count; examples) | Evidence | Why it matters | Recommended fix | Effort |
|---|---|---|---|---|---|---|---|
| AI-01 | **HIGH** | A | **At least 7 confirmed live 404s** in the tested URLs; **488** local sitemap routes are absent from the live sitemap. Examples: `https://www.superpest.in/services/cockroach-control/`, `https://www.superpest.in/pest-control-in-jaipur/amer/`, `https://www.superpest.in/privacy-policy/`. | Local [sitemap.xml](./sitemap.xml) contains 537 URLs; public `https://www.superpest.in/sitemap.xml` contains 49. All 49 listed live URLs returned 200, but the three example URLs and the live Terms, termite, Ajmer City, and Beawar City URLs returned 404. | Search and AI systems cannot quote or rank content that is not published at its intended URL. The live legal-page 404s also weaken user trust. | Compare the deployed file tree with the intended site build; publish the intended pages, verify canonical routes and legal pages, then regenerate and submit the sitemap. Check every sitemap URL after deployment. | Large |
| AI-02 | **MEDIUM** | C | **385 of 461 indexable area pages** participate in at least one same-district text-similarity pair at or above 60% (467 pairs total under the stated lexical method). Examples: [Durgapura](./pest-control-in-jaipur/durgapura/index.html), [Sitapura](./pest-control-in-jaipur/sitapura/index.html), [Gopalpura](./pest-control-in-jaipur/gopalpura/index.html). | Automated comparison of visible HTML text after removing script/style/navigation/header/footer and common terms; see Appendix. | Similar pages can be difficult for search systems to distinguish and may provide little additional value to a person asking about one locality. This similarity measure flags review candidates; it does not prove copying or a search penalty. | Add genuinely locality-specific information, service availability, customer questions, and substantiated local examples. Consolidate pages where there is no distinct useful content; do not mass-rewrite with merely swapped place names. | Large |
| AI-03 | **MEDIUM** | C | 3 pages under 300 visible main-content words (excluding common site chrome): [Contact](./contact/index.html) (95), [Service Location](./service-location/index.html) (243), [Cockroach Control](./services/cockroach-control/index.html) (261). | Static-HTML word-count screen. Contact is a transactional page, so its low word count alone is not proof of poor quality. | The service/location pages may not answer enough practical questions for customers or AI systems; the contact page should remain simple but clearly explain how enquiries are handled. | Review whether these pages need useful, specific details (treatment process, safety/preparation, service coverage, or what happens after contacting the company). Avoid padding word count. | Medium |
| AI-04 | **MEDIUM** | C | **0 blog article HTML pages**; one blog listing page: [blog/index.html](./blog/index.html). | Full local HTML inventory and `blog/**/index.html` file listing; the page itself uses `Blog` JSON-LD at [blog/index.html:25](./blog/index.html). | The blog landing page promises guidance, but there are no separate article pages in this project for answer-oriented pest questions. | Publish useful, expert-reviewed articles only when the business can provide accurate, safe, distinct advice. The requested core service topics (cockroach, termite, bed bug, rodent, ant, wasp, fogging, hotels, hostels, factories) do have local service/customer-type pages. | Large |
| AI-05 | **HIGH** | D | **537 pages** repeated the “30 years” claim in the original audit. Examples: [index.html:1109](./index.html), [contact/index.html:409](./contact/index.html), [terms-and-conditions/index.html:169](./terms-and-conditions/index.html). | The original audit's [llms-full.txt](./llms-full.txt) copy listed a founding year that the owner has since corrected to 2001. As of 2026, the accurate experience claim is 25 years. Although the working-tree footer copy was changed to 28 years, it and its generators still require correction. | An incorrect experience claim can undermine trust and conflicts with the confirmed founding year. | Update the shared footer copy, all affected pages, and their generators to state 25 years in 2026; keep the founding year as 2001 in the AI-facing files. | Small |
| AI-06 | **MEDIUM** | D / E / F | **2 AI-facing text files** call Beawar a second office; **11 pages** mention Beawar in structured data; Beawar links occur in **11 HTML files**. Examples: [llms.txt:5](./llms.txt), [pest-control-in-beawar/index.html](./pest-control-in-beawar/index.html), [service-location/index.html](./service-location/index.html). | The AI files explicitly claim another office and give an address. Schema mentions and nine linked routes describe Beawar service areas, not postal offices; the only `PostalAddress` found is Jaipur. No Beawar Maps embed/link was found. Complete page inventory is in Appendix E. | AI-facing summaries can be treated as business facts. The office claim conflicts with the requested Jaipur-only office rule; service-area references should not be mistaken for office locations. | Remove/correct the Beawar office/address claim in both AI files. Retain only accurate service-area schema and links; keep Beawar out of office/address schema and maps. | Small |
| AI-07 | **MEDIUM** | E | **6 FAQ schema questions across 4 service pages** were not found as visible text on their corresponding pages. Examples: [bed-bug-eradication/index.html:79](./services/bed-bug-eradication/index.html), [fly-management-systems/index.html:63](./services/fly-management-systems/index.html), [termite-control/index.html:87](./services/termite-control/index.html). | The structured `name` values are present in JSON-LD, but normalized visible-page text did not contain those six questions. | Structured facts should match visible content; hidden or mismatched FAQ markup may be ignored and reduces confidence in the page representation. | Make the six questions and answers visibly match the JSON-LD, or remove/update the unsupported schema entries. | Small |
| AI-08 | **MEDIUM** | A / E | **5 pages** lack a canonical; **5 pages** use apex-host canonicals while the site redirects to `www`; **4 indexable pages** lack both Open Graph and Twitter metadata. Examples: [about/index.html](./about/index.html), [contact/index.html](./contact/index.html), [privacy-policy/index.html](./privacy-policy/index.html). | Automated checks across all 574 HTML files. The five apex canonicals are Privacy Policy, Terms, Ant Control, Pre-construction Anti-termite, and Termite Piping; the local sitemap uses `www`. The four indexable social-metadata omissions are Blog, Contact, Commercial, and Residential; the other 37 pages without social tags are redirect stubs. | Missing canonicals make URL consolidation less explicit; mixed canonical hosts disagree with the primary redirect/sitemap host; missing social metadata makes page previews less controlled. | Add self-referencing canonicals to the five missing pages, normalize the five apex canonicals to `www`, and add OG/Twitter title, description, and image tags to the four content pages. | Small |
| AI-09 | **MEDIUM** | G | **All sampled live routes** lacked CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, and `Permissions-Policy`; HSTS was present. Examples checked: `/`, `/contact/`, `/pest-control-in-jaipur/`. | Read-only GET/HEAD response headers from GitHub Pages; `Strict-Transport-Security: max-age=31556952` was present. Other listed headers were absent. Direct GitHub Pages does not apply arbitrary response headers from repository config; see [GITHUB_PAGES_SECURITY_HEADERS.md](./GITHUB_PAGES_SECURITY_HEADERS.md). | These headers improve browser-side protections and are part of the requested technical trust baseline. Their absence is not a robots block, but should be recorded. | Enable Enforce HTTPS in GitHub Pages. If the other headers are required, use a supported proxy/CDN or host that can set response headers; begin CSP in report-only mode there. | Medium |
| AI-10 | **LOW** | G | **1,673 image references** are WebP and have alt text and width/height; only **62** declare `loading="lazy"`. | Full HTML image-element scan; example with explicit dimensions and loading priority: [pest-control-in-jaipur/amer/index.html:190](./pest-control-in-jaipur/amer/index.html). | Image format, alt text, and dimensions are positive. Loading most below-the-fold images eagerly may increase network work and affect perceived speed; image loading should be chosen by position, not applied blindly. | Lazy-load below-the-fold images, while keeping the hero/LCP image eager and prioritized. Measure actual page weight and Core Web Vitals after deployment. | Medium |

### Positive findings

- `robots.txt` has no `Disallow` rules and applies `Allow: /` to the wildcard group ([robots.txt:2-4](./robots.txt)).
- All 537 non-redirect content pages are represented in the **local** sitemap; the 37 omitted routes are noindex legacy redirect stubs whose targets exist locally.
- The local indexable page set includes 17 service URLs (overview plus 16 service pages), 41 district pages, 461 live-content area pages (plus 37 redirect stubs), and 9 audience-specific `pest-control-for-*` pages.
- The automated internal-link graph found no unlinked indexable pages. Every district page links to its area pages, every area page links back to its district, and maximum calculated home-to-page depth is 3.
- No weak anchors matching “click here,” “read more,” “learn more,” “view,” or “here” were found by the literal-text check.
- Every checked JSON-LD block parsed. Main types: `Service` (530 nodes), `BreadcrumbList` (532), `FAQPage` (485), `WebPage` (490), plus one each of `LocalBusiness`, `WebSite`, `AboutPage`, `Blog`, and `ContactPage`.
- The one `LocalBusiness` postal address is Jaipur. The 11 structured-data pages containing the text “Beawar” use it as a service-area/location fact, not a Beawar postal office address. No Beawar Maps URL was found in local HTML.
- All 1,673 referenced `<img>` elements were WebP and had `alt`, `width`, and `height` attributes. No `localhost` or `127.0.0.1` reference was found in the HTML.
- The source includes [llms.txt](./llms.txt), [llms-full.txt](./llms-full.txt), and [security.txt](./.well-known/security.txt). Presence locally does not confirm every optional file is deployed.

## Pages needing the most work — top 20

The first seven below are confirmed public 404s. Remaining entries are local review priorities based on low main-content counts or high same-district similarity; they were not individually confirmed as live 404s.

1. `https://www.superpest.in/services/cockroach-control/` — live 404; local content is 261 words.
2. `https://www.superpest.in/services/termite-control/` — live 404.
3. `https://www.superpest.in/pest-control-in-jaipur/amer/` — live 404; local area page exists.
4. `https://www.superpest.in/pest-control-in-beawar/beawar-city/` — live 404; local area page exists.
5. `https://www.superpest.in/pest-control-in-ajmer/ajmer-city/` — live 404; local area page exists.
6. `https://www.superpest.in/privacy-policy/` — live 404; local page exists and is linked in footers.
7. `https://www.superpest.in/terms-and-conditions/` — live 404; local page exists and is linked in footers.
8. [contact/index.html](./contact/index.html) — 95 visible main-content words and no canonical/OG/Twitter tags; live page returned 200.
9. [service-location/index.html](./service-location/index.html) — 243 visible main-content words.
10. [services/cockroach-control/index.html](./services/cockroach-control/index.html) — 261 visible main-content words.
11. [pest-control-in-jaipur/durgapura/index.html](./pest-control-in-jaipur/durgapura/index.html) — highest same-district similarity pair count (9).
12. [pest-control-in-udaipur/fatehpura/index.html](./pest-control-in-udaipur/fatehpura/index.html) — 8 high-similarity peers.
13. [pest-control-in-udaipur/sector-5/index.html](./pest-control-in-udaipur/sector-5/index.html) — 8 high-similarity peers.
14. [pest-control-in-jaipur/sitapura/index.html](./pest-control-in-jaipur/sitapura/index.html) — 8 high-similarity peers.
15. [pest-control-in-jaipur/gopalpura/index.html](./pest-control-in-jaipur/gopalpura/index.html) — 8 high-similarity peers.
16. [pest-control-in-jaipur/mansarovar/index.html](./pest-control-in-jaipur/mansarovar/index.html) — 7 high-similarity peers.
17. [pest-control-in-jaipur/jawahar-nagar/index.html](./pest-control-in-jaipur/jawahar-nagar/index.html) — 7 high-similarity peers.
18. [pest-control-in-jaipur/chomu/index.html](./pest-control-in-jaipur/chomu/index.html) — 7 high-similarity peers.
19. [pest-control-in-udaipur/bhuwana/index.html](./pest-control-in-udaipur/bhuwana/index.html) — 6 high-similarity peers.
20. [pest-control-in-sri-ganganagar/gharsana/index.html](./pest-control-in-sri-ganganagar/gharsana/index.html) — 6 high-similarity peers.

## Quick wins and recommended fix order

### Under an hour each (after business facts are confirmed)

1. Correct the experience claim to 25 years in 2026 and keep it consistent with the confirmed 2001 founding year in the shared footer and AI-facing files.
2. Remove or correct the Beawar **office** statement in `llms.txt` and `llms-full.txt`; retain accurate service-area mentions as needed.
3. Add canonical tags and OG/Twitter tags to the identified content pages.
4. Align the six FAQ questions/answers between visible text and JSON-LD.
5. Publish and verify the Privacy Policy and Terms pages at their intended public URLs.

### Recommended order

1. **Resolve the live deployment mismatch first.** Compare the production build with the intended 537-URL local sitemap, restore required pages, and retest every route and sitemap entry. Do not submit a sitemap containing 404s.
2. Confirm factual business details (founding/experience, office locations, contact details, hours, and reviews) with the owner, then make local HTML and AI-facing files consistent.
3. Repair canonical/social metadata and visible FAQ/schema mismatches.
4. Review the three short main-content pages and the 385 area pages flagged by similarity. Improve only where useful, unique local information can be supported.
5. For headers, decide whether to remain on direct GitHub Pages (with its header limitations) or use a service/host that can set the requested response headers.
6. Complete the off-site checks in Section H and repeat public status/sitemap checks after publishing.

## Not verified

- Whether Googlebot, Bingbot, OpenAI, Perplexity, Claude, or Gemini actually crawled or indexed the production pages; robots.txt only expresses crawl preferences.
- Firewall, CDN, abuse-protection, or any other host-side crawler blocks beyond the observed public GitHub Pages responses.
- HTTP status for all 574 local page URLs. The public sitemap’s 49 listed URLs all returned 200; 13 representative URLs were checked separately, of which 7 returned 404.
- Public response headers for every URL, and `X-Robots-Tag` behavior outside the sampled responses.
- Google Search Console/Bing Webmaster Tools setup, sitemap submission, index coverage, manual actions, security issues, or AI Overview citations.
- The founding year is confirmed by the owner as 2001; the experience claim should be 25 years in 2026. Working-tree page copy and generators still state 28 years and need correction.
- The authenticity of visible homepage testimonials and five-star graphics. No `Review`/`AggregateRating` structured data was found; this does not prove the testimonials are false.
- Whether social/profile links are current and correct, whether local listings match the site, or whether the Jaipur Google Business Profile is complete.
- Live page weight, mobile Core Web Vitals, field performance, and whether eager image loading is materially harming users.
- Full Git history, deployed file inventory beyond public HTTP checks, and unlisted URLs not in the public sitemap.

## Manual off-site checklist (Section H)

These items were **not checked or passed** in this audit:

- [ ] Confirm the Jaipur Google Business Profile is verified, complete, current, and has genuine recent reviews.
- [ ] Confirm the Beawar profile’s current status; do not publish it as an office if it is not an active, usable office. Keep truthful service-area coverage separate.
- [ ] Compare business name, phone, email, Jaipur address, and opening hours against major Indian directories and map listings; correct inconsistencies at their source.
- [ ] Set up/verify Google Search Console and Bing Webmaster Tools for the canonical `https://www.superpest.in/` property.
- [ ] Submit the live sitemap after the 404/deployment mismatch is corrected; review indexing, crawl, and security reports.
- [ ] Test profile/social URLs and any business citations directly; local code presence does not prove that a profile is working or controlled by the business.
- [ ] Monthly, try a small fixed prompt set in Google Search/AI Overviews, Bing/Copilot, ChatGPT Search, Perplexity, and Gemini, such as “pest control in Jaipur,” “termite treatment in Jaipur,” and “safe bed bug treatment for hotels in Rajasthan.” Record the date, prompt, whether the company is cited, and the cited sources. This is monitoring, not a ranking guarantee.

## Appendix — automated checks and samples

### A. robots.txt rules

Live `https://www.superpest.in/robots.txt` returned 200 and matched the local file. It contains no `Disallow` directive.

| User-agent group in file | Rule | Result for `/` |
|---|---|---|
| `*` | `Allow: /` | Allowed for Googlebot, Bingbot, OAI-SearchBot, ChatGPT-User, PerplexityBot, ClaudeBot, and other agents that honor the wildcard group. |
| `GPTBot` | `Allow: /` and `/llms.txt` | Allowed explicitly. |
| `Google-Extended` | `Allow: /` and `/llms.txt` | Allowed explicitly; Google Search crawling is governed by Googlebot. |
| `anthropic-ai` | `Allow: /` and `/llms.txt` | Allowed explicitly for this named agent. `ClaudeBot` is not named separately, but falls under `*` absent a more specific group. |
| `Bingbot`, `OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `ClaudeBot` | No dedicated group | No block is present; each inherits the wildcard `Allow: /` under standard robots matching. |

The public host identifies as GitHub Pages (`Server: GitHub.com`). No host firewall configuration was available for inspection.

### B. Sitemap, redirects, and statuses

- Local source: 574 HTML files; sitemap has 537 URLs, all HTTPS `www.superpest.in` URLs with `lastmod`. The other 37 files are `noindex, follow` legacy stubs using a zero-second meta refresh and JavaScript redirect; all 37 targets exist locally.
- Local sitemap `lastmod` distribution: 487 at `2026-10-09`, 41 at `2026-10-10`, 8 at `2026-09-06`, and 1 at `2026-10-12`.
- Live sitemap: 49 URLs, all with `lastmod` `2026-09-06`; all 49 returned HTTP 200 without a redirect. This is 488 fewer entries than the local sitemap.
- Live apex `http://superpest.in/` and `https://superpest.in/` each returned a single 301 to `https://www.superpest.in/`.
- Confirmed live 404 examples: `/services/cockroach-control/`, `/services/termite-control/`, `/pest-control-in-jaipur/amer/`, `/pest-control-in-beawar/beawar-city/`, `/pest-control-in-ajmer/ajmer-city/`, `/privacy-policy/`, `/terms-and-conditions/`.
- The 37 local redirect stubs are not counted as orphan indexable pages. The redirect behavior of those legacy URLs on the live host was not tested.

### C. All-page checks

- Page inventory: 574 HTML files; 537 indexable content pages and 37 noindex redirect stubs.
- Page families: 17 service URLs including the overview; 41 district pages; 498 area-route files, of which 37 are legacy stubs; 9 customer-type pages.
- Five content pages lack canonical links: About, Contact, Commercial, Residential, and the Beawar district page.
- All 537 indexable pages have exactly one `<h1>` tag. The 37 legacy redirect stubs have no H1, as expected for redirect documents.
- Three indexable pages have under 300 words of visible content after excluding script/style/navigation/header/footer: Contact (95), Service Location (243), Cockroach Control (261). Word counts are a screening aid, not a quality score.
- No `localhost` or `127.0.0.1` URLs were found in HTML.
- Sampled raw source showed headings, main text, links, FAQs, and contact details in HTML. A separate blog article did not exist to sample; the local Blog route is only a listing page.

**Manual raw-source sample set:** 41 local pages were reviewed across categories: Home; About; Contact; all 17 service URLs (overview plus 16 detailed services); hotel, hostel, and factory customer pages; district pages for Ajmer, Jaipur, Jodhpur, Kota, and Udaipur; 10 area pages across Jaipur, Ajmer, Beawar, Banswara, Jodhpur, Kota, and Udaipur (including Amer, Durgapura, Malviya Nagar, Ajmer City, Ana Sagar, Beawar City, Banswara City, Jodhpur City, Kota City, and Udaipur City); Blog listing; Privacy Policy; and Terms. Automated checks ran across all 574 HTML files. No separate blog-post HTML pages were present.

### D. Similarity and orphan checks

- Similarity method: same-district pairwise Jaccard similarity over visible content words after removing script/style/navigation/header/footer and a fixed list of common generic terms. This is a reproducible lexical screen, not semantic plagiarism detection.
- Result: 467 pairs among the 461 indexable area pages scored at least 0.60; 385 pages participate in at least one such pair. No pair scored 1.00 after excluding site chrome.
- Highest pair counts and examples: Durgapura (9 peers); Fatehpura, Udaipur (8); Sector 5, Udaipur (8); Sitapura (8); Gopalpura (8).
- District-to-area link omissions: 0. Area-to-district link omissions: 0. Indexable pages with no inbound internal links: 0. Maximum calculated depth from Home: 3 clicks.
- Thirty-seven legacy redirect stubs have no inbound links, but are noindex and are not meant to be indexable destinations.
- Literal weak-anchor phrase check (`click here`, `read more`, `learn more`, `view`, `here`): 0 matches.

### E. JSON-LD and metadata checks

- JSON-LD parse errors: 0.
- Counts by type: `LocalBusiness` 1; `WebSite` 1; `AboutPage` 1; `Blog` 1; `ContactPage` 1; `CollectionPage` 2; `WebPage` 490; `Service` 530; `FAQPage` 485; `BreadcrumbList` 532.
- No `Article`, `Review`, or `AggregateRating` type was found. The Blog collection is marked up, but there are no individual article pages.
- Six FAQ question names did not match visible text after normalization; examples are listed under AI-07.
- Area pages use Service/area information. The only `PostalAddress` node found is Jaipur; no Beawar postal office entity or Maps link was found.
- Beawar schema inventory (11 files): `commercial-pest-control/index.html`, `residential-pest-control/index.html`, `pest-control-in-beawar/index.html`, `pest-control-in-beawar/ajmer-road/index.html`, `pest-control-in-beawar/beawar-city/index.html`, `pest-control-in-beawar/bijainagar/index.html`, `pest-control-in-beawar/jaipur-road/index.html`, `pest-control-in-beawar/jawaja/index.html`, `pest-control-in-beawar/masuda/index.html`, `pest-control-in-beawar/sendra-road/index.html`, and `pest-control-in-beawar/todgarh/index.html`. These schema mentions are service-area/locality facts, not office addresses. Beawar-related internal links occur in 11 HTML files: `service-location/index.html`, `services/wasp-hornet-nest-removal/index.html`, and those nine Beawar district/area pages; they point to nine service-area routes. No Beawar Maps embed/link was found. The explicit “additional office” and Beawar street-address claims are in `llms.txt` and `llms-full.txt` (AI-06).
- Four indexable pages lack OG and Twitter metadata: Blog, Contact, Commercial, and Residential. Thirty-seven additional pages lack these tags because they are legacy redirect stubs.
- Root HTML `lang` values: 536 `en`, 38 `en-IN`; 39 pages contain Hindi-language sections marked `lang="hi"`.

### F. Images, headers, and optional files

- Image elements: 1,673 references; all use `.webp`; all have `alt`, `width`, and `height`. 62 declare `loading="lazy"`.
- The live GET/HEAD sample found HSTS but not CSP, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy`, or `X-Robots-Tag`.
- Local `llms.txt`, `llms-full.txt`, and `.well-known/security.txt` exist. `llms.txt`/`llms-full.txt` publication on the live host was not checked.
- A front-end secret-shaped credential scan found zero candidates in 586 readable HTML/JS/MJS/CSS text files. No credential value is reproduced here; this does not cover Git history or unlisted deployed assets.
