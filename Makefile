serve-docs:
	mkdocs serve -f docs/mkdocs.yml

recreate-queues:
	docker exec lexy-queue rabbitmqctl stop_app
	docker exec lexy-queue rabbitmqctl reset
	docker exec lexy-queue rabbitmqctl start_app

inspect-celery:
	docker exec lexy-celeryworker celery inspect active -t 10.0
