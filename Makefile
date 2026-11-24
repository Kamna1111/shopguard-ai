.PHONY: help setup-python lint format-check test project-test api api-test api-component-test ai-eval ai-security-test perf-test perf-smoke db-migrate db-seed web-install web web-build ui-test ui-test-chromium ui-report ui-browsers quality-report docker-up docker-down docker-logs docker-build

help:
	@echo "ShopGuard AI commands:"
	@echo "  make setup-python  Create .venv and install Python development tools"
	@echo "  make lint          Check Python formatting and common errors"
	@echo "  make format-check  Check formatting without changing files"
	@echo "  make test          Run repository setup checks"
	@echo "  make project-test  Run project, AI evaluation, and dashboard unit checks"
	@echo "  make api           Start the local API server"
	@echo "  make api-test      Run HTTP API automation (API server must be running)"
	@echo "  make api-component-test Run API component tests"
	@echo "  make ai-eval       Evaluate support answers against the golden question set"
	@echo "  make ai-security-test Check AI prompt-injection and unsafe-output protections"
	@echo "  make perf-test     Run a small k6 API load check (API server must be running)"
	@echo "  make perf-smoke    Run a 1-user, 10-second k6 smoke check"
	@echo "  make db-migrate    Apply database changes"
	@echo "  make db-seed       Add demo products"
	@echo "  make web-install   Install storefront and Playwright packages"
	@echo "  make web           Start the customer storefront"
	@echo "  make web-build     Check and build the storefront"
	@echo "  make ui-test       Run browser tests in Chromium, Firefox and WebKit"
	@echo "  make ui-test-chromium Run browser tests in Chromium"
	@echo "  make ui-browsers   Install Playwright browser engines"
	@echo "  make quality-report Build a combined Markdown quality report"
	@echo "  make docker-up     Build and start the shop, API, and database in Docker"
	@echo "  make docker-down   Stop the Docker services (keeps database data)"
	@echo "  make docker-logs   Follow Docker service logs"
	@echo "  make docker-build  Build the Docker images without starting services"

setup-python:
	python3.15 -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements-dev.txt

lint:
	.venv/bin/ruff check .

format-check:
	.venv/bin/ruff format --check .

test:
	.venv/bin/python -m pytest

project-test:
	.venv/bin/python automation/reporting/run_pytest_suite.py project-tests tests automation/ai/tests/test_evaluation.py automation/dashboard/tests

api:
	PYTHONPATH=apps/api .venv/bin/uvicorn app.main:app --reload

api-test:
	.venv/bin/python automation/reporting/run_pytest_suite.py api automation/api/tests -v --log-cli-level=INFO

api-component-test:
	.venv/bin/python automation/reporting/run_pytest_suite.py api-components apps/api/tests -v

ai-eval:
	AI_PROVIDER=mock .venv/bin/python automation/ai/evaluate_rag.py

ai-security-test:
	.venv/bin/python automation/reporting/run_pytest_suite.py ai-security automation/ai/tests/test_security.py -v

perf-test:
	mkdir -p outputs/test-results
	k6 run automation/performance/shop-read-load.js

perf-smoke:
	mkdir -p outputs/test-results
	SHOPGUARD_LOAD_VUS=1 SHOPGUARD_LOAD_DURATION=10s SHOPGUARD_LOAD_PAUSE_SECONDS=1 k6 run automation/performance/shop-read-load.js

db-migrate:
	.venv/bin/alembic -c apps/api/alembic.ini upgrade head

db-seed:
	PYTHONPATH=apps/api .venv/bin/python -m app.seed

web-install:
	cd apps/web && npm install

web:
	cd apps/web && npm run dev

web-build:
	cd apps/web && npm run build

ui-browsers:
	cd apps/web && npx playwright install chromium firefox webkit

ui-test:
	cd apps/web && npm run test:e2e; status=$$?; cd ../.. && .venv/bin/python automation/reporting/normalize_junit.py browser outputs/test-results/browser-junit.xml; report_status=$$?; if [ $$status -ne 0 ]; then exit $$status; else exit $$report_status; fi

ui-test-chromium:
	cd apps/web && npm run test:e2e:chromium; status=$$?; cd ../.. && .venv/bin/python automation/reporting/normalize_junit.py browser outputs/test-results/browser-junit.xml; report_status=$$?; if [ $$status -ne 0 ]; then exit $$status; else exit $$report_status; fi

ui-report:
	cd apps/web && npm run report

quality-report:
	PYTHONPATH=apps/api .venv/bin/python automation/reporting/build_quality_report.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build
