install: docker-build
	echo "Установка"

run:
	docker compose up

run-build:
	docker compose up --build

docker-build:
	docker compose build --build-arg UID=$$(id -u) --build-arg GID=$$(id -g) web