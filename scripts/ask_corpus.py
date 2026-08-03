"""Hoi dap khong dung LLM: truy xuat va hien thi cac doan nguon lien quan."""

from __future__ import annotations

import argparse
import hashlib
import math
import re
import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ingest import build_knowledge_base
from src.chunking import RecursiveChunker


TOKEN_RE = re.compile(r"[\wÀ-ỹ]+", re.UNICODE)
DIMENSION = 4096


def lexical_embed(text: str) -> list[float]:
    """Tao vector token va bigram, co bo dau de query co/khong dau deu tim duoc."""
    normalized = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    tokens = TOKEN_RE.findall(normalized)
    features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
    vector = [0.0] * DIMENSION
    for feature in features:
        index = int(hashlib.sha256(feature.encode("utf-8")).hexdigest(), 16) % DIMENSION
        vector[index] += 1.0
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


def show_results(store, question: str, category: str | None) -> None:
    if category:
        results = store.search_with_filter(question, top_k=3, metadata_filter={"category": category})
    else:
        results = store.search(question, top_k=3)

    if not results:
        print("Khong tim thay doan tai lieu phu hop.")
        return

    print("\nCac doan tai lieu lien quan:")
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        print(f"\n[{rank}] {metadata.get('title', metadata.get('doc_id'))}")
        print(f"    doc_id: {metadata.get('doc_id')} | score: {result['score']:.3f}")
        print(f"    source: {metadata.get('source_url', 'khong co URL')}")
        print("    " + "\n    ".join(result["content"].strip().splitlines()))


def main() -> None:
    parser = argparse.ArgumentParser(description="Tra cuu corpus quy dinh sinh vien khong dung LLM.")
    parser.add_argument("question", nargs="*", help="Cau hoi can tra cuu. Bo trong de vao che do nhap lien tuc.")
    parser.add_argument("--category", choices=["scholarship", "tuition", "conduct-evaluation", "student-affairs"])
    args = parser.parse_args()

    store = build_knowledge_base(
        ROOT / "data" / "md",
        embedding_fn=lexical_embed,
        chunker=RecursiveChunker(chunk_size=500),
        collection_name="student_regulations_qa",
    )
    print(f"Da nap {store.get_collection_size()} chunk. Nhap 'exit' de ket thuc.")

    initial_question = " ".join(args.question).strip()
    if initial_question:
        show_results(store, initial_question, args.category)
        return

    while True:
        question = input("\nCau hoi: ").strip()
        if question.lower() in {"exit", "quit", "thoat"}:
            break
        if question:
            show_results(store, question, args.category)


if __name__ == "__main__":
    main()
