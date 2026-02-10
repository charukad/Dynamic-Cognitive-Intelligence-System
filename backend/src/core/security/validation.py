"""Input and output validation for security."""

import html
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, validator

from src.core import get_logger

logger = get_logger(__name__)


class ValidationResult(BaseModel):
    """Result of validation check."""
    
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    sanitized_value: Optional[Any] = None


class InputValidator:
    """
    Validates and sanitizes user inputs.
    
    Prevents injection attacks, XSS, and malformed data.
    """

    # Maximum lengths
    MAX_QUERY_LENGTH = 10000
    MAX_NAME_LENGTH = 255
    MAX_DESCRIPTION_LENGTH = 5000

    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"';?\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\s",
        r"UNION\s+SELECT",
        r"OR\s+1\s*=\s*1",
        r"--",
        r"/\*.*\*/",
    ]

    SCRIPT_PATTERNS = [
        r"<script[^>]*>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
    ]

    def validate_query(self, query: str) -> ValidationResult:
        """
        Validate user query input.
        
        Args:
            query: User query string
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []

        # Check length
        if not query or not query.strip():
            errors.append("Query cannot be empty")
            return ValidationResult(is_valid=False, errors=errors)

        if len(query) > self.MAX_QUERY_LENGTH:
            errors.append(f"Query exceeds maximum length of {self.MAX_QUERY_LENGTH}")

        # Check for SQL injection
        for pattern in self.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                errors.append("Query contains potentially dangerous SQL patterns")
                break

        # Check for XSS
        for pattern in self.SCRIPT_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                errors.append("Query contains potentially dangerous script patterns")
                break

        # Sanitize
        sanitized = self._sanitize_text(query)

        # Check for excessive special characters
        special_char_count = sum(1 for c in query if not c.isalnum() and not c.isspace())
        if special_char_count > len(query) * 0.3:
            warnings.append("Query contains many special characters")

        is_valid = len(errors) == 0

        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized if is_valid else None,
        )

    def validate_agent_name(self, name: str) -> ValidationResult:
        """Validate agent name."""
        errors = []

        if not name or not name.strip():
            errors.append("Name cannot be empty")
        elif len(name) > self.MAX_NAME_LENGTH:
            errors.append(f"Name exceeds maximum length of {self.MAX_NAME_LENGTH}")
        elif not re.match(r'^[a-zA-Z0-9_\- ]+$', name):
            errors.append("Name contains invalid characters (only alphanumeric, spaces, -, _ allowed)")

        sanitized = self._sanitize_text(name)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=sanitized,
        )

    def validate_description(self, description: str) -> ValidationResult:
        """Validate description text."""
        errors = []
        warnings = []

        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            errors.append(f"Description exceeds maximum length of {self.MAX_DESCRIPTION_LENGTH}")

        # Check for scripts
        for pattern in self.SCRIPT_PATTERNS:
            if re.search(pattern, description, re.IGNORECASE):
                errors.append("Description contains potentially dangerous content")
                break

        sanitized = self._sanitize_text(description)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized,
        )

    def validate_json_field(self, field_name: str, value: Any) -> ValidationResult:
        """Validate JSON field values."""
        errors = []

        # Check for reasonable size
        if isinstance(value, str) and len(value) > 50000:
            errors.append(f"{field_name} is too large")

        # Check for nested depth (prevent DoS)
        if isinstance(value, (dict, list)):
            if self._get_nesting_depth(value) > 10:
                errors.append(f"{field_name} has excessive nesting depth")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            sanitized_value=value,
        )

    def _sanitize_text(self, text: str) -> str:
        """Sanitize text by escaping HTML and removing control characters."""
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f]', '', text)
        
        # HTML escape
        text = html.escape(text)
        
        # Trim
        text = text.strip()
        
        return text

    def _get_nesting_depth(self, obj: Any, depth: int = 0) -> int:
        """Calculate nesting depth of dict/list."""
        if not isinstance(obj, (dict, list)):
            return depth

        if isinstance(obj, dict):
            if not obj:
                return depth
            return max(self._get_nesting_depth(v, depth + 1) for v in obj.values())
        else:  # list
            if not obj:
                return depth
            return max(self._get_nesting_depth(item, depth + 1) for item in obj)


class OutputValidator:
    """
    Validates model outputs before returning to users.
    
    Ensures safe and appropriate content.
    """

    def validate_output(self, text: str) -> ValidationResult:
        """
        Validate model output.
        
        Args:
            text: Generated text
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []

        # Check for reasonable length
        if len(text) > 50000:
            warnings.append("Output is very long")

        # Check for control characters
        if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', text):
            errors.append("Output contains invalid control characters")

        # Sanitize
        sanitized = html.escape(text)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            sanitized_value=sanitized,
        )


# Global instances
input_validator = InputValidator()
output_validator = OutputValidator()
