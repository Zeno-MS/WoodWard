"""
src/services/canonical_lock_service.py
CanonicalLockService — validates canonical files, emits run-time hashes,
and enforces figure lock consistency.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from schemas.canonical import CanonManifest
from src.core.exceptions import CanonValidationError, FigureMismatchError
from src.core.hashing import CanonHash, hash_canon
from src.repositories.canonical_repo import CanonicalRepo


class CanonicalLockService:
    """
    Provides three functions:
    1. validate_canon — schema-validate all canonical YAML files (hard-stop on error)
    2. emit_canon_hash — hash the canonical directory and persist the hash as a run artifact
    3. check_figure_lock — verify that a computed value matches the locked canonical value
    """

    def validate_canon(self, canonical_path: Path) -> None:
        """
        Load and validate all canonical YAML files.
        Raises CanonValidationError (hard-stop) if any file fails schema validation.
        """
        repo = CanonicalRepo(canonical_path)
        repo.validate_all()

    def emit_canon_hash(
        self, canonical_path: Path, runs_path: Path, run_id: str
    ) -> CanonHash:
        """
        Hash the entire canonical/ directory and write the result to
        runs/{run_id}/canon_hash.json.

        Returns the CanonHash for use in the current run.
        """
        canon_hash = hash_canon(canonical_path)

        run_dir = runs_path / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        hash_file = run_dir / "canon_hash.json"
        hash_file.write_text(canon_hash.to_json(), encoding="utf-8")

        return canon_hash

    def check_figure_lock(
        self,
        figure_id: str,
        computed_value: float,
        canon: CanonManifest,
        tolerance: float = 1.0,
    ) -> None:
        """
        Verify that a computed value matches the locked canonical figure value.

        Args:
            figure_id: The figure to check (must exist in canon.figures)
            computed_value: The freshly computed value
            canon: The loaded CanonManifest
            tolerance: Allowed absolute difference (default 1.0 to handle float rounding)

        Raises:
            CanonValidationError: if figure_id is not found in canon
            FigureMismatchError: if |computed_value - canonical_value| > tolerance
        """
        figure = canon.get_figure(figure_id)
        if figure is None:
            raise CanonValidationError(
                f"Figure '{figure_id}' not found in canonical manifest",
                context={"figure_id": figure_id},
            )

        canonical_value = figure.value
        diff = abs(computed_value - canonical_value)

        if diff > tolerance:
            raise FigureMismatchError(
                figure_id=figure_id,
                computed_value=computed_value,
                canonical_value=canonical_value,
                notes=f"Difference of {diff:.2f} exceeds tolerance of {tolerance:.2f}",
            )
