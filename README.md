<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="resources/redkeep-logo/png/transparent/redkeep-lockup-light-1200w.png">
    <img alt="Redkeep" width="380" src="resources/redkeep-logo/png/transparent/redkeep-lockup-dark-1200w.png">
  </picture>
</p>

<p align="center"><em>Redkeep: a self-hosted VAPT workbench for pentesting your own stack in an isolated lab</em></p>

Redkeep is a standalone vulnerability-assessment & penetration-testing (VAPT)
workbench. It brings up a **disposable, isolated copy** of a target application
on a private Docker network and runs network, web-application, and API security
tests against it, centralising every finding in [DefectDojo](https://www.defectdojo.org/)
and exporting industry-standard reports (OWASP, PTES, NIST SP 800-115, CVSS).

It is designed to test **your own stack** under explicit authorisation. See
[`docs/rules-of-engagement.md`](docs/rules-of-engagement.md) and
[`docs/scope.md`](docs/scope.md) before running anything.

## Why "isolated lab"

Redkeep **never** points active scanners or exploit modules at production or
staging. The only authorised targets are services on the private lab network
defined in [`lab/docker-compose.yml`](lab/docker-compose.yml). This is enforced
in code by the target allowlist gate in
[`runner/vapt/targets.py`](runner/vapt/targets.py): any target outside the
configured lab network is refused before a single packet is sent.

## Components

| Path       | What it is                                                              |
|------------|-------------------------------------------------------------------------|
| `lab/`     | Isolated environment: a throwaway copy of the target + a Kali toolbox.  |
| `hub/`     | DefectDojo — the findings & reporting hub, plus its bootstrap config.   |
| `runner/`  | The `vapt` CLI that drives the tools and ingests results into the hub.  |
| `ui/`      | The launcher UI — a dependency-free local control panel (`start-redkeep`). |
| `reports/` | Report templates and generated output (output is gitignored).           |
| `docs/`    | Scope, rules of engagement, methodology, and the engagement runbook.    |

## Quick start

### Easiest — the launcher UI

```bash
cp config.example.yaml config.yaml          # lab network + targets
cp lab/.env.example lab/.env                 # CRM build-context paths + throwaway DB creds
cp lab/target/.env.example lab/target/.env   # runtime env for the CRM services
./start-redkeep.sh                           # or double-click start-redkeep.bat on Windows
```

This opens a local control panel in your browser (127.0.0.1 only) where you can
start the lab, run scans, and open reports. It drives the same safety-gated
runner underneath, and nothing idles in the background once you close it.

### Or from the command line

```bash
make lab-up                   # start the isolated target (no scanners idling)
make scan PROFILE=quick       # run a quick pass + build the offline report
make report                   # rebuild the latest report
make lab-down                 # stop the target
# optional heavy hub for cross-run tracking:
make hub-up && make bootstrap
```

Full walkthrough: [`docs/running-an-engagement.md`](docs/running-an-engagement.md).

## Scope of this repo

- **In scope:** network, web-application, and API testing of the lab target.
- **Out of scope (deferred):** mobile application testing. A mobile module
  (MobSF / Frida) may be added later; it is intentionally **not** built here.

## Tooling

Automated passes are driven by **OWASP ZAP** (Burp Community cannot be scripted;
use it manually from the Kali toolbox for deep-dives). Network testing uses
**Nmap** and **Metasploit** (auxiliary/scanner modules only). API testing adds
**schemathesis** (spec-driven fuzzing) and **Newman** (authenticated flows).
