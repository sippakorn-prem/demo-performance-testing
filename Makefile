.PHONY: help up down restart logs migrate migrate-create migrate-downgrade migrate-history migrate-current seed seed-massive seed-massive-local test-baseline test-load test-stress test-spike test-soak test-concurrency test-capacity test-resilience locust-ui

help:
	@echo "Performance Testing Workshop - Makefile Commands"
	@echo ""
	@echo "Docker Commands:"
	@echo "  make up          - Start all services (API, Postgres, Prometheus, Grafana)"
	@echo "  make down        - Stop all services"
	@echo "  make restart     - Restart all services"
	@echo "  make logs        - Show logs from all services"
	@echo ""
	@echo "Database Migrations (runs in Docker container):"
	@echo "  make migrate           - Run database migrations (upgrade to head)"
	@echo "  make migrate-create    - Create a new migration (use: make migrate-create MSG='description')"
	@echo "  make migrate-downgrade - Downgrade one revision"
	@echo "  make migrate-history   - Show migration history"
	@echo "  make migrate-current   - Show current migration version"
	@echo ""
	@echo "Data Seeding (runs in Docker container):"
	@echo "  make seed              - Seed minimal data (10K products) via API startup"
	@echo "  make seed-massive      - Seed massive data (100K+ products, cart items)"
	@echo "  make seed-massive-local - Seed massive data locally (requires DATABASE_URL)"
	@echo ""
	@echo "Locust Test Commands (runs in Docker container):"
	@echo "  make test-baseline     - Run baseline test (10 users)"
	@echo "  make test-load          - Run load test (50 users)"
	@echo "  make test-stress        - Run stress test (staged ramp-up)"
	@echo "  make test-spike         - Run spike test (200 users, fast spawn)"
	@echo "  make test-soak          - Run soak test (30 users, 30 minutes)"
	@echo "  make test-concurrency   - Run concurrency test (100 users, same product)"
	@echo "  make test-capacity      - Run capacity test (stepwise, SLO validation)"
	@echo "  make test-resilience    - Run resilience test (50 users, introduce failures)"
	@echo "  make locust-ui          - Start Locust web UI (http://localhost:8089)"
	@echo ""
	@echo "Note: Make sure API is running before running tests!"
	@echo "      Start API with: make up"

up:
	docker-compose up -d --build
	@echo "Services started!"
	@echo "API: http://localhost:8000"
	@echo "Grafana: http://localhost:3500 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "Locust UI: http://localhost:8089 (use 'make locust-ui' to start)"

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

seed:
	@echo "Minimal seeding happens automatically on API startup"
	@echo "For massive data, use: make seed-massive"

seed-massive:
	@echo "Seeding massive data (100K+ products, cart items)..."
	@echo "This may take a few minutes..."
	@if docker ps --filter "name=demo-api" --format "{{.Status}}" | grep -q "Up"; then \
		docker exec demo-api python -m app.seed_data; \
	else \
		echo "API container not running. Please start it first with: make up"; \
		exit 1; \
	fi

seed-massive-local:
	@echo "Seeding massive data locally (requires DATABASE_URL env var)..."
	@echo "This may take a few minutes..."
	python -m app.seed_data

migrate:
	@echo "Running database migrations in Docker container..."
	@if docker ps --filter "name=demo-api" --format "{{.Status}}" | grep -q "Up"; then \
		docker exec demo-api alembic upgrade head; \
	else \
		echo "API container not running. Please start it first with: make up"; \
		exit 1; \
	fi

migrate-create:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG is required. Usage: make migrate-create MSG='your message'"; \
		exit 1; \
	fi
	@echo "Creating new migration in Docker container..."
	@if docker ps --filter "name=demo-api" --format "{{.Status}}" | grep -q "Up"; then \
		docker exec demo-api alembic revision --autogenerate -m "$(MSG)"; \
	else \
		echo "API container not running. Please start it first with: make up"; \
		exit 1; \
	fi

migrate-downgrade:
	@echo "Downgrading database by one revision in Docker container..."
	@if docker ps --filter "name=demo-api" --format "{{.Status}}" | grep -q "Up"; then \
		docker exec demo-api alembic downgrade -1; \
	else \
		echo "API container not running. Please start it first with: make up"; \
		exit 1; \
	fi

migrate-history:
	@echo "Migration history:"
	@if docker ps --filter "name=demo-api" --format "{{.Status}}" | grep -q "Up"; then \
		docker exec demo-api alembic history; \
	else \
		echo "API container not running. Please start it first with: make up"; \
		exit 1; \
	fi

migrate-current:
	@echo "Current migration version:"
	@if docker ps --filter "name=demo-api" --format "{{.Status}}" | grep -q "Up"; then \
		docker exec demo-api alembic current; \
	else \
		echo "API container not running. Please start it first with: make up"; \
		exit 1; \
	fi

test-baseline:
	@echo "Running baseline test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-baseline \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_baseline.py \
		--host http://api:8000 \
		--users 10 \
		--spawn-rate 2

test-load:
	@echo "Running load test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-load \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_load.py \
		--host http://api:8000 \
		--users 50 \
		--spawn-rate 5

test-stress:
	@echo "Running stress test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-stress \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_stress.py \
		--host http://api:8000

test-spike:
	@echo "Running spike test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-spike \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_spike.py \
		--host http://api:8000 \
		--users 200 \
		--spawn-rate 50

test-soak:
	@echo "Running soak test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-soak \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_soak.py \
		--host http://api:8000 \
		--users 30 \
		--spawn-rate 3 \
		--run-time 30m

test-concurrency:
	@echo "Running concurrency test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-concurrency \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_concurrency.py \
		--host http://api:8000 \
		--users 100 \
		--spawn-rate 20

test-capacity:
	@echo "Running capacity test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-capacity \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_capacity.py \
		--host http://api:8000

test-resilience:
	@echo "Running resilience test in Docker container..."
	@echo "Open Locust UI at http://localhost:8089 to start the test"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-resilience \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_resilience.py \
		--host http://api:8000 \
		--users 50 \
		--spawn-rate 5

locust-ui:
	@echo "Starting Locust web UI..."
	@echo "Access at http://localhost:8089"
	@echo "Select a test file and configure your test parameters"
	@NETWORK=$$(docker inspect -f '{{range $$net, $$v := .NetworkSettings.Networks}}{{printf "%s\n" $$net}}{{end}}' demo-api 2>/dev/null | head -1); \
	if [ -z "$$NETWORK" ]; then \
		echo "Error: API container (demo-api) not running. Please run 'make up' first."; \
		exit 1; \
	fi; \
	docker run --rm -it \
		--network $$NETWORK \
		--name demo-locust-ui \
		-v $$(pwd)/test:/mnt/test \
		-e PYTHONPATH=/mnt \
		-p 8089:8089 \
		locustio/locust:latest \
		-f /mnt/test/locust_baseline.py \
		--host http://api:8000
