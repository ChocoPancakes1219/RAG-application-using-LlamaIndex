from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile

from app.domain.rag.schemas import QueryRequest


def create_internal_rag_router(
    document_service,
    query_service,
    default_user_id: str,
    config,
) -> APIRouter:
    router = APIRouter()

    async def verify_internal_api_key(
        x_internal_api_key: Annotated[str | None, Header(alias="X-Internal-API-Key")] = None,
    ) -> str:
        if not config.airag_internal_api_key:
            raise HTTPException(status_code=503, detail="Internal API key is not configured.")
        if not config.is_valid_internal_api_key(x_internal_api_key):
            raise HTTPException(status_code=401, detail="Invalid internal API key.")
        return x_internal_api_key

    InternalAuth = Annotated[str, Depends(verify_internal_api_key)]

    @router.post("/internal/rag/documents")
    async def ingest_documents(
        _: InternalAuth,
        user_id: Annotated[str, Form(...)],
        files: Annotated[list[UploadFile], File(...)],
    ):
        return await document_service.ingest_files(user_id=user_id, files=files)

    @router.get("/internal/rag/documents")
    async def list_documents(_: InternalAuth, user_id: str):
        return document_service.list_documents(user_id)

    @router.get("/internal/rag/documents/{document_id}")
    async def get_document(_: InternalAuth, document_id: str, user_id: str):
        return document_service.get_document(user_id=user_id, document_id=document_id)

    @router.delete("/internal/rag/documents/{document_id}", status_code=204)
    async def delete_document(_: InternalAuth, document_id: str, user_id: str):
        document_service.delete_document(user_id=user_id, document_id=document_id)

    @router.post("/internal/rag/query")
    async def query_documents(_: InternalAuth, request: QueryRequest):
        return query_service.query(request)

    @router.post("/ingest")
    async def legacy_ingest(
        _: InternalAuth,
        files: Annotated[list[UploadFile], File(...)],
        user_id: Annotated[str, Form()] = default_user_id,
    ):
        return await document_service.ingest_files(user_id=user_id, files=files)

    @router.get("/query")
    async def legacy_query(_: InternalAuth, query: str, user_id: str = default_user_id):
        return query_service.query(
            QueryRequest(user_id=user_id, query=query, top_k=3)
        )

    return router
