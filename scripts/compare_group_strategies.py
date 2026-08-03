"""So sanh bon chien luoc chunking tren nam benchmark chung cua nhom."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import build_knowledge_base
from scripts.run_retrieval_benchmark import BENCHMARKS, is_relevant_result, lexical_embed
from src.chunking import FixedSizeChunker, RecursiveChunker, SentenceChunker


STRATEGIES = {
    "Thanh vien 1 - FixedSize": FixedSizeChunker(chunk_size=500, overlap=50),
    "Thanh vien 2 - Sentence": SentenceChunker(max_sentences_per_chunk=3),
    "Thanh vien 3 - Recursive 500": RecursiveChunker(chunk_size=500),
    "Thanh vien 4 - Recursive 350 + filter": RecursiveChunker(chunk_size=350),
}


def main() -> None:
    for name, chunker in STRATEGIES.items():
        store = build_knowledge_base(
            ROOT / "data" / "md",
            embedding_fn=lexical_embed,
            chunker=chunker,
            collection_name=name.lower().replace(" ", "_"),
        )
        hits = 0
        details = []
        for benchmark in BENCHMARKS:
            metadata_filter = benchmark.get("metadata_filter")
            if metadata_filter:
                results = store.search_with_filter(benchmark["query"], top_k=3, metadata_filter=metadata_filter)
            else:
                results = store.search(benchmark["query"], top_k=3)
            hit = any(is_relevant_result(item, benchmark) for item in results)
            hits += int(hit)
            details.append("Y" if hit else "N")
        print(f"{name}: chunks={store.get_collection_size()}, hits={hits}/5, score={hits * 2}/10, queries={','.join(details)}")


if __name__ == "__main__":
    main()
