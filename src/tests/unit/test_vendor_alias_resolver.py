"""
tests/unit/test_vendor_alias_resolver.py
Unit tests for VendorAliasResolver.
Key test: Maxim Healthcare and Amergis resolve to the same vendor_id.
"""
from __future__ import annotations

import pytest

from schemas.canonical import RebrandHistory, VendorScope
from src.core.exceptions import ScopeUndeclaredError
from src.services.vendor_alias_resolver import VendorAliasResolver


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def vendor_scope() -> list[VendorScope]:
    """Minimal vendor scope mirroring the real vps_2026 canonical data."""
    return [
        VendorScope(
            vendor_id="amergis",
            canonical_name="Amergis Healthcare",
            aliases=[
                "Amergis",
                "Maxim Healthcare",
                "Maxim Healthcare Services",
                "Maxim",
            ],
            rebrand_history=[
                RebrandHistory(**{"from": "Maxim Healthcare Services", "to": "Amergis Healthcare", "effective_date": "2023-01-01"})
            ],
            canonical_total_included=True,
        ),
        VendorScope(
            vendor_id="aveanna_healthcare",
            canonical_name="Aveanna Healthcare",
            aliases=["Aveanna", "Aveanna Healthcare LLC"],
            rebrand_history=[],
            canonical_total_included=False,
        ),
        VendorScope(
            vendor_id="stepping_stones",
            canonical_name="Stepping Stones Group",
            aliases=["Stepping Stones", "The Stepping Stones Group"],
            rebrand_history=[],
            canonical_total_included=False,
        ),
    ]


@pytest.fixture
def resolver() -> VendorAliasResolver:
    return VendorAliasResolver()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_resolves_amergis_by_canonical_name(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """Canonical name 'Amergis Healthcare' must resolve to vendor_id='amergis'."""
    result = resolver.resolve("Amergis Healthcare", vendor_scope)
    assert result is not None
    assert result.vendor_id == "amergis"


def test_resolves_maxim_as_amergis_alias(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """'Maxim Healthcare' must resolve to the same vendor_id='amergis' as Amergis."""
    result = resolver.resolve("Maxim Healthcare", vendor_scope)
    assert result is not None
    assert result.vendor_id == "amergis"


def test_resolves_maxim_services_as_amergis_alias(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """'Maxim Healthcare Services' must also resolve to vendor_id='amergis'."""
    result = resolver.resolve("Maxim Healthcare Services", vendor_scope)
    assert result is not None
    assert result.vendor_id == "amergis"


def test_resolves_maxim_short_as_amergis(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """'Maxim' (short form) must resolve to vendor_id='amergis'."""
    result = resolver.resolve("Maxim", vendor_scope)
    assert result is not None
    assert result.vendor_id == "amergis"


def test_case_insensitive_resolution(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """Resolution must be case-insensitive."""
    result = resolver.resolve("amergis healthcare", vendor_scope)
    assert result is not None
    assert result.vendor_id == "amergis"

    result2 = resolver.resolve("MAXIM HEALTHCARE", vendor_scope)
    assert result2 is not None
    assert result2.vendor_id == "amergis"


def test_resolves_aveanna(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """Aveanna Healthcare must resolve to vendor_id='aveanna_healthcare'."""
    result = resolver.resolve("Aveanna Healthcare", vendor_scope)
    assert result is not None
    assert result.vendor_id == "aveanna_healthcare"
    assert result.canonical_total_included is False


def test_undeclared_vendor_returns_none(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """An unknown vendor name must return None."""
    result = resolver.resolve("Unknown Staffing Co LLC", vendor_scope)
    assert result is None


def test_undeclared_vendor_raises_scope_error(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """resolve_or_raise must raise ScopeUndeclaredError for unknown vendors."""
    with pytest.raises(ScopeUndeclaredError) as exc_info:
        resolver.resolve_or_raise("Fake Vendor Inc", vendor_scope)
    assert "Fake Vendor Inc" in str(exc_info.value)


def test_assert_canonical_known_vendor(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """assert_canonical must return the VendorScope for a known vendor_id."""
    result = resolver.assert_canonical("amergis", vendor_scope)
    assert result.vendor_id == "amergis"


def test_assert_canonical_unknown_raises(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """assert_canonical must raise ScopeUndeclaredError for an unknown vendor_id."""
    with pytest.raises(ScopeUndeclaredError):
        resolver.assert_canonical("nonexistent_vendor_id", vendor_scope)


def test_get_all_aliases_includes_rebrand_names(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """get_all_aliases must include both the canonical name and all historical names."""
    aliases = resolver.get_all_aliases("amergis", vendor_scope)
    assert "Amergis Healthcare" in aliases
    assert "Maxim Healthcare" in aliases
    assert "Maxim Healthcare Services" in aliases
    assert "Maxim" in aliases


def test_aveanna_not_in_canonical_total(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """Aveanna is excluded from the $32.1M canonical total."""
    result = resolver.assert_canonical("aveanna_healthcare", vendor_scope)
    assert result.canonical_total_included is False


def test_stepping_stones_not_in_canonical_total(
    resolver: VendorAliasResolver, vendor_scope: list[VendorScope]
) -> None:
    """Stepping Stones is excluded from the $32.1M canonical total."""
    result = resolver.assert_canonical("stepping_stones", vendor_scope)
    assert result.canonical_total_included is False
