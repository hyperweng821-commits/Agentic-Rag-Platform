"""Pure AF-3A-1 retrieval request validation and normalization."""

import unicodedata
from collections.abc import Mapping
from dataclasses import dataclass, field

_QUERY_FIELD = "query"
_REQUESTED_COUNT_FIELD = "requested_count"
_ALLOWED_FIELDS = frozenset({_QUERY_FIELD, _REQUESTED_COUNT_FIELD})

_DEFAULT_REQUESTED_COUNT = 10
_MIN_REQUESTED_COUNT = 1
_MAX_REQUESTED_COUNT = 50
_MIN_QUERY_SCALARS = 1
_MAX_QUERY_SCALARS = 2_048
_MIN_QUERY_UTF8_BYTES = 1
_MAX_QUERY_UTF8_BYTES = 4_096
_MIN_SURROGATE = 0xD800
_MAX_SURROGATE = 0xDFFF

_ADR_008_WHITESPACE = frozenset(
    "\u0009\u000a\u000b\u000c\u000d"
    "\u0020"
    "\u0085"
    "\u00a0"
    "\u1680"
    "\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"
    "\u2028\u2029\u202f"
    "\u205f"
    "\u3000"
)


class RetrievalRequestValidationError(ValueError):
    """Signal invalid retrieval input without retaining or disclosing it."""

    def __init__(self) -> None:
        super().__init__("Retrieval request validation failed.")


@dataclass(frozen=True, slots=True)
class RetrievalRequest:
    """Validated retrieval input safe to pass to later retrieval slices."""

    normalized_query: str = field(repr=False)
    requested_count: int


def _validate_query_scalar_domain(query: str) -> None:
    if any(_MIN_SURROGATE <= ord(character) <= _MAX_SURROGATE for character in query):
        raise RetrievalRequestValidationError
    try:
        query.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise RetrievalRequestValidationError from None


def _normalize_adr_008_whitespace(query: str) -> str:
    output: list[str] = []
    interior_space_pending = False

    for character in query:
        if character in _ADR_008_WHITESPACE:
            if output:
                interior_space_pending = True
            continue
        if interior_space_pending:
            output.append("\u0020")
            interior_space_pending = False
        output.append(character)

    return "".join(output)


def parse_retrieval_request(payload: object) -> RetrievalRequest:
    """Validate and normalize one closed-shape runtime retrieval mapping."""

    if not isinstance(payload, Mapping):
        raise RetrievalRequestValidationError

    keys = tuple(payload)
    if any(type(key) is not str for key in keys):
        raise RetrievalRequestValidationError

    key_set = set(keys)
    if len(key_set) != len(keys) or _QUERY_FIELD not in key_set or not key_set <= _ALLOWED_FIELDS:
        raise RetrievalRequestValidationError

    query = payload[_QUERY_FIELD]
    requested_count = payload.get(_REQUESTED_COUNT_FIELD, _DEFAULT_REQUESTED_COUNT)
    if type(query) is not str or type(requested_count) is not int:
        raise RetrievalRequestValidationError
    if not _MIN_REQUESTED_COUNT <= requested_count <= _MAX_REQUESTED_COUNT:
        raise RetrievalRequestValidationError

    _validate_query_scalar_domain(query)
    if "\u0000" in query:
        raise RetrievalRequestValidationError

    nfc_query = unicodedata.normalize("NFC", query)
    normalized_query = _normalize_adr_008_whitespace(nfc_query)

    scalar_count = len(normalized_query)
    if not _MIN_QUERY_SCALARS <= scalar_count <= _MAX_QUERY_SCALARS:
        raise RetrievalRequestValidationError

    utf8_byte_count = len(normalized_query.encode("utf-8", errors="strict"))
    if not _MIN_QUERY_UTF8_BYTES <= utf8_byte_count <= _MAX_QUERY_UTF8_BYTES:
        raise RetrievalRequestValidationError

    return RetrievalRequest(
        normalized_query=normalized_query,
        requested_count=requested_count,
    )
