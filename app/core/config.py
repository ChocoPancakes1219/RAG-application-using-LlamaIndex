import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class AppConfig:
    root_dir: Path
    data_dir: Path
    storage_dir: Path
    metadata_path: Path
    chunk_size: int = 512
    chunk_overlap: int = 50
    similarity_top_k: int = 3
    default_user_id: str = "demo-user"
    redis_url: str = "redis://localhost:6379/0"
    redis_password: str | None = None
    celery_task_always_eager: bool = True
    airag_internal_api_key: str | None = None
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_name: str = "airag_chunks"
    elasticsearch_url: str = "http://localhost:9200"
    elasticsearch_api_key: str | None = None
    elasticsearch_index_name: str = "airag_chunks"

    @classmethod
    def from_root(cls, root_dir: Path) -> "AppConfig":
        data_dir = root_dir / "data"
        storage_dir = root_dir / "storage"
        return cls(
            root_dir=root_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            metadata_path=storage_dir / "documents.json",
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            redis_password=os.getenv("REDIS_PASSWORD") or None,
            celery_task_always_eager=_env_bool("CELERY_TASK_ALWAYS_EAGER", True),
            airag_internal_api_key=os.getenv("AIRAG_INTERNAL_API_KEY") or None,
            qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
            qdrant_api_key=os.getenv("QDRANT_API_KEY") or None,
            qdrant_collection_name=os.getenv(
                "QDRANT_COLLECTION_NAME",
                "airag_chunks",
            ),
            elasticsearch_url=os.getenv(
                "ELASTICSEARCH_URL",
                "http://localhost:9200",
            ),
            elasticsearch_api_key=os.getenv("ELASTICSEARCH_API_KEY") or None,
            elasticsearch_index_name=os.getenv(
                "ELASTICSEARCH_INDEX_NAME",
                "airag_chunks",
            ),
        )

    def ensure_directories(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def user_data_dir(self, user_id: str) -> Path:
        return self.data_dir / user_id

    def user_storage_dir(self, user_id: str) -> Path:
        return self.storage_dir / user_id

    def is_valid_internal_api_key(self, candidate: str | None) -> bool:
        if not self.airag_internal_api_key or not candidate:
            return False
        return secrets.compare_digest(self.airag_internal_api_key, candidate)

    @property
    def redis_url_with_auth(self) -> str:
        parsed = urlsplit(self.redis_url)
        if not self.redis_password or "@" in parsed.netloc:
            return self.redis_url
        netloc = f":{self.redis_password}@{parsed.netloc}"
        return urlunsplit(
            (parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment)
        )


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}
