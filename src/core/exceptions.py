"""
src/core/exceptions.py
Custom exceptions for Woodward Core v2.
All Woodward runtime errors inherit from WoodwardError.
Build failures must hard-stop — do not catch WoodwardError generically
unless you intend to handle it fully.
"""
from __future__ import annotations


class WoodwardError(Exception):
    """Base exception for all Woodward runtime errors."""

    def __init__(self, message: str, context: dict | None = None) -> None:
        super().__init__(message)
        self.context: dict = context or {}

    def __str__(self) -> str:
        base = super().__str__()
        if self.context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{base} [{ctx_str}]"
        return base


class CanonValidationError(WoodwardError):
    """
    Raised when a canonical YAML file fails schema validation.
    This is a hard-stop condition — the run must not proceed.
    """


class FigureMismatchError(WoodwardError):
    """
    Raised when a computed figure value does not match the locked canonical value.
    Provides figure_id, computed_value, and canonical_value in context.
    """

    def __init__(
        self,
        figure_id: str,
        computed_value: float,
        canonical_value: float,
        notes: str = "",
    ) -> None:
        message = (
            f"Figure mismatch for '{figure_id}': "
            f"computed={computed_value}, canonical={canonical_value}"
        )
        if notes:
            message += f" — {notes}"
        super().__init__(
            message,
            context={
                "figure_id": figure_id,
                "computed_value": computed_value,
                "canonical_value": canonical_value,
            },
        )


class BlockedClaimError(WoodwardError):
    """
    Raised when a blocked claim is encountered in a publication-bound context.
    Contains claim_id and reason in context.
    """

    def __init__(self, claim_id: str, reason: str = "") -> None:
        message = f"Blocked claim '{claim_id}' cannot enter publication assembly"
        if reason:
            message += f": {reason}"
        super().__init__(message, context={"claim_id": claim_id, "reason": reason})


class UnsupportedClaimError(WoodwardError):
    """
    Raised when a claim has no public-citable support chain
    but is being used in a publication-bound workflow.
    """

    def __init__(self, claim_id: str, reason: str = "") -> None:
        message = f"Claim '{claim_id}' lacks a complete public-citable support chain"
        if reason:
            message += f": {reason}"
        super().__init__(message, context={"claim_id": claim_id, "reason": reason})


class PublicationBlockedError(WoodwardError):
    """
    Raised when article assembly is blocked by one or more unresolved conditions
    (unresolved right-of-reply, open publication blocks, failed adversarial review).
    """

    def __init__(self, article_id: str, reasons: list[str]) -> None:
        message = (
            f"Publication of article '{article_id}' is blocked. "
            f"Reasons: {'; '.join(reasons)}"
        )
        super().__init__(message, context={"article_id": article_id, "reasons": reasons})


class HallucinatedContextError(WoodwardError):
    """
    Raised when an LLM response references a context_id, claim_id, or figure_id
    that does not exist in the current canonical state or records.
    This is a build failure — runs must not continue with hallucinated references.
    """

    def __init__(self, ref_type: str, ref_id: str, section_id: str = "") -> None:
        message = (
            f"Hallucinated {ref_type} reference: '{ref_id}'"
        )
        if section_id:
            message += f" in section '{section_id}'"
        super().__init__(
            message,
            context={"ref_type": ref_type, "ref_id": ref_id, "section_id": section_id},
        )


class ScopeUndeclaredError(WoodwardError):
    """
    Raised when a vendor or figure used in a workflow is not declared
    in the canonical vendor_scope or figures manifests.
    """

    def __init__(self, scope_type: str, identifier: str, article_id: str = "") -> None:
        message = f"Undeclared {scope_type} scope: '{identifier}'"
        if article_id:
            message += f" in article '{article_id}'"
        super().__init__(
            message,
            context={
                "scope_type": scope_type,
                "identifier": identifier,
                "article_id": article_id,
            },
        )


class DenominatorMixError(WoodwardError):
    """
    Raised when figures with incompatible denominators (e.g., budgeted vs. actual,
    Object 7 total vs. staffing-vendor subset) are mixed in the same calculation
    or comparison without explicit canonical metadata permitting it.
    """

    def __init__(self, figure_ids: list[str], reason: str = "") -> None:
        message = f"Denominator mix detected for figures: {figure_ids}"
        if reason:
            message += f" — {reason}"
        super().__init__(
            message, context={"figure_ids": figure_ids, "reason": reason}
        )


class MigrationError(WoodwardError):
    """
    Raised when a database migration fails.
    Contains db_name and migration_file in context.
    """

    def __init__(self, db_name: str, migration_file: str, reason: str = "") -> None:
        message = f"Migration failed for '{db_name}' ({migration_file})"
        if reason:
            message += f": {reason}"
        super().__init__(
            message,
            context={"db_name": db_name, "migration_file": migration_file, "reason": reason},
        )
