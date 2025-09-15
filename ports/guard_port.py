from abc import ABC, abstractmethod
from enum import Enum
from typing import Any


class GuardAction(Enum):
    """Actions that can be taken by the guard."""

    ALLOW = "allow"
    BLOCK = "block"
    FILTER = "filter"
    WARN = "warn"


class GuardResult:
    """Result of a guard check."""

    def __init__(
        self,
        action: GuardAction,
        confidence: float,
        reason: str,
        filtered_content: str | None = None,
    ):
        self.action = action
        self.confidence = confidence
        self.reason = reason
        self.filtered_content = filtered_content


class GuardPort(ABC):
    """Port for security and content filtering operations."""

    @abstractmethod
    def check_content(self, content: str, context: str = "") -> GuardResult:
        """
        Check content for security, safety, and policy violations.

        Args:
            content: Text content to check
            context: Optional context for the check

        Returns:
            GuardResult with action and details
        """
        pass

    @abstractmethod
    def check_pii(self, content: str) -> GuardResult:
        """
        Check for personally identifiable information (PII).

        Args:
            content: Text content to check

        Returns:
            GuardResult with PII detection results
        """
        pass

    @abstractmethod
    def check_toxicity(self, content: str) -> GuardResult:
        """
        Check for toxic or harmful content.

        Args:
            content: Text content to check

        Returns:
            GuardResult with toxicity assessment
        """
        pass

    @abstractmethod
    def check_url_safety(self, url: str) -> GuardResult:
        """
        Check if a URL is safe to access.

        Args:
            url: URL to check

        Returns:
            GuardResult with URL safety assessment
        """
        pass

    @abstractmethod
    def filter_content(self, content: str, filters: list[str]) -> str:
        """
        Apply content filters to text.

        Args:
            content: Text content to filter
            filters: List of filter names to apply

        Returns:
            Filtered content
        """
        pass

    @abstractmethod
    def redact_pii(self, content: str, pii_types: list[str | None] = None) -> str:
        """
        Redact PII from content.

        Args:
            content: Text content to redact
            pii_types: Specific PII types to redact (None for all)

        Returns:
            Content with PII redacted
        """
        pass

    @abstractmethod
    def validate_domain(self, domain: str) -> bool:
        """
        Validate if a domain is allowed.

        Args:
            domain: Domain to validate

        Returns:
            True if domain is allowed, False otherwise
        """
        pass

    @abstractmethod
    def get_policy_violations(self, content: str) -> list[dict[str, Any]]:
        """
        Get detailed policy violations found in content.

        Args:
            content: Text content to analyze

        Returns:
            List of violation details
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if the guard service is available and healthy.

        Returns:
            True if healthy, False otherwise
        """
        pass
