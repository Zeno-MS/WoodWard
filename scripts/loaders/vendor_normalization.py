from __future__ import annotations

from datetime import datetime
from typing import Any


VENDOR_ALIASES: dict[str, dict[str, Any]] = {
    "AMERGIS HEALTHCARE STAFFING INC": {
        "normalized_name": "Amergis/Maxim",
        "vendor_type": "Staffing Agency",
        "parent_company": "Maxim Healthcare Services",
        "aliases": [
            "Amergis Education",
            "Amergis Healthcare",
            "Amergis Staffing",
            "AMERGIS EDUCATION",
            "AMERGIS EDUCATION STAFFING",
        ],
        "notes": "Rebranded from Maxim Healthcare Staffing in 2022. $150M Medicaid fraud settlement (2011).",
    },
    "MAXIM HEALTHCARE SERVICES INC": {
        "normalized_name": "Amergis/Maxim",
        "vendor_type": "Staffing Agency",
        "parent_company": "Maxim Healthcare Services",
        "aliases": ["Maxim Healthcare Staffing", "Maxim Healthcare"],
        "notes": "Pre-rebrand name. Same entity as Amergis Healthcare Staffing.",
    },
    "SOLIANT HEALTH LLC": {
        "normalized_name": "Soliant Health",
        "vendor_type": "Staffing Agency",
        "parent_company": None,
        "aliases": ["Soliant"],
        "notes": "Competitor to Amergis in VPS staffing ecosystem.",
    },
    "PIONEER HEALTHCARE SERVICES LLC": {
        "normalized_name": "Pioneer Healthcare",
        "vendor_type": "Staffing Agency",
        "parent_company": None,
        "aliases": [],
        "notes": "Staffing agency — investigation target.",
    },
    "PIONEER TRUST BANK/CORP INC": {
        "normalized_name": "Pioneer Trust Bank",
        "vendor_type": "Bank",
        "parent_company": None,
        "aliases": [],
        "notes": "Financial institution. NOT a staffing vendor.",
    },
    "PIONEER CREDIT RECEOVERY": {
        "normalized_name": "Pioneer Credit Recovery",
        "vendor_type": "Collections",
        "parent_company": None,
        "aliases": [],
        "notes": "Collections agency. Unrelated to staffing.",
    },
    "PIONEER ATHLETICS": {
        "normalized_name": "Pioneer Athletics",
        "vendor_type": "Supply",
        "parent_company": None,
        "aliases": [],
        "notes": "Athletic supplies. Unrelated to staffing.",
    },
}

TARGET_VENDORS = {"Amergis/Maxim", "Soliant Health", "Pioneer Healthcare"}


def normalize_vendor(raw_payee: str) -> dict[str, Any]:
    payee = (raw_payee or "").strip()
    if not payee:
        return {
            "normalized_name": "",
            "vendor_type": "Unknown",
            "parent_company": None,
            "notes": None,
        }

    upper = payee.upper()
    if upper in VENDOR_ALIASES:
        return VENDOR_ALIASES[upper]

    for meta in VENDOR_ALIASES.values():
        for alias in meta.get("aliases", []):
            alias_upper = alias.upper()
            if alias_upper in upper or upper in alias_upper:
                return meta

    return {
        "normalized_name": payee,
        "vendor_type": "Unknown",
        "parent_company": None,
        "notes": None,
    }


def entry_date_to_fiscal_year(entry_date_str: str) -> str:
    dt = datetime.strptime(entry_date_str, "%m/%d/%Y")
    if dt.month >= 9:
        return f"{dt.year}-{str(dt.year + 1)[2:]}"
    return f"{dt.year - 1}-{str(dt.year)[2:]}"


def normalize_date(date_str: str | None) -> str | None:
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None
