"""
src/core/logging.py
Structured logging setup for Woodward Core v2.
Uses Python standard logging + Rich for console output.
Include run_id in all log records when available.
"""
from __future__ import annotations

import logging
import logging.config
from typing import Optional

# Rich handler is optional — fall back gracefully if not installed
try:
    from rich.logging import RichHandler
    _RICH_AVAILABLE = True
except ImportError:
    _RICH_AVAILABLE = False


class RunContextFilter(logging.Filter):
    """
    Injects run_id into every log record when set.
    Usage:
        set_run_id("my-run-123")
        logger.info("Starting verification")  # record.run_id = "my-run-123"
    """

    _run_id: Optional[str] = None

    @classmethod
    def set_run_id(cls, run_id: Optional[str]) -> None:
        cls._run_id = run_id

    @classmethod
    def clear_run_id(cls) -> None:
        cls._run_id = None

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = self._run_id or "-"
        return True


def configure_logging(level: str = "INFO", run_id: Optional[str] = None) -> None:
    """
    Configure root logging for the Woodward application.
    Call this once at application startup.
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Clear any existing handlers on root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()

    run_filter = RunContextFilter()
    if run_id:
        RunContextFilter.set_run_id(run_id)

    if _RICH_AVAILABLE:
        handler: logging.Handler = RichHandler(
            rich_tracebacks=True,
            show_time=True,
            show_path=False,
        )
        formatter = logging.Formatter(
            fmt="[run=%(run_id)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [run=%(run_id)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    handler.addFilter(run_filter)
    handler.setLevel(numeric_level)

    root_logger.setLevel(numeric_level)
    root_logger.addHandler(handler)

    # Quiet noisy third-party loggers
    for noisy in ("httpx", "httpcore", "urllib3", "openai", "anthropic"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger. The run_id will be injected via RunContextFilter."""
    return logging.getLogger(name)


def set_run_id(run_id: Optional[str]) -> None:
    """Set the run_id that will be injected into all log records."""
    RunContextFilter.set_run_id(run_id)


def clear_run_id() -> None:
    """Clear the run_id from log context."""
    RunContextFilter.clear_run_id()
