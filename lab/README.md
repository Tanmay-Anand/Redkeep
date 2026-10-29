# Lab — the isolated environment

This brings up a **disposable copy of the full example-app service set** plus a
**Kali toolbox**, all on the private `redkeep-lab` bridge network
(`172.30.0.0/24`). Target services publish **no host ports** — they are only
reachable from inside the lab network, which is the isolation boundary.

## Setup

```bash
cp .env.example .env                       # TARGET_*_PATH build contexts + throwaway DB creds (parse-time)
cp target/.env.example target/.env         # runtime env passed into the target services
docker compose build                       # build the target services + Kali toolbox
docker compose up -d                       # start the lab
```

The `TARGET_*_PATH` values are Docker **build contexts** pointing at the real
target-app repos. Redkeep only reads them to build images; it never writes to
those repos.

## Running tools

The runner lives inside the Kali toolbox (the repo is mounted at `/redkeep`):

```bash
docker compose exec kali vapt network --profile full
docker compose exec kali vapt web
docker compose exec kali vapt api
```

From inside Kali, DefectDojo is reached at `http://host.docker.internal:8081`
(set `defectdojo.url` in `config.yaml` accordingly when running in-container).

## Reset between runs

```bash
./target/reset.sh      # drops + re-seeds the target DB, recreates services
```

## Tear down

```bash
docker compose down            # stop + remove containers (keeps DB volume)
docker compose down -v         # also remove the DB volume
```

## Isolation notes

- Target services have no published ports; only Kali shares their network.
- Set `INTEGRATIONS_ENABLED=false` (and equivalents) in `target/.env` so the
  target makes no outbound calls to payment/SMS/email/webhook providers.
- Never add a production or staging address anywhere in this lab.
