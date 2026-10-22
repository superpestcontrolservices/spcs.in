# Security verification tests

These tests are not run against your Supabase project by this repository change.

## Local form tests

Run with Node.js 20 or newer from the workspace root:

```powershell
node --experimental-default-type=module --test tests/forms.test.mjs
```

They cover normalized valid input, missing/malformed/oversized data, a submission made too quickly, and a message containing script markup. The browser status is checked via `textContent`; no user message is used to build HTML.

## Supabase RLS tests

Run this only against a disposable staging project after reviewing and applying `supabase/security.sql`. A valid enquiry test inserts a marked test row and does not delete it. Review/remove that test row later through your authorized admin workflow, not with the public key.

1. Run the inventory queries at the end of `supabase/security.sql` to obtain every table in the `public` schema.
2. For each table, choose a primary-key equality filter whose value you have verified does not exist. The enquiry-rate-limit table uses the `ip_hash` primary key; other tables may use UUIDs, integers, or text.
3. In PowerShell, set the staging project URL, **publishable/anon key only**, comma-separated table names, and a JSON map of those safe filters:

   ```powershell
   $env:SUPABASE_URL = "https://YOUR_STAGING_PROJECT.supabase.co"
   $env:SUPABASE_ANON_KEY = "YOUR_STAGING_PUBLISHABLE_OR_ANON_KEY"
   $env:SUPABASE_TABLES = "enquiries,enquiry_rate_limits"
   $env:RLS_PROBE_FILTERS_JSON = '{"enquiries":"id=eq.00000000-0000-0000-0000-000000000000","enquiry_rate_limits":"ip_hash=eq.0000000000000000000000000000000000000000000000000000000000000000"}'
   $env:RLS_TEST_CONFIRM = "staging-only"
   node tests/rls_check.mjs
   ```

   Add every additional public table to both the table list and filter map. Confirm each filter value is absent through an authorized read before running. The script uses only `apikey` with the public key and requests rollback preference for update probes; do not run it if you cannot guarantee that probe filters match no existing row.
4. The script expects public `SELECT`, `UPDATE`, and `DELETE` attempts to return 401/403; a successful response, including an empty result, fails the test. It expects a valid anonymous enquiry insert to succeed and invalid/oversized inserts to fail. It never prints the supplied key or response body.
5. Clear test environment values when finished:

   ```powershell
   Remove-Item Env:SUPABASE_URL, Env:SUPABASE_ANON_KEY, Env:SUPABASE_TABLES, Env:RLS_PROBE_FILTERS_JSON, Env:RLS_TEST_CONFIRM
   ```
