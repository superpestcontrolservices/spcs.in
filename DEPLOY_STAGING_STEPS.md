# Staging deployment and enquiry verification

Do not run these steps against the production Supabase project. Use a separate staging project and a staging copy of the site.

1. In `data/site-claims.json`, enter only owner-approved experience/certification wording and set `reviewsVerified` to the appropriate reviewed value. In `js/security-config.mjs`, enter the staging Supabase URL, public publishable key, and Turnstile site key. Never place a service key or Turnstile secret in browser code.
2. In the staging Supabase dashboard, open **Project Settings → Edge Functions → Secrets**. Set `SUPABASE_SERVICE_ROLE_KEY`, `TURNSTILE_SECRET_KEY`, a randomly generated `RATE_LIMIT_HMAC_SECRET`, `RESEND_API_KEY`, `ENQUIRY_NOTIFICATION_FROM` (a verified Resend sender), and `ENQUIRY_NOTIFICATION_TO` there. Set `ALLOWED_ORIGINS` to the exact staging origin and `ALLOWED_TURNSTILE_HOSTS` to its hostname (without a scheme). Do not put secret values in the repository or print them in logs.
3. Review `supabase/enquiry_setup.sql` line by line. Confirm the staging project and that `public.enquiries` has the expected columns, then run this limited setup in that staging project's **SQL Editor**. It changes access only for the enquiry and rate-limit tables. Do not run it against production as part of this checklist.
4. From the project root, link the Supabase CLI to the staging project and deploy only the submit function:

   ```powershell
   supabase link --project-ref YOUR_STAGING_PROJECT_REF
   supabase functions deploy submit-enquiry
   ```

5. Set `SUPABASE_URL`, `SUPABASE_ANON_KEY` (the staging public publishable key only), `SUPABASE_TABLES`, `RLS_PROBE_FILTERS_JSON`, and `RLS_TEST_CONFIRM=staging-only` in the environment expected by `tests/rls_check.mjs`. Use verified-absent equality filters for the tables being probed, then run:

   ```powershell
   node tests/rls_check.mjs
   ```

   Do not supply a service-role key to this test. Confirm the script rejects public read, update, and delete access.
6. Build and publish a staging copy through GitHub Pages/Jekyll. Keep `.nojekyll` absent so `_config.yml` exclusions are applied; inspect the generated artifact and confirm it contains none of `data/`, `tools/`, `scripts/`, `tests/`, `supabase/`, SQL files, CSV reports, or internal Markdown reports. Submit one valid enquiry, one invalid enquiry, and one oversized enquiry. Confirm only the valid enquiry is stored, its email notification reaches the configured inbox, and the browser receives no enquiry row or technical error details.
7. Using an anonymous staging request, confirm enquiries cannot be read, updated, or deleted. Check both the REST API and any relevant RPC/storage paths; do not use an owner token for this check.
8. Sign in through the authorized owner workflow and confirm the owner can read the valid staging enquiry. Verify no anonymous response reveals row data or technical errors.
9. Run `node scripts/predeploy-check.mjs --publish-dir _site` against the exact generated directory intended for publication. Resolve every error before release.
10. Keep staging records separate from real customer data. Remove test records only through the staging project's normal owner-approved process.
