from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """Vector-store wrapper with an in-memory fallback and optional ChromaDB."""

    def __init__(
        self,
        collection_name: str = "documents",
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> None:
        self._embedding_fn = embedding_fn or _mock_embed
        self._collection_name = collection_name
        self._use_chroma = False
        self._store: list[dict[str, Any]] = []
        self._collection = None
        self._client = None
        self._next_index = 0

        try:
            import chromadb

            self._client = chromadb.Client()
            self._collection = self._client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._use_chroma = True
        except Exception:
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        metadata = dict(doc.metadata or {})
        # Keep the source document id placed on chunks by ingest.chunk_document.
        metadata.setdefault("doc_id", doc.id)
        record = {
            "id": f"{doc.id}-{self._next_index}",
            "content": doc.content,
            "metadata": metadata,
            "embedding": self._embedding_fn(doc.content),
        }
        self._next_index += 1
        return record

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        if top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        results = [
            {
                "id": record["id"],
                "content": record["content"],
                "metadata": dict(record["metadata"]),
                "score": _dot(query_embedding, record["embedding"]),
            }
            for record in records
        ]
        results.sort(key=lambda result: result["score"], reverse=True)
        return results[:top_k]

    @staticmethod
    def _format_chroma_results(response: dict) -> list[dict[str, Any]]:
        ids = response.get("ids", [[]])[0] or []
        documents = response.get("documents", [[]])[0] or []
        metadatas = response.get("metadatas", [[]])[0] or []
        distances = response.get("distances", [[]])[0] or []
        return [
            {
                "id": record_id,
                "content": content,
                "metadata": metadata or {},
                "score": 1.0 - float(distance),
            }
            for record_id, content, metadata, distance in zip(
                ids, documents, metadatas, distances
            )
        ]

    def add_documents(self, docs: list[Document]) -> None:
        """Embed and store every document or chunk."""
        records = [self._make_record(doc) for doc in docs]
        if not records:
            return

        if self._use_chroma and self._collection is not None:
            self._collection.add(
                ids=[record["id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
            )
            return

        self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Return the highest-scoring results for a query."""
        if top_k <= 0:
            return []
        if not self._use_chroma or self._collection is None:
            return self._search_records(query, self._store, top_k)

        result_count = min(top_k, self._collection.count())
        if result_count == 0:
            return []
        response = self._collection.query(
            query_embeddings=[self._embedding_fn(query)],
            n_results=result_count,
        )
        return self._format_chroma_results(response)

    def get_collection_size(self) -> int:
        """Return the number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            return self._collection.count()
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict | None = None
    ) -> list[dict[str, Any]]:
        """Filter by metadata before ranking with the query embedding."""
        if top_k <= 0:
            return []
        if not metadata_filter:
            return self.search(query, top_k)

        if not self._use_chroma or self._collection is None:
            candidates = [
                record
                for record in self._store
                if all(
                    record["metadata"].get(key) == value
                    for key, value in metadata_filter.items()
                )
            ]
            return self._search_records(query, candidates, top_k)

        result_count = min(top_k, self._collection.count())
        if result_count == 0:
            return []
        response = self._collection.query(
            query_embeddings=[self._embedding_fn(query)],
            n_results=result_count,
            where=metadata_filter,
        )
        return self._format_chroma_results(response)

    def delete_document(self, doc_id: str) -> bool:
        """Delete every chunk belonging to one source document."""
        if self._use_chroma and self._collection is not None:
            matches = self._collection.get(where={"doc_id": doc_id})
            ids = matches.get("ids", [])
            if not ids:
                return False
            self._collection.delete(ids=ids)
            return True

        original_size = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
        ]
        return len(self._store) < original_size
