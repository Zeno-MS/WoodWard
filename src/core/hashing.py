"""
src/core/hashing.py
Deterministic SHA-256 hashing for files and the canonical directory.
The canon hash is emitted at the start of every workflow run to prove
that the canonical state at run time matches what was locked.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class CanonHash:
    """
    Represents a snapshot of the canonical/ directory at a point in time.
    Fields:
        timestamp: ISO 8601 UTC string when the hash was computed
        individual_hashes: {relative_path: sha256_hex} for every file hashed
        combined_hash: sha256 of all individual hashes concatenated in sorted path order
        schema_version: value from canonical/schema_version.yaml if readable, else None
    """
    timestamp: str
    individual_hashes: dict[str, str]
    combined_hash: str
    schema_version: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "individual_hashes": self.individual_hashes,
            "combined_hash": self.combined_hash,
            "schema_version": self.schema_version,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> CanonHash:
        return cls(
            timestamp=data["timestamp"],
            individual_hashes=data["individual_hashes"],
            combined_hash=data["combined_hash"],
            schema_version=data.get("schema_version"),
        )


def hash_file(path: Path) -> str:
    """
    Compute the SHA-256 hash of a single file.
    Reads the file in binary mode in 64KB chunks to handle large files efficiently.
    """
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def hash_directory(path: Path) -> dict[str, str]:
    """
    Compute SHA-256 hashes for all files in a directory (recursive).
    Returns {relative_path_str: sha256_hex} sorted by path.
    Hidden files (starting with .) are excluded.
    """
    if not path.is_dir():
        raise ValueError(f"hash_directory: path is not a directory: {path}")

    result: dict[str, str] = {}
    for file_path in sorted(path.rglob("*")):
        if not file_path.is_file():
            continue
        # Skip hidden files and __pycache__
        parts = file_path.parts
        if any(p.startswith(".") or p == "__pycache__" for p in parts):
            continue
        relative = str(file_path.relative_to(path))
        result[relative] = hash_file(file_path)

    return result


def hash_canon(canonical_path: Path) -> CanonHash:
    """
    Hash the entire canonical/ directory and return a CanonHash.

    The combined_hash is computed as the SHA-256 of the concatenation of
    "path:hash\n" strings in sorted path order. This makes it deterministic
    and sensitive to any file addition, modification, or deletion.
    """
    if not canonical_path.is_dir():
        raise ValueError(f"hash_canon: canonical path does not exist: {canonical_path}")

    individual_hashes = hash_directory(canonical_path)
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Build the combined hash from sorted (path, hash) pairs
    combined_input = "\n".join(
        f"{k}:{v}" for k, v in sorted(individual_hashes.items())
    ).encode("utf-8")
    combined_hash = hashlib.sha256(combined_input).hexdigest()

    # Try to read schema_version
    schema_version = None
    schema_file = canonical_path / "schema_version.yaml"
    if schema_file.exists():
        try:
            import yaml  # type: ignore
            with open(schema_file) as f:
                data = yaml.safe_load(f)
                schema_version = data.get("schema_version")
        except Exception:
            pass

    return CanonHash(
        timestamp=timestamp,
        individual_hashes=individual_hashes,
        combined_hash=combined_hash,
        schema_version=schema_version,
    )
