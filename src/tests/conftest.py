"""
src/tests/conftest.py
Shared test fixtures for Woodward Core v2 test suite.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path for all tests
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
