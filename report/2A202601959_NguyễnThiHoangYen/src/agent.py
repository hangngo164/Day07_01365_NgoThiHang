from __future__ import annotations

from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        if not question:
            return ""

        context_chunks = self.store.search(question, top_k=top_k)
        if not context_chunks:
            return (
                "No relevant context found in the knowledge store. "
                "Please add documents or try a different question."
            )

        context_lines: list[str] = []
        for index, item in enumerate(context_chunks, start=1):
            content = item.get("content", "").strip()
            metadata = item.get("metadata") or {}
            doc_id = item.get("doc_id") or metadata.get("doc_id") or f"chunk_{index}"
            source = metadata.get("source") or metadata.get("file_path")
            if source:
                context_lines.append(f"[{index}] doc_id={doc_id} source={source}: {content}")
            else:
                context_lines.append(f"[{index}] doc_id={doc_id}: {content}")

        context_text = "\n".join(context_lines)
        
        # 🎯 Đã thêm lại Instruction chính xác theo yêu cầu của Testcase:
        prompt = (
            "Instruction: chỉ dùng context; nói rõ khi context không đủ.\n"
            f"Context:\n{context_text}\n"
            f"Question: {question}\n"
            "Answer:"
        )

        return self.llm_fn(prompt)