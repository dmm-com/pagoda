# Webhook destinations

Webhook verification and entry notifications use the same outbound transport.
HTTP and HTTPS endpoints are supported, with the following restrictions:

- Every address returned by DNS must be a public, globally routable address.
  Private, loopback, link-local, shared, reserved, multicast, and IPv6 transition
  addresses are rejected. The transport checks existing verified webhooks again
  for every notification, so changing DNS cannot bypass this policy.
- Connections use the checked numeric address. The HTTP Host header and HTTPS
  SNI and certificate hostname remain those of the original URL.
- HTTPS requires a trusted, unexpired certificate matching the endpoint hostname,
  using the default Requests CA bundle. Self-signed certificates are rejected.
- Redirects are rejected. Register the final endpoint URL directly.
- URL credentials and caller-supplied routing or transport headers (including
  Host, Content-Length, and Transfer-Encoding) are rejected. Authentication
  headers such as Authorization and application headers remain supported.
- Environment proxies and implicit netrc credentials are not used.

Connections have a five-second connect timeout and a ten-second read timeout.
DNS resolution uses the system resolver. If a connection cannot be established,
the transport can try another already-checked public address. It does not retry
POST requests after TLS or response failures, and closes responses without
downloading their bodies.

Registration keeps an unreachable or rejected endpoint unverified and records
the verification error. A transport failure marks the notification job as failed
after the other eligible endpoints have been attempted. Existing endpoints using internal addresses, self-signed
certificates, redirects, or custom routing headers must be updated to satisfy
these restrictions.
