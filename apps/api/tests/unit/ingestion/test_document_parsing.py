"""Unit tests for trusted-metadata document parser selection and extraction."""

from collections.abc import Sequence
from dataclasses import dataclass

import pytest

from app.ingestion.document_parsing import (
    DocumentArtifact,
    DocumentParseError,
    EmptyDocumentError,
    EncryptedPdfError,
    InvalidTextEncodingError,
    NoExtractableTextError,
    PdfDocumentParser,
    PdfPage,
    UnsupportedDocumentTypeError,
    create_default_parser_registry,
)


def _pdf_with_text(text: str) -> bytes:
    escaped_text = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 12 Tf 72 720 Td ({escaped_text}) Tj ET".encode()
    objects = (
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    )
    document = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for object_number, body in enumerate(objects, start=1):
        offsets.append(len(document))
        document.extend(f"{object_number} 0 obj\n".encode())
        document.extend(body)
        document.extend(b"\nendobj\n")
    xref_offset = len(document)
    document.extend(f"xref\n0 {len(objects) + 1}\n".encode())
    document.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        document.extend(f"{offset:010d} 00000 n \n".encode())
    document.extend(
        (
            f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode()
    )
    return bytes(document)


def test_plain_text_parser_preserves_ordered_utf8_text() -> None:
    parsed = create_default_parser_registry().parse(
        DocumentArtifact(
            content="First\nSecond \N{SNOWMAN}".encode(),
            media_type="text/plain",
            filename="notes.txt",
        )
    )

    assert len(parsed.sections) == 1
    assert parsed.sections[0].text == "First\nSecond \N{SNOWMAN}"
    assert parsed.sections[0].page_number is None


def test_text_parser_removes_utf8_byte_order_mark() -> None:
    parsed = create_default_parser_registry().parse(
        DocumentArtifact(
            content=b"\xef\xbb\xbfBOM content",
            media_type="text/plain",
            filename="bom.txt",
        )
    )

    assert parsed.sections[0].text == "BOM content"


def test_markdown_parser_preserves_markdown_structure() -> None:
    markdown = "# Heading\n\n- first\n- second\n\n```python\nprint('kept')\n```"

    parsed = create_default_parser_registry().parse(
        DocumentArtifact(
            content=markdown.encode(),
            media_type="text/markdown",
            filename="guide.markdown",
        )
    )

    assert parsed.sections[0].text == markdown


def test_pdf_parser_extracts_text_and_one_based_page_number() -> None:
    parsed = create_default_parser_registry().parse(
        DocumentArtifact(
            content=_pdf_with_text("Extractable PDF text"),
            media_type="application/pdf",
            filename="document.pdf",
        )
    )

    assert parsed.sections[0].text.strip() == "Extractable PDF text"
    assert parsed.sections[0].page_number == 1


@pytest.mark.parametrize("content", [b"", b" \r\n\t "])
def test_text_parser_rejects_empty_or_whitespace_only_content(content: bytes) -> None:
    with pytest.raises(EmptyDocumentError, match="contains no text"):
        create_default_parser_registry().parse(
            DocumentArtifact(
                content=content,
                media_type="text/plain",
                filename="empty.txt",
            )
        )


def test_text_parser_rejects_invalid_utf8() -> None:
    with pytest.raises(InvalidTextEncodingError, match="valid UTF-8"):
        create_default_parser_registry().parse(
            DocumentArtifact(
                content=b"\xff\xfeinvalid",
                media_type="text/plain",
                filename="invalid.txt",
            )
        )


@pytest.mark.parametrize(
    ("media_type", "filename"),
    [
        ("application/octet-stream", "program.exe"),
        ("text/plain", "mismatched.md"),
        ("text/markdown", "mismatched.txt"),
    ],
)
def test_registry_rejects_unsupported_or_mismatched_trusted_metadata(
    media_type: str,
    filename: str,
) -> None:
    with pytest.raises(UnsupportedDocumentTypeError, match="not supported"):
        create_default_parser_registry().parse(
            DocumentArtifact(
                content=b"content",
                media_type=media_type,
                filename=filename,
            )
        )


@dataclass
class _FakePage:
    text: str

    def extract_text(self) -> str:
        return self.text


@dataclass
class _FakeReader:
    pages: Sequence[PdfPage]
    is_encrypted: bool = False


def test_pdf_parser_rejects_pdf_without_extractable_text() -> None:
    parser = PdfDocumentParser(
        reader_factory=lambda _: _FakeReader(pages=(_FakePage(""), _FakePage(" \n")))
    )

    with pytest.raises(NoExtractableTextError, match="OCR is not supported"):
        parser.parse(b"%PDF-1.7\n")


def test_pdf_parser_rejects_encrypted_pdf() -> None:
    parser = PdfDocumentParser(reader_factory=lambda _: _FakeReader(pages=(), is_encrypted=True))

    with pytest.raises(EncryptedPdfError, match="Encrypted PDF"):
        parser.parse(b"%PDF-1.7\n")


def test_pdf_parser_normalizes_known_reader_failure() -> None:
    def failing_reader(_: bytes) -> _FakeReader:
        raise ValueError("provider detail")

    with pytest.raises(DocumentParseError, match="could not be parsed") as exc_info:
        PdfDocumentParser(reader_factory=failing_reader).parse(b"%PDF-1.7\n")

    assert isinstance(exc_info.value.__cause__, ValueError)
