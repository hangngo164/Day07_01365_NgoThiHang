from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store. The
    embedding_fn parameter allows injection of mock embeddings for tests.
    """

    import uuid
from typing import Any, Callable

# Các import khác của bạn...


class EmbeddingStore:

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
        self._next_index = 0

        try:
            import chromadb
            from chromadb.config import Settings

            # 1. Khởi tạo EphemeralClient (In-Memory ChromaDB) và tắt telemetry
            client = chromadb.EphemeralClient(
                settings=Settings(anonymized_telemetry=False)
            )

            # 2. Sinh unique suffix để tránh đụng độ Collection giữa các testcase (Lớp phòng thủ chống lỗi dimension)
            unique_coll_name = f"{collection_name}_{uuid.uuid4().hex[:8]}"

            self._collection = client.create_collection(name=unique_coll_name)
            self._use_chroma = True
        except Exception:
            # Fallback về In-Memory Store thuần nếu không load được ChromaDB
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        if not doc or not getattr(doc, "content", None):
            raise ValueError("Document content cannot be empty.")

        metadata = getattr(doc, "metadata", None) or {}
        metadata = (
            metadata.copy() if isinstance(metadata, dict) else dict(metadata)
        )

        doc_id = (
            metadata.get("doc_id")
            or getattr(doc, "id", None)
            or f"doc_{self._next_index}"
        )
        metadata["doc_id"] = doc_id

        embedding = getattr(
            doc, "embedding", None
        ) or self._embedding_fn(doc.content)

        record = {
            "doc_id": doc_id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }
        self._next_index += 1
        return record

    def _search_records(
        self, query: str, records: list[dict[str, Any]], top_k: int
    ) -> list[dict[str, Any]]:
        if not query or top_k <= 0 or not records:
            return []

        query_embedding = self._embedding_fn(query)
        scored_records: list[tuple[float, dict[str, Any]]] = []

        for record in records:
            embedding = record.get("embedding")
            if embedding is None:
                continue

            score = _dot(query_embedding, embedding)
            scored_records.append((score, record))

        scored_records.sort(key=lambda item: item[0], reverse=True)
        return [
            {
                "score": score,
                **record,
            }
            for score, record in scored_records[:top_k]
        ]

    def _format_chroma_results(
        self, results: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        ids = results.get("ids", [[]])[0]
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        raw_embeddings = results.get("embeddings")
        raw_distances = results.get("distances")

        embeddings = (
            raw_embeddings[0] if raw_embeddings else [None] * len(ids)
        )
        distances = (
            raw_distances[0] if raw_distances else [0.0] * len(ids)
        )

        formatted_results = []
        for doc_id, content, embedding, metadata, dist in zip(
            ids, documents, embeddings, metadatas, distances
        ):
            # Quy đổi Distance sang Similarity Score chuẩn xác
            similarity_score = 1.0 / (1.0 + float(dist if dist is not None else 0.0))
            formatted_results.append(
                {
                    "doc_id": doc_id,
                    "content": content,
                    "embedding": embedding,
                    "metadata": metadata or {},
                    "score": similarity_score,
                }
            )

        return formatted_results

    def add_documents(self, docs: list[Document]) -> None:
        """Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...],
        embeddings=[...]) For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]

        if self._use_chroma and self._collection is not None:
            self._collection.add(
                ids=[record["doc_id"] for record in records],
                documents=[record["content"] for record in records],
                embeddings=[record["embedding"] for record in records],
                metadatas=[record["metadata"] for record in records],
            )
        else:
            self._store.extend(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored
        embeddings.
        """
        if not query or top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
                include=[
                    "documents",
                    "metadatas",
                    "embeddings",
                    "distances",
                ],
            )
            return self._format_chroma_results(results)

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                return 0
        return len(self._store)

    def search_with_filter(
        self, query: str, top_k: int = 3, metadata_filter: dict = None
    ) -> list[dict]:
        """Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity
        search.
        """
        if not query or top_k <= 0:
            return []

        if metadata_filter is None:
            metadata_filter = {}

        if self._use_chroma and self._collection is not None:
            query_kwargs: dict[str, Any] = {
                "query_texts": [query],
                "n_results": top_k,
                "include": [
                    "documents",
                    "metadatas",
                    "embeddings",
                    "distances",
                ],
            }
            if metadata_filter:
                query_kwargs["where"] = metadata_filter

            results = self._collection.query(**query_kwargs)
            return self._format_chroma_results(results)

        filtered_records = [
            record
            for record in self._store
            if all(
                record["metadata"].get(key) == value
                for key, value in metadata_filter.items()
            )
        ]
        return self._search_records(query, filtered_records, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            before_count = self.get_collection_size()
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                try:
                    self._collection.delete(ids=[doc_id])
                except Exception:
                    return False

            after_count = self.get_collection_size()
            return after_count < before_count

        initial_size = len(self._store)
        self._store = [
            record
            for record in self._store
            if record["metadata"].get("doc_id") != doc_id
            and record.get("doc_id") != doc_id
        ]
        return len(self._store) < initial_size