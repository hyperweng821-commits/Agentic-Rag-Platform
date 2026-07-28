"""Document parsing boundaries for server-managed AF-2B source artifacts."""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from io import BytesIO
from pathlib import PurePath
from typing import Protocol, cast

from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError, PdfReadError


class DocumentProcessingError(Exception):
    """Base class for safe, explicit document-processing failures."""


class UnsupportedDocumentTypeError(DocumentProcessingError):
    """Trusted document metadata does not identify a supported parser."""


class DocumentParseError(DocumentProcessingError):
    """A supported artifact could not be parsed safely."""


class InvalidTextEncodingError(DocumentParseError):
    """A text artifact is not valid UTF-8."""


class EmptyDocumentError(DocumentProcessingError):
    """A document contains no meaningful text."""


class NoExtractableTextError(EmptyDocumentError):
    """A PDF contains no extractable text and would require OCR."""


class EncryptedPdfError(DocumentParseError):
    """An encrypted PDF cannot be processed without a password."""


@dataclass(frozen=True, slots=True)
class DocumentArtifact:
    """Bytes and trusted metadata loaded from server-managed storage."""

    content: bytes
    media_type: str
    filename: str


@dataclass(frozen=True, slots=True)
class ParsedSection:
    """One ordered section of parsed source text."""

    text: str
    page_number: int | None = None

    def __post_init__(self) -> None:
        if self.page_number is not None and self.page_number < 1:
            raise ValueError("page_number must be one-based when provided.")


@dataclass(frozen=True, slots=True)
class ParsedDocument:
    """Ordered parser output prior to deterministic normalization."""

    sections: tuple[ParsedSection, ...]


class DocumentParser(Protocol):
    """Parser implementation selected from trusted document metadata."""

    @property
    def supported_media_types(self) -> frozenset[str]:
        """Return the exact media types accepted by this parser."""
        ...

    @property
    def supported_extensions(self) -> frozenset[str]:
        """Return the lowercase filename extensions accepted by this parser."""
        ...

    def parse(self, content: bytes) -> ParsedDocument:
        """Parse one immutable in-memory artifact."""
        ...


class Utf8TextDocumentParser:
    """Strict UTF-8 parser shared by plain-text and Markdown artifacts."""

    def __init__(
        self,
        *,
        media_types: Iterable[str],
        extensions: Iterable[str],
    ) -> None:
        self._supported_media_types = frozenset(media_types)
        self._supported_extensions = frozenset(extension.lower() for extension in extensions)
        if not self._supported_media_types or not self._supported_extensions:
            raise ValueError("A text parser must support at least one media type and extension.")

    @property
    def supported_media_types(self) -> frozenset[str]:
        return self._supported_media_types

    @property
    def supported_extensions(self) -> frozenset[str]:
        return self._supported_extensions

    def parse(self, content: bytes) -> ParsedDocument:
        try:
            text = content.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError as exc:
            raise InvalidTextEncodingError("The document is not valid UTF-8 text.") from exc
        if not text.strip():
            raise EmptyDocumentError("The document contains no text.")
        return ParsedDocument(sections=(ParsedSection(text=text),))


class PdfPage(Protocol):
    """Subset of a PDF page used by the provider-independent parser."""

    def extract_text(self) -> str:
        """Extract text in the page's stored reading order."""
        ...


class PdfReaderLike(Protocol):
    """Subset of a PDF reader used by the provider-independent parser."""

    @property
    def is_encrypted(self) -> bool:
        """Whether the PDF requires decryption."""
        ...

    @property
    def pages(self) -> Sequence[PdfPage]:
        """Ordered PDF pages."""
        ...


PdfReaderFactory = Callable[[bytes], PdfReaderLike]


def _create_pdf_reader(content: bytes) -> PdfReaderLike:
    return cast(PdfReaderLike, PdfReader(BytesIO(content), strict=False))


class PdfDocumentParser:
    """Extract ordered text from PDFs without performing OCR."""

    _EXTRACTION_ERRORS = (
        FileNotDecryptedError,
        PdfReadError,
        KeyError,
        TypeError,
        ValueError,
    )

    def __init__(self, reader_factory: PdfReaderFactory = _create_pdf_reader) -> None:
        self._reader_factory = reader_factory

    @property
    def supported_media_types(self) -> frozenset[str]:
        return frozenset({"application/pdf"})

    @property
    def supported_extensions(self) -> frozenset[str]:
        return frozenset({".pdf"})

    def parse(self, content: bytes) -> ParsedDocument:
        if not content:
            raise EmptyDocumentError("The document contains no data.")
        try:
            reader = self._reader_factory(content)
            if reader.is_encrypted:
                raise EncryptedPdfError("Encrypted PDF documents are not supported.")
            sections = tuple(
                ParsedSection(text=page.extract_text() or "", page_number=page_number)
                for page_number, page in enumerate(reader.pages, start=1)
            )
        except EncryptedPdfError:
            raise
        except self._EXTRACTION_ERRORS as exc:
            raise DocumentParseError("The PDF document could not be parsed.") from exc

        if not any(section.text.strip() for section in sections):
            raise NoExtractableTextError(
                "The PDF contains no extractable text; OCR is not supported."
            )
        return ParsedDocument(sections=sections)


class DocumentParserRegistry:
    """Select a parser using exact trusted media-type and extension metadata."""

    def __init__(self, parsers: Iterable[DocumentParser]) -> None:
        parser_map: dict[tuple[str, str], DocumentParser] = {}
        for parser in parsers:
            for media_type in parser.supported_media_types:
                for extension in parser.supported_extensions:
                    key = (media_type, extension)
                    if key in parser_map:
                        raise ValueError(
                            "Multiple document parsers are registered for "
                            f"{media_type} {extension}."
                        )
                    parser_map[key] = parser
        if not parser_map:
            raise ValueError("At least one document parser must be registered.")
        self._parsers = parser_map

    def parse(self, artifact: DocumentArtifact) -> ParsedDocument:
        extension = PurePath(artifact.filename).suffix.lower()
        parser = self._parsers.get((artifact.media_type, extension))
        if parser is None:
            raise UnsupportedDocumentTypeError(
                "The stored document type is not supported for processing."
            )
        return parser.parse(artifact.content)


def create_default_parser_registry() -> DocumentParserRegistry:
    """Create parsers for the exact file types accepted by AF-1 intake."""

    return DocumentParserRegistry(
        (
            Utf8TextDocumentParser(
                media_types=("text/plain",),
                extensions=(".txt",),
            ),
            Utf8TextDocumentParser(
                media_types=("text/markdown",),
                extensions=(".md", ".markdown"),
            ),
            PdfDocumentParser(),
        )
    )
