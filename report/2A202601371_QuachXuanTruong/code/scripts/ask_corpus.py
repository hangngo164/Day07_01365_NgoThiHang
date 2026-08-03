"""Interactive grounded retrieval over the regulations corpus, without an LLM API."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import build_knowledge_base
from scripts.run_retrieval_benchmark import select_chunker, select_embedder


def show_results(store, question: str, metadata_filter: dict[str, str]) -> None:
    results = (
        store.search_with_filter(question, top_k=3, metadata_filter=metadata_filter)
        if metadata_filter
        else store.search(question, top_k=3)
    )
    if not results:
        print("Không tìm thấy đoạn tài liệu phù hợp.")
        return

    print("\nCác đoạn nguồn liên quan:")
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        print(f"\n[{rank}] {metadata.get('title', metadata.get('doc_id'))}")
        print(
            f"    doc_id: {metadata.get('doc_id')} | "
            f"chunk: {metadata.get('chunk_index')} | score: {result['score']:.4f}"
        )
        print(f"    source: {metadata.get('source_url', 'không có URL')}")
        print("    " + "\n    ".join(result["content"].strip().splitlines()))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tra cứu corpus quy định bằng semantic retrieval hoặc baseline lexical."
    )
    parser.add_argument("question", nargs="*", help="Câu hỏi; bỏ trống để nhập liên tục.")
    parser.add_argument("--embedding", choices=["local", "lexical", "mock"], default="lexical")
    parser.add_argument(
        "--chunker",
        choices=["fixed", "sentence", "recursive", "recursive350", "regulation"],
        default="recursive350",
    )
    parser.add_argument("--category")
    parser.add_argument("--audience", choices=["student", "staff", "faculty", "all"])
    args = parser.parse_args()

    embedder, backend = select_embedder(args.embedding)
    store = build_knowledge_base(
        ROOT / "data" / "md",
        embedding_fn=embedder,
        chunker=select_chunker(args.chunker),
        collection_name=f"corpus_qa_{args.embedding}_{args.chunker}",
    )
    metadata_filter = {
        key: value
        for key, value in {"category": args.category, "audience": args.audience}.items()
        if value
    }
    print(
        f"Đã nạp {store.get_collection_size()} chunk | "
        f"embedder={backend} | chunker={args.chunker}"
    )
    if metadata_filter:
        print(f"Lọc metadata: {metadata_filter}")

    initial_question = " ".join(args.question).strip()
    if initial_question:
        show_results(store, initial_question, metadata_filter)
        return 0

    while True:
        question = input("\nCâu hỏi (gõ exit để thoát): ").strip()
        if question.casefold() in {"exit", "quit", "thoát"}:
            return 0
        if question:
            show_results(store, question, metadata_filter)


if __name__ == "__main__":
    raise SystemExit(main())
