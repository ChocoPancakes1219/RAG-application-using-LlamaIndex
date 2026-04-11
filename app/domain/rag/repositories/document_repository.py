import json
from pathlib import Path

from app.domain.rag.schemas import DocumentRecord


class DocumentRepository:
    def __init__(self, metadata_path: Path) -> None:
        self._metadata_path = metadata_path
        self._metadata_path.parent.mkdir(parents=True, exist_ok=True)

    def list_by_user(self, user_id: str) -> list[DocumentRecord]:
        records = self._load()
        items = [
            DocumentRecord.model_validate(payload)
            for payload in records.values()
            if payload["user_id"] == user_id
        ]
        items.sort(key=lambda item: item.created_at, reverse=True)
        return items

    def get(self, document_id: str) -> DocumentRecord | None:
        records = self._load()
        payload = records.get(document_id)
        if payload is None:
            return None
        return DocumentRecord.model_validate(payload)

    def upsert(self, record: DocumentRecord) -> DocumentRecord:
        records = self._load()
        records[record.document_id] = record.model_dump(mode="json")
        self._save(records)
        return record

    def delete(self, document_id: str) -> None:
        records = self._load()
        records.pop(document_id, None)
        self._save(records)

    def _load(self) -> dict[str, dict]:
        if not self._metadata_path.exists():
            return {}
        raw = json.loads(self._metadata_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return {}
        return raw

    def _save(self, payload: dict[str, dict]) -> None:
        self._metadata_path.write_text(
            json.dumps(payload, ensure_ascii=True, indent=2),
            encoding="utf-8",
        )
