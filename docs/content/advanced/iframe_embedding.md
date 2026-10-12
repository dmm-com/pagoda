---
title: Embedding the UI in an iframe
---

By default, iframe embedding remains disabled. To allow specific parent origins
for `/ui/` and its subpaths, plus `/auth/login` and `/auth/login/`, set a
comma-separated list in `.env`:

```dotenv
AIRONE_IFRAME_ALLOWED_ORIGINS=https://confl.arms.dmm.com,https://wiki.example.com
```

Specify complete HTTP(S) origins, including a port when needed, without paths or
trailing slashes. Wildcards are not supported. Restart Django after changing the
setting. Unset or empty values retain the existing `X-Frame-Options` protection.
Other paths, including logout, SSO, and API routes, retain their existing protection.
The login page is allowed so unauthenticated UI redirects can be displayed.
External SSO providers may still prohibit framing; use a separate tab to log in
in that case.

The UI response receives a CSP `frame-ancestors` policy instead of
`X-Frame-Options`. Existing CSP policies remain enforced and may further restrict
embedding. A reverse proxy must not inject conflicting framing restrictions.
Cross-site session cookies and browser third-party cookie restrictions still
apply. This setting does not change CORS, CSRF, or API permissions.

Allowing `/ui/` also permits embedding editing screens; it does not make the UI
read-only. Only configure trusted parent origins, since their pages could induce
users to perform unintended actions through clickjacking.
