install: docker-build
	echo "Установка"

run:
	docker compose up

run-build:
	docker compose up --build

docker-shell:
	docker compose run --rm web python manage.py shell

docker-build:
	docker compose build --build-arg UID=$$(id -u) --build-arg GID=$$(id -g) web