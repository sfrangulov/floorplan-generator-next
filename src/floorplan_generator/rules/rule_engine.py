"""Rule engine base classes."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import StrEnum

from pydantic import BaseModel

from floorplan_generator.core.models import Apartment


class RuleStatus(StrEnum):
    """Status of a rule validation result."""

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


class RuleResult(BaseModel):
    """Result of a single rule validation."""

    rule_id: str
    status: RuleStatus
    message: str
    details: dict | None = None


class RuleValidator(ABC):
    """Abstract base class for all rule validators."""

    rule_id: str
    name: str
    description: str
    is_mandatory: bool
    regulatory_basis: str

    @abstractmethod
    def validate(self, apartment: Apartment) -> RuleResult:
        """Validate an apartment against this rule."""

    def _pass(self, msg: str, details: dict | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            status=RuleStatus.PASS,
            message=msg,
            details=details,
        )

    def _fail(self, msg: str, details: dict | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            status=RuleStatus.FAIL,
            message=msg,
            details=details,
        )

    def _warn(self, msg: str, details: dict | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            status=RuleStatus.WARN,
            message=msg,
            details=details,
        )

    def _skip(self, msg: str, details: dict | None = None) -> RuleResult:
        return RuleResult(
            rule_id=self.rule_id,
            status=RuleStatus.SKIP,
            message=msg,
            details=details,
        )


class MockAlwaysPassRule(RuleValidator):
    """Base for mock rules (P29-P34). Always returns PASS with 'mock' in message."""

    is_mandatory = False

    def validate(self, apartment: Apartment) -> RuleResult:
        return self._pass(f"{self.name}: mock — always PASS")
