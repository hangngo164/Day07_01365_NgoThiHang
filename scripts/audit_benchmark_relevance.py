"""Hien thi thu hang cua chunk co evidence gold answer cho tung benchmark."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import build_knowledge_base
from scripts.run_retrieval_benchmark import BENCHMARKS, is_relevant_result, lexical_embed
from src.chunking import FixedSizeChunker


def main() -> None:
    store = build_knowledge_base(
        ROOT / "data" / "md",
        embedding_fn=lexical_embed,
        chunker=FixedSizeChunker(chunk_size=500, overlap=50),
        collection_name="benchmark_relevance_audit",
    )
    for benchmark in BENCHMARKS:
        metadata_filter = benchmark.get("metadata_filter")
        results = (
            store.search_with_filter(benchmark["query"], top_k=100, metadata_filter=metadata_filter)
            if metadata_filter
            else store.search(benchmark["query"], top_k=100)
        )
        matches = [
            (rank, item["metadata"].get("doc_id"), item["metadata"].get("chunk_index"), item["score"])
            for rank, item in enumerate(results, start=1)
            if is_relevant_result(item, benchmark)
        ]
        print(f"{benchmark['id']}: {matches[:3] or 'no evidence chunk in top-100'}")


if __name__ == "__main__":
    main()
