---
title: Installation and Configuration
weight: 10
---

## Production signing key

With `DJANGO_CONFIGURATION=Prd`, Pagoda requires `AIRONE_SECRET_KEY` and
rejects blank values and published defaults. Generate a unique random key with
`django.core.management.utils.get_random_secret_key()`, store it in your
deployment's secret store, and pass it as the `AIRONE_SECRET_KEY` environment
variable.
Use the same value for all web and worker processes in the deployment. For Helm,
set `airone.secretKey` or set `airone.existingSecret` to the name of a Secret
with a `secretKey` entry.

Keep an existing secure key across upgrades. If you previously relied on the
bundled default, configure a new key before upgrading and restart all processes
that use it. Changing the key signs users out and invalidates outstanding
password reset links.
