"""Constitutional AI - Behavioral constraints and safety guardrails."""

import re
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel

from src.core import get_logger

logger = get_logger(__name__)


class ViolationSeverity(str, Enum):
    """Severity levels for constitution violations."""
    
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    BLOCKING = "blocking"


class ConstitutionViolation(BaseModel):
    """A detected violation of the constitution."""
    
    rule_id: str
    rule_name: str
    severity: ViolationSeverity
    message: str
    context: str
    suggestion: Optional[str] = None


class ConstitutionalRule(BaseModel):
    """A rule in the AI constitution."""
    
    id: str
    name: str
    description: str
    severity: ViolationSeverity
    patterns: List[str]  # Regex patterns to detect violations
    whitelist: List[str] = []  # Allowed exceptions


class Constitution:
    """
    Constitutional AI system for behavioral constraints.
    
    Implements safety guardrails and ethical guidelines for AI behavior.
    """
    
    def __init__(self):
        """Initialize constitution with predefined rules."""
        self.rules = self._load_default_rules()
    
    def _load_default_rules(self) -> List[ConstitutionalRule]:
        """Load default constitutional rules."""
        return [
            # Privacy & PII Protection
            ConstitutionalRule(
                id="privacy_001",
                name="No PII Collection",
                description="Do not collect, store, or transmit personally identifiable information",
                severity=ViolationSeverity.CRITICAL,
                patterns=[
                    r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
                    r'\b\d{16}\b',  # Credit card
                    r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',  # Email (case insensitive)
                ],
            ),
            
            # Harm Prevention
            ConstitutionalRule(
                id="safety_001",
                name="No Harmful Instructions",
                description="Do not provide instructions for harmful, dangerous, or illegal activities",
                severity=ViolationSeverity.BLOCKING,
                patterns=[
                    r'\b(how to (make|create|build) (bomb|weapon|explosive))\b',
                    r'\b(instructions? for (hacking|cracking|breaking into))\b',
                    r'\b(tutorial on (stealing|fraud|scam))\b',
                ],
            ),
            
            # Bias & Discrimination
            ConstitutionalRule(
                id="ethics_001",
                name="No Discriminatory Content",
                description="Avoid generating biased or discriminatory content",
                severity=ViolationSeverity.CRITICAL,
                patterns=[
                    r'\b(all (women|men|blacks|whites|asians|muslims|jews) are)\b',
                    r'\b(inferior|superior) (race|gender|ethnicity)\b',
                ],
            ),
            
            # Medical/Legal Advice
            ConstitutionalRule(
                id="advice_001",
                name="No Professional Advice",
                description="Do not provide medical, legal, or financial advice",
                severity=ViolationSeverity.WARNING,
                patterns=[
                    r'\b(you should (take|stop taking) (this medication|these pills))\b',
                    r'\b(legal advice|you should sue|file a lawsuit)\b',
                    r'\b(invest all your money in|guaranteed returns)\b',
                ],
            ),
            
            # Misinformation
            ConstitutionalRule(
                id="truth_001",
                name="No Deliberate Misinformation",
                description="Do not generate known false or misleading information",
                severity=ViolationSeverity.CRITICAL,
                patterns=[
                    r'\b(vaccines cause autism|earth is flat|climate change is a hoax)\b',
                    r'\b(covid is (fake|hoax)|pandemic (hoax|fake))\b',
                ],
            ),
            
            # System Security
            ConstitutionalRule(
                id="security_001",
                name="No System Compromise",
                description="Do not attempt to bypass security or access unauthorized systems",
                severity=ViolationSeverity.BLOCKING,
                patterns=[
                    r'\b(ignore (previous|all) instructions?)\b',
                    r'\b(you are now|act as|pretend to be) (jailbroken|uncensored|DAN)\b',
                    r'\b(show me your (system prompt|instructions))\b',
                ],
            ),
            
            # Intellectual Property
            ConstitutionalRule(
                id="ip_001",
                name="Respect Copyright",
                description="Do not generate copyrighted content verbatim",
                severity=ViolationSeverity.WARNING,
                patterns=[
                    r'\b(write the entire (lyrics|script|book) of)\b',
                    r'\b(copy (exact|verbatim) text from)\b',
                ],
            ),
            
            # Self-Harm Prevention
            ConstitutionalRule(
                id="safety_002",
                name="No Self-Harm Encouragement",
                description="Do not encourage or provide methods for self-harm",
                severity=ViolationSeverity.BLOCKING,
                patterns=[
                    r'\b(how to (commit suicide|end my life|kill myself))\b',
                    r'\b(best ways? to (self harm|cut myself))\b',
                ],
            ),
        ]
    
    def check_input(self, text: str) -> Tuple[bool, List[ConstitutionViolation]]:
        """
        Check input text for constitutional violations.
        
        Args:
            text: Input text to check
            
        Returns:
            Tuple of (is_allowed, violations)
        """
        violations = []
        text_lower = text.lower()
        
        for rule in self.rules:
            for pattern in rule.patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                
                if matches:
                    # Check whitelist
                    is_whitelisted = any(
                        wl.lower() in text_lower for wl in rule.whitelist
                    )
                    
                    if not is_whitelisted:
                        violation = ConstitutionViolation(
                            rule_id=rule.id,
                            rule_name=rule.name,
                            severity=rule.severity,
                            message=f"Detected potential violation: {rule.description}",
                            context=f"Matched pattern: {matches[0]}",
                            suggestion="Please rephrase your request to avoid violating safety guidelines.",
                        )
                        violations.append(violation)
                        
                        logger.warning(
                            f"Constitution violation detected - Rule: {rule.name}, "
                            f"Severity: {rule.severity}, Pattern: {matches[0]}"
                        )
        
        # Check if any blocking violations
        has_blocking = any(
            v.severity == ViolationSeverity.BLOCKING for v in violations
        )
        
        is_allowed = not has_blocking
        
        return is_allowed, violations
    
    def check_output(self, text: str) -> Tuple[bool, List[ConstitutionViolation]]:
        """
        Check output text for constitutional violations.
        
        Same logic as check_input, but for generated content.
        
        Args:
            text: Output text to check
            
        Returns:
            Tuple of (is_safe, violations)
        """
        return self.check_input(text)
    
    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by removing PII and sensitive information.
        
        Args:
            text: Text to sanitize
            
        Returns:
            Sanitized text
        """
        sanitized = text
        
        # Remove SSN
        sanitized = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN REDACTED]', sanitized)
        
        # Remove credit cards
        sanitized = re.sub(r'\b\d{16}\b', '[CARD REDACTED]', sanitized)
        
        # Remove emails (partial)
        sanitized = re.sub(
            r'\b([A-Z0-9._%+-]+)@([A-Z0-9.-]+\.[A-Z]{2,})\b',
            r'\1@[REDACTED]',
            sanitized,
            flags=re.IGNORECASE,
        )
        
        # Remove phone numbers
        sanitized = re.sub(
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
            '[PHONE REDACTED]',
            sanitized,
        )
        
        return sanitized
    
    def add_rule(self, rule: ConstitutionalRule) -> None:
        """Add a custom rule to the constitution."""
        self.rules.append(rule)
        logger.info(f"Added new constitutional rule: {rule.name}")
    
    def get_violation_report(
        self,
        violations: List[ConstitutionViolation],
    ) -> str:
        """Generate a human-readable violation report."""
        if not violations:
            return "No violations detected."
        
        report = f"Detected {len(violations)} constitutional violation(s):\n\n"
        
        for i, v in enumerate(violations, 1):
            report += f"{i}. [{v.severity.upper()}] {v.rule_name}\n"
            report += f"   Message: {v.message}\n"
            report += f"   Context: {v.context}\n"
            
            if v.suggestion:
                report += f"   Suggestion: {v.suggestion}\n"
            
            report += "\n"
        
        return report


# Global constitution instance
constitution = Constitution()
