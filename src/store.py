from __future__ import annotations

from typing import Any, Callable

from .chunking import _dot
from .embeddings import _mock_embed
from .models import Document


class EmbeddingStore:
    """
    A vector store for text chunks.

    Tries to use ChromaDB if available; falls back to an in-memory store.
    The embedding_fn parameter allows injection of mock embeddings for tests.
    """

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

            client = chromadb.Client()
            self._collection = client.get_or_create_collection(name=self._collection_name)
            self._use_chroma = True
        except Exception:
            self._use_chroma = False
            self._collection = None

    def _make_record(self, doc: Document) -> dict[str, Any]:
        embedding = self._embedding_fn(doc.content)
        metadata = dict(doc.metadata or {})
        metadata.setdefault("doc_id", doc.id)
        return {
            "id": doc.id,
            "content": doc.content,
            "embedding": embedding,
            "metadata": metadata,
        }

    def _search_records(self, query: str, records: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
        if not records or top_k <= 0:
            return []

        query_embedding = self._embedding_fn(query)
        scored = []
        for record in records:
            embedding = record.get("embedding", [])
            score = _dot(query_embedding, embedding)
            scored.append(
                {
                    "id": record.get("id"),
                    "content": record.get("content", ""),
                    "metadata": record.get("metadata", {}),
                    "embedding": embedding,
                    "score": score,
                }
            )
        scored.sort(key=lambda item: item["score"], reverse=True)
        return scored[:top_k]

    def add_documents(self, docs: list[Document]) -> None:
        """
        Embed each document's content and store it.

        For ChromaDB: use collection.add(ids=[...], documents=[...], embeddings=[...])
        For in-memory: append dicts to self._store
        """
        if not docs:
            return

        records = [self._make_record(doc) for doc in docs]
        if self._use_chroma and self._collection is not None:
            ids = [record["id"] for record in records]
            documents = [record["content"] for record in records]
            embeddings = [record["embedding"] for record in records]
            metadatas = [record["metadata"] for record in records]
            self._collection.add(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
            self._next_index += len(records)
        else:
            self._store.extend(records)
            self._next_index += len(records)

    def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Find the top_k most similar documents to query.

        For in-memory: compute dot product of query embedding vs all stored embeddings.
        """
        if top_k <= 0:
            return []

        if self._use_chroma and self._collection is not None:
            results = self._collection.query(query_texts=[query], n_results=top_k)
            documents = results.get("documents", [[]])[0] if results.get("documents") else []
            metadatas = results.get("metadatas", [[]])[0] if results.get("metadatas") else []
            distances = results.get("distances", [[]])[0] if results.get("distances") else []
            ids = results.get("ids", [[]])[0] if results.get("ids") else []
            output: list[dict[str, Any]] = []
            for idx, content in enumerate(documents):
                distance = distances[idx] if idx < len(distances) else 0.0
                score = 1.0 - float(distance)
                output.append(
                    {
                        "id": ids[idx] if idx < len(ids) else None,
                        "content": content,
                        "metadata": metadatas[idx] if idx < len(metadatas) else {},
                        "score": score,
                    }
                )
            return output

        return self._search_records(query, self._store, top_k)

    def get_collection_size(self) -> int:
        """Return the total number of stored chunks."""
        if self._use_chroma and self._collection is not None:
            try:
                data = self._collection.get()
                return len(data.get("ids", []))
            except Exception:
                return 0
        return len(self._store)

    def search_with_filter(self, query: str, top_k: int = 3, metadata_filter: dict = None) -> list[dict]:
        """
        Search with optional metadata pre-filtering.

        First filter stored chunks by metadata_filter, then run similarity search.
        """
        if not metadata_filter:
            return self.search(query, top_k=top_k)

        if self._use_chroma and self._collection is not None:
            candidates = self._collection.get()
            ids = candidates.get("ids", [])
            documents = candidates.get("documents", [])
            metadatas = candidates.get("metadatas", [])
            records = []
            for idx, doc_id in enumerate(ids):
                metadata = metadatas[idx] if idx < len(metadatas) and metadatas[idx] is not None else {}
                if all(metadata.get(key) == value for key, value in metadata_filter.items()):
                    records.append(
                        {
                            "id": doc_id,
                            "content": documents[idx] if idx < len(documents) else "",
                            "metadata": metadata,
                            "embedding": self._embedding_fn(documents[idx] if idx < len(documents) else ""),
                        }
                    )
            return self._search_records(query, records, top_k)

        filtered = [
            record
            for record in self._store
            if all(record.get("metadata", {}).get(key) == value for key, value in metadata_filter.items())
        ]
        return self._search_records(query, filtered, top_k)

    def delete_document(self, doc_id: str) -> bool:
        """
        Remove all chunks belonging to a document.

        Returns True if any chunks were removed, False otherwise.
        """
        if self._use_chroma and self._collection is not None:
            before = self.get_collection_size()
            try:
                self._collection.delete(where={"doc_id": doc_id})
            except Exception:
                self._collection.delete(where={"id": doc_id})
            return self.get_collection_size() < before

        before = len(self._store)
        self._store = [record for record in self._store if record.get("metadata", {}).get("doc_id") != doc_id]
        return len(self._store) < before
