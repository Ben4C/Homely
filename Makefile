SHELL := /bin/bash
.PHONY: help api web test check
help:
	@echo "API: make api | Web: make web | API tests: make test | Checks: make check"
api:
	cd apps/api && python -m uvicorn app.main:app --reload --port 8000
web:
	cd apps/web && npm run dev
test:
	cd apps/api && python -m pytest -q
check:
	cd apps/api && python -m pytest -q
	cd apps/web && npm run typecheck
