"""Deterministic character-based chunking with stable source metadata."""

import hashlib
import re
from dataclasses import dataclass

from app.ingestion.text_normalization import NormalizedDocument

_TOKEN_PATTERN = re.compile(r"\S+")


@dataclass(frozen=True, slots=True)
class ChunkingConfig:
    """Validated deterministic character-window configuration."""

    chunk_size: int
    overlap: int

    def __post_init__(self) -> None:
        if isinstance(self.chunk_size, bool) or not isinstance(self.chunk_size, int):
            raise ValueError("chunk_size must be an integer.")
        if isinstance(self.overlap, bool) or not isinstance(self.overlap, int):
            raise ValueError("overlap must be an integer.")
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero.")
        if self.overlap < 0:
            raise ValueError("overlap must be non-negative.")
        if self.overlap >= self.chunk_size:
            raise ValueError("overlap must be smaller than chunk_size.")


@dataclass(frozen=True, slots=True)
class TextChunk:
    """One stable ordered chunk derived from normalized source text."""

    chunk_index: int
    text: str
    token_count: int
    start_offset: int
    end_offset: int
    content_hash: str
    page_numbers: tuple[int, ...]

    def __post_init__(self) -> None:
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be non-negative.")
        if not self.text:
            raise ValueError("A text chunk cannot be empty.")
        if self.token_count < 0:
            raise ValueError("token_count must be non-negative.")
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError("Chunk offsets must describe a non-empty range.")
        if len(self.content_hash) != 64:
            raise ValueError("content_hash must be a SHA-256 hexadecimal digest.")
        if any(page_number < 1 for page_number in self.page_numbers):
            raise ValueError("page_numbers must be one-based.")


class DeterministicChunker:
    """Split normalized text deterministically, preferring textual boundaries."""

    def __init__(self, config: ChunkingConfig) -> None:
        self._config = config

    def chunk(self, document: NormalizedDocument) -> tuple[TextChunk, ...]:
        text = document.text
        chunks: list[TextChunk] = []
        next_start = 0

        while next_start < len(text):
            start_offset = self._skip_whitespace(text, next_start)
            if start_offset >= len(text):
                break

            hard_end = min(start_offset + self._config.chunk_size, len(text))
            selected_end = self._select_end(text, start_offset, hard_end)
            end_offset = self._trim_trailing_whitespace(text, start_offset, selected_end)
            if end_offset <= start_offset:
                next_start = max(selected_end, start_offset + 1)
                continue

            chunk_text = text[start_offset:end_offset]
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    text=chunk_text,
                    token_count=len(_TOKEN_PATTERN.findall(chunk_text)),
                    start_offset=start_offset,
                    end_offset=end_offset,
                    content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
                    page_numbers=self._page_numbers(
                        document,
                        start_offset=start_offset,
                        end_offset=end_offset,
                    ),
                )
            )

            if end_offset == len(text):
                break
            next_start = max(
                end_offset - self._config.overlap,
                start_offset + 1,
            )

        return tuple(chunks)

    def _select_end(self, text: str, start_offset: int, hard_end: int) -> int:
        if hard_end == len(text):
            return hard_end

        minimum_boundary = start_offset + max(
            self._config.overlap + 1,
            self._config.chunk_size // 2,
        )
        if minimum_boundary >= hard_end:
            return hard_end

        paragraph_boundary = text.rfind("\n\n", minimum_boundary, hard_end)
        if paragraph_boundary >= minimum_boundary:
            return paragraph_boundary

        line_boundary = text.rfind("\n", minimum_boundary, hard_end)
        if line_boundary >= minimum_boundary:
            return line_boundary

        sentence_boundary = max(
            text.rfind(". ", minimum_boundary, hard_end),
            text.rfind("! ", minimum_boundary, hard_end),
            text.rfind("? ", minimum_boundary, hard_end),
        )
        if sentence_boundary >= minimum_boundary:
            return sentence_boundary + 1

        whitespace_boundary = max(
            text.rfind(" ", minimum_boundary, hard_end),
            text.rfind("\t", minimum_boundary, hard_end),
        )
        if whitespace_boundary >= minimum_boundary:
            return whitespace_boundary

        return hard_end

    @staticmethod
    def _skip_whitespace(text: str, start_offset: int) -> int:
        while start_offset < len(text) and text[start_offset].isspace():
            start_offset += 1
        return start_offset

    @staticmethod
    def _trim_trailing_whitespace(text: str, start_offset: int, end_offset: int) -> int:
        while end_offset > start_offset and text[end_offset - 1].isspace():
            end_offset -= 1
        return end_offset

    @staticmethod
    def _page_numbers(
        document: NormalizedDocument,
        *,
        start_offset: int,
        end_offset: int,
    ) -> tuple[int, ...]:
        page_numbers: list[int] = []
        for span in document.source_spans:
            if span.start_offset >= end_offset or span.end_offset <= start_offset:
                continue
            if span.page_number is not None and span.page_number not in page_numbers:
                page_numbers.append(span.page_number)
        return tuple(page_numbers)
