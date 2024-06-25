SHELL=/usr/bin/env bash
BASEDIR = $(shell pwd)

.PHONY:build
build:
	docker buildx bake -f docker/docker-bake.hcl

.PHONY:inspect
inspect:
	docker compose exec jupyter /bin/bash

.PHONY:down
down:
	docker compose down

.PHONY:start # called `start` instead of `up` because it does more than `docker compose up`
start:
	docker compose pull;
	docker compose up -d --build --remove-orphans;
	docker compose logs -f jupyter || true;

.PHONY:logs
logs:
	docker compose logs -f jupyter || true;

.PHONY:dev
dev:
	if [[ "$$(docker compose ps | grep 'jupyter')" == "" ]]; then \
		docker compose pull; \
		docker compose up -d --build && \
		(sleep 1; python -m webbrowser "http://localhost:8888"); \
		docker compose logs -f jupyter || true; \
	else \
		docker compose down jupyter && \
		docker compose up -d jupyter && \
		(sleep 1; python -m webbrowser "http://localhost:8888"); \
		docker compose logs -f jupyter || true; \
	fi


.env:
	@if [[ ! -e ./.env ]]; then \
		cp env.example .env; \
		echo "Don't forget to set your OPENAI key in the .env file!"; \
	fi

