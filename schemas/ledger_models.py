"""
schemas/ledger_models.py
Pydantic v2 models matching the ledger.db schema.
ledger.db is the sole monetary source of truth.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Vendor(BaseModel):
    vendor_id: str
    canonical_name: str
    notes: Optional[str] = None
    created_at: Optional[str] = None


class VendorAlias(BaseModel):
    alias_id: str
    vendor_id: str
    alias: str
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None


class SourceDocument(BaseModel):
    doc_id: str
    title: Optional[str] = None
    doc_type: Optional[str] = None
    fiscal_year: Optional[str] = None
    source_class: Optional[str] = None
    file_path: Optional[str] = None
    url: Optional[str] = None
    date_acquired: Optional[str] = None
    notes: Optional[str] = None


class Payment(BaseModel):
    payment_id: str
    vendor_id: str
    amount: float
    fiscal_year: str
    payment_date: Optional[str] = None
    warrant_number: Optional[str] = None
    doc_id: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"Payment amount must be non-negative, got {v}")
        return v


class FiscalRollup(BaseModel):
    rollup_id: str
    vendor_id: str
    fiscal_year: str
    total_amount: float
    payment_count: Optional[int] = None
    source_doc_ids: Optional[str] = None  # JSON-encoded list of doc_ids
    computed_at: Optional[str] = None

    @field_validator("total_amount")
    @classmethod
    def total_must_be_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"FiscalRollup total_amount must be non-negative, got {v}")
        return v


ALLOWED_DERIVATION_STATUSES = {"pending", "computed", "verified", "mismatch", "csv_source", "doc_source"}


class FigureDerivation(BaseModel):
    derivation_id: str
    figure_id: str
    sql_query: str = Field(..., description="The SQL query used to compute the figure")
    computed_value: Optional[float] = None
    canonical_value: Optional[float] = None
    status: Optional[str] = None
    computed_at: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ALLOWED_DERIVATION_STATUSES:
            raise ValueError(
                f"Invalid derivation status '{v}'. Must be one of: {ALLOWED_DERIVATION_STATUSES}"
            )
        return v


class FigureLock(BaseModel):
    lock_id: str
    figure_id: str
    locked_value: float
    locked_at: Optional[str] = None
    locked_by: Optional[str] = None
    canon_hash: Optional[str] = None

    @field_validator("locked_value")
    @classmethod
    def locked_value_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"FigureLock locked_value must be non-negative, got {v}")
        return v


class DedupAudit(BaseModel):
    audit_id: str
    source: Optional[str] = None
    total_records: Optional[int] = None
    dedup_records: Optional[int] = None
    method: Optional[str] = None
    run_at: Optional[str] = None
