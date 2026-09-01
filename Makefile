# RecoverAI Monorepo Makefile

.PHONY: up down logs test integration-test simulation smoke diagnostics release-smoke clean help

help:
	@echo "RecoverAI Developer & Operations Commands:"
	@echo "  make up               - Build and start all Docker services"
	@echo "  make down             - Stop and remove all Docker containers"
	@echo "  make logs             - View live logs from Docker stack"
	@echo "  make test             - Run unit test suite (Phases 1-14)"
	@echo "  make integration-test - Run Phase 12-14 E2E integration test suite"
	@echo "  make simulation       - Run Phase 10 500-case recovery simulation engine"
	@echo "  make smoke            - Run Phase 12 system health & integration smoke test"
	@echo "  make diagnostics      - Run Phase 13 full system integration diagnostics"
	@echo "  make release-smoke    - Run Phase 14 release candidate smoke test"

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	python -m pytest tests/unit/ -v

integration-test:
	python -m pytest tests/integration/ -v

simulation:
	python -m backend.app.simulation.run_simulation

smoke:
	python -m scripts.smoke_test

diagnostics:
	python -m scripts.diagnostics

release-smoke:
	python -m scripts.release_smoke_test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
