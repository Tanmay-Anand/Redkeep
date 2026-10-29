# Rules of Engagement (RoE)

Redkeep performs **authorised** security testing of your own stack. These rules
are binding on anyone running the tooling in this repo.

## 1. Authorisation

- Testing is permitted **only** against the disposable target brought up by
  [`lab/docker-compose.yml`](../lab/docker-compose.yml) on the private lab
  network.
- Running Redkeep against any system you do not own and are not explicitly
  authorised to test is prohibited.

## 2. Authorised targets

- The authorised target set is the lab network CIDR(s) and hostnames listed
  under `lab.allowed_cidrs` / `lab.allowed_hosts` in `config.yaml`.
- The runner enforces this in code: see
  [`runner/vapt/targets.py`](../runner/vapt/targets.py). A target that does not
  resolve into an allowed CIDR is refused **before** any tool is launched.

## 3. Prohibited targets

- **Production** and **staging** environments are never valid targets, even
  read-only. Do not add their addresses to `config.yaml`.
- No scanning of third-party or shared infrastructure (payment providers,
  identity providers, SaaS dependencies), even if the lab target talks to them.

## 4. Permitted activities

- Network discovery and service/version enumeration (Nmap, Metasploit
  **auxiliary/scanner** modules only).
- Web-application scanning (OWASP ZAP, nuclei, nikto).
- API testing (schemathesis spec fuzzing, ZAP API scan, authenticated Newman
  flows) with **test** credentials only.

## 5. Prohibited activities

- No destructive exploitation, no denial-of-service, no data exfiltration
  beyond what is needed to demonstrate a finding.
- No use of real user credentials, real payment instruments, or real
  government/financial identifiers. Test accounts and seed data only.
- No active Metasploit **exploit** modules against the target without an
  explicit, separately recorded decision in the engagement notes.

## 6. Data handling

- The target database is seeded with throwaway data and reset between runs
  (see [`lab/target/reset.sh`](../lab/target/reset.sh)).
- Scan output and reports under `reports/output/` are gitignored and must not
  be committed or shared outside the authorised team.

## 7. Stop conditions

- Stop immediately and reset the lab if the target becomes unstable, if real
  data is discovered in the target, or if any traffic is observed leaving the
  lab network.
