.PHONY: dev lint test generate-api

dev:
	docker compose up

lint:
	cd apps/backend && ruff check app tests && mypy app
	@if [ -f apps/frontend/package.json ]; then cd apps/frontend && npm run lint; fi

test:
	cd apps/backend && python -m unittest discover -s tests -t ../..

generate-api:
	curl -fsS http://localhost:8000/openapi.json -o api-contract/openapi.json
	@if [ -f apps/frontend/package.json ]; then cd apps/frontend && npm run generate-api; fi
