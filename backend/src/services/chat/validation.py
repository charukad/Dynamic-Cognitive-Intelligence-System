"""Validation helpers for chat API and transport boundaries."""

from __future__ import annotations

import re
from typing import Any


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9:_-]{1,255}$")
CONTROL_CHARACTER_PATTERN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
MAX_CHAT_CONTENT_LENGTH = 20000
MAX_FEEDBACK_LENGTH = 4000
MAX_METADATA_DEPTH = 8
MAX_METADATA_ITEMS = 200
MAX_METADATA_KEY_LENGTH = 128
MAX_METADATA_STRING_LENGTH = 5000


def normalize_optional_text(value: str | None) -> str | None:
    """Normalize optional text input."""
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def validate_identifier(value: str | None, field_name: str) -> str | None:
    """Validate IDs passed through chat APIs."""
    normalized = normalize_optional_text(value)
    if normalized is None:
        return None

    if not IDENTIFIER_PATTERN.fullmatch(normalized):
        raise ValueError(
            f"{field_name} must contain only letters, numbers, ':', '_', or '-'"
        )
    return normalized


def validate_chat_text(
    value: str | None,
    *,
    field_name: str,
    max_length: int = MAX_CHAT_CONTENT_LENGTH,
    allow_empty: bool = False,
) -> str:
    """Validate chat message text without mutating the meaning of the prompt."""
    if value is None:
        raise ValueError(f"{field_name} is required")

    normalized = value.strip()
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} cannot be empty")
    if len(normalized) > max_length:
        raise ValueError(f"{field_name} exceeds maximum length of {max_length}")
    if CONTROL_CHARACTER_PATTERN.search(normalized):
        raise ValueError(f"{field_name} contains unsupported control characters")
    return normalized


def validate_metadata_dict(value: dict[str, Any] | None, field_name: str) -> dict[str, Any]:
    """Validate JSON metadata payloads used by chat APIs."""
    metadata = value or {}
    if not isinstance(metadata, dict):
        raise ValueError(f"{field_name} must be an object")

    _walk_metadata(metadata, field_name=field_name, depth=1)
    return metadata


def validate_feedback_text(value: str | None) -> str | None:
    """Validate optional free-form feedback text."""
    normalized = normalize_optional_text(value)
    if normalized is None:
        return None
    if len(normalized) > MAX_FEEDBACK_LENGTH:
        raise ValueError(f"text_feedback exceeds maximum length of {MAX_FEEDBACK_LENGTH}")
    if CONTROL_CHARACTER_PATTERN.search(normalized):
        raise ValueError("text_feedback contains unsupported control characters")
    return normalized


def _walk_metadata(value: Any, *, field_name: str, depth: int) -> int:
    """Walk metadata recursively and validate size and supported types."""
    if depth > MAX_METADATA_DEPTH:
        raise ValueError(f"{field_name} exceeds maximum nesting depth of {MAX_METADATA_DEPTH}")

    if isinstance(value, dict):
        total_items = len(value)
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{field_name} keys must be strings")
            if len(key) > MAX_METADATA_KEY_LENGTH:
                raise ValueError(
                    f"{field_name} key '{key[:32]}' exceeds {MAX_METADATA_KEY_LENGTH} characters"
                )
            total_items += _walk_metadata(nested_value, field_name=field_name, depth=depth + 1)
        if total_items > MAX_METADATA_ITEMS:
            raise ValueError(f"{field_name} exceeds maximum size of {MAX_METADATA_ITEMS} items")
        return total_items

    if isinstance(value, list):
        total_items = len(value)
        for nested_value in value:
            total_items += _walk_metadata(nested_value, field_name=field_name, depth=depth + 1)
        if total_items > MAX_METADATA_ITEMS:
            raise ValueError(f"{field_name} exceeds maximum size of {MAX_METADATA_ITEMS} items")
        return total_items

    if isinstance(value, str):
        if len(value) > MAX_METADATA_STRING_LENGTH:
            raise ValueError(
                f"{field_name} string values exceed maximum length of {MAX_METADATA_STRING_LENGTH}"
            )
        if CONTROL_CHARACTER_PATTERN.search(value):
            raise ValueError(f"{field_name} contains unsupported control characters")
        return 1

    if value is None or isinstance(value, bool | int | float):
        return 1

    raise ValueError(f"{field_name} contains unsupported value type: {type(value).__name__}")
