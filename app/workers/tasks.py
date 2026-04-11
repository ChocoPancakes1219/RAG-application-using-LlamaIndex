from __future__ import annotations

from app.workers.celery_app import celery_app


class WorkerTaskDispatcher:
    """Celery-backed dispatcher with sync fallback for local development."""

    def __init__(self, config) -> None:
        self._config = config
        self._celery_app = celery_app

    @property
    def celery_enabled(self) -> bool:
        return self._celery_app is not None

    def dispatch_ingest(self, eager_callback, *args, **kwargs):
        if self._should_run_eager():
            return eager_callback(*args, **kwargs)
        self._celery_app.send_task("airag.rebuild_user_index", args=list(args))
        return None

    def dispatch_delete(self, eager_callback, *args, **kwargs):
        if self._should_run_eager():
            return eager_callback(*args, **kwargs)
        self._celery_app.send_task("airag.delete_user_index", args=list(args))
        return None

    def _should_run_eager(self) -> bool:
        return self._celery_app is None or self._config.celery_task_always_eager


def _load_document_service():
    from app.server import DOCUMENT_SERVICE

    return DOCUMENT_SERVICE


def _run_rebuild_user_index(user_id: str) -> None:
    _load_document_service().process_ingest_job(user_id)


def _run_delete_user_index(user_id: str) -> None:
    _load_document_service().process_delete_job(user_id)


if celery_app is not None:
    @celery_app.task(name="airag.rebuild_user_index")
    def rebuild_user_index_task(user_id: str) -> None:
        _run_rebuild_user_index(user_id)


    @celery_app.task(name="airag.delete_user_index")
    def delete_user_index_task(user_id: str) -> None:
        _run_delete_user_index(user_id)
