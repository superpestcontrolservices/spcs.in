# Manual Containment Checklist

Follow these steps in order. Do not paste credentials into tickets, chat, source files, or public issue trackers. The Phase 1 audit found a browser-visible Supabase publishable key (prefix only: `sb_pub`) in [js/script.min.js](./js/script.min.js); it did not identify a service-role key or third-party API credential in the available workspace. Git history and deployed files were unavailable, so this is not proof that no other credentials were exposed.

## 1. Secure accounts and rotate credentials

1. Use a trusted, updated device and a password manager. Change the account password for each service below to a unique password, then enable two-factor authentication (2FA) and save recovery codes offline:
   - **Supabase:** sign in to the Supabase dashboard, open your account/profile settings, then Password/Security and enable 2FA.
   - **GitHub:** profile menu → **Settings** → **Password and authentication** → enable 2FA.
   - **Hosting provider:** open the provider’s account/team security settings and enable 2FA. The workspace suggests a static/Jekyll site, but does not establish the host; identify it from your hosting account and billing records.
   - **Domain registrar:** open account security settings and enable 2FA; confirm domain lock and auto-renewal.
   - **Email provider:** secure the mailbox used for password resets first; enable 2FA and review recovery addresses, forwarding rules, filters, and active sessions.
   - **Google accounts:** visit Google Account → **Security** → enable 2-Step Verification; review recent activity and signed-in devices.
   - **Cloudflare, if used:** account profile → **Authentication**; enable 2FA and review active sessions.
2. **Supabase project API key:** in the Supabase dashboard, select the project → **Project Settings** → **API Keys** (or the current API/key-management screen). Identify the publishable key used by the website by matching it locally; the audit reports only its `sb_pub` prefix and does not reproduce the value.
   - Create/rotate the publishable key using the dashboard’s supported key-management flow. Check Supabase’s current key-rotation guidance first so the old key is not revoked before all active deployments are updated.
   - After verifying the replacement works, revoke the old publishable key if the dashboard permits. Update the website’s existing key reference in [js/script.min.js](./js/script.min.js) and any hosting build/environment setting that you find. Phase 3 is intended to move browser configuration into one config file; do not place a service-role/secret key there.
   - No third-party API key was identified in the available working tree. If your full-history scan, provider dashboards, or deployed files reveal any other key/token, rotate it at its issuer and update every legitimate consumer before revoking the old value.
3. In Supabase, **Project Settings → API Keys**, verify that no service-role/secret key has ever been placed in website files, committed to Git, or configured as a public frontend variable. A service-role key must be treated as compromised if it may have been exposed; rotate it from the dashboard and update only trusted server-side/function secrets. Never add it to this static site.
4. Review and revoke unknown sessions, recovery methods, OAuth grants, app passwords, personal access tokens, and backup codes for all accounts above.

## 2. Inspect the Supabase project

1. Select the correct project in the Supabase dashboard and confirm its project reference/URL against the website configuration.
2. Open **Authentication → Users**. Compare each user with your own records. Investigate unknown users and delete only accounts you have verified are unauthorized; preserve legitimate users and data.
3. Open **Logs** (including API, Auth, and database/Postgres logs where available). Review the period before and after the suspected compromise for unfamiliar IPs, unusual query volume, repeated failures, schema changes, and unexpected data access. Export evidence before making changes.
4. Open **Table Editor** and inspect table definitions and recent/modified records for unexpected tables, columns, policies, and added, changed, or missing rows. Do not delete rows or tables as a containment shortcut. Preserve an export first and investigate differences.
5. Open **Storage** and inspect every bucket, access setting, policy, and recent object change. Make buckets private by default unless public access is explicitly required for non-sensitive assets.
6. Open **Edge Functions** and inspect deployed functions, source, secrets, logs, and deployment times. Investigate unknown functions or unexpected changes before disabling anything that may support a legitimate service.
7. Review database **Roles**, grants, RLS status, and policies for every table. For the `enquiries` table, specifically verify that anonymous/public users cannot select, update, or delete customer rows, and that public inserts cannot set privileged fields. Do not assume the website’s publishable key provides data confidentiality.
8. Open **Authentication → Settings** and disable public sign-ups if new users do not need to self-register. Check whether changing this setting affects any legitimate application before saving.
9. Check the Supabase **Security Advisor** and record its findings. Do not run SQL from an unreviewed source or make destructive database changes during investigation.

## 3. Inspect GitHub access and automation

1. In the organization/repository settings, review **Collaborators and teams**, outside collaborators, deploy keys, GitHub Apps, OAuth authorizations, personal access tokens, webhooks, and repository secrets. Remove or rotate only access you have confirmed is unauthorized; preserve evidence first.
2. Review **Actions → workflows/runs** and repository workflow files for unexpected jobs, deployment destinations, or secret access. Review recent deployments and commit authors with your team.
3. Enable **Settings → Code security and analysis → Secret scanning** and **push protection** if available for your plan. Enable **Dependabot alerts** and security updates.
4. Protect the default branch (normally `main`) under **Settings → Branches / Rulesets**: require pull requests, require appropriate checks/reviews, and disallow force pushes and deletion.
5. This workspace was not available as a Git repository, so no branch or GitHub configuration was changed. Perform these checks in the actual repository and run a full-history scan across all branches. If secrets are found in history, rotate them first; history rewriting requires a coordinated team plan and is not performed by this checklist.

## 4. Inspect hosting and deployment

1. Identify the hosting provider from the domain’s DNS records and your hosting account. The workspace contains a `CNAME` and `_config.yml`, which suggest a static custom-domain/Jekyll-style deployment but do not identify the production provider conclusively.
2. In the hosting dashboard, review **team members**, access roles, deploy hooks, connected GitHub apps, environment variables, build commands, domains, and recent deploys. Revoke unknown access and rotate any exposed deployment credentials.
3. Verify that public build variables contain only intended public values. Remove service-role keys, passwords, tokens, and other secrets from browser-visible variables; put necessary server credentials only in the hosting provider’s protected server-side/function secret store.
4. Compare the latest deployed file list with the intended build output. Investigate unexpected scripts, archives, backups, source maps, `.env` files, debug files, or Git metadata before removing anything; preserve a forensic copy first.
5. Confirm HTTPS redirection and inspect the deployed response headers after recovery. Production headers and the deployed folder could not be checked during Phase 1.

## 5. Check Google Search Console

1. Open Google Search Console and select the verified `superpest.in` property.
2. Check **Security issues** and **Manual actions**. Save screenshots/details of any warning and inspect affected URLs.
3. Remove confirmed malicious content through the trusted deployment process, verify the clean live pages, then use **Request a review** for any Security issue or Manual action that Google flagged. Do not request review until the underlying issue has been fixed.

## 6. Preserve backups and evidence

1. Before database or hosting changes, export Supabase data using the dashboard’s supported export/backup process and retain an offline copy in an access-controlled location. Verify that the export can be opened and that the backup includes the data and schema you need. Do not delete or drop tables.
2. Make an offline copy of the actual Git repository, including refs/history and relevant deployment configuration. Keep it encrypted and limit access; do not publish it or upload it to an unapproved service.
3. Record timestamps, affected accounts, key identifiers (never full key values in the report), suspicious requests, and actions taken. Preserve logs and the original compromised files for investigation.

## 7. Assess possible personal-data exposure

If customer enquiry information may have been accessed or disclosed, promptly consult an Indian privacy lawyer and a qualified incident-response/security professional. Ask them to assess applicable obligations under the **Digital Personal Data Protection Act, 2023**, its applicable rules/commencement provisions, and **CERT-In directions** (including any applicable incident-reporting timelines and log-retention requirements). Preserve evidence and do not delay seeking advice while determining the scope. This checklist is not legal advice.

## Phase 1 limitation

The audit report is in [SECURITY_AUDIT.md](./SECURITY_AUDIT.md). It found no confirmed service-role/secret key in available source text, but could not inspect all Git history, the deployed folder, the live Supabase project, or hosting account settings. Treat the corresponding checks above as outstanding until completed.
