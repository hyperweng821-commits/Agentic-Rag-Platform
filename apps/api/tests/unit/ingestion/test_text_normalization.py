"""Unit tests for deterministic structure-preserving text normalization."""

import pytest

from app.ingestion.document_parsing import EmptyDocumentError, ParsedDocument, ParsedSection
from app.ingestion.text_normalization import TextNormalizer, normalize_text


def test_normalization_is_deterministic_and_normalizes_line_endings() -> None:
    source = "\ufeffHeading\r\n\rParagraph one.\r\r\nParagraph two.\n"

    first = normalize_text(source)
    second = normalize_text(source)

    assert first == second
    assert first == "Heading\n\nParagraph one.\n\nParagraph two."
    assert "\r" not in first


def test_normalization_safely_replaces_controls_and_reduces_blank_lines() -> None:
    source = "first\x00control\n\n \n\nsecond\x07control"

    assert normalize_text(source) == "first control\n\nsecond control"


def test_normalization_preserves_markdown_indentation_and_structure() -> None:
    source = "\n# Heading  \n\n\n  - nested item\n\n```python\n  value = 1\n```\n"

    assert normalize_text(source) == ("# Heading\n\n  - nested item\n\n```python\n  value = 1\n```")


def test_section_normalization_produces_stable_page_source_spans() -> None:
    normalized = TextNormalizer().normalize(
        ParsedDocument(
            sections=(
                ParsedSection(text=" Page one \r\n", page_number=1),
                ParsedSection(text="\n\n", page_number=2),
                ParsedSection(text="Page three", page_number=3),
            )
        )
    )

    assert normalized.text == "Page one\n\nPage three"
    assert normalized.source_spans[0].start_offset == 0
    assert normalized.source_spans[0].end_offset == len("Page one")
    assert normalized.source_spans[0].section_index == 0
    assert normalized.source_spans[0].page_number == 1
    assert normalized.source_spans[1].start_offset == len("Page one\n\n")
    assert normalized.source_spans[1].end_offset == len(normalized.text)
    assert normalized.source_spans[1].section_index == 2
    assert normalized.source_spans[1].page_number == 3


@pytest.mark.parametrize("source", ["", " \r\n\t ", "\x00\x07"])
def test_normalization_rejects_empty_result(source: str) -> None:
    with pytest.raises(EmptyDocumentError, match="contains no text"):
        normalize_text(source)
