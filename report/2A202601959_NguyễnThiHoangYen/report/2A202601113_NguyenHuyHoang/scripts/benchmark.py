#!/usr/bin/env python3
"""Chạy 5 câu hỏi đánh giá của nhóm PRAI trên corpus `data/md`.

Bộ câu hỏi + gold answer là bộ chung của nhóm; mọi thành viên chạy CÙNG bộ này,
chỉ khác chiến lược chunking truyền vào.

Mặc định là chiến lược tôi phụ trách trong nhóm — SentenceChunker, 3 câu/chunk.
Chạy không cần cờ nào, không cần PYTHONPATH, không cần biến môi trường:

    python scripts/benchmark.py

Các biến thể dùng để so sánh trong báo cáo:

    python scripts/benchmark.py --max-sentences 5      # tinh chỉnh số câu/chunk
    python scripts/benchmark.py --chunker legal --chunk-size 900
    python scripts/benchmark.py --top-k 10             # nới top-k
    python scripts/benchmark.py --provider mock        # đối chứng: điểm ngẫu nhiên
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

# Chạy được từ bất kỳ thư mục nào và bất kỳ shell nào, không cần đặt PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Console Windows mặc định là cp1252 và không in được tiếng Việt.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv  # noqa: E402

from ingest import build_knowledge_base  # noqa: E402
from src import (
    FixedSizeChunker,
    HeadingChunker,
    KnowledgeBaseAgent,
    LegalArticleChunker,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
)
from src.embeddings import (
    EMBEDDING_PROVIDER_ENV,
    LOCAL_EMBEDDING_MODEL,
    OPENAI_EMBEDDING_MODEL,
    LocalEmbedder,
    OpenAIEmbedder,
)

DATA_DIR = "data/md"

# 5 câu hỏi đánh giá của nhóm — xem REPORT_NHOM.md §3 để đối chiếu gold answer.
# Mỗi câu rơi vào MỘT tài liệu khác nhau và `gold_snippet` đã được kiểm chứng là
# chuỗi DUY NHẤT trong corpus, nên chấm điểm không bị nhập nhằng giữa hai văn bản.
QUERIES: list[dict] = [
    {
        "id": 1,
        "query": "Mức hỗ trợ sinh hoạt phí tối thiểu cho sinh viên là bao nhiêu một tháng?",
        "gold": "Tối thiểu 2 triệu đồng/tháng, hỗ trợ trong cả khóa học (4 năm học)",
        "gold_doc": "4618-nam-2024-quy-dinh-hoc-bong-vnu",
        "gold_snippet": "2 triệu đồng/tháng",
        "filter": None,
    },
    {
        "id": 2,
        "query": "Sinh viên cần điểm trung bình học kỳ bao nhiêu để được xét học bổng loại xuất sắc?",
        "gold": "Điểm trung bình học kỳ từ 3,60 trở lên và điểm rèn luyện đạt loại xuất sắc",
        "gold_doc": "970-nam-hoc-2023-2024",
        "gold_snippet": "3,60",
        "filter": None,
    },
    {
        "id": 3,
        "query": "Kết quả rèn luyện của sinh viên được phân thành mấy loại?",
        "gold": "05 loại: xuất sắc, tốt, khá, trung bình và yếu (xuất sắc từ 90 đến 100 điểm)",
        "gold_doc": "40-2026-tt-bgddt",
        "gold_snippet": "05 loại",
        "filter": None,
    },
    {
        "id": 4,
        "query": "Nhiệm vụ của sinh viên được quy định như thế nào trong quy chế công tác học sinh, sinh viên?",
        "gold": "Điều 4 — Nhiệm vụ của sinh viên, Thông tư 10/2016/TT-BGDĐT",
        "gold_doc": "10-2016-tt-bgddt-ve-quy-che-cong-tac-hssv",
        "gold_snippet": "Nhiệm vụ của sinh viên",
        "filter": {"audience": "student"},
    },
    {
        "id": 5,
        "query": "Những đối tượng nào được giảm 70% học phí?",
        "gold": "Điều 16 Nghị định 81/2021/NĐ-CP: học sinh, sinh viên học các ngành nghệ thuật truyền thống và đặc thù",
        "gold_doc": "81signed",
        "gold_snippet": "giảm 70% học phí",
        "filter": None,
    },
]

# `size` mang nghĩa khác nhau tuỳ chiến lược: số ký tự với các chunker cắt theo
# độ dài, và SỐ CÂU với SentenceChunker (xem --max-sentences).
CHUNKERS = {
    "fixed": lambda size: FixedSizeChunker(chunk_size=size, overlap=size // 8),
    "sentence": lambda size: SentenceChunker(max_sentences_per_chunk=size),
    "recursive": lambda size: RecursiveChunker(chunk_size=size),
    "heading": lambda size: HeadingChunker(max_chunk_size=size),
    "legal": lambda size: LegalArticleChunker(max_chunk_size=size),
}


def select_embedder(provider: str | None = None):
    """Chọn backend nhúng: tham số --provider, nếu không thì EMBEDDING_PROVIDER."""
    load_dotenv(override=False)
    provider = (provider or os.getenv(EMBEDDING_PROVIDER_ENV, "mock")).strip().lower()
    if provider == "local":
        try:
            return LocalEmbedder(model_name=os.getenv("LOCAL_EMBEDDING_MODEL", LOCAL_EMBEDDING_MODEL))
        except Exception as error:
            print(f"[!] Local embedder không sẵn sàng ({error}); dùng mock.", file=sys.stderr)
    elif provider == "openai":
        try:
            return OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", OPENAI_EMBEDDING_MODEL))
        except Exception as error:
            print(f"[!] OpenAI embedder không sẵn sàng ({error}); dùng mock.", file=sys.stderr)
    return _mock_embed


def _tokens(text: str) -> set[str]:
    return {t for t in re.split(r"\W+", text.lower()) if len(t) > 1}


def extractive_llm(prompt: str) -> str:
    """LLM thay thế: trích câu khớp nhất với câu hỏi trong chunk hạng 1.

    Lab này chấm chất lượng TRUY XUẤT, và repo không kèm API key. Hàm này giữ
    cho câu trả lời luôn bám ngữ cảnh (grounded 100%, không bịa) để có thể đánh
    giá thủ công xem chunk truy xuất được có chứa gold answer hay không.

    Phiên bản đầu cắt 300 ký tự ĐẦU chunk, và trượt khi thông tin cần nằm ở cuối
    (ví dụ "khoảng 500 sinh viên" ở vị trí 369/400). Nay chấm điểm từng câu theo
    số từ trùng với câu hỏi rồi trả về câu tốt nhất kèm câu liền sau làm ngữ cảnh.
    """
    marker = "NGỮ CẢNH:\n"
    if marker not in prompt:
        return "(không dựng được ngữ cảnh)"

    context = prompt.split(marker, 1)[1].split("\n\nCÂU HỎI:", 1)[0]
    chunk = context.split("\n\n[2]", 1)[0].strip()
    question = prompt.split("CÂU HỎI: ", 1)[1].split("\n", 1)[0] if "CÂU HỎI: " in prompt else ""

    sentences = [s.strip() for s in re.split(r"(?<=[.!?:])\s+|\n", chunk) if len(s.strip()) > 25]
    if not sentences:
        return chunk[:300].replace("\n", " ")

    query_tokens = _tokens(question)
    scored = [(len(query_tokens & _tokens(s)), index) for index, s in enumerate(sentences)]
    best_score, best = max(scored)
    if best_score == 0:
        return chunk[:300].replace("\n", " ")

    answer = " ".join(sentences[best : best + 2])
    return answer[:400].replace("\n", " ")


def main() -> int:
    parser = argparse.ArgumentParser(description="Chạy 5 benchmark query của nhóm PRAI.")
    parser.add_argument("--chunker", choices=sorted(CHUNKERS), default="sentence")
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--max-sentences", type=int, default=3,
                        help="số câu/chunk cho --chunker sentence (mặc định: 3)")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--provider", choices=["mock", "local", "openai"], default="local",
                        help="backend nhúng (mặc định: local — mock chỉ để kiểm tra pipeline)")
    args = parser.parse_args()

    if not Path(DATA_DIR).exists():
        print(f"Không tìm thấy {DATA_DIR}", file=sys.stderr)
        return 1

    embedder = select_embedder(args.provider)
    backend = getattr(embedder, "_backend_name", type(embedder).__name__)
    size = args.max_sentences if args.chunker == "sentence" else args.chunk_size
    chunker = CHUNKERS[args.chunker](size)

    store = build_knowledge_base(DATA_DIR, embedding_fn=embedder, chunker=chunker)
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)

    print("=" * 78)
    print(f"Backend nhúng : {backend}")
    unit = "câu/chunk" if args.chunker == "sentence" else "ký tự"
    print(f"Chiến lược    : {args.chunker} ({size} {unit}), top_k={args.top_k}")
    print(f"Corpus        : {store.get_collection_size()} chunk từ {DATA_DIR}")
    is_mock = backend == "mock embeddings fallback"
    if is_mock:
        print("[!] MOCK — điểm gần như ngẫu nhiên, KHÔNG dùng số này cho báo cáo.")
    print("=" * 78)

    hits_top1 = hits_top3 = 0
    snip_top1 = snip_top3 = 0
    answers_with_gold = 0
    for item in QUERIES:
        if item["filter"]:
            results = store.search_with_filter(item["query"], top_k=args.top_k, metadata_filter=item["filter"])
            tag = f"  [filter={item['filter']}]"
        else:
            results = store.search(item["query"], top_k=args.top_k)
            tag = ""

        retrieved_docs = [r["metadata"].get("doc_id") for r in results]
        in_top1 = bool(retrieved_docs) and retrieved_docs[0] == item["gold_doc"]
        in_top3 = item["gold_doc"] in retrieved_docs
        hits_top1 += in_top1
        hits_top3 += in_top3

        # Thước đo mịn hơn: chunk có thực sự CHỨA gold answer không, thay vì
        # chỉ đến từ đúng tài liệu. Với corpus nhỏ, chỉ số cấp tài liệu bão hòa.
        snippet = item["gold_snippet"]
        snip_in_top1 = bool(results) and snippet in results[0]["content"]
        snip_in_top3 = any(snippet in r["content"] for r in results)
        snip_top1 += snip_in_top1
        snip_top3 += snip_in_top3

        print(f"\nQ{item['id']}{tag}: {item['query']}")
        print(f"  Gold      : {item['gold']}")
        print(f"  Gold doc  : {item['gold_doc']}  ->  top1={'CO' if in_top1 else 'KHONG'}  top3={'CO' if in_top3 else 'KHONG'}")
        print(f"  Gold text : \"{snippet}\"  ->  top1={'CO' if snip_in_top1 else 'KHONG'}  top3={'CO' if snip_in_top3 else 'KHONG'}")
        for rank, result in enumerate(results, start=1):
            mark = "*" if snippet in result["content"] else (
                "~" if result["metadata"].get("doc_id") == item["gold_doc"] else " "
            )
            preview = result["content"][:64].replace("\n", " ")
            print(f"   {mark}#{rank} {result['score']:+.3f} {result['metadata'].get('doc_id'):26s} {preview}")
        answer = agent.answer(item["query"], top_k=args.top_k)
        has_gold = snippet in answer
        print(f"  Agent [{'DUNG   ' if has_gold else 'THIEU  '}]: {answer}")
        answers_with_gold += has_gold

    total = len(QUERIES)
    print("\n" + "=" * 78)
    print(f"[tai lieu] Gold doc  trong top-1: {hits_top1}/{total}   |   top-3: {hits_top3}/{total}")
    print(f"[chunk   ] Gold text trong top-1: {snip_top1}/{total}   |   top-3: {snip_top3}/{total}")
    print(f"[agent   ] Cau tra loi CHUA gold text: {answers_with_gold}/{total}")
    print("=" * 78)
    if is_mock:
        # Cảnh báo lặp lại ở cuối: người đọc thường chỉ nhìn phần kết quả.
        print("\n" + "!" * 78)
        print("! BACKEND = MOCK. Điểm trên gần như NGẪU NHIÊN và vô nghĩa.")
        print("! MockEmbedder băm MD5 cả chuỗi nên vector không mang ngữ nghĩa.")
        print("! Chạy lại bằng embedder thật:  python scripts/benchmark.py --provider local")
        print("!" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
