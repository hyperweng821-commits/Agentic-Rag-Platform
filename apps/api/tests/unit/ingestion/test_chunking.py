"""Unit tests for deterministic boundary-aware document chunking."""

import hashlib

import pytest

from app.ingestion.chunking import ChunkingConfig, DeterministicChunker
from app.ingestion.document_parsing import ParsedDocument, ParsedSection
from app.ingestion.text_normalization import TextNormalizer


def test_chunk_output_indexes_offsets_and_hashes_are_stable() -> None:
    document = TextNormalizer().normalize(
        ParsedDocument(sections=(ParsedSection(text="abcdefghijklmnopqrstuvwxyz"),))
    )
    chunker = DeterministicChunker(ChunkingConfig(chunk_size=10, overlap=2))

    first = chunker.chunk(document)
    second = chunker.chunk(document)

    assert first == second
    assert [chunk.chunk_index for chunk in first] == [0, 1, 2]
    assert [chunk.text for chunk in first] == [
        "abcdefghij",
        "ijklmnopqr",
        "qrstuvwxyz",
    ]
    assert [(chunk.start_offset, chunk.end_offset) for chunk in first] == [
        (0, 10),
        (8, 18),
        (16, 26),
    ]
    for chunk in first:
        assert document.text[chunk.start_offset : chunk.end_offset] == chunk.text
        assert chunk.content_hash == hashlib.sha256(chunk.text.encode()).hexdigest()


def test_chunker_prefers_paragraph_boundary() -> None:
    document = TextNormalizer().normalize(
        ParsedDocument(
            sections=(
                ParsedSection(
                    text="First paragraph has words.\n\nSecond paragraph also has words."
                ),
            )
        )
    )

    chunks = DeterministicChunker(ChunkingConfig(chunk_size=40, overlap=0)).chunk(document)

    assert chunks[0].text == "First paragraph has words."
    assert chunks[1].text == "Second paragraph also has words."


def test_chunker_applies_overlap_after_textual_boundary() -> None:
    document = TextNormalizer().normalize(
        ParsedDocument(sections=(ParsedSection(text="alpha bravo charlie delta echo foxtrot"),))
    )

    chunks = DeterministicChunker(ChunkingConfig(chunk_size=20, overlap=5)).chunk(document)

    assert chunks[0].text == "alpha bravo charlie"
    assert chunks[1].start_offset == chunks[0].end_offset - 5
    assert chunks[1].text.startswith(chunks[0].text[-5:])
    assert all(chunk.text for chunk in chunks)


def test_chunker_maps_chunks_to_one_or_more_pdf_pages() -> None:
    document = TextNormalizer().normalize(
        ParsedDocument(
            sections=(
                ParsedSection(text="Page one words", page_number=1),
                ParsedSection(text="Page two words", page_number=2),
            )
        )
    )

    chunks = DeterministicChunker(ChunkingConfig(chunk_size=len(document.text), overlap=0)).chunk(
        document
    )

    assert chunks[0].page_numbers == (1, 2)


def test_chunker_counts_non_whitespace_tokens() -> None:
    document = TextNormalizer().normalize(
        ParsedDocument(sections=(ParsedSection(text="one two\nthree"),))
    )

    chunks = DeterministicChunker(ChunkingConfig(chunk_size=100, overlap=0)).chunk(document)

    assert chunks[0].token_count == 3


@pytest.mark.parametrize(
    ("chunk_size", "overlap"),
    [
        (0, 0),
        (-1, 0),
        (10, -1),
        (10, 10),
        (10, 11),
        (True, 0),
        (10, False),
    ],
)
def test_invalid_chunk_configuration_is_rejected(
    chunk_size: int,
    overlap: int,
) -> None:
    with pytest.raises(ValueError):
        ChunkingConfig(chunk_size=chunk_size, overlap=overlap)


def test_maximum_valid_overlap_always_makes_progress() -> None:
    document = TextNormalizer().normalize(
        ParsedDocument(sections=(ParsedSection(text="abcdefghij"),))
    )

    chunks = DeterministicChunker(ChunkingConfig(chunk_size=4, overlap=3)).chunk(document)

    assert [chunk.start_offset for chunk in chunks] == list(range(7))
    assert chunks[-1].text == "ghij"
    assert len(chunks) == 7
