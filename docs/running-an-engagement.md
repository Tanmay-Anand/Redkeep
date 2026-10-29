# Running an engagement

End-to-end walkthrough. Everything runs against the **isolated lab** only.

## 0. One-time setup

```bash
cp config.example.yaml config.yaml           # set lab network, targets, (optional) DefectDojo
cp lab/.env.example lab/.env                  # CRM_*_PATH build contexts + throwaway DB creds
cp lab/target/.env.example lab/target/.env    # runtime env for the CRM services
```

Review [`docs/scope.md`](scope.md) and [`docs/rules-of-engagement.md`](rules-of-engagement.md).

## 1. Build + start the isolated target

```bash
make lab-build        # or: ./redkeep.ps1 lab-build
make lab-up           # or: ./redkeep.ps1 lab-up
```

Only the CRM target services start. The Kali toolbox does **not** start here —
it runs on demand and exits after each command.

## Easiest path — the launcher UI

Instead of the commands below, you can run everything from a browser:

```bash
./start-redkeep.sh        # or double-click start-redkeep.bat on Windows
```

This opens a local control panel (127.0.0.1 only) with buttons to start/stop the
lab, run a scan (pick scope + profile), and open reports. The command-line steps
below do the same thing and are what the UI calls under the hood.

## 2. Run the passes

```bash
make scan PROFILE=quick      # smoke pass (fast, passive)
make scan PROFILE=full       # full engagement (active scans, all tools)

# or a single domain:
make network
make web
make api
```

Each run writes raw tool output to a timestamped folder under
`reports/output/` and builds `report.html` there.

## 3. Review findings

- **Offline (default):** open the `report.html` in the latest
  `reports/output/<timestamp>-*/` folder.
- **Rebuild the report** any time: `make report`.

## 4. (Optional) DefectDojo for cross-run tracking

Only if you want historical tracking/triage across runs:

```bash
make hub-up                                  # starts DefectDojo (heavy)
# get an API token from http://localhost:8081, put it in config.yaml,
# set defectdojo.enabled: true and url: http://host.docker.internal:8081
make bootstrap                               # create product + engagement
make scan PROFILE=full                       # now also ingests into DefectDojo
make hub-down                                # stop it when done
```

## 5. Reset between runs

```bash
make lab-reset        # drop + re-seed the target DB
```

## 6. Shut everything down

```bash
make lab-down         # stop the target
make down-all         # stop target + hub
```

---

## Resource use & gaming

Redkeep is built so it never quietly eats your laptop's resources:

- The **Kali toolbox is ephemeral** — it runs one command (`run --rm`) then
  exits. It never idles in the background and has **no restart policy**, so it
  won't come back after a reboot or a Docker restart.
- **DefectDojo is off by default.** The heavy hub only runs when you explicitly
  `make hub-up`, and you can run full assessments with just the lab up.
- The CRM **target** services only run while you want them; stop them with
  `make lab-down`.

Before launching a game, free everything in one shot:

```powershell
./redkeep.ps1 gaming-safe
```

This stops all Redkeep containers **and** runs `wsl --shutdown`, which releases
the RAM Docker Desktop's WSL2 backend holds. Quit Docker Desktop too if you want
it completely idle. (`make gaming-safe` does the stop and reminds you to run
`wsl --shutdown`.)
