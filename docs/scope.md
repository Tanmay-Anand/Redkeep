# Scope

## Target

A disposable, isolated copy of the **full example-app service set**, brought up
on the private lab network by [`lab/docker-compose.yml`](../lab/docker-compose.yml):

| Service            | Lab hostname          | Notes                                  |
|--------------------|-----------------------|----------------------------------------|
| API                | `target-api`          | Core REST API                          |
| Platform           | `target-platform`     | Platform service                       |
| Admin              | `target-admin`        | Admin API                              |
| Reports            | `target-reports`      | Reporting API                          |
| UI                 | `target-ui`           | Web front-end                          |
| Database           | `target-db`           | Seeded with throwaway data (not a scan target by default) |

## Testing domains (in scope)

1. **Network** — host discovery, port/service/version enumeration, NSE checks.
2. **Web application** — OWASP WSTG-aligned scanning of the UI and web surfaces.
3. **API security** — OWASP API Security Top 10, spec-driven fuzzing, authn/authz.

## Out of scope

- **Mobile application testing** — deferred. The mobile app exists but is
  intentionally excluded from this engagement. A MobSF/Frida module may be added
  later as a separate component.
- Source-code review and dependency/SCA scanning (can be added later as a module).
- Social engineering and physical security.
- Any production or staging system.

## Standards applied

- OWASP Web Security Testing Guide (WSTG)
- OWASP API Security Top 10
- OWASP Application Security Verification Standard (ASVS)
- PTES (Penetration Testing Execution Standard)
- NIST SP 800-115
- CVSS v3.1 for severity scoring
