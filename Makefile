serve-docs:
	mkdocs serve -f docs/mkdocs.yml

recreate-queues:
	docker exec lexy-queue rabbitmqctl stop_app
	docker exec lexy-queue rabbitmqctl reset
	docker exec lexy-queue rabbitmqctl start_app

inspect-celery:
	docker exec lexy-celeryworker celery inspect active -t 10.0

update-dev-containers:
	# rebuild lexyserver and lexyworker
	docker-compose up --build -d --no-deps lexyserver lexyworker
	# run DB migrations
	alembic upgrade head
