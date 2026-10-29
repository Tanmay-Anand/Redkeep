# Redkeep — convenience targets. Nothing here idles in the background: the Kali
# toolbox runs with `run --rm` (ephemeral) and the optional DefectDojo hub is
# only up when you explicitly start it.

LAB := docker compose -f lab/docker-compose.yml
HUB := docker compose -f hub/docker-compose.yml
PROFILE ?= quick

TARGETS := target-db target-api target-platform target-post-sales target-reports-api target-ui

.PHONY: help lab-build lab-up lab-down lab-reset hub-up hub-down bootstrap \
        scan network web api report shell down-all gaming-safe

help:
	@echo "Redkeep targets:"
	@echo "  make lab-build          build CRM target images + Kali toolbox"
	@echo "  make lab-up             start the isolated target (no scanners idling)"
	@echo "  make lab-down           stop the target"
	@echo "  make lab-reset          drop + re-seed the target DB"
	@echo "  make scan PROFILE=quick run all passes (quick|full|...) + offline report"
	@echo "  make network|web|api    run a single domain pass"
	@echo "  make report             rebuild the offline HTML report (latest run)"
	@echo "  make shell              drop into the Kali toolbox (ephemeral)"
	@echo "  make hub-up|hub-down    start/stop the OPTIONAL DefectDojo hub"
	@echo "  make bootstrap          create the DefectDojo product/engagement"
	@echo "  make down-all           stop everything (lab + hub)"
	@echo "  make gaming-safe        stop everything + remind how to free WSL RAM"

lab-build:
	$(LAB) build

lab-up:
	$(LAB) up -d $(TARGETS)

lab-down:
	$(LAB) down

lab-reset:
	bash lab/target/reset.sh

# Ephemeral toolbox: runs one command then is removed (--rm). Never left running.
scan:
	$(LAB) run --rm kali vapt run --profile $(PROFILE)

network:
	$(LAB) run --rm kali vapt network

web:
	$(LAB) run --rm kali vapt web

api:
	$(LAB) run --rm kali vapt api

report:
	$(LAB) run --rm kali vapt report

shell:
	$(LAB) run --rm kali bash

# Optional heavy hub — only when you want cross-run tracking.
hub-up:
	$(HUB) up -d

hub-down:
	$(HUB) down

bootstrap:
	$(LAB) run --rm kali python3 hub/config/bootstrap.py --config config.yaml

down-all:
	-$(LAB) down
	-$(HUB) down

gaming-safe: down-all
	@echo ""
	@echo "All Redkeep containers stopped. To reclaim RAM from the WSL2 backend"
	@echo "before gaming, run in PowerShell:   wsl --shutdown"
	@echo "and quit Docker Desktop. Or just run:   ./redkeep.ps1 gaming-safe"
