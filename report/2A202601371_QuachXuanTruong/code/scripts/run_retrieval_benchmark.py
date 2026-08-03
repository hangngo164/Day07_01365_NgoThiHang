"""Run the five shared benchmarks with semantic or reproducible embeddings."""

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
from src import (
    FixedSizeChunker,
    LocalEmbedder,
    RecursiveChunker,
    RegulationSectionChunker,
    SentenceChunker,
    _mock_embed,
)


TOKEN_RE = re.compile(r"[\wÀ-ỹ]+", re.UNICODE)
DIMENSION = 4096


def normalize_text(text: str) -> str:
    """Normalize accents and whitespace for OCR-tolerant evidence checks."""
    normalized = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def lexical_embed(text: str) -> list[float]:
    """Deterministic token/bigram baseline that runs without model downloads."""
    vector = [0.0] * DIMENSION
    tokens = TOKEN_RE.findall(normalize_text(text))
    features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
    for feature in features:
        index = int(hashlib.sha256(feature.encode("utf-8")).hexdigest(), 16) % DIMENSION
        vector[index] += 1.0
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


BENCHMARKS = [
    {
        "id": "q1",
        "query": "Sinh vien phai dong hoc phi va bao hiem y te day du, dung thoi han khong?",
        "semantic_query": "Sinh viên phải đóng học phí và bảo hiểm y tế đầy đủ, đúng thời hạn như thế nào?",
        "semantic_filter": {"category": "student-affairs"},
        "gold_answer": "Sinh vien phai dong hoc phi va bao hiem y te day du, dung thoi han.",
        "expected_doc_ids": [
            "10-2016-tt-bgddt-ve-quy-che-cong-tac-hssv",
            "quy-che-32-ngay-05-1-2017-quy-che-cong-tac-sinh-vien-tai-dai-hoc-quoc-gia-ha-noi",
        ],
        "evidence_markers": ["dong hoc phi bao hiem y te"],
    },
    {
        "id": "q2",
        "query": "Khi danh gia ket qua ren luyen, quy trinh va tieu chi can bao dam khach quan, cong khai, cong bang va chinh xac nhu the nao?",
        "semantic_query": "Khi đánh giá kết quả rèn luyện, quy trình và tiêu chí cần bảo đảm khách quan, công khai, công bằng và chính xác như thế nào?",
        "semantic_filter": {"category": "conduct-evaluation"},
        "gold_answer": "Danh gia phai dung quy trinh, khach quan, cong khai, cong bang, chinh xac; bao dam binh dang, dan chu va phoi hop cac don vi lien quan.",
        "expected_doc_ids": ["16-2015-tt-bgddt-ve-diem-ren-luyen"],
        "evidence_markers": ["khach quan cong khai cong bang chinh xac"],
    },
    {
        "id": "q3",
        "query": "Quy dinh quan ly va su dung hoc bong cua Dai hoc Quoc gia Ha Noi ap dung doi voi hoc sinh, sinh vien, hoc vien cao hoc va nghien cuu sinh nao?",
        "semantic_query": "Quy định quản lý và sử dụng học bổng của Đại học Quốc gia Hà Nội áp dụng đối với học sinh, sinh viên, học viên cao học và nghiên cứu sinh nào?",
        "semantic_filter": {"category": "scholarship"},
        "gold_answer": "Ap dung cho hoc sinh, sinh vien, hoc vien cao hoc, nghien cuu sinh cua DHQGHN va cac don vi, bo phan chuc nang lien quan.",
        "expected_doc_ids": ["4618-nam-2024-quy-dinh-hoc-bong-vnu"],
        "evidence_markers": ["ap dung doi voi hoc sinh sinh vien hoc vien cao"],
    },
    {
        "id": "q4",
        "query": "Hoc phi tu nam hoc 2023 2024 cua co so giao duc chua tu bao dam chi thuong xuyen duoc quy dinh nhu the nao?",
        "semantic_query": "Học phí từ năm học 2023–2024 của cơ sở chưa tự bảo đảm chi thường xuyên được quy định như thế nào?",
        "semantic_filter": {"category": "tuition"},
        "gold_answer": "Giu on dinh bang muc thu hoc phi nam hoc 2021-2022 do Hoi dong nhan dan tinh da ban hanh tai dia phuong.",
        "expected_doc_ids": ["97-cpsigned"],
        "evidence_markers": ["giu on dinh muc thu hoc phi"],
    },
    {
        "id": "q5",
        "query": "Sinh vien chuong trinh cu nhan khoa hoc tai nang nao duoc xet cap hoc bong ho tro chi phi hoc tap?",
        "semantic_query": "Sinh viên chương trình cử nhân khoa học tài năng nào được xét học bổng hỗ trợ chi phí học tập?",
        "semantic_filter": {"category": "scholarship"},
        "gold_answer": "Sinh vien cac chuong trinh cu nhan khoa hoc tai nang Toan hoc, Vat ly, Hoa hoc va Sinh hoc duoc xet cap hoc bong ho tro chi phi hoc tap.",
        "expected_doc_ids": ["970-nam-hoc-2023-2024"],
        "evidence_markers": ["vat ly hoc hoa hoc sinh hoc duoc xet cap"],
        "metadata_filter": {"category": "scholarship"},
    },
]


def is_relevant_result(result: dict, benchmark: dict) -> bool:
    """A hit needs both the expected source and an answer-evidence marker."""
    if result.get("metadata", {}).get("doc_id") not in benchmark["expected_doc_ids"]:
        return False
    content = normalize_text(result.get("content", ""))
    return any(marker in content for marker in benchmark["evidence_markers"])


def select_embedder(name: str):
    if name == "lexical":
        return lexical_embed, "lexical token/bigram"
    if name == "mock":
        return _mock_embed, "mock embeddings fallback"
    embedder = LocalEmbedder()
    return embedder, embedder._backend_name


def select_chunker(name: str):
    if name == "fixed":
        return FixedSizeChunker(chunk_size=500, overlap=50)
    if name == "recursive":
        return RecursiveChunker(chunk_size=500)
    if name == "recursive350":
        return RecursiveChunker(chunk_size=350)
    if name == "regulation":
        return RegulationSectionChunker(chunk_size=500)
    return SentenceChunker(max_sentences_per_chunk=3)


def retrieval_settings(benchmark: dict, embedding: str) -> tuple[str, dict | None]:
    """Use accented queries and purposeful metadata filters for semantic retrieval."""
    if embedding == "local":
        return (
            benchmark.get("semantic_query", benchmark["query"]),
            benchmark.get("semantic_filter", benchmark.get("metadata_filter")),
        )
    return benchmark["query"], benchmark.get("metadata_filter")


def run_benchmark(embedding: str = "lexical", chunking: str = "recursive") -> int:
    embedder, backend = select_embedder(embedding)
    store = build_knowledge_base(
        ROOT / "data" / "md",
        embedding_fn=embedder,
        chunker=select_chunker(chunking),
        collection_name=f"benchmark_{embedding}_{chunking}",
    )
    print(
        f"embedder={backend}\nchunker={chunking}\n"
        f"collection_size={store.get_collection_size()}"
    )
    for benchmark in BENCHMARKS:
        query, metadata_filter = retrieval_settings(benchmark, embedding)
        results = (
            store.search_with_filter(
                query, top_k=3, metadata_filter=metadata_filter
            )
            if metadata_filter
            else store.search(query, top_k=3)
        )
        hit = any(is_relevant_result(item, benchmark) for item in results)
        print(f"\n{benchmark['id']} evidence_top3={hit}")
        for rank, item in enumerate(results, start=1):
            preview = " ".join(item["content"].split())[:180]
            print(
                f"  {rank}. score={item['score']:.4f} "
                f"doc_id={item['metadata'].get('doc_id')} "
                f"chunk={item['metadata'].get('chunk_index')}\n"
                f"     {preview}"
            )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--embedding", choices=["local", "lexical", "mock"], default="lexical")
    parser.add_argument(
        "--chunker",
        choices=["fixed", "sentence", "recursive", "recursive350", "regulation"],
        default="recursive",
    )
    args = parser.parse_args()
    return run_benchmark(args.embedding, args.chunker)


if __name__ == "__main__":
    raise SystemExit(main())
