.PHONY: help install dev test clean docker-build docker-up docker-down k8s-deploy k8s-delete init-db

help:
	@echo "Enterprise VPN - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install      - Install Python dependencies"
	@echo "  dev          - Run development server"
	@echo "  test         - Run tests"
	@echo "  clean        - Clean build artifacts"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-up    - Start Docker Compose"
	@echo "  docker-down  - Stop Docker Compose"
	@echo "  k8s-deploy   - Deploy to Kubernetes"
	@echo "  k8s-delete   - Delete Kubernetes resources"
	@echo "  init-db      - Initialize database"

install:
	pip install -r requirements.txt

dev:
	uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

docker-build:
	docker build -f infrastructure/docker/Dockerfile -t enterprise-vpn:latest .

docker-up:
	cd infrastructure/docker && docker-compose up -d

docker-down:
	cd infrastructure/docker && docker-compose down

k8s-deploy:
	kubectl apply -f infrastructure/kubernetes/

k8s-delete:
	kubectl delete -f infrastructure/kubernetes/

init-db:
	python scripts/deployment/init_db.py

