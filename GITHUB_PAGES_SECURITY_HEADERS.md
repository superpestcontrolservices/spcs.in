# Security headers on direct GitHub Pages

The project files (`CNAME`, `_config.yml`, and `.nojekyll`) indicate GitHub Pages, and the owner confirmed this domain is served directly without a Cloudflare proxy. GitHub Pages does not provide a repository configuration file for arbitrary HTTP response headers. An `_headers`, `netlify.toml`, `vercel.json`, or `.htaccess` file would not configure headers on this deployment, so none is added.

In particular, do not use a CSP `<meta>` tag as a substitute: it cannot set `Content-Security-Policy-Report-Only`, HSTS, or `frame-ancestors`.

## Current source review

- The static source scan found no non-schema `http://` resource URLs. This does not verify the live site or redirects.
- The site currently has inline scripts across many pages. A report-only policy must allow them while observing breakages; do not switch this policy to enforcing without removing/allowlisting inline scripts safely.
- The form uses Supabase Edge Functions and Cloudflare Turnstile. The relevant browser origins are the configured Supabase project and `https://challenges.cloudflare.com`. No Google Fonts, Google Maps embeds, analytics, or other third-party script was identified in the available HTML/CSS.

## Required deployment choice

To serve custom headers, either put a supported reverse proxy/CDN in front of GitHub Pages or move the site to a host that supports response headers. If you later place Cloudflare in front, configure a **Response Header Transform Rule** for all site paths and start with:

```text
Content-Security-Policy-Report-Only: default-src 'self'; script-src 'self' 'unsafe-inline' https://challenges.cloudflare.com; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://challenges.cloudflare.com; font-src 'self' data:; connect-src 'self' https://yrxymyoegbxjssrcvjwr.supabase.co https://challenges.cloudflare.com; frame-src https://challenges.cloudflare.com; object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'
Strict-Transport-Security: max-age=31536000
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()
```

Before enforcing CSP, review browser console/report data for at least one complete release cycle. Remove inline scripts or replace them with reviewed hashes/nonces before removing `'unsafe-inline'`. Retain only origins that the site actually needs. Do not add `includeSubDomains` to HSTS until every subdomain is confirmed HTTPS-capable.

## GitHub Pages HTTPS and contact

In the repository’s GitHub Pages settings, verify the custom domain, enable **Enforce HTTPS**, and wait for the certificate status to be healthy. GitHub Pages manages that redirect setting; this repository cannot prove it is enabled.

The existing [`.well-known/security.txt`](./.well-known/security.txt) contains a contact email and URL and does not need a placeholder replacement. Once deployed, request the security headers with `curl -I https://superpest.in/` and record which required headers the actual response is missing. No live request was made for this audit.
