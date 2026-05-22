.PHONY: dev lint test generate-api test-e2e test-e2e-ui

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

test-e2e:
	cd tests/e2e && npm install --silent && npx playwright install chromium --with-deps && npx playwright test

test-e2e-ui:
	cd tests/e2e && npx playwright test --ui
