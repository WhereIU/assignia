install: docker-build
	echo "Установка завершена"

run:
	docker compose up

test:
	docker compose run --rm web pytest

run-build:
	docker compose up --build

run-prod:
	docker compose -f docker-compose.prod.yml up

run-build-prod:
	docker compose -f docker-compose.prod.yml up --build

docker-shell:
	docker compose run --rm web python manage.py shell

exec-web:
	docker compose exec web bash

docker-build:
	docker compose build --build-arg UID=$$(id -u) --build-arg GID=$$(id -g) web

docker-migrate:
	docker compose run --rm web python manage.py makemigrations
	docker compose -f docker-compose.prod.yml run --rm web python manage.py migrate

save-images:
	docker save -o assignia-images.tar python:3.11-slim postgres:15 nginx:latest

load-images:
	docker load -i assignia-images.tar

deploy-ansible:
	ansible-playbook -i ansible/hosts.ini ansible/deploy.yml

deploy-local-ansible:
	ansible-playbook -i ansible/hosts.ini ansible/deploy_local.yml
