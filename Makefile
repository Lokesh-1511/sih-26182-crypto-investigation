.PHONY: help install test run-backend run-frontend seed docker-up docker-down clean

help:
	@echo "SIH 26182 Crypto Investigation Copilot"
	@echo "--------------------------------------"
	@echo "make install      : Install backend & frontend dependencies"
	@echo "make test         : Run pytest test suite"
	@echo "make run-backend  : Start FastAPI backend server"
	@echo "make run-frontend : Start React Vite dev server"
	@echo "make seed         : Seed local database with demo fixtures"
	@echo "make docker-up    : Launch full application via Docker Compose"
	@echo "make docker-down  : Stop Docker containers"
	@echo "make clean        : Remove cached files and test artifacts"

install:
	pip install -r backend/requirements.txt
	cd frontend && npm install

test:
	python -m pytest tests/ -v

run-backend:
	uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

seed:
	python scripts/seed_demo_data.py
	python scripts/create_demo_case.py

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache frontend/dist
