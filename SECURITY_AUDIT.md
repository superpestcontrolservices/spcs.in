# Security Audit — Phase 1

**Scope:** Read-only review of the available workspace for Super Pest Control Services. No source, deployment, database, or account changes were made. No live service was contacted.

**Overall result:** No confirmed exploitable vulnerability was identified in the inspected workspace. Public enquiry-data confidentiality cannot be confirmed without reviewing the Supabase project’s RLS, grants, and policies. Git history, deployed files, and live response headers were unavailable, so this is not a complete forensic or production audit.

## Findings (ranked)

| # | Severity | File / line | Finding and risk | Recommended fix / action |
|---|---|---|---|---|
| 1 | MEDIUM — configuration check; not confirmed vulnerability | [js/script.min.js:1](./js/script.min.js) | The browser sends a `POST` to `/rest/v1/enquiries` using a Supabase URL and a publishable key beginning `sb_pub` (only the first six characters are shown). The request includes name, phone, email, service, message, and client-supplied `status: "New"`. No browser `SELECT`, `UPDATE`, `DELETE`, or RPC call was identified. RLS, grants, and column restrictions are not represented in the available site files, so public read access and permitted insert fields remain unverified. | In Supabase, verify RLS is enabled and anonymous users cannot select, update, or delete enquiry rows. Restrict anonymous inserts to intended fields and enforce validation/status assignment on the server or database. Never place a service-role key in browser code. |
| 2 | MEDIUM — configuration check; not confirmed vulnerability | [contact/index.html:242](./contact/index.html), [pest-control-in-ajmer/index.html:979](./pest-control-in-ajmer/index.html), [js/script.min.js:1](./js/script.min.js) | Forms have required-field/browser constraints and the shared handler checks required values and a phone pattern. No visible CAPTCHA, honeypot, or minimum submission-time check was found. Client checks can be bypassed; server-side validation and anti-abuse controls are not verifiable here. | Validate and limit all fields at the server/database boundary. Confirm suitable abuse controls for the public enquiry endpoint. |
| 3 | LOW — deployment configuration not verified | [_config.yml:1](./_config.yml), [CNAME:1](./CNAME) | The available files indicate a Jekyll-style static site with a custom domain, but no response-header configuration was found in the workspace. This does not prove that production headers are absent. The actual hosting platform and deployed CSP, HSTS, `X-Content-Type-Options`, framing, Referrer-Policy, and Permissions-Policy headers could not be checked. | Verify headers and hosting configuration in the provider dashboard or against the deployed response. Configure the applicable host-level security headers after checking site dependencies. |
| 4 | LOW — audit coverage limitation | Git history and deployed output unavailable | The workspace was not available as a Git repository. Branches, working-tree changes, and all-branch history could not be inspected; historical secrets and changes therefore remain unaudited. The deployed folder could not be compared with tracked files. | Run a full-history secret scan in the actual repository, including every branch and reachable commit. Compare deployment output with the intended build and review recent commits/deploys. |

## Secret and key scan

- No private key, service-role/secret key, or JWT pattern was identified in the inspected source/config text. No JWT was available to decode; consequently, no role or expiry can be reported.
- The Supabase browser key at [js/script.min.js:1](./js/script.min.js) begins `sb_pub`. This is a publishable client key, not a service-role key or JWT; it is expected to be visible to browsers. Its full value is intentionally not reproduced.
- The site-verification metadata at [index.html:14](./index.html) is public verification metadata, not an API credential.
- **Limit:** This finding applies only to available working-tree text. Full Git history, untracked/deployed files, and remote configuration were not available for scanning.

## Browser API and data access

- **Supabase:** One browser data operation was identified in [js/script.min.js:1](./js/script.min.js): `POST /rest/v1/enquiries` with form fields and a client-supplied status. No browser select/read, update, delete, RPC, storage, or auth operations were identified in the reviewed browser code.
- **Other APIs:** No other external browser API calls were identified. The service worker at [sw.js:46](./sw.js) handles same-origin static GET caching/fetch fallback.
- Enquiry/customer data confidentiality depends on database policies not present in the static site workspace. Whether other apps share the Supabase project cannot be determined from these files.

## Compromise indicators

- No clear malicious remote script loader, dynamic code execution, or other obvious compromise indicator was identified in the inspected site scripts.
- First-party scripts identified include [js/script.min.js](./js/script.min.js) (example reference: [index.html:1322](./index.html)) and [js/location-reviews.js](./js/location-reviews.js) (example reference: [pest-control-in-rajsamand/rajsamand-city/index.html:427](./pest-control-in-rajsamand/rajsamand-city/index.html)). No remote `<script src>` or SRI attributes were found.
- `innerHTML` / `insertAdjacentHTML` uses identified in [js/script.min.js:1](./js/script.min.js) and [js/location-reviews.js:121](./js/location-reviews.js) appear to build fixed markup; no flow of enquiry/user-supplied content into those sinks was identified. The form handler displays the submitted name in an alert, not as HTML. No confirmed XSS was found.
- No Git history was available to establish when relevant files changed. Local filesystem timestamps reported for `index.html` and `contact/index.html` were 2026-10-14, and for `js/script.min.js` and `js/location-reviews.js` were 2026-10-13; timestamps alone do not establish suspicious changes.
- No deployed-folder inventory was available, so extra or untracked deployed files could not be checked.

## Forms and validation

- Contact form markup: [contact/index.html:242](./contact/index.html); another form example: [pest-control-in-ajmer/index.html:979](./pest-control-in-ajmer/index.html). The forms use required fields and browser-side phone/length constraints; the shared script performs required-value and phone-pattern checks.
- No visible CAPTCHA, honeypot, or minimum-time check was identified.
- Message is optional. Browser-side checks are not a substitute for server/database validation.

## Hosting, headers, and transport

- [CNAME](./CNAME) and [_config.yml](./_config.yml) suggest a static custom-domain/Jekyll-style project; they do not conclusively identify the production host.
- No header configuration file or CSP meta policy was identified in the workspace. Production header state, HTTPS redirects, TLS configuration, and mixed content were not verified because no live requests were made.
- An existing [`.well-known/security.txt`](./.well-known/security.txt) provides an email and web contact and a canonical URL. It is not an API credential.

## Dependencies and related applications

- No `package.json` or lockfile was identified in the available site workspace; therefore `npm audit` or an equivalent manifest-based vulnerability check was not available.
- A local `.venv` was present, but whether it is tracked or deployed could not be verified. No separate backend/admin/scheduler application was identified in the inspected workspace. Other applications using the same Supabase project cannot be discovered from this static site alone.

## Environment limitations and next step

The workspace is not a Git repository, so the requested `security-hardening` branch cannot be created here and working-tree/history scans across all branches could not be completed. Live Supabase, hosting, and account settings were not accessed. Treat the Supabase RLS/grant review and the unavailable history/deployment checks as open items before making any claim that customer data is protected.

**Phase 1 is complete. No Phase 2 or Phase 3 work has been started.**
