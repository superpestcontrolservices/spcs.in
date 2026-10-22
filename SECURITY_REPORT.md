# Super Pest Control Services — Security Report

**Assessment date:** 2026-10-17  
**Scope:** Available static-site workspace only. No live Supabase project, hosting account, deployment, or user data was accessed or modified.

## Executive summary

No confirmed service-role key, secret key, JWT, private key, or third-party API credential was found in the available text files during the final working-tree scan. The original browser code contained a Supabase **publishable** key; the value was removed from the shared script, and the new public configuration contains a replacement placeholder pending rotation. This is not evidence that all Git history or deployed files are clean: the provided workspace has no Git repository and Git is unavailable here.

The browser no longer submits directly to the enquiries table. A hardened client submits to a Supabase Edge Function; the function validates inputs, verifies Turnstile, applies IP rate limits through a restricted database RPC, and inserts with `return=minimal`. The RLS SQL is prepared for review only and was not executed. **Customer-data confidentiality is therefore not yet verified against the live project.**

## Ranked findings

| # | Severity | File / line | Status and risk | Required action |
|---|---|---|---|---|
| 1 | MEDIUM — unverified backend control | [supabase/security.sql:126](./supabase/security.sql) | The SQL now restricts anonymous enquiry inserts and denies public reads/changes, but it has not been applied or tested against the actual schema. Until verified, public read access to customer data remains an open question. | Review the schema and SQL, run it in staging first, then inspect grants/RLS and run [tests/rls_check.mjs](./tests/rls_check.mjs) using only a public key. |
| 2 | MEDIUM — hosting limitation | [GITHUB_PAGES_SECURITY_HEADERS.md:3](./GITHUB_PAGES_SECURITY_HEADERS.md) | The owner confirmed direct GitHub Pages hosting. It does not support arbitrary response headers through repository config, so CSP, HSTS, and the other requested headers cannot be set by this workspace. No live response was checked. | Enable GitHub Pages **Enforce HTTPS**. To configure the requested headers, put a supported proxy/CDN in front or move to a host that supports them; then verify with `curl -I`. |
| 3 | LOW — repository/history coverage | [SECURITY_AUDIT.md:14](./SECURITY_AUDIT.md) | No Git executable or repository metadata is available here. All-branch history, deployed files, recent commits, and history-level secret exposure remain unchecked; the requested branch was not created. | In the actual repository, scan every branch and commit. If a real credential appears in history, rotate it first and coordinate a rewrite. Conditional commands are below. |
| 4 | LOW — configuration and deployment pending | [js/security-config.mjs](./js/security-config.mjs), [supabase/DEPLOYMENT.md](./supabase/DEPLOYMENT.md) | The rotated public key and Turnstile site key are placeholders; the function is not deployed. Forms intentionally reject submission until configured. | Add the rotated publishable/site keys, store the Turnstile secret and rate-limit HMAC secret in Supabase Function secrets, review/apply SQL, then deploy and test in staging. Never put a service-role key in the website. |

No confirmed exploitable vulnerability was established from the inspected workspace. The items above are open verification/deployment risks, not proof of production compromise or proof that the database is safe.

## Changes made

- Removed the embedded Supabase URL/key and direct `/rest/v1/enquiries` browser submission from the shared script. The browser now calls only the Edge Function.
- Added browser-side trim/required/length/email/phone validation, a hidden honeypot, a minimum three-second submit delay, a Turnstile container, generic status messages using `textContent`, and no returned enquiry rows.
- Added `supabase/functions/submit-enquiry/index.ts` and a restricted IP-hash rate-limit RPC in the review-only SQL. The function keeps the service-role credential in platform secrets, validates fields, verifies Turnstile hostname/action, rate-limits, and inserts with `Prefer: return=minimal`.
- Added [supabase/security.sql](./supabase/security.sql), which enables RLS for public tables, blocks anonymous reads/updates/deletes, grants anonymous insert only on intended enquiry columns, provides an owner-only authenticated enquiry SELECT policy, and includes inspection/rollback guidance. It does not modify Storage policies; it includes queries and review instructions.
- Added `rel="noopener noreferrer"` to all 3,515 `_blank` links across 537 HTML files. Normalized 56 relative shared-script URLs so those pages load the common script from the site root.
- Removed inline event attributes, added Jekyll deployment exclusions for secrets/backups/build-only security files, added `.gitignore` rules, a Gitleaks pre-commit hook, and setup instructions.
- The existing [`.well-known/security.txt`](./.well-known/security.txt) already has contact details; it was not overwritten.
- Added a GitHub Pages header-limitation note. No ineffective `_headers`, `.htaccess`, or other unsupported header config was added.

## Manual actions still required (in order)

1. **Secure and rotate credentials.** Follow [MANUAL_STEPS.md](./MANUAL_STEPS.md). Replace the publishable-key placeholder only after rotating the key in Supabase. No service-role key was detected, but if your full-history/deployment review finds one, rotate it immediately and keep its replacement server-side only.
2. **Review Supabase access before production.** Inspect tables, owner fields, current policies, and existing rows. Review `supabase/security.sql` carefully; its public-schema loop revokes existing policies/grants and may require adjustments for legitimate admin tables. Run it only after backing up and testing in staging. Replace `YOUR-USER-UUID`. Do not execute it blindly.
3. **Configure and deploy the function.** Add a real Turnstile site key to the public config and its secret to Supabase Function secrets. Add a random `RATE_LIMIT_HMAC_SECRET` there as well. Follow [supabase/DEPLOYMENT.md](./supabase/DEPLOYMENT.md); do not deploy until staging tests pass.
4. **Run RLS probes in staging.** Follow [tests/README.md](./tests/README.md). It uses only a public key, requires staging confirmation and verified-absent probe filters, uses rollback preference for update/delete probes, and leaves a marked valid test insert for authorized cleanup.
5. **Address response headers and HTTPS.** Direct GitHub Pages cannot apply these response headers from a checked-in file. Enable **Enforce HTTPS** in repository Pages settings. To add CSP/HSTS and the other headers, place a supported proxy/CDN in front or migrate hosting. [GITHUB_PAGES_SECURITY_HEADERS.md](./GITHUB_PAGES_SECURITY_HEADERS.md) contains a tailored report-only policy proposal and enforcement guidance. No production `curl` request was made.
6. **Scan actual Git history and deployment.** This workspace was not a Git checkout. Scan all branches, deployed output, GitHub Actions, hosting variables, and account access from the actual project before declaring containment complete.
7. **If history contains a secret:** rotate/revoke it first, coordinate with every collaborator, then use a fresh clone and a replacements file stored outside the repository. For `git filter-repo`, the replacements file format is `literal:<OLD_SECRET_VALUE>==>***REMOVED***`. Conditional commands (not run here):

   ```powershell
   git clone --mirror <REPOSITORY_URL> security-rewrite.git
   Set-Location security-rewrite.git
   git filter-repo --replace-text C:/secure/replacements.txt
   git remote add origin <REPOSITORY_URL>
   git push --force --mirror origin
   ```

   This rewrites remote history and may conflict with protected/host-managed refs. Have the repository owner review the refs and coordinate the rewrite; all collaborators must re-clone afterward. Do not run these commands unless a real historical secret is confirmed and the team approves the rewrite.
8. If customer personal data may have been exposed, consult an Indian privacy lawyer and incident-response professional about applicable DPDP Act 2023 requirements and CERT-In directions.

## Verification performed

- Scanned 626 readable text files in the final working tree with credential-pattern checks (excluding `.git`, dependency/build directories, and virtual environments). The only nine broad-pattern hits were literal `service_role` identifier references in the SQL, function, and security documentation; no credential values, private keys, or JWTs were found, so no JWT needed role/expiry decoding. This is not a substitute for Gitleaks on the actual Git history.
- `node --check` passed for the shared script, form modules, and RLS test script.
- `node --test tests/forms.test.mjs`: **5 passed, 0 failed**. Cases cover valid/normalized data, empty/malformed/oversized values, fast submission, and script markup.
- Local browser smoke test of the contact form used a fake Turnstile widget and a mocked Edge Function response; valid submission succeeded, script text remained inert, and no Supabase/hosting request was made. The city-page form injection, honeypot, and Turnstile container were also present.
- A 20-page sample (home, contact, blog, service, policy, city and area pages) retained page titles, JSON-LD blocks, and internal root links. The transformations changed only targeted script/link/event attributes; exact before/after Git comparison was unavailable. Four sampled pages currently have no canonical tag (`about`, `contact`, `commercial-pest-control`, `residential-pest-control`); no baseline was available to determine whether this predates the task.
- Static scanning found no non-schema `http://` resource references. Live mixed content, HTTPS redirect, and response headers remain unverified.
- No dependency manifest/lockfile or Jekyll/Deno build tool is available in this workspace, so no `npm audit`, production build, or Edge Function type-check could be run. No live RLS test, deployment, or production build scan was performed.

## Monthly security routine

- Review Supabase users, API/database logs, RLS policies, grants, Storage buckets, Edge Functions, and Security Advisor alerts.
- Run the public-key RLS checks in staging and verify enquiry rows remain unreadable to anonymous users.
- Review keys and rotate on a planned schedule or immediately after suspected exposure; confirm no service-role secret enters browser bundles or Git history.
- Review GitHub collaborators, deploy keys, tokens, Actions workflows/secrets, webhooks, Dependabot, and branch protection.
- Update dependencies and review the resulting security advisories; test backups with a restore exercise.
- Check HTTPS/header status after hosting changes and review Search Console security issues.

No process can guarantee 100 percent security. Remaining risks include unreviewed Git history and deployed files, unknown live Supabase policies until you apply and test the SQL, the public nature of a static site, third-party Turnstile availability, and the lack of custom response headers on direct GitHub Pages.
