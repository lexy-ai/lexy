# reference: https://docs.celeryq.dev/en/stable/userguide/testing.html


class TestCelery:

    def test_celery_app(self, celery_app, celery_worker, settings, celery_settings):
        print(f"{celery_app = }")
        print(f"{celery_app.conf.broker_url = }")
        print(f"{celery_app.conf.result_backend = }")
        assert celery_app

        # assert that result_backend is set to the value in test settings
        assert celery_app.conf.result_backend == celery_settings.result_backend

        assert 'lexy.transformers.text.embeddings.minilm' in celery_app.tasks
        assert 'lexy.db.save_records_to_index' in celery_app.tasks

        save_records_task = celery_app.tasks.get('lexy.db.save_records_to_index')
        assert save_records_task is not None
        assert save_records_task.db.bind.engine.url.database == 'lexy_tests'
        assert save_records_task.db.bind.engine.url.render_as_string(hide_password=False) == settings.sync_database_url

        text_embeddings_task = celery_app.tasks.get('lexy.transformers.text.embeddings.minilm')
        assert text_embeddings_task is not None

        eager_task = text_embeddings_task.apply(args=['hello world'])
        eager_result = eager_task.get().tolist()
        assert isinstance(eager_result, list)
        assert all(isinstance(elem, float) for elem in eager_result)

        eager_task = text_embeddings_task.apply(args=[['hello', 'world']])
        eager_result = eager_task.get().tolist()
        assert isinstance(eager_result, list)
        assert all(isinstance(elem, list) for elem in eager_result)
        assert all(isinstance(elem, float) for elem in eager_result[0])
        assert all(isinstance(elem, float) for elem in eager_result[1])

        # this hangs unless we include the celery_worker fixture
        task = text_embeddings_task.apply_async(args=[['hello', 'world']])
        assert isinstance(task.id, str)
        result = task.get().tolist()
        assert isinstance(result, list)
        assert all(isinstance(elem, list) for elem in result)
        assert all(isinstance(elem, float) for elem in result[0])
        assert all(isinstance(elem, float) for elem in result[1])

        # this times out unless we include the celery_worker fixture
        task2 = text_embeddings_task.delay('hello world')
        assert isinstance(task2.id, str)
        result2 = task2.get(timeout=10).tolist()
        assert isinstance(result2, list)
        assert all(isinstance(elem, float) for elem in result2)

    def test_celery_config(self, celery_config):
        assert celery_config

    def test_celery_worker(self, celery_worker):
        print(f"{celery_worker = }")
        assert celery_worker

    def test_celery_session_worker(self, celery_session_worker):
        print(f"{celery_session_worker = }")
        assert celery_session_worker
