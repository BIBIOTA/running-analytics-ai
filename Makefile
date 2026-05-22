.PHONY: dev lint test generate-api

dev:
	docker compose up

lint:
	cd apps/backend && ruff check app tests && ruff format --check app tests && mypy app
	@if [ -f apps/frontend/package.json ]; then cd apps/frontend && npm run lint; fi

test:
	cd apps/backend && pytest

generate-api:
	curl -fsS http://localhost:8000/openapi.json -o api-contract/openapi.json
	@if [ -f apps/frontend/package.json ]; then cd apps/frontend && npm run generate-api; fi
