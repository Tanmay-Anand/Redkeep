# runner — the `vapt` CLI

The orchestration layer. It drives the external tools, enforces the target
allowlist, and ingests/reports results.

## Module map

| Module         | Responsibility                                                     |
|----------------|--------------------------------------------------------------------|
| `cli.py`       | Argument parsing + dispatch (`network`/`web`/`api`/`run`/`report`). |
| `config.py`    | Loads `config.yaml`, resolves run directories.                     |
| `targets.py`   | **Safety gate** — refuses any target outside the lab network.      |
| `profiles.py`  | Loads scan profiles from `profiles/*.yaml`.                        |
| `network.py`   | Nmap + optional Metasploit auxiliary scanners.                     |
| `web.py`       | OWASP ZAP (automation framework), nuclei, nikto.                   |
| `api.py`       | schemathesis, ZAP API scan, optional Newman.                       |
| `auth.py`      | Builds auth headers/cookies from `config.yaml -> auth` (Phase 4).  |
| `ingest.py`    | Optional DefectDojo ingestion (off unless `defectdojo.enabled`).   |
| `report.py`    | Offline HTML report from raw tool output.                          |
| `util.py`      | Logging + subprocess helpers.                                      |

## The safety gate

Every pass calls `targets.assert_allowed()` before launching a tool. A target is
allowed only if it is in `lab.allowed_hosts` or resolves into a
`lab.allowed_cidrs` network; a CIDR target must sit inside an allowed CIDR.
Anything else raises `TargetNotAllowed` and the run aborts with exit code 3
before any packet is sent. This is what keeps scans off production/staging.

## Running

Inside the Kali toolbox (where all the tools live):

```bash
vapt run --profile full        # all passes
vapt web --report              # one domain + offline report
vapt report                    # rebuild report for the latest run
```

On the host for development (tools not required for `--help` / unit use):

```bash
pip install ./runner
vapt --help
```

## Exit codes

| Code | Meaning                              |
|------|--------------------------------------|
| 0    | OK                                   |
| 2    | config not found                     |
| 3    | target refused by the safety gate    |
| 130  | interrupted                          |
