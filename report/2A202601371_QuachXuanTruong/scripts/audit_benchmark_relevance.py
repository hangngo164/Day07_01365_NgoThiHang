"""Show the rank of every gold-evidence chunk for a chosen configuration."""

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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding", choices=["local", "lexical", "mock"], default="lexical")
    parser.add_argument(
        "--chunker",
        choices=["fixed", "sentence", "recursive", "recursive350", "regulation"],
        default="recursive350",
    )
    args = parser.parse_args()

    embedder, backend = select_embedder(args.embedding)
    store = build_knowledge_base(
        ROOT / "data" / "md",
        embedding_fn=embedder,
        chunker=select_chunker(args.chunker),
        collection_name=f"audit_{args.embedding}_{args.chunker}",
    )
    print(f"embedder={backend}; chunker={args.chunker}")
    for benchmark in BENCHMARKS:
        query, metadata_filter = retrieval_settings(benchmark, args.embedding)
        results = (
            store.search_with_filter(
                query, top_k=100, metadata_filter=metadata_filter
            )
            if metadata_filter
            else store.search(query, top_k=100)
        )
        evidence = [
            (
                rank,
                item["metadata"].get("doc_id"),
                item["metadata"].get("chunk_index"),
                round(item["score"], 4),
            )
            for rank, item in enumerate(results, start=1)
            if is_relevant_result(item, benchmark)
        ]
        print(f"{benchmark['id']}: {evidence[:3] or 'no evidence in top-100'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
