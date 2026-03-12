"""
src/services/audit_runner.py
AuditRunner — runs all integrity checks against canonical state, ledger.db, and records.db.

This is the Phase 7 audit engine. Each check method can be called independently or
via run_full_audit() which runs all checks and produces a JSON-serializable AuditReport.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field

from schemas.canonical import CanonManifest
from src.core.hashing import hash_canon
from src.core.settings import WoodwardSettings
from src.repositories.canonical_repo import CanonicalRepo
from src.repositories.comms_repo import CommsRepo
from src.repositories.ledger_repo import LedgerRepo
from src.repositories.records_repo import RecordsRepo
from src.services.figure_verifier import FigureVerifier, FigureVerificationResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models for the audit report
# ---------------------------------------------------------------------------

class AuditCheck(BaseModel):
    """Result of a single audit check."""
    name: str
    status: str  # "pass" | "fail"
    details: list[str] = Field(default_factory=list)
    count: int = 0  # Number of issues found (0 = pass)


class AuditReport(BaseModel):
    """Full audit report with all check results."""
    audit_timestamp: str
    canon_hash: str
    checks: list[AuditCheck] = Field(default_factory=list)
    overall_status: str = "pass"  # "pass" | "fail"
    summary: dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# AuditRunner
# ---------------------------------------------------------------------------

class AuditRunner:
    """
    Runs all integrity checks against canonical state, ledger.db, and records.db.
    Each check method returns an AuditCheck.
    run_full_audit() aggregates all checks into an AuditReport.
    """

    def __init__(
        self,
        settings: WoodwardSettings,
        canonical_repo: CanonicalRepo,
        ledger_repo: LedgerRepo,
        records_repo: RecordsRepo,
        comms_repo: CommsRepo,
    ) -> None:
        self.settings = settings
        self.canonical_repo = canonical_repo
        self.ledger_repo = ledger_repo
        self.records_repo = records_repo
        self.comms_repo = comms_repo

    async def run_full_audit(self) -> AuditReport:
        """Run all audit checks and return a complete AuditReport."""
        timestamp = datetime.now(timezone.utc).isoformat()

        # Load canonical state
        canon = self.canonical_repo.load_all()
        canon_hash_obj = hash_canon(self.settings.canonical_path_obj)
        canon_hash = canon_hash_obj.combined_hash

        # Run all checks
        checks: list[AuditCheck] = []

        check_figures = await self.verify_all_locked_figures(canon)
        checks.append(check_figures)

        check_support = await self.verify_support_chains(canon)
        checks.append(check_support)

        check_banned = await self.detect_stale_banned_references(canon)
        checks.append(check_banned)

        check_orphaned = await self.detect_orphaned_claims(canon)
        checks.append(check_orphaned)

        check_missing_docs = await self.detect_missing_source_documents()
        checks.append(check_missing_docs)

        # Determine overall status
        overall_status = "pass" if all(c.status == "pass" for c in checks) else "fail"

        # Build summary
        summary = {
            "total_checks": len(checks),
            "passed": sum(1 for c in checks if c.status == "pass"),
            "failed": sum(1 for c in checks if c.status == "fail"),
            "total_issues": sum(c.count for c in checks),
            "locked_figures": len(canon.get_locked_figures()),
            "total_claims_registry": len(canon.claims),
            "total_banned_claims": len(canon.banned_claims),
        }

        report = AuditReport(
            audit_timestamp=timestamp,
            canon_hash=canon_hash,
            checks=checks,
            overall_status=overall_status,
            summary=summary,
        )

        logger.info(
            f"Audit complete: {overall_status.upper()} — "
            f"{summary['passed']}/{summary['total_checks']} checks passed, "
            f"{summary['total_issues']} total issues"
        )

        return report

    # ------------------------------------------------------------------
    # Check 1: Verify all locked figures
    # ------------------------------------------------------------------

    async def verify_all_locked_figures(
        self, canon: Optional[CanonManifest] = None
    ) -> AuditCheck:
        """
        Load all locked figures from canonical/figures.yaml.
        For each, run figure_verifier to confirm the canonical value matches
        the derivation. Report pass/fail per figure.
        """
        if canon is None:
            canon = self.canonical_repo.load_all()

        locked_figures = canon.get_locked_figures()
        verifier = FigureVerifier()

        details: list[str] = []
        fail_count = 0

        for figure in locked_figures:
            result: FigureVerificationResult = await verifier.verify(
                figure.figure_id, canon, self.ledger_repo
            )
            if result.status == "pass":
                details.append(
                    f"PASS: {figure.figure_id} "
                    f"(canonical={figure.value:,.0f}, computed={result.computed_value:,.0f})"
                )
            elif result.status == "no_derivation":
                details.append(
                    f"WARN: {figure.figure_id} — no derivation found (not a failure)"
                )
            else:
                fail_count += 1
                details.append(
                    f"FAIL: {figure.figure_id} — {result.notes}"
                )

        status = "fail" if fail_count > 0 else "pass"

        return AuditCheck(
            name="verify_all_locked_figures",
            status=status,
            details=details,
            count=fail_count,
        )

    # ------------------------------------------------------------------
    # Check 2: Verify support chains
    # ------------------------------------------------------------------

    async def verify_support_chains(
        self, canon: Optional[CanonManifest] = None
    ) -> AuditCheck:
        """
        Load all claims from records.db where status != 'blocked'.
        For each, check that claim_support rows exist and that the
        support chain is complete. Report any claims that are publishable
        but lack complete support.
        """
        if canon is None:
            canon = self.canonical_repo.load_all()

        details: list[str] = []
        fail_count = 0

        # Get all non-blocked claims from records.db
        async with self.records_repo.db_connection() as db:
            async with db.execute(
                "SELECT claim_id, article_id, status, public_citable, "
                "support_chain_complete FROM claims "
                "WHERE status != 'blocked'"
            ) as cursor:
                rows = await cursor.fetchall()

        for row in rows:
            claim_id = row[0]
            article_id = row[1]
            status = row[2]
            public_citable = row[3]
            support_chain_complete = row[4]

            # Only check claims that could be published
            if status == "verified" and public_citable == 1:
                if support_chain_complete != 1:
                    fail_count += 1
                    details.append(
                        f"FAIL: {claim_id} (article={article_id}) — "
                        f"verified+public_citable but support_chain_complete=0"
                    )
                    continue

                # Check that at least one claim_support row exists
                support_rows = await self.records_repo.get_claim_support(claim_id)
                if not support_rows:
                    fail_count += 1
                    details.append(
                        f"FAIL: {claim_id} (article={article_id}) — "
                        f"support_chain_complete=1 but no ClaimSupport rows"
                    )
                else:
                    details.append(
                        f"PASS: {claim_id} — {len(support_rows)} support doc(s)"
                    )

        status = "fail" if fail_count > 0 else "pass"

        return AuditCheck(
            name="verify_support_chains",
            status=status,
            details=details,
            count=fail_count,
        )

    # ------------------------------------------------------------------
    # Check 3: Detect stale banned references
    # ------------------------------------------------------------------

    async def detect_stale_banned_references(
        self, canon: Optional[CanonManifest] = None
    ) -> AuditCheck:
        """
        Load banned_claims.yaml. Scan claims_registry.yaml and figures.yaml
        for any reference to a banned ID. Also scan records.db claims table
        for any claim whose claim_id matches a banned entry.
        """
        if canon is None:
            canon = self.canonical_repo.load_all()

        banned_claims = canon.banned_claims
        banned_ids = {b.ban_id for b in banned_claims}

        details: list[str] = []
        fail_count = 0

        # Check claims_registry.yaml for claim_ids matching banned ban_ids
        registry_claim_ids = {c.claim_id for c in canon.claims}
        for ban_id in banned_ids:
            if ban_id in registry_claim_ids:
                fail_count += 1
                details.append(
                    f"FAIL: Banned ID '{ban_id}' found as claim_id in claims_registry.yaml"
                )

        # Check figures.yaml for figure_ids matching banned ban_ids
        figure_ids = {f.figure_id for f in canon.figures}
        for ban_id in banned_ids:
            if ban_id in figure_ids:
                fail_count += 1
                details.append(
                    f"FAIL: Banned ID '{ban_id}' found as figure_id in figures.yaml"
                )

        # Check records.db claims table for claim_ids matching banned ban_ids
        for ban_id in banned_ids:
            claim = await self.records_repo.get_claim(ban_id)
            if claim is not None:
                fail_count += 1
                details.append(
                    f"FAIL: Banned ID '{ban_id}' found as claim_id in records.db"
                )

        if fail_count == 0:
            details.append(
                f"PASS: No stale banned references found "
                f"({len(banned_ids)} banned IDs checked)"
            )

        status = "fail" if fail_count > 0 else "pass"

        return AuditCheck(
            name="detect_stale_banned_references",
            status=status,
            details=details,
            count=fail_count,
        )

    # ------------------------------------------------------------------
    # Check 4: Detect orphaned claims
    # ------------------------------------------------------------------

    async def detect_orphaned_claims(
        self, canon: Optional[CanonManifest] = None
    ) -> AuditCheck:
        """
        Find claims in records.db that have no corresponding entry in
        canonical/claims_registry.yaml, or claims in the registry that
        have no corresponding row in records.db.
        """
        if canon is None:
            canon = self.canonical_repo.load_all()

        registry_ids = {c.claim_id for c in canon.claims}

        # Get all claim_ids from records.db
        async with self.records_repo.db_connection() as db:
            async with db.execute("SELECT claim_id FROM claims") as cursor:
                db_rows = await cursor.fetchall()
        db_ids = {row[0] for row in db_rows}

        details: list[str] = []
        fail_count = 0

        # Claims in DB but not in registry
        in_db_not_registry = db_ids - registry_ids
        for cid in sorted(in_db_not_registry):
            fail_count += 1
            details.append(
                f"FAIL: Claim '{cid}' exists in records.db but not in claims_registry.yaml"
            )

        # Claims in registry but not in DB
        in_registry_not_db = registry_ids - db_ids
        for cid in sorted(in_registry_not_db):
            fail_count += 1
            details.append(
                f"FAIL: Claim '{cid}' exists in claims_registry.yaml but not in records.db"
            )

        if fail_count == 0:
            details.append(
                f"PASS: All {len(registry_ids)} registry claims have matching records.db rows"
            )

        status = "fail" if fail_count > 0 else "pass"

        return AuditCheck(
            name="detect_orphaned_claims",
            status=status,
            details=details,
            count=fail_count,
        )

    # ------------------------------------------------------------------
    # Check 5: Detect missing source documents
    # ------------------------------------------------------------------

    async def detect_missing_source_documents(self) -> AuditCheck:
        """
        Find claims in records.db where the support chain references
        a document_id that doesn't exist in the documents table.
        """
        details: list[str] = []
        fail_count = 0

        # Get all support rows with doc_id references
        async with self.records_repo.db_connection() as db:
            async with db.execute(
                "SELECT cs.support_id, cs.claim_id, cs.doc_id "
                "FROM claim_support cs "
                "WHERE cs.doc_id IS NOT NULL"
            ) as cursor:
                support_rows = await cursor.fetchall()

        for row in support_rows:
            support_id = row[0]
            claim_id = row[1]
            doc_id = row[2]

            doc = await self.records_repo.get_document(doc_id)
            if doc is None:
                fail_count += 1
                details.append(
                    f"FAIL: ClaimSupport '{support_id}' (claim={claim_id}) "
                    f"references doc_id='{doc_id}' which does not exist in documents table"
                )

        if fail_count == 0:
            details.append(
                f"PASS: All {len(support_rows)} support document references are valid"
            )

        status = "fail" if fail_count > 0 else "pass"

        return AuditCheck(
            name="detect_missing_source_documents",
            status=status,
            details=details,
            count=fail_count,
        )
