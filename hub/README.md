# Hub — DefectDojo

DefectDojo is the central findings & reporting hub. It ingests every tool's
native output, de-duplicates, tracks findings across runs, scores with CVSS, and
exports reports.

## Start it

```bash
cd hub
docker compose up -d        # DefectDojo at http://localhost:8081
```

First start takes a few minutes (the `initializer` migrates the DB and creates
the admin user). Default admin credentials come from the compose env
(`DD_ADMIN_USER` / `DD_ADMIN_PASSWORD`) — change them for anything beyond a
throwaway lab.

> This compose mirrors the upstream DefectDojo topology using the published
> images. Upstream (github.com/DefectDojo/django-DefectDojo) is authoritative;
> if it drifts, use upstream's compose and keep the host port `8081` and the
> API token wired into `config.yaml`.

## Get an API token

1. Log in to http://localhost:8081.
2. Go to your user → **API v2 Key**.
3. Put it in `config.yaml` under `defectdojo.api_token`.

## Bootstrap the product + engagement

```bash
python hub/config/bootstrap.py --config config.yaml
```

This creates the `example-app` product and the `redkeep-engagement` engagement
(idempotent). The runner ingests findings into that engagement.
