from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

from app.core.config import AppConfig

try:  # pragma: no cover - optional dependency in local env
    from celery import Celery
except ImportError:  # pragma: no cover - optional dependency in local env
    Celery = None


ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")


def create_celery_app(config: AppConfig):
    if Celery is None:
        return None

    app = Celery(
        "min_minisaas_airag",
        broker=config.redis_url_with_auth,
        backend=config.redis_url_with_auth,
    )
    app.conf.task_always_eager = config.celery_task_always_eager
    app.conf.task_default_queue = "airag"
    app.conf.imports = ("app.workers.tasks",)
    app.conf.task_routes = {
        "airag.rebuild_user_index": {"queue": "airag-index"},
        "airag.delete_user_index": {"queue": "airag-index"},
    }
    return app


celery_app = create_celery_app(AppConfig.from_root(ROOT_DIR))

if celery_app is not None:  # pragma: no branch
    import app.workers.tasks  # noqa: F401
