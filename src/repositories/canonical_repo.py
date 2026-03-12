"""
src/repositories/canonical_repo.py
Loads and validates canonical YAML files from the canonical/ directory.
This is the primary interface to canonical state in the Woodward system.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml  # type: ignore
from pydantic import ValidationError

from schemas.canonical import (
    ArticleRecord,
    BannedClaim,
    CanonManifest,
    CanonicalFigure,
    ClaimRecord,
    SchemaVersion,
    SourcePolicy,
    VendorScope,
    RebrandHistory,
)
from src.core.exceptions import CanonValidationError


class CanonicalRepo:
    """
    Repository for reading and validating canonical YAML files.

    All methods raise CanonValidationError on schema violations.
    The canonical directory path is injected at construction time.
    """

    def __init__(self, canonical_path: Path) -> None:
        if not canonical_path.is_dir():
            raise CanonValidationError(
                f"Canonical path does not exist or is not a directory: {canonical_path}"
            )
        self._path = canonical_path

    def _load_yaml(self, filename: str) -> dict | list:
        file_path = self._path / filename
        if not file_path.exists():
            raise CanonValidationError(
                f"Canonical file not found: {file_path}",
                context={"file": filename},
            )
        with open(file_path, encoding="utf-8") as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise CanonValidationError(
                    f"YAML parse error in {filename}: {e}",
                    context={"file": filename},
                ) from e

    def load_schema_version(self) -> SchemaVersion:
        data = self._load_yaml("schema_version.yaml")
        try:
            return SchemaVersion.model_validate(data)
        except ValidationError as e:
            raise CanonValidationError(
                f"schema_version.yaml validation failed: {e}",
                context={"file": "schema_version.yaml"},
            ) from e

    def load_figures(self) -> list[CanonicalFigure]:
        data = self._load_yaml("figures.yaml")
        figures_raw = data.get("figures", []) if isinstance(data, dict) else data
        figures = []
        errors = []
        for i, item in enumerate(figures_raw):
            try:
                figures.append(CanonicalFigure.model_validate(item))
            except ValidationError as e:
                errors.append(f"figures.yaml[{i}] ({item.get('figure_id', '?')}): {e}")
        if errors:
            raise CanonValidationError(
                f"figures.yaml has {len(errors)} validation error(s):\n" + "\n".join(errors),
                context={"file": "figures.yaml"},
            )
        return figures

    def load_vendor_scope(self) -> list[VendorScope]:
        data = self._load_yaml("vendor_scope.yaml")
        vendors_raw = data.get("vendors", []) if isinstance(data, dict) else data
        vendors = []
        errors = []
        for i, item in enumerate(vendors_raw):
            try:
                # Normalize rebrand_history: 'from' key is aliased to 'from_name'
                if "rebrand_history" in item:
                    normalized_history = []
                    for entry in item["rebrand_history"]:
                        normalized_history.append(
                            RebrandHistory.model_validate(entry)
                        )
                    item = dict(item)
                    item["rebrand_history"] = [r.model_dump(by_alias=True) for r in normalized_history]
                vendors.append(VendorScope.model_validate(item))
            except (ValidationError, Exception) as e:
                errors.append(f"vendor_scope.yaml[{i}] ({item.get('vendor_id', '?')}): {e}")
        if errors:
            raise CanonValidationError(
                f"vendor_scope.yaml has {len(errors)} validation error(s):\n" + "\n".join(errors),
                context={"file": "vendor_scope.yaml"},
            )
        return vendors

    def load_articles(self) -> list[ArticleRecord]:
        data = self._load_yaml("articles.yaml")
        articles_raw = data.get("articles", []) if isinstance(data, dict) else data
        articles = []
        errors = []
        for i, item in enumerate(articles_raw):
            # Tolerate the YAML key collision 'article_4\n    article_id' seen in seed
            if isinstance(item, dict):
                # Remove any accidental duplicate key artifacts
                clean = {k: v for k, v in item.items() if k != "article_4"}
            else:
                clean = item
            try:
                articles.append(ArticleRecord.model_validate(clean))
            except ValidationError as e:
                errors.append(f"articles.yaml[{i}] ({item.get('article_id', '?')}): {e}")
        if errors:
            raise CanonValidationError(
                f"articles.yaml has {len(errors)} validation error(s):\n" + "\n".join(errors),
                context={"file": "articles.yaml"},
            )
        return articles

    def load_claims(self) -> list[ClaimRecord]:
        data = self._load_yaml("claims_registry.yaml")
        claims_raw = data.get("claims", []) if isinstance(data, dict) else data
        claims = []
        errors = []
        for i, item in enumerate(claims_raw):
            try:
                claims.append(ClaimRecord.model_validate(item))
            except ValidationError as e:
                errors.append(f"claims_registry.yaml[{i}] ({item.get('claim_id', '?')}): {e}")
        if errors:
            raise CanonValidationError(
                f"claims_registry.yaml has {len(errors)} validation error(s):\n" + "\n".join(errors),
                context={"file": "claims_registry.yaml"},
            )
        return claims

    def load_banned_claims(self) -> list[BannedClaim]:
        data = self._load_yaml("banned_claims.yaml")
        bans_raw = data.get("banned_claims", []) if isinstance(data, dict) else data
        bans = []
        errors = []
        for i, item in enumerate(bans_raw):
            try:
                bans.append(BannedClaim.model_validate(item))
            except ValidationError as e:
                errors.append(f"banned_claims.yaml[{i}] ({item.get('ban_id', '?')}): {e}")
        if errors:
            raise CanonValidationError(
                f"banned_claims.yaml has {len(errors)} validation error(s):\n" + "\n".join(errors),
                context={"file": "banned_claims.yaml"},
            )
        return bans

    def load_source_policy(self) -> SourcePolicy:
        data = self._load_yaml("source_policy.yaml")
        try:
            return SourcePolicy.model_validate(data)
        except ValidationError as e:
            raise CanonValidationError(
                f"source_policy.yaml validation failed: {e}",
                context={"file": "source_policy.yaml"},
            ) from e

    def load_all(self) -> CanonManifest:
        """
        Load all canonical files and return a CanonManifest.
        Raises CanonValidationError if any file fails validation.
        """
        return CanonManifest(
            schema_version=self.load_schema_version(),
            figures=self.load_figures(),
            vendors=self.load_vendor_scope(),
            articles=self.load_articles(),
            claims=self.load_claims(),
            banned_claims=self.load_banned_claims(),
            source_policy=self.load_source_policy(),
        )

    def validate_all(self) -> None:
        """
        Validate all canonical files. Raises CanonValidationError on the first failure.
        Used by boot-time validation and the CLI canon validate command.
        """
        self.load_all()
