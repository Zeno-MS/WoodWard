"""
src/core/types.py
Type aliases for Woodward Core v2.
Import these from here rather than redefining them in individual modules.
"""
from __future__ import annotations

from typing import Literal

# ---------------------------------------------------------------------------
# ID types — all are strings but named distinctly for readability
# ---------------------------------------------------------------------------

FigureId = str
ClaimId = str
ArticleId = str
VendorId = str
RunId = str
DerivationId = str
SectionId = str
DocumentId = str
ChunkId = str
ThreadId = str

# ---------------------------------------------------------------------------
# Source class — governs what may be cited in publication-bound drafts
# ---------------------------------------------------------------------------

SourceClass = Literal[
    "public_record",
    "public_reporting",
    "public_records_response",
    "public_agency_finding",
    "internal_nonpublic",
    "memory_only",
    "insider_awareness",
    "webapp_export",
]

# ---------------------------------------------------------------------------
# Claim status lifecycle
# ---------------------------------------------------------------------------

ClaimStatus = Literal[
    "draft",
    "verified",
    "blocked",
    "superseded",
    "pending_review",
]

# ---------------------------------------------------------------------------
# Figure status
# ---------------------------------------------------------------------------

FigureStatus = Literal[
    "locked",
    "provisional",
    "superseded",
]

# ---------------------------------------------------------------------------
# Article status
# ---------------------------------------------------------------------------

ArticleStatus = Literal[
    "locked_baseline",
    "draft",
    "published",
]

# ---------------------------------------------------------------------------
# Source policy disposition
# ---------------------------------------------------------------------------

SourcePolicyStatus = Literal[
    "allowed",
    "blocked",
    "pending_review",
]

# ---------------------------------------------------------------------------
# Adversarial finding severity
# ---------------------------------------------------------------------------

FindingSeverity = Literal["blocker", "warning", "note"]

# ---------------------------------------------------------------------------
# Derivation status
# ---------------------------------------------------------------------------

DerivationStatus = Literal["pending", "computed", "verified", "mismatch"]

# ---------------------------------------------------------------------------
# Figure verification result status
# ---------------------------------------------------------------------------

VerificationStatus = Literal["pass", "fail", "no_derivation"]
