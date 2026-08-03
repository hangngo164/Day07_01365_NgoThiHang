#!/usr/bin/env python3
"""Agent hỏi đáp tương tác trên corpus `data/md` — dùng cho demo Giai đoạn 2.

    python scripts/ask.py

Chạy được từ mọi shell (PowerShell / bash), không cần PYTHONPATH và không cần
biến môi trường. Mặc định dùng embedder local và chiến lược tôi phụ trách trong
nhóm: SentenceChunker, 3 câu/chunk — trùng cấu hình đã báo cáo ở REPORT_CANHAN §5.

Tuỳ chọn:
    --max-sentences 5                     đổi số câu/chunk (chunker sentence)
    --chunker legal --chunk-size 900      đổi sang chiến lược khác
    --top-k 3                             số chunk đưa vào ngữ cảnh
    --audience student                    lọc metadata trước khi tìm kiếm

Lệnh trong phiên:
    :audience student   bật lọc theo đối tượng
    :audience off       tắt lọc
    :k 5                đổi top-k
    :stats              thống kê store
    :quit               thoát
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

# Chạy được từ bất kỳ thư mục nào và bất kỳ shell nào, không cần đặt PYTHONPATH.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from ingest import build_knowledge_base  # noqa: E402
from scripts.benchmark import CHUNKERS, DATA_DIR, extractive_llm, select_embedder  # noqa: E402
from src import KnowledgeBaseAgent  # noqa: E402


def render(results: list[dict]) -> None:
    if not results:
        print("  (không truy xuất được chunk nào — thử tắt lọc bằng `:audience off`)")
        return
    for rank, result in enumerate(results, start=1):
        meta = result["metadata"]
        print(f"  #{rank}  score={result['score']:+.3f}  [{meta.get('audience')}] {meta.get('doc_id')}")
        print(f"      {result['content'][:180].replace(chr(10), ' ')}")
        print(f"      nguồn: {meta.get('source_url')}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Agent hỏi đáp trên corpus HUS.")
    parser.add_argument("--chunker", choices=sorted(CHUNKERS), default="sentence")
    parser.add_argument("--chunk-size", type=int, default=400)
    parser.add_argument("--max-sentences", type=int, default=3,
                        help="số câu/chunk cho --chunker sentence (mặc định: 3)")
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--audience", default=None, help="lọc sẵn theo đối tượng, vd: student")
    parser.add_argument("--data-dir", default=DATA_DIR, help=f"thư mục corpus (mặc định: {DATA_DIR})")
    parser.add_argument("--provider", choices=["mock", "local", "openai"], default="local",
                        help="backend nhúng (mặc định: local)")
    args = parser.parse_args()

    embedder = select_embedder(args.provider)
    backend = getattr(embedder, "_backend_name", type(embedder).__name__)
    # `size` là SỐ CÂU với SentenceChunker, số ký tự với các chunker còn lại.
    size = args.max_sentences if args.chunker == "sentence" else args.chunk_size
    chunker = CHUNKERS[args.chunker](size)

    print(f"Đang nạp {args.data_dir} …")
    store = build_knowledge_base(args.data_dir, embedding_fn=embedder, chunker=chunker)
    agent = KnowledgeBaseAgent(store=store, llm_fn=extractive_llm)

    top_k = args.top_k
    audience = args.audience

    print("=" * 74)
    print(f"Backend nhúng : {backend}")
    unit = "câu/chunk" if args.chunker == "sentence" else "ký tự"
    print(f"Chiến lược    : {args.chunker} ({size} {unit}) → {store.get_collection_size()} chunk")
    if backend == "mock embeddings fallback":
        print("[!] MOCK — kết quả gần như ngẫu nhiên. Đặt EMBEDDING_PROVIDER=local.")
    print("Gõ câu hỏi, hoặc :quit để thoát. :audience student | :k 5 | :stats")
    print("=" * 74)

    while True:
        try:
            line = input("\n❯ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not line:
            continue

        if line in (":quit", ":q", ":exit"):
            return 0
        if line == ":stats":
            docs = Counter(r["metadata"].get("doc_id") for r in store._store)
            print(f"  {store.get_collection_size()} chunk / {len(docs)} tài liệu, top_k={top_k}, lọc={audience or 'off'}")
            for doc_id, count in docs.most_common():
                print(f"    {count:3d}  {doc_id}")
            continue
        if line.startswith(":audience"):
            value = line.split(maxsplit=1)[1].strip() if " " in line else "off"
            audience = None if value in ("off", "none", "-") else value
            print(f"  lọc audience = {audience or 'off'}")
            continue
        if line.startswith(":k"):
            try:
                top_k = max(1, int(line.split()[1]))
                print(f"  top_k = {top_k}")
            except (IndexError, ValueError):
                print("  cú pháp: :k 5")
            continue

        metadata_filter = {"audience": audience} if audience else None
        if metadata_filter:
            results = store.search_with_filter(line, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = store.search(line, top_k=top_k)

        print(f"\n  ── Truy xuất (top-{top_k}{', lọc=' + audience if audience else ''}) ──")
        render(results)

        print("\n  ── Trả lời ──")
        if metadata_filter:
            # KnowledgeBaseAgent.answer() gọi store.search() nên KHÔNG áp dụng
            # metadata_filter. Trả lời trực tiếp từ kết quả đã lọc để phần hiển
            # thị khớp với phần truy xuất ở trên.
            answer = results[0]["content"][:300].replace("\n", " ") if results else "(không có ngữ cảnh)"
            print(f"  {answer}")
            print("  [i] Agent tự nó không nhận metadata_filter — câu trên lấy từ chunk đã lọc.")
        else:
            print(f"  {agent.answer(line, top_k=top_k)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
