"""
src/services/vendor_alias_resolver.py
Resolves vendor names (including historical rebrand names) to canonical VendorScope entries.
Critical for deduplication: Maxim Healthcare and Amergis are the same vendor.
"""
from __future__ import annotations

from typing import Optional

from schemas.canonical import VendorScope
from src.core.exceptions import ScopeUndeclaredError


class VendorAliasResolver:
    """
    Resolves vendor name strings to their canonical VendorScope entry.

    Matching is case-insensitive and strips common punctuation variants.
    The resolver checks:
    1. canonical_name exact match
    2. aliases list (case-insensitive)
    3. rebrand_history from/to names (case-insensitive)
    """

    def _normalize(self, name: str) -> str:
        """Normalize a name string for comparison."""
        return name.strip().lower().replace(",", "").replace(".", "")

    def resolve(self, name: str, vendor_scope: list[VendorScope]) -> Optional[VendorScope]:
        """
        Attempt to resolve a vendor name string to a VendorScope.
        Returns None if no match is found.
        """
        normalized = self._normalize(name)

        for vendor in vendor_scope:
            # Check canonical name
            if self._normalize(vendor.canonical_name) == normalized:
                return vendor

            # Check aliases list
            for alias in vendor.aliases:
                if self._normalize(alias) == normalized:
                    return vendor

            # Check rebrand history (both from and to names)
            for rebrand in vendor.rebrand_history:
                if self._normalize(rebrand.from_name) == normalized:
                    return vendor
                if self._normalize(rebrand.to) == normalized:
                    return vendor

        return None

    def assert_canonical(
        self, vendor_id: str, vendor_scope: list[VendorScope]
    ) -> VendorScope:
        """
        Return the VendorScope for a vendor_id, or raise ScopeUndeclaredError
        if the vendor_id is not declared in the canonical scope.

        Use this when you have a vendor_id and need to assert it is valid.
        """
        for vendor in vendor_scope:
            if vendor.vendor_id == vendor_id:
                return vendor

        raise ScopeUndeclaredError(
            scope_type="vendor",
            identifier=vendor_id,
        )

    def get_all_aliases(
        self, vendor_id: str, vendor_scope: list[VendorScope]
    ) -> list[str]:
        """
        Return all known name strings for a vendor: canonical name + aliases +
        rebrand history names.

        Raises ScopeUndeclaredError if vendor_id is not found.
        """
        vendor = self.assert_canonical(vendor_id, vendor_scope)

        all_names: list[str] = [vendor.canonical_name]
        all_names.extend(vendor.aliases)

        for rebrand in vendor.rebrand_history:
            if rebrand.from_name not in all_names:
                all_names.append(rebrand.from_name)
            if rebrand.to not in all_names:
                all_names.append(rebrand.to)

        return all_names

    def resolve_or_raise(
        self, name: str, vendor_scope: list[VendorScope], article_id: str = ""
    ) -> VendorScope:
        """
        Resolve a vendor name or raise ScopeUndeclaredError.
        Use this in strict enforcement contexts.
        """
        result = self.resolve(name, vendor_scope)
        if result is None:
            raise ScopeUndeclaredError(
                scope_type="vendor",
                identifier=name,
                article_id=article_id,
            )
        return result
