from __future__ import annotations

import math
import re


class FixedSizeChunker:
    """
    Split text into fixed-size chunks with optional overlap.

    Rules:
        - Each chunk is at most chunk_size characters long.
        - Consecutive chunks share overlap characters.
        - The last chunk contains whatever remains.
        - If text is shorter than chunk_size, return [text].
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50) -> None:
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        if len(text) <= self.chunk_size:
            return [text]

        step = self.chunk_size - self.overlap
        chunks: list[str] = []
        for start in range(0, len(text), step):
            chunk = text[start : start + self.chunk_size]
            chunks.append(chunk)
            if start + self.chunk_size >= len(text):
                break
        return chunks


class SentenceChunker:
    """
    Split text into chunks of at most max_sentences_per_chunk sentences.

    Sentence detection: split on ". ", "! ", "? " or ".\n".
    Strip extra whitespace from each chunk.
    """

    def __init__(self, max_sentences_per_chunk: int = 3) -> None:
        self.max_sentences_per_chunk = max(1, max_sentences_per_chunk)

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip())]
        sentences = [sentence for sentence in sentences if sentence]

        chunks: list[str] = []
        for start in range(0, len(sentences), self.max_sentences_per_chunk):
            group = sentences[start : start + self.max_sentences_per_chunk]
            chunks.append(" ".join(group))
        return chunks


class RecursiveChunker:
    """
    Recursively split text using separators in priority order.

    Default separator priority:
        ["\n\n", "\n", ". ", " ", ""]
    """

    DEFAULT_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def __init__(self, separators: list[str] | None = None, chunk_size: int = 500) -> None:
        self.separators = self.DEFAULT_SEPARATORS if separators is None else list(separators)
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        return self._split(text, self.separators)

    def _split(self, current_text: str, remaining_separators: list[str]) -> list[str]:
        if not current_text:
            return []
        if len(current_text) <= self.chunk_size:
            return [current_text]

        # No usable separator left ("" is the character-level fallback):
        # slice hard so the caller always gets a non-empty result.
        if not remaining_separators or remaining_separators[0] == "":
            return [
                current_text[start : start + self.chunk_size]
                for start in range(0, len(current_text), self.chunk_size)
            ]

        separator = remaining_separators[0]
        rest = remaining_separators[1:]
        pieces = [piece for piece in current_text.split(separator) if piece]
        if len(pieces) <= 1:
            return self._split(current_text, rest)

        chunks: list[str] = []
        buffer = ""
        for piece in pieces:
            candidate = piece if not buffer else buffer + separator + piece
            if len(candidate) <= self.chunk_size:
                buffer = candidate
                continue

            if buffer:
                chunks.append(buffer)
            if len(piece) <= self.chunk_size:
                buffer = piece
            else:
                chunks.extend(self._split(piece, rest))
                buffer = ""

        if buffer:
            chunks.append(buffer)
        return chunks


class HeadingChunker:
    """
    Split Markdown by heading, keeping each section under its own heading.

    Designed for the HUS corpus, where every document is a regulation or a
    service guide organised as `## Section` / `### Sub-section`. A fixed-size
    window cuts across those boundaries and strands a rule half-way through a
    chunk; splitting on headings keeps one rule in one chunk instead.

    The heading text is prepended to every chunk it produces, so a chunk still
    carries its own topic even after the surrounding document is gone — that
    context is what the embedding sees at query time.

    Sections longer than max_chunk_size fall back to RecursiveChunker so no
    chunk grows unbounded.
    """

    HEADING = re.compile(r"^(#{1,6})\s+(.*)$")

    def __init__(self, max_chunk_size: int = 700, min_chunk_size: int = 80) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        sections = self._split_sections(text)
        chunks: list[str] = []
        for heading, body in sections:
            body = body.strip()
            if not body:
                continue

            section = f"{heading}\n{body}" if heading else body
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
                continue

            # Oversized section: split the body, then re-attach the heading so
            # every piece keeps the topic it belongs to.
            splitter = RecursiveChunker(chunk_size=self.max_chunk_size - len(heading) - 1)
            for piece in splitter.chunk(body):
                chunks.append(f"{heading}\n{piece}" if heading else piece)

        return self._merge_tiny(chunks)

    def _split_sections(self, text: str) -> list[tuple[str, str]]:
        """Return (heading_line, body) pairs; heading is "" for text before the first one."""
        sections: list[tuple[str, str]] = []
        heading = ""
        body: list[str] = []

        for line in text.splitlines():
            if self.HEADING.match(line.strip()):
                sections.append((heading, "\n".join(body)))
                heading = line.strip()
                body = []
            else:
                body.append(line)
        sections.append((heading, "\n".join(body)))
        return sections

    def _merge_tiny(self, chunks: list[str]) -> list[str]:
        """Fold a heading-only or near-empty chunk into the next one."""
        merged: list[str] = []
        for chunk in chunks:
            if merged and len(chunk) < self.min_chunk_size:
                merged[-1] = f"{merged[-1]}\n\n{chunk}"
            else:
                merged.append(chunk)
        return merged


class LegalArticleChunker:
    """
    Split Vietnamese legal documents on `Điều N` boundaries.

    The group corpus is Thông tư / Nghị định / Quy chế converted from PDF. That
    conversion emits `## Trang N` headings, so splitting on Markdown headings
    cuts on *page* boundaries — an arbitrary line that carries no meaning and
    strands an article across two chunks. The real unit of a Vietnamese legal
    text is the article (`Điều 16. Đối tượng được giảm học phí…`), so this
    chunker cuts there instead and drops the pagination markers entirely.

    Each chunk is prefixed with its chapter and article heading, so a chunk
    still states which rule it belongs to once it leaves the document.
    """

    PAGE_MARKER = re.compile(r"^#{1,6}\s*Trang\s*\d+\s*$", re.MULTILINE)
    ARTICLE = re.compile(r"^\s*(Điều\s+\d+)\s*[.:]?\s*(.*)$")
    CHAPTER = re.compile(r"^\s*(Chương\s+[IVXLC]+|Chương\s+\d+)\s*[.:]?\s*(.*)$")

    def __init__(self, max_chunk_size: int = 900, min_chunk_size: int = 80) -> None:
        self.max_chunk_size = max_chunk_size
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []

        text = self.PAGE_MARKER.sub("", text)

        chapter = ""
        heading = ""
        body: list[str] = []
        sections: list[tuple[str, str]] = []

        for line in text.splitlines():
            chapter_match = self.CHAPTER.match(line)
            if chapter_match:
                chapter = " ".join(part for part in chapter_match.groups() if part).strip()
                continue

            article_match = self.ARTICLE.match(line)
            if article_match:
                sections.append((self._label(chapter, heading), "\n".join(body)))
                heading = " ".join(part for part in article_match.groups() if part).strip()
                body = []
            else:
                body.append(line)
        sections.append((self._label(chapter, heading), "\n".join(body)))

        chunks: list[str] = []
        for label, section_body in sections:
            section_body = section_body.strip()
            if not section_body:
                continue

            section = f"{label}\n{section_body}" if label else section_body
            if len(section) <= self.max_chunk_size:
                chunks.append(section)
                continue

            splitter = RecursiveChunker(chunk_size=max(self.max_chunk_size - len(label) - 1, 100))
            for piece in splitter.chunk(section_body):
                chunks.append(f"{label}\n{piece}" if label else piece)

        return self._merge_tiny(chunks)

    @staticmethod
    def _label(chapter: str, heading: str) -> str:
        return " — ".join(part for part in (chapter, heading) if part)

    def _merge_tiny(self, chunks: list[str]) -> list[str]:
        merged: list[str] = []
        for chunk in chunks:
            if merged and len(chunk) < self.min_chunk_size:
                merged[-1] = f"{merged[-1]}\n\n{chunk}"
            else:
                merged.append(chunk)
        return merged


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def compute_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """
    Compute cosine similarity between two vectors.

    cosine_similarity = dot(a, b) / (||a|| * ||b||)

    Returns 0.0 if either vector has zero magnitude.
    """
    if not vec_a or not vec_b:
        return 0.0

    norm_a = math.sqrt(_dot(vec_a, vec_a))
    norm_b = math.sqrt(_dot(vec_b, vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return _dot(vec_a, vec_b) / (norm_a * norm_b)


class ChunkingStrategyComparator:
    """Run all built-in chunking strategies and compare their results."""

    def compare(self, text: str, chunk_size: int = 200) -> dict:
        strategies = {
            "fixed_size": FixedSizeChunker(chunk_size=chunk_size, overlap=chunk_size // 10),
            "by_sentences": SentenceChunker(max_sentences_per_chunk=3),
            "recursive": RecursiveChunker(chunk_size=chunk_size),
        }

        comparison: dict = {}
        for name, chunker in strategies.items():
            chunks = chunker.chunk(text)
            total_length = sum(len(chunk) for chunk in chunks)
            comparison[name] = {
                "count": len(chunks),
                "avg_length": (total_length / len(chunks)) if chunks else 0.0,
                "chunks": chunks,
            }
        return comparison
