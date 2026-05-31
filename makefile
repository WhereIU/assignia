setup: install install-prod
	echo "Полная установка завершена"

install: docker-build
	echo "Установка разработки завершена"

install-prod: docker-build-prod
	echo "Установка продакшена завершена"

run:
	docker compose up

run-prod:
	docker compose -f docker-compose.prod.yml up

test:
	docker compose run --rm web pytest

run-build:
	docker compose up --build

run-build-prod:
	docker compose -f docker-compose.prod.yml up --build

docker-build:
	docker compose build

docker-build-prod:
	docker compose -f docker-compose.prod.yml build

docker-migrate:
	docker compose run --rm web python manage.py makemigrations
	docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate

docker-shell:
	docker compose run --rm web python manage.py shell

exec-web:
	docker compose exec web bash

save-images:
	docker save -o assignia-images.tar python:3.11-slim postgres:15 nginx:latest redis:7-alpine

load-images:
	docker load -i assignia-images.tar

deploy-ansible:
	ansible-playbook -i ansible/hosts.ini ansible/deploy.yml

deploy-local-ansible:
	ansible-playbook -i ansible/hosts.ini ansible/deploy_local.yml
