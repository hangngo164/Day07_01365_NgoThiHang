from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from ingest import build_knowledge_base
from src import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    LocalEmbedder,
    OpenAIEmbedder,
    RecursiveChunker,
    RegulationSectionChunker,
    SentenceChunker,
    _mock_embed,
)

DEFAULT_DATA_DIR = "data/md"


def _select_embedder():
    """Choose semantic local embeddings by default, with explicit safe fallback."""
    load_dotenv(override=False)
    provider = os.getenv(EMBEDDING_PROVIDER_ENV, "local").strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(
                model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL)
            )
        except Exception as error:
            print(f"Không dùng được local embedder ({error}); chuyển sang mock.")
            return _mock_embed
    if provider == "openai":
        try:
            return OpenAIEmbedder(
                model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL)
            )
        except Exception as error:
            print(f"Không dùng được OpenAI embedder ({error}); chuyển sang mock.")
            return _mock_embed
    return _mock_embed


def _select_chunker():
    """Read CHUNKING_STRATEGY: fixed, sentence, recursive, or regulation."""
    strategy = os.getenv("CHUNKING_STRATEGY", "sentence").strip().lower()
    if strategy == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=50), strategy
    if strategy == "recursive":
        return RecursiveChunker(chunk_size=500), strategy
    if strategy in {"regulation", "section", "sections"}:
        return RegulationSectionChunker(chunk_size=500), "regulation"
    return SentenceChunker(max_sentences_per_chunk=3), "sentence"


def demo_llm(prompt: str) -> str:
    """A visible placeholder for checking the grounded prompt without an API."""
    preview = prompt[:500].replace("\n", " ")
    return f"[DEMO LLM] Prompt grounded in retrieved context: {preview}..."


def run_manual_demo(question: str | None = None, data_dir: str | None = None) -> int:
    load_dotenv(override=False)
    corpus = Path(data_dir or os.getenv("LAB_DATA_DIR", DEFAULT_DATA_DIR))
    query = question or "Tóm tắt nội dung chính của quy định về học bổng."
    if not corpus.exists():
        print(f"Không tìm thấy corpus: {corpus}")
        return 1

    embedder = _select_embedder()
    chunker, strategy = _select_chunker()
    store = build_knowledge_base(
        corpus,
        embedding_fn=embedder,
        chunker=chunker,
        collection_name="lab7_manual_demo",
    )
    backend = getattr(embedder, "_backend_name", embedder.__class__.__name__)
    print(f"Corpus: {corpus} | chunker: {strategy} | embedder: {backend}")
    print(f"Đã nạp {store.get_collection_size()} chunk.")
    if backend == "mock embeddings fallback":
        print("Cảnh báo: mock chỉ phù hợp smoke test, không dùng để kết luận retrieval.")

    print(f"\nCâu hỏi: {query}")
    for rank, result in enumerate(store.search(query, top_k=3), start=1):
        metadata = result["metadata"]
        preview = " ".join(result["content"].split())[:180]
        print(
            f"{rank}. score={result['score']:.4f} "
            f"doc_id={metadata.get('doc_id')} chunk={metadata.get('chunk_index')}\n"
            f"   {preview}"
        )

    print("\n=== KnowledgeBaseAgent ===")
    print(KnowledgeBaseAgent(store, demo_llm).answer(query, top_k=3))
    return 0


def main() -> int:
    question = " ".join(sys.argv[1:]).strip() or None
    return run_manual_demo(question=question)


if __name__ == "__main__":
    raise SystemExit(main())
