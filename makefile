up:
	docker-compose up --build

down:
	docker-compose down -v

logs:
	docker-compose logs -f api

migrate:
	docker-compose run --rm alembic upgrade head

revision:
	docker-compose run --rm alembic revision --autogenerate -m "new migration"

ps:
	docker-compose ps

shell:
	docker-compose exec api bash

test:
	docker-compose run --rm api pytest -v
