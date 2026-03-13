.PHONY: help clean flush install build up down logs bash run migrate makemigrations shell showmigrations ps restart createsuperuser initdev

# Capture additional arguments as empty targets
%:
	@:

help:
	@echo "Available commands:"
	@echo "  make clean					- Clean cache and temporary files"
	@echo "  make flush					- Clean all + delete migrations, data and media folders (with confirmation)"
	@echo "  make install					- Install dependencies"
	@echo "  make build					- Build docker image"
	@echo "  make up [args]				- Start docker development server"
	@echo "  make down [args]				- Stop docker development server"
	@echo "  make logs [args]				- View docker logs (e.g., make logs -f backend)"
	@echo "  make bash					- Open bash in docker container"
	@echo "  make run					- Start development server"
	@echo "  make migrate [args]				- Apply migrations"
	@echo "  make makemigrations [args]			- Create new migrations"
	@echo "  make shell					- Open Django shell"
	@echo "  make showmigrations				- Show migrations"
	@echo "  make ps					- Show docker containers"
	@echo "  make restart					- Restart docker containers"
	@echo "  make createsuperuser				- Create a superuser using SUPERUSER_USERNAME and SUPERUSER_PASSWORD env vars"
	@echo "  make initdev					- Initialize development environment with fixtures"

clean:
	@echo "Cleaning cache files..."
	@find . -path "*/__pycache__/*" -delete
	@find . -path "*/__pycache__" -delete
	@find . -path "*/.pytest_cache/*" -delete
	@find . -path "*/.pytest_cache" -delete
	@find . -path "*/.ruff_cache/*" -delete
	@find . -path "*/.ruff_cache" -delete
	@find . -name ".coverage" -delete
	@find . -name ".coverage.*" -delete
	@find api -name ".coverage" -delete 2>/dev/null || true
	@find api -name ".coverage.*" -delete 2>/dev/null || true
	@rm -rf htmlcov 2>/dev/null || true
	@rm -rf api/htmlcov 2>/dev/null || true
	@echo "✓ Cleanup completed"

flush:
	@echo "⚠️  WARNING: This will delete:"
	@echo "   - All cache and temporary files (clean)"
	@echo "   - The 'data' folder"
	@echo "   - The 'api/media' folder"
	@echo ""
	@read -p "Are you sure you want to proceed? (y/n): " confirm && \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		echo ""; \
		$(MAKE) clean; \
		echo "Deleting data folder..."; \
		rm -rf data 2>/dev/null || true; \
		echo "✓ Data folder deleted"; \
		echo "Deleting api/media folder..."; \
		rm -rf api/media 2>/dev/null || true; \
		echo "✓ Media folder deleted"; \
		echo ""; \
		echo "✓ Flush completed successfully"; \
	else \
		echo "Operation cancelled."; \
	fi

install:
	pip install -r requirements.txt

build:
	docker compose build --no-cache

up:
	docker compose up -d $(filter-out $@,$(MAKECMDGOALS))

down:
	docker compose down $(filter-out $@,$(MAKECMDGOALS))

logs:
	docker compose logs -f $(filter-out $@,$(MAKECMDGOALS))

bash:
	docker compose exec backend bash

run:
	docker compose run --rm --service-ports backend

migrate:
	docker compose exec backend python manage.py migrate $(filter-out $@,$(MAKECMDGOALS))

makemigrations:
	docker compose exec backend python manage.py makemigrations $(filter-out $@,$(MAKECMDGOALS))

shell:
	docker compose exec backend python manage.py shell

showmigrations:
	docker compose exec backend python manage.py showmigrations

ps:
	docker compose ps -a

restart:
	docker compose restart $(filter-out $@,$(MAKECMDGOALS))

createsuperuser:
	@echo "Creating superuser from container environment variables..."
	@docker compose exec backend sh -c 'if [ -z "$$SUPERUSER_USERNAME" ] || [ -z "$$SUPERUSER_PASSWORD" ]; then echo "Error: SUPERUSER_USERNAME and SUPERUSER_PASSWORD environment variables must be set in the container"; exit 1; fi; echo "Creating superuser with username: $$SUPERUSER_USERNAME"; python manage.py create_superuser --email $$SUPERUSER_USERNAME --password $$SUPERUSER_PASSWORD'

initdev:
	make clean
	make up
	make makemigrations
	make migrate
# 	make createsuperuser
	make restart
