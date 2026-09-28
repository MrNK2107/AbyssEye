.PHONY: all setup test lint train batch-extract build up down prod-up prod-down clean

PYTHON ?= python

all: setup test

setup:
	$(PYTHON) -m pip install --upgrade pip
	pip install -r requirements.txt
	cd frontend && npm install

test:
	$(PYTHON) -m pytest -v

train:
	$(PYTHON) scripts/train_models.py

ablation:
	$(PYTHON) experiments/run_ablation_study.py

batch-extract:
	$(PYTHON) scripts/batch_extract_dataset.py --dataset all --max-samples 100

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

prod-up:
	docker compose -f docker-compose.prod.yml up -d --build

prod-down:
	docker compose -f docker-compose.prod.yml down

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf frontend/.next frontend/out
