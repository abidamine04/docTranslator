.PHONY: dev test

dev:
	docker compose up --build

test:
	docker compose run --rm api pytest
	docker compose run --rm web npm test

