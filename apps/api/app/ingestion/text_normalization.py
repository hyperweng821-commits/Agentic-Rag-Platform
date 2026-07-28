"""Deterministic, structure-preserving text normalization for AF-2B."""

from dataclasses import dataclass
from unicodedata import category

from app.ingestion.document_parsing import EmptyDocumentError, ParsedDocument

_UTF8_BOM = "\ufeff"
_PRESERVED_CONTROLS = frozenset({"\n", "\t"})


@dataclass(frozen=True, slots=True)
class SourceSpan:
    """Normalized character range associated with one ordered source section."""

    start_offset: int
    end_offset: int
    section_index: int
    page_number: int | None = None

    def __post_init__(self) -> None:
        if self.start_offset < 0 or self.end_offset <= self.start_offset:
            raise ValueError("A source span must contain a non-empty character range.")
        if self.section_index < 0:
            raise ValueError("section_index must be non-negative.")
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be one-based when provided.")


@dataclass(frozen=True, slots=True)
class NormalizedDocument:
    """Deterministically normalized text and its source-section ranges."""

    text: str
    source_spans: tuple[SourceSpan, ...]

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise EmptyDocumentError("The normalized document contains no text.")
        if any(span.end_offset > len(self.text) for span in self.source_spans):
            raise ValueError("A source span extends beyond normalized document text.")


def _sanitize_character(character: str) -> str:
    if character in _PRESERVED_CONTROLS:
        return character
    character_category = category(character)
    if character_category == "Cc":
        return " "
    if character_category == "Cs":
        return "\ufffd"
    return character


def _normalize_fragment(text: str) -> str:
    normalized = text.removeprefix(_UTF8_BOM).replace("\r\n", "\n").replace("\r", "\n")
    normalized = "".join(_sanitize_character(character) for character in normalized)

    output_lines: list[str] = []
    blank_pending = False
    for raw_line in normalized.split("\n"):
        line = raw_line.rstrip(" \t")
        if not line.strip(" \t"):
            if output_lines:
                blank_pending = True
            continue
        if blank_pending:
            output_lines.append("")
            blank_pending = False
        output_lines.append(line)
    return "\n".join(output_lines).strip(" \t")


def normalize_text(text: str) -> str:
    """Normalize one text value and reject an empty normalized result."""

    normalized = _normalize_fragment(text)
    if not normalized.strip():
        raise EmptyDocumentError("The normalized document contains no text.")
    return normalized


class TextNormalizer:
    """Normalize parsed sections while retaining deterministic source offsets."""

    def normalize(self, document: ParsedDocument) -> NormalizedDocument:
        fragments: list[str] = []
        source_spans: list[SourceSpan] = []
        current_offset = 0

        for section_index, section in enumerate(document.sections):
            normalized_section = _normalize_fragment(section.text)
            if not normalized_section.strip():
                continue
            if fragments:
                current_offset += 2
            start_offset = current_offset
            fragments.append(normalized_section)
            current_offset += len(normalized_section)
            source_spans.append(
                SourceSpan(
                    start_offset=start_offset,
                    end_offset=current_offset,
                    section_index=section_index,
                    page_number=section.page_number,
                )
            )

        normalized_text = "\n\n".join(fragments)
        if not normalized_text.strip():
            raise EmptyDocumentError("The normalized document contains no text.")
        return NormalizedDocument(
            text=normalized_text,
            source_spans=tuple(source_spans),
        )
