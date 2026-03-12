"""
tests/unit/test_hashing.py
Unit tests for the canonical hashing functions.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

from src.core.hashing import CanonHash, hash_canon, hash_directory, hash_file


# ---------------------------------------------------------------------------
# Tests: hash_file
# ---------------------------------------------------------------------------

def test_hash_file_is_deterministic(tmp_path: Path) -> None:
    """SHA-256 of the same file content must always produce the same hash."""
    f = tmp_path / "test.txt"
    f.write_text("Vancouver Public Schools paid $13,326,622 to staffing vendors.")

    hash1 = hash_file(f)
    hash2 = hash_file(f)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256 hex = 64 chars


def test_hash_file_changes_on_content_change(tmp_path: Path) -> None:
    """A different file content must produce a different hash."""
    f = tmp_path / "test.txt"
    f.write_text("Original content")
    hash1 = hash_file(f)

    f.write_text("Modified content — even one character change matters")
    hash2 = hash_file(f)

    assert hash1 != hash2


def test_hash_file_is_hex_string(tmp_path: Path) -> None:
    """hash_file must return a valid hex string."""
    f = tmp_path / "test.yaml"
    f.write_text("key: value\n")
    result = hash_file(f)
    int(result, 16)  # Will raise ValueError if not valid hex


# ---------------------------------------------------------------------------
# Tests: hash_directory
# ---------------------------------------------------------------------------

def test_hash_directory_includes_all_files(tmp_path: Path) -> None:
    """hash_directory must return an entry for every file in the directory."""
    d = tmp_path / "canon"
    d.mkdir()
    (d / "figures.yaml").write_text("figures: []")
    (d / "vendor_scope.yaml").write_text("vendors: []")
    (d / "schema_version.yaml").write_text("schema_version: '1.0.0'")

    result = hash_directory(d)

    assert len(result) == 3
    assert "figures.yaml" in result
    assert "vendor_scope.yaml" in result
    assert "schema_version.yaml" in result


def test_hash_directory_is_deterministic(tmp_path: Path) -> None:
    """Two calls to hash_directory on the same files must produce the same result."""
    d = tmp_path / "canon"
    d.mkdir()
    (d / "figures.yaml").write_text("figures: []\n")
    (d / "claims.yaml").write_text("claims: []\n")

    result1 = hash_directory(d)
    result2 = hash_directory(d)

    assert result1 == result2


def test_hash_directory_excludes_hidden_files(tmp_path: Path) -> None:
    """Hidden files (starting with .) must not appear in the hash."""
    d = tmp_path / "canon"
    d.mkdir()
    (d / "figures.yaml").write_text("figures: []")
    (d / ".hidden_file").write_text("secret")

    result = hash_directory(d)

    assert ".hidden_file" not in result
    assert "figures.yaml" in result


def test_hash_directory_handles_subdirectories(tmp_path: Path) -> None:
    """Files in subdirectories must be included with relative paths."""
    d = tmp_path / "canon"
    d.mkdir()
    sub = d / "sub"
    sub.mkdir()
    (d / "root.yaml").write_text("root: true")
    (sub / "nested.yaml").write_text("nested: true")

    result = hash_directory(d)

    assert "root.yaml" in result
    # Nested file should appear with a relative path
    assert any("nested.yaml" in k for k in result)


# ---------------------------------------------------------------------------
# Tests: hash_canon
# ---------------------------------------------------------------------------

def test_hash_canon_returns_canon_hash_object(tmp_path: Path) -> None:
    """hash_canon must return a CanonHash with required fields."""
    d = tmp_path / "canonical"
    d.mkdir()
    (d / "figures.yaml").write_text("figures: []\n")
    (d / "schema_version.yaml").write_text(
        "schema_version: '1.0.0'\ncreated: '2026-03-12'\n"
        "investigation: test\nlocked_by: test\n"
    )

    result = hash_canon(d)

    assert isinstance(result, CanonHash)
    assert result.combined_hash
    assert len(result.combined_hash) == 64
    assert result.timestamp
    assert result.individual_hashes


def test_hash_canon_includes_schema_version(tmp_path: Path) -> None:
    """hash_canon must read and include schema_version from schema_version.yaml."""
    d = tmp_path / "canonical"
    d.mkdir()
    (d / "schema_version.yaml").write_text(
        "schema_version: '1.0.0'\ncreated: '2026-03-12'\n"
        "investigation: vps_2026\nlocked_by: woodward-core-v2\n"
    )

    result = hash_canon(d)
    assert result.schema_version == "1.0.0"


def test_canon_hash_changes_on_file_modification(tmp_path: Path) -> None:
    """Modifying any canonical file must change the combined hash."""
    d = tmp_path / "canonical"
    d.mkdir()
    figures_file = d / "figures.yaml"
    figures_file.write_text("figures: []\n")
    (d / "schema_version.yaml").write_text("schema_version: '1.0.0'\ncreated: x\ninvestigation: t\nlocked_by: t\n")

    hash_before = hash_canon(d)

    # Modify the figures file
    figures_file.write_text("figures:\n  - figure_id: new_fig\n")

    hash_after = hash_canon(d)

    assert hash_before.combined_hash != hash_after.combined_hash


def test_canon_hash_to_dict_roundtrip(tmp_path: Path) -> None:
    """CanonHash.to_dict() -> CanonHash.from_dict() must be lossless."""
    d = tmp_path / "canonical"
    d.mkdir()
    (d / "test.yaml").write_text("key: value\n")

    original = hash_canon(d)
    restored = CanonHash.from_dict(original.to_dict())

    assert restored.combined_hash == original.combined_hash
    assert restored.individual_hashes == original.individual_hashes
    assert restored.schema_version == original.schema_version


def test_hash_canon_raises_on_nonexistent_directory(tmp_path: Path) -> None:
    """hash_canon must raise ValueError if the directory doesn't exist."""
    nonexistent = tmp_path / "does_not_exist"

    with pytest.raises(ValueError, match="canonical path does not exist"):
        hash_canon(nonexistent)
