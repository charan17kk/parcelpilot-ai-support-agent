import uuid
from typing import Any

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext
from app.config import Settings
from app.db.models import Document, DocumentChunk
from app.db.repositories import SupportRepository
from app.reliability import ReliabilityService
from app.services.embeddings import LocalEmbeddingService


class RetrievalService:
    def __init__(self, db: AsyncSession, auth: AuthContext, settings: Settings):
        self.db = db
        self.auth = auth
        self.settings = settings
        self.repository = SupportRepository(db, auth)
        self._embedding_model: LocalEmbeddingService | None = None

    def embedding_model(self) -> LocalEmbeddingService:
        if self._embedding_model is None:
            self._embedding_model = LocalEmbeddingService(self.settings.embedding_model)
        return self._embedding_model

    async def search_documents(
        self,
        query: str,
        document_types: list[str] | None = None,
        include_deprecated: bool = False,
        account_id: uuid.UUID | None = None,
    ) -> list[dict[str, Any]]:
        vector = self.embedding_model().embed_one(query)
        base_filters = [self.repository.document_access_clause()]
        if document_types:
            base_filters.append(Document.document_type.in_(document_types))
        if not include_deprecated:
            base_filters.append(Document.status != "deprecated")
        if account_id is not None:
            base_filters.append(
                or_(Document.account_id.is_(None), Document.account_id == account_id)
            )

        vector_distance = DocumentChunk.embedding.cosine_distance(vector)
        vector_statement = (
            select(DocumentChunk, Document, vector_distance.label("distance"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(*base_filters)
            .order_by(vector_distance, desc(Document.authority_rank))
            .limit(self.settings.document_top_k)
        )
        vector_rows = (await self.db.execute(vector_statement)).all()

        ts_query = func.plainto_tsquery("english", query)
        lexical_rank = func.ts_rank_cd(DocumentChunk.search_vector, ts_query)
        lexical_statement = (
            select(DocumentChunk, Document, lexical_rank.label("rank"))
            .join(Document, Document.id == DocumentChunk.document_id)
            .where(*base_filters, DocumentChunk.search_vector.op("@@")(ts_query))
            .order_by(desc(lexical_rank), desc(Document.authority_rank))
            .limit(self.settings.document_top_k)
        )
        lexical_rows = (await self.db.execute(lexical_statement)).all()

        merged: dict[uuid.UUID, dict[str, Any]] = {}
        for rank_index, row in enumerate(vector_rows, start=1):
            chunk, document, distance = row
            merged[chunk.id] = self._serialize_hit(
                chunk, document, score=1 / (60 + rank_index), semantic_distance=float(distance)
            )
        for rank_index, row in enumerate(lexical_rows, start=1):
            chunk, document, rank = row
            hit = merged.setdefault(
                chunk.id,
                self._serialize_hit(chunk, document, score=0.0, semantic_distance=None),
            )
            hit["score"] += 1 / (60 + rank_index)
            hit["lexical_rank"] = float(rank)

        ranked = sorted(
            merged.values(),
            key=lambda hit: (hit["score"], hit["authority_rank"]),
            reverse=True,
        )
        return ranked[: self.settings.document_top_k]

    @staticmethod
    def _serialize_hit(
        chunk: DocumentChunk,
        document: Document,
        *,
        score: float,
        semantic_distance: float | None,
    ) -> dict[str, Any]:
        return {
            "chunk_id": str(chunk.id),
            "document_id": str(document.id),
            "title": document.title,
            "filename": document.filename,
            "document_type": document.document_type,
            "version": document.version,
            "status": document.status,
            "authority_class": document.authority_class,
            "authority_label": ReliabilityService.label(document.authority_class),
            "authority_rank": document.authority_rank,
            "effective_from": document.effective_from.isoformat() if document.effective_from else None,
            "effective_to": document.effective_to.isoformat() if document.effective_to else None,
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "section_heading": chunk.section_heading,
            "content": chunk.content,
            "score": score,
            "semantic_distance": semantic_distance,
        }
