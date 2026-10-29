# Methodology

Redkeep follows a conventional VAPT lifecycle aligned to **PTES** and
**NIST SP 800-115**, mapping web/API findings to OWASP references.

## Phases (PTES-aligned)

1. **Pre-engagement** — scope and rules of engagement
   ([`scope.md`](scope.md), [`rules-of-engagement.md`](rules-of-engagement.md)).
2. **Intelligence gathering / discovery** — network sweep and service
   enumeration (`vapt network`).
3. **Vulnerability analysis** — web and API scanning (`vapt web`, `vapt api`).
4. **Exploitation (bounded)** — manual verification from the Kali toolbox
   (Burp Community, Metasploit aux). Exploit modules only by recorded decision.
5. **Post-exploitation** — out of scope for this workbench.
6. **Reporting** — centralise in DefectDojo, export a standards-mapped report
   (`vapt report`).

## NIST SP 800-115 mapping

| NIST stage            | Redkeep activity                                   |
|-----------------------|----------------------------------------------------|
| Planning              | `docs/` scope + RoE                                |
| Discovery             | `vapt network` (Nmap, msf aux)                     |
| Attack                | `vapt web`, `vapt api` (ZAP, nuclei, schemathesis) |
| Reporting             | DefectDojo ingestion + `vapt report`               |

## Finding classification

Every finding is recorded in DefectDojo with:

- **Severity** — CVSS v3.1 base score (Critical/High/Medium/Low/Info).
- **OWASP reference** — WSTG id for web, API Security Top 10 id for API.
- **ASVS** — relevant verification requirement where applicable.
- **Evidence** — request/response or tool output sufficient to reproduce.
- **Remediation** — concrete, developer-oriented fix guidance.

## Severity → action

| Severity  | Expectation                                      |
|-----------|--------------------------------------------------|
| Critical  | Fix before any release; verify with a re-scan.   |
| High      | Fix in the current cycle.                        |
| Medium    | Scheduled remediation.                            |
| Low/Info  | Backlog / hardening.                              |
