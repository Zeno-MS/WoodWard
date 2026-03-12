"""
src/services/scope_reconciler.py
ScopeReconciler — validates that all figures and vendors referenced in an article
are declared in the canonical manifest, and detects denominator mixing errors.
"""
from __future__ import annotations

from schemas.canonical import CanonManifest
from src.core.exceptions import DenominatorMixError, ScopeUndeclaredError

# Figure IDs that are "budgeted" denominators
_BUDGETED_FIGURE_IDS = {
    "object7_budget_fy2425",
}

# Figure IDs that are "actual" denominators
_ACTUAL_FIGURE_IDS = {
    "object7_actual_fy2425",
    "fy2425_staffing_vendor_total",
    "cumulative_staffing_baseline",
    "amergis_fy2425_total",
    "ospi_advance_requested",
    "ospi_advance_approved",
}

# Figure ID pairs that must not be mixed without explicit disclosure
# Each tuple: (budgeted_figure_id, actual_figure_id)
_INCOMPATIBLE_DENOMINATOR_PAIRS = [
    ("object7_budget_fy2425", "fy2425_staffing_vendor_total"),
    ("object7_budget_fy2425", "amergis_fy2425_total"),
]


class ScopeReconciler:
    """
    Validates article scope declarations against the canonical manifest.

    Two primary checks:
    1. validate_article_scope — every vendor_id and figure_id used in the article
       must be declared in the canonical manifest.
    2. validate_denominator_consistency — mixing budgeted and actual figures without
       explicit canon metadata permitting it raises DenominatorMixError.
    """

    def validate_article_scope(
        self,
        article_id: str,
        figure_ids: list[str],
        vendor_ids: list[str],
        canon: CanonManifest,
    ) -> None:
        """
        Raises ScopeUndeclaredError if any figure_id or vendor_id is not in the canon manifest.

        Does NOT validate that the figures are locked — only that they are declared.
        """
        errors: list[str] = []

        # Check article is declared
        article = canon.get_article(article_id)
        if article is None:
            errors.append(f"Article '{article_id}' is not declared in articles.yaml")

        # Check all figure_ids
        for fid in figure_ids:
            if canon.get_figure(fid) is None:
                errors.append(f"Figure '{fid}' is not declared in figures.yaml")

        # Check all vendor_ids
        for vid in vendor_ids:
            if canon.get_vendor(vid) is None:
                errors.append(f"Vendor '{vid}' is not declared in vendor_scope.yaml")

        if errors:
            raise ScopeUndeclaredError(
                scope_type="article",
                identifier=article_id,
                article_id=article_id,
            )

    def validate_denominator_consistency(
        self,
        figure_ids: list[str],
        canon: CanonManifest,
    ) -> None:
        """
        Raises DenominatorMixError if figure_ids contains an incompatible mix
        of budgeted and actual denominators.

        The $10,592,850 Object 7 overage is derived from budget vs. actual.
        The $13,326,622 staffing total is a payment sum, NOT an Object 7 number.
        These must not be presented as equivalent without explicit labeling.

        The check:
        - If any BUDGETED figure and any ACTUAL figure (from incompatible pairs)
          appear together, raise DenominatorMixError.
        """
        fid_set = set(figure_ids)

        for budgeted_id, actual_id in _INCOMPATIBLE_DENOMINATOR_PAIRS:
            if budgeted_id in fid_set and actual_id in fid_set:
                # Check if the canon allows this combination via metadata
                # (Currently no canon metadata for this — always raise)
                raise DenominatorMixError(
                    figure_ids=[budgeted_id, actual_id],
                    reason=(
                        f"'{budgeted_id}' (budgeted) and '{actual_id}' (actual payment sum) "
                        "cannot be mixed in the same calculation without explicit disclosure. "
                        "These represent different denominators and different scopes."
                    ),
                )

    def reconcile(
        self,
        article_id: str,
        figure_ids: list[str],
        vendor_ids: list[str],
        canon: CanonManifest,
        check_denominators: bool = True,
    ) -> None:
        """
        Run both validations. Convenience method for workflow use.
        """
        self.validate_article_scope(article_id, figure_ids, vendor_ids, canon)
        if check_denominators:
            self.validate_denominator_consistency(figure_ids, canon)
