"""Nap corpus quy dinh sinh vien vao EmbeddingStore va chay 5 benchmark queries."""

from __future__ import annotations

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
DIMENSION = 1024


def lexical_embed(text: str) -> list[float]:
    """Embedding cuc bo theo token, phu hop de benchmark khong can tai model ngoai."""
    vector = [0.0] * DIMENSION
    normalized = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    normalized = "".join(char for char in normalized if not unicodedata.combining(char))
    tokens = TOKEN_RE.findall(normalized)
    features = tokens + [f"{left}_{right}" for left, right in zip(tokens, tokens[1:])]
    for token in features:
        index = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16) % DIMENSION
        vector[index] += 1.0
    magnitude = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / magnitude for value in vector]


BENCHMARKS = [
    {
        "id": "q1",
        "query": "Sinh vien phai dong hoc phi va bao hiem y te day du, dung thoi han khong?",
        "gold_answer": "Sinh vien phai dong hoc phi va bao hiem y te day du, dung thoi han.",
        "expected_doc_ids": [
            "10-2016-tt-bgddt-ve-quy-che-cong-tac-hssv",
            "quy-che-32-ngay-05-1-2017-quy-che-cong-tac-sinh-vien-tai-dai-hoc-quoc-gia-ha-noi",
        ],
    },
    {
        "id": "q2",
        "query": "Khi danh gia ket qua ren luyen, quy trinh va tieu chi can bao dam khach quan, cong khai, cong bang va chinh xac nhu the nao?",
        "gold_answer": "Danh gia phai dung quy trinh, khach quan, cong khai, cong bang, chinh xac; bao dam binh dang, dan chu va phoi hop cac don vi lien quan.",
        "expected_doc_ids": ["16-2015-tt-bgddt-ve-diem-ren-luyen"],
    },
    {
        "id": "q3",
        "query": "Quy dinh quan ly va su dung hoc bong cua Dai hoc Quoc gia Ha Noi ap dung doi voi hoc sinh, sinh vien, hoc vien cao hoc va nghien cuu sinh nao?",
        "gold_answer": "Ap dung cho hoc sinh, sinh vien, hoc vien cao hoc, nghien cuu sinh cua DHQGHN va cac don vi, bo phan chuc nang lien quan.",
        "expected_doc_ids": ["4618-nam-2024-quy-dinh-hoc-bong-vnu"],
    },
    {
        "id": "q4",
        "query": "Hoc phi tu nam hoc 2023 2024 cua co so giao duc chua tu bao dam chi thuong xuyen duoc quy dinh nhu the nao?",
        "gold_answer": "Giu on dinh bang muc thu hoc phi nam hoc 2021-2022 do Hoi dong nhan dan tinh da ban hanh tai dia phuong.",
        "expected_doc_ids": ["97-cpsigned"],
    },
    {
        "id": "q5",
        "query": "Sinh vien chuong trinh cu nhan khoa hoc tai nang nao duoc xet cap hoc bong ho tro chi phi hoc tap?",
        "gold_answer": "Sinh vien cac chuong trinh cu nhan khoa hoc tai nang Toan hoc, Vat ly, Hoa hoc va Sinh hoc duoc xet cap hoc bong ho tro chi phi hoc tap.",
        "expected_doc_ids": ["970-nam-hoc-2023-2024"],
        "metadata_filter": {"category": "scholarship"},
    },
]


def main() -> None:
    store = build_knowledge_base(
        "data/md",
        embedding_fn=lexical_embed,
        chunker=RecursiveChunker(chunk_size=500),
        collection_name="student_regulations_benchmark",
    )
    print(f"collection_size={store.get_collection_size()}")
    for benchmark in BENCHMARKS:
        filter_value = benchmark.get("metadata_filter")
        if filter_value:
            results = store.search_with_filter(benchmark["query"], top_k=3, metadata_filter=filter_value)
        else:
            results = store.search(benchmark["query"], top_k=3)
        hit = any(item["metadata"].get("doc_id") in benchmark["expected_doc_ids"] for item in results)
        print(f"{benchmark['id']} hit_top3={hit}")
        for rank, item in enumerate(results, start=1):
            snippet = " ".join(item["content"].split())[:180]
            print(
                f"  {rank}. doc_id={item['metadata'].get('doc_id')} "
                f"chunk={item['metadata'].get('chunk_index')} score={item['score']:.4f}\n"
                f"     {snippet}"
            )


if __name__ == "__main__":
    main()
