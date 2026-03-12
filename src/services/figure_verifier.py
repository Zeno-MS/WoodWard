"""
src/services/figure_verifier.py
FigureVerifier — verifies locked figures by recomputing from ledger.db derivations.
The core anti-drift service: if a figure can't be reproduced from its SQL derivation,
the build hard-stops.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from schemas.canonical import CanonManifest
from src.core.exceptions import FigureMismatchError
from src.repositories.ledger_repo import LedgerRepo


@dataclass
class FigureVerificationResult:
    """Result of verifying a single locked figure."""
    figure_id: str
    derivation_id: Optional[str]
    computed_value: Optional[float]
    canonical_value: float
    status: str  # "pass" | "fail" | "no_derivation"
    notes: str = ""

    @property
    def passed(self) -> bool:
        return self.status == "pass"


class FigureVerifier:
    """
    Verifies that locked canonical figures can be reproduced from ledger.db derivations.

    Process per figure:
    1. Load the CanonicalFigure from the manifest
    2. Look up the FigureDerivation in ledger.db by derivation_id
    3. If a derivation exists and has a computed_value, compare to canonical value
    4. If derivation exists but has no computed_value, execute the SQL query
    5. Return FigureVerificationResult with status=pass|fail|no_derivation
    """

    TOLERANCE = 1.0  # Allowed absolute difference (handles float precision)

    async def verify(
        self,
        figure_id: str,
        canon: CanonManifest,
        ledger: LedgerRepo,
    ) -> FigureVerificationResult:
        """
        Verify a single figure.

        Returns FigureVerificationResult. Does NOT raise on mismatch — the caller
        (verify_figure workflow) decides whether to hard-stop.
        """
        figure = canon.get_figure(figure_id)
        if figure is None:
            return FigureVerificationResult(
                figure_id=figure_id,
                derivation_id=None,
                computed_value=None,
                canonical_value=0.0,
                status="no_derivation",
                notes=f"Figure '{figure_id}' not found in canonical manifest",
            )

        canonical_value = figure.value

        # Look up derivation from ledger.db
        derivation = await ledger.get_derivation_for_figure(figure_id)

        if derivation is None:
            return FigureVerificationResult(
                figure_id=figure_id,
                derivation_id=None,
                computed_value=None,
                canonical_value=canonical_value,
                status="no_derivation",
                notes=f"No derivation record found for figure '{figure_id}' in ledger.db",
            )

        # Use pre-computed value if available
        if derivation.computed_value is not None:
            computed_value = derivation.computed_value
        else:
            # Execute the derivation SQL query against ledger.db
            computed_value = await self._execute_derivation_query(
                ledger, derivation.sql_query, figure_id
            )

        if computed_value is None:
            return FigureVerificationResult(
                figure_id=figure_id,
                derivation_id=derivation.derivation_id,
                computed_value=None,
                canonical_value=canonical_value,
                status="no_derivation",
                notes=f"Derivation SQL returned no result for figure '{figure_id}'",
            )

        diff = abs(computed_value - canonical_value)
        if diff <= self.TOLERANCE:
            return FigureVerificationResult(
                figure_id=figure_id,
                derivation_id=derivation.derivation_id,
                computed_value=computed_value,
                canonical_value=canonical_value,
                status="pass",
                notes=f"Match within tolerance (diff={diff:.4f})",
            )
        else:
            return FigureVerificationResult(
                figure_id=figure_id,
                derivation_id=derivation.derivation_id,
                computed_value=computed_value,
                canonical_value=canonical_value,
                status="fail",
                notes=(
                    f"Mismatch: computed={computed_value:.2f}, "
                    f"canonical={canonical_value:.2f}, diff={diff:.2f}"
                ),
            )

    async def verify_and_raise(
        self,
        figure_id: str,
        canon: CanonManifest,
        ledger: LedgerRepo,
    ) -> FigureVerificationResult:
        """
        Verify and raise FigureMismatchError on failure.
        Use this in strict workflow contexts where a mismatch must hard-stop.
        """
        result = await self.verify(figure_id, canon, ledger)
        if result.status == "fail":
            raise FigureMismatchError(
                figure_id=figure_id,
                computed_value=result.computed_value or 0.0,
                canonical_value=result.canonical_value,
                notes=result.notes,
            )
        return result

    async def _execute_derivation_query(
        self, ledger: LedgerRepo, sql_query: str, figure_id: str
    ) -> Optional[float]:
        """
        Execute a derivation SQL query against ledger.db and return the scalar result.
        The query must return a single numeric value in the first column of the first row.
        """
        async with ledger.db_connection() as db:
            try:
                async with db.execute(sql_query) as cursor:
                    row = await cursor.fetchone()
                    if row is None or row[0] is None:
                        return None
                    return float(row[0])
            except Exception as e:
                return None
