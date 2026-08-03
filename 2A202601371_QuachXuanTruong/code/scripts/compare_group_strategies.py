"""Compare baseline, sentence, recursive, and regulation-section chunking."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import build_knowledge_base
from scripts.run_retrieval_benchmark import (
    BENCHMARKS,
    is_relevant_result,
    retrieval_settings,
    select_chunker,
    select_embedder,
)


STRATEGIES = ("fixed", "sentence", "recursive", "recursive350")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding", choices=["local", "lexical", "mock"], default="lexical")
    args = parser.parse_args()

    embedder, backend = select_embedder(args.embedding)
    print(f"embedder={backend}")
    for name in STRATEGIES:
        store = build_knowledge_base(
            ROOT / "data" / "md",
            embedding_fn=embedder,
            chunker=select_chunker(name),
            collection_name=f"compare_{args.embedding}_{name}",
        )
        hits = []
        for benchmark in BENCHMARKS:
            query, metadata_filter = retrieval_settings(benchmark, args.embedding)
            results = (
                store.search_with_filter(
                    query, top_k=3, metadata_filter=metadata_filter
                )
                if metadata_filter
                else store.search(query, top_k=3)
            )
            hits.append(any(is_relevant_result(item, benchmark) for item in results))
        print(
            f"{name}: chunks={store.get_collection_size()}, "
            f"evidence_hits={sum(hits)}/5, "
            f"queries={','.join('Y' if hit else 'N' for hit in hits)}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
