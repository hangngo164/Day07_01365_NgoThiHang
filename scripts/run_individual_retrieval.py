"""Chay nam benchmark cho Thanh vien 1: FixedSizeChunker 500/50."""

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
        collection_name="ngo_thi_hang_fixed_size",
    )
    print(f"collection_size={store.get_collection_size()}")
    for benchmark in BENCHMARKS:
        metadata_filter = benchmark.get("metadata_filter")
        if metadata_filter:
            results = store.search_with_filter(benchmark["query"], top_k=3, metadata_filter=metadata_filter)
        else:
            results = store.search(benchmark["query"], top_k=3)
        top = results[0]
        hit = any(is_relevant_result(item, benchmark) for item in results)
        snippet = " ".join(top["content"].split())[:220]
        print(
            f"{benchmark['id']} hit_top3={hit} doc_id={top['metadata'].get('doc_id')} "
            f"chunk={top['metadata'].get('chunk_index')} score={top['score']:.4f}\n{snippet}\n"
        )


if __name__ == "__main__":
    main()
