"""Run an individual Phase 2 configuration on the shared five questions."""

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
        collection_name=f"individual_{args.embedding}_{args.chunker}",
    )
    print(
        f"embedder={backend}\nchunker={args.chunker}\n"
        f"collection_size={store.get_collection_size()}"
    )
    for benchmark in BENCHMARKS:
        query, metadata_filter = retrieval_settings(benchmark, args.embedding)
        results = (
            store.search_with_filter(
                query, top_k=3, metadata_filter=metadata_filter
            )
            if metadata_filter
            else store.search(query, top_k=3)
        )
        hit = any(is_relevant_result(item, benchmark) for item in results)
        if not results:
            print(f"\n{benchmark['id']} evidence_top3={hit}; no results")
            continue
        top = results[0]
        preview = " ".join(top["content"].split())[:220]
        print(
            f"\n{benchmark['id']} evidence_top3={hit} "
            f"doc_id={top['metadata'].get('doc_id')} "
            f"chunk={top['metadata'].get('chunk_index')} "
            f"score={top['score']:.4f}\n{preview}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
