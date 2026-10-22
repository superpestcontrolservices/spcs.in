# Enquiry function deployment

This function is not deployed by this change. Configure and review the project before deploying.

1. In the Supabase dashboard, confirm the intended project and that `public.enquiries` has the expected columns (`name`, `phone`, `email`, `service`, `message`, `status`). Review and run `supabase/enquiry_setup.sql` in that project's SQL Editor. This setup is limited to `public.enquiries`, its owned sequences, and `public.enquiry_rate_limits`; it removes existing policies on those two tables and grants their access only to `service_role`. Do not run the broader `supabase/security.sql` for this form setup.
2. Create a Cloudflare Turnstile widget for `superpest.in` and `www.superpest.in`. Put its **site key** in `js/security-config.mjs`; put its **secret key** in the Supabase Edge Function secret store only.
3. Generate a random secret for `RATE_LIMIT_HMAC_SECRET` and store it only in the Supabase Function secrets. Do not commit secrets or put them in browser configuration.
4. In `js/security-config.mjs`, replace `REPLACE_WITH_ROTATED_SUPABASE_PUBLISHABLE_KEY` with the rotated Supabase publishable key. This public key is sent as the `apikey` header; it is not a service-role key.
5. Configure Resend with a verified sender domain. Store `RESEND_API_KEY`, `ENQUIRY_NOTIFICATION_FROM` (the verified sender address), and `ENQUIRY_NOTIFICATION_TO` (the business inbox) as Supabase Edge Function secrets. The function stores every accepted enquiry in Supabase and emails the notification; if email delivery fails after storage, the form tells the customer to call.
6. Install the Supabase CLI, authenticate, and link to the project:

   ```powershell
   supabase login
   supabase link --project-ref YOUR_PROJECT_REF
   ```

7. Set `TURNSTILE_SECRET_KEY`, `RATE_LIMIT_HMAC_SECRET`, and the Resend values in **Project Settings → Edge Functions → Secrets** (or use the Supabase CLI’s protected secret workflow). Confirm the platform-provided `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are available to the function. Never put service-role or Resend keys in website files.
8. Review `supabase/config.toml`. `verify_jwt = false` is required for this public endpoint because the browser uses a publishable API key, not a user JWT. The function instead checks the site origin, Turnstile response, input validation, and server-side IP rate limit. Keep the service-role key exclusively in function secrets.
9. Deploy only after reviewing the code and completing a staging test:

   ```powershell
   supabase functions deploy submit-enquiry
   ```

10. Test one valid submission and the invalid, oversized, honeypot, Turnstile-failure, rate-limit, and email-provider-failure cases in staging. Confirm the function returns no enquiry row or technical details to the browser and that anonymous clients cannot read or change stored enquiries.
