"""
Structured error tracking to replace bare ``except Exception: pass`` patterns.

Provides:

- ``ErrorTracker`` — thread-safe in-memory error store with JSONL persistence
- ``ErrorLogEntry`` — immutable dataclass for a single error record
- ``error_tracker_context`` — dual-use context manager / decorator
- ``FileLock`` — cross-platform exclusive file lock for log writes

Severity levels (ordered by weight)::

    CRITICAL (40) > ERROR (30) > WARNING (20) > INFO (10)

Every error receives a deterministic hash-based ID derived from
``stage + error_type + message + timestamp``, compatible with the project's
artifact-hash conventions in ``paper_workflow.supervision.passport``.

Usage::

    # Direct use
    tracker = ErrorTracker(log_dir=Path("./logs"))
    eid = tracker.track("preprocessing", "ValueError", "Column 'age' missing",
                        details={"dataset": "GSE12345"}, severity="error")
    if tracker.has_critical():
        print(tracker.export_summary())

    # Context manager (auto-tracks unhandled exceptions)
    with error_tracker_context("enrichment", log_dir=Path("./logs")) as et:
        run_enrichment()

    # Decorator
    @error_tracker_context("differential_expression")
    def run_de():
        ...
"""

from __future__ import annotations

import functools
import hashlib
import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, ClassVar, Dict, List, Optional, Union

# ---------------------------------------------------------------------------
# Severity constants
# ---------------------------------------------------------------------------

_SEVERITY_WEIGHTS: Dict[str, int] = {
    "critical": 40,
    "error": 30,
    "warning": 20,
    "info": 10,
}

_SEVERITY_ORDER: List[str] = ["info", "warning", "error", "critical"]

# Canonical uppercase aliases — normalise on ingestion
_SEVERITY_ALIASES: Dict[str, str] = {
    "CRITICAL": "critical",
    "ERROR": "error",
    "WARNING": "warning",
    "INFO": "info",
}


def _normalise_severity(raw: str) -> str:
    """Fold a raw severity string into its canonical lowercase form."""
    key = raw.strip().lower()
    return _SEVERITY_ALIASES.get(key, key)


def _severity_weight(severity: str) -> int:
    """Return the numeric weight of a severity level (0 if unknown)."""
    return _SEVERITY_WEIGHTS.get(_normalise_severity(severity), 0)


# ---------------------------------------------------------------------------
# File lock — cross-platform exclusive lock for JSONL writes
# ---------------------------------------------------------------------------


class FileLock:
    """Cross-platform exclusive file lock using OS-level primitives.

    Uses ``msvcrt.locking`` on Windows and ``fcntl.flock`` on Unix.
    Operates as a context manager.

    Usage::

        with FileLock("/path/to/file.lock"):
            # safe to write
            pass
    """

    def __init__(self, lock_path: Path) -> None:
        """*lock_path* is the filesystem path used as the lock file."""
        self._lock_path = Path(lock_path)
        self._lock_fd: Optional[int] = None

    def acquire(self) -> None:
        """Create the lock file and acquire an exclusive lock."""
        self._lock_path.parent.mkdir(parents=True, exist_ok=True)
        # Open (or create) the lock file in read-write mode
        fd = os.open(str(self._lock_path), os.O_RDWR | os.O_CREAT, 0o644)
        try:
            if os.name == "nt":
                # Windows: lock the entire file
                import msvcrt
                msvcrt.locking(fd, msvcrt.LK_LOCK, 1)
            else:
                # Unix: flock exclusive, blocking
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_EX)
        except Exception:
            os.close(fd)
            raise
        self._lock_fd = fd

    def release(self) -> None:
        """Release the lock and close the file descriptor."""
        if self._lock_fd is None:
            return
        fd: int = self._lock_fd
        self._lock_fd = None
        try:
            if os.name == "nt":
                import msvcrt
                # Move to position 0 and unlock
                os.lseek(fd, 0, os.SEEK_SET)
                msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(fd, fcntl.LOCK_UN)
        except Exception:
            pass
        finally:
            try:
                os.close(fd)
            except OSError:
                pass

    def __enter__(self) -> FileLock:
        self.acquire()
        return self

    def __exit__(self, *args: Any) -> None:
        self.release()


# ---------------------------------------------------------------------------
# ErrorLogEntry — immutable record of a single tracked error
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ErrorLogEntry:
    """A single tracked error, warning, or informational event.

    Attributes
    ----------
    error_id : str
        Deterministic hash-based ID (12 hex chars).
    timestamp : str
        ISO-8601 UTC timestamp of when the error was recorded.
    stage : str
        Pipeline stage name (e.g. ``"preprocessing"``).
    error_type : str
        Exception class name or category label.
    message : str
        Human-readable description.
    details : dict
        Arbitrary supplementary key-value data.
    severity : str
        One of ``critical``, ``error``, ``warning``, ``info``.
    handled : bool
        Whether the error was caught and handled (``True``) or is unhandled.
    """

    error_id: str
    timestamp: str
    stage: str
    error_type: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    severity: str = "error"
    handled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Return the entry as a JSON-serialisable dictionary."""
        return {
            "error_id": self.error_id,
            "timestamp": self.timestamp,
            "stage": self.stage,
            "error_type": self.error_type,
            "message": self.message,
            "details": self.details,
            "severity": self.severity,
            "handled": self.handled,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ErrorLogEntry:
        """Reconstruct an entry from a dictionary (e.g. read from JSONL)."""
        return cls(
            error_id=data.get("error_id", "unknown"),
            timestamp=data.get("timestamp", ""),
            stage=data.get("stage", "unknown"),
            error_type=data.get("error_type", "unknown"),
            message=data.get("message", ""),
            details=data.get("details", {}),
            severity=data.get("severity", "error"),
            handled=data.get("handled", True),
        )


# ---------------------------------------------------------------------------
# ErrorTracker
# ---------------------------------------------------------------------------


class ErrorTracker:
    """Thread-safe structured error tracker with JSONL persistence.

    Accumulates errors in memory and optionally persists every entry to an
    append-only ``error_log.jsonl`` file.  Severity-aware filtering lets
    callers query for critical / error / warning events before advancing
    pipeline stages.

    Parameters
    ----------
    log_dir : pathlib.Path, optional
        Directory where ``error_log.jsonl`` is written.  If ``None``,
        entries are kept in memory only (no disk I/O).
    passport : PaperPassport, optional
        If provided, CRITICAL errors also record an integrity event via
        ``passport.record_integrity_event()``.
    auto_flush : bool
        When ``True`` (default), every ``track()`` call immediately
        appends to the JSONL log.  Set to ``False`` to batch writes.
    """

    # --- severity weight map (class-level) ---
    SEVERITY_WEIGHTS: ClassVar[Dict[str, int]] = _SEVERITY_WEIGHTS

    def __init__(
        self,
        log_dir: Optional[Path] = None,
        passport: Any = None,  # PaperPassport, optional to avoid hard import
        auto_flush: bool = True,
    ) -> None:
        self._log_dir: Optional[Path] = Path(log_dir) if log_dir else None
        self._log_path: Optional[Path] = (
            self._log_dir / "error_log.jsonl" if self._log_dir else None
        )
        self._lock_path: Optional[Path] = (
            self._log_dir / "error_log.lock" if self._log_dir else None
        )
        self._passport = passport
        self._auto_flush = auto_flush

        # In-memory store: list of ErrorLogEntry objects
        self._entries: List[ErrorLogEntry] = []
        self._lock = threading.Lock()

        # Ensure log directory exists
        if self._log_dir:
            self._log_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------

    def track(
        self,
        stage: str,
        error_type: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        severity: str = "error",
    ) -> str:
        """Record an error and return its deterministic error ID.

        Parameters
        ----------
        stage : str
            Pipeline stage name.
        error_type : str
            Exception class name or error category.
        message : str
            Human-readable description.
        details : dict, optional
            Supplementary key-value data.
        severity : str
            One of ``critical``, ``error``, ``warning``, ``info``.

        Returns
        -------
        str
            The 12-character hex error ID.
        """
        severity = _normalise_severity(severity)
        timestamp = datetime.now(timezone.utc).isoformat()
        error_id = _make_error_id(stage, error_type, message, timestamp)

        entry = ErrorLogEntry(
            error_id=error_id,
            timestamp=timestamp,
            stage=stage,
            error_type=error_type,
            message=message,
            details=details or {},
            severity=severity,
            handled=True,
        )

        with self._lock:
            self._entries.append(entry)

        # Persist immediately if auto_flush is enabled
        if self._auto_flush:
            self.write_to_log(entry.to_dict())

        # Record CRITICAL events in the passport integrity ledger
        if severity == "critical" and self._passport is not None:
            try:
                self._passport.record_integrity_event(
                    "critical_error",
                    {
                        "error_id": error_id,
                        "stage": stage,
                        "error_type": error_type,
                        "message": message,
                    },
                )
            except Exception:
                # Passport recording is best-effort — never let a passport
                # failure mask the original error.
                pass

        return error_id

    def get_errors(
        self,
        stage: Optional[str] = None,
        min_severity: str = "warning",
    ) -> List[Dict[str, Any]]:
        """Return errors filtered by stage and minimum severity.

        Parameters
        ----------
        stage : str, optional
            If provided, only return entries for this pipeline stage.
        min_severity : str
            Minimum severity level to include (default ``"warning"``).

        Returns
        -------
        list[dict]
            Entries as dictionaries, sorted newest-first.
        """
        threshold = _severity_weight(min_severity)

        with self._lock:
            entries = list(self._entries)

        result: List[Dict[str, Any]] = []
        for entry in entries:
            if stage is not None and entry.stage != stage:
                continue
            if _severity_weight(entry.severity) < threshold:
                continue
            result.append(entry.to_dict())

        # Newest first
        result.reverse()
        return result

    def has_critical(self, stage: Optional[str] = None) -> bool:
        """Check whether any CRITICAL errors have been recorded.

        Parameters
        ----------
        stage : str, optional
            If provided, only check within the given pipeline stage.

        Returns
        -------
        bool
            ``True`` if at least one critical error exists.
        """
        with self._lock:
            entries = list(self._entries)

        for entry in entries:
            if entry.severity != "critical":
                continue
            if stage is not None and entry.stage != stage:
                continue
            return True
        return False

    def export_summary(self) -> Dict[str, Any]:
        """Return a summary dictionary suitable for reporting.

        Returns
        -------
        dict
            Keys: ``total``, ``by_severity``, ``by_stage``, ``by_error_type``,
            ``has_critical``, ``oldest_timestamp``, ``newest_timestamp``.
        """
        with self._lock:
            entries = list(self._entries)

        by_severity: Dict[str, int] = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        by_stage: Dict[str, int] = {}
        by_error_type: Dict[str, int] = {}

        oldest: Optional[str] = None
        newest: Optional[str] = None

        for entry in entries:
            sev = entry.severity
            by_severity[sev] = by_severity.get(sev, 0) + 1

            stg = entry.stage
            by_stage[stg] = by_stage.get(stg, 0) + 1

            etype = entry.error_type
            by_error_type[etype] = by_error_type.get(etype, 0) + 1

            if oldest is None or entry.timestamp < oldest:
                oldest = entry.timestamp
            if newest is None or entry.timestamp > newest:
                newest = entry.timestamp

        return {
            "total": len(entries),
            "by_severity": by_severity,
            "by_stage": by_stage,
            "by_error_type": by_error_type,
            "has_critical": by_severity.get("critical", 0) > 0,
            "oldest_timestamp": oldest,
            "newest_timestamp": newest,
        }

    def clear_stage(self, stage: str) -> None:
        """Remove all entries for the given pipeline stage.

        Parameters
        ----------
        stage : str
            Pipeline stage whose errors should be cleared.
        """
        with self._lock:
            self._entries = [e for e in self._entries if e.stage != stage]

    def write_to_log(self, error_entry: Dict[str, Any]) -> None:
        """Append a single error entry dict to the JSONL log file.

        Thread-safe: uses :class:`FileLock` to serialise concurrent writers.

        If no *log_dir* was configured at init, this is a no-op.

        Parameters
        ----------
        error_entry : dict
            A dictionary as returned by ``ErrorLogEntry.to_dict()``.
        """
        if self._log_path is None or self._lock_path is None:
            return

        line = json.dumps(error_entry, ensure_ascii=False) + "\n"

        with FileLock(self._lock_path):
            with open(self._log_path, "a", encoding="utf-8") as fh:
                fh.write(line)

    # ------------------------------------------------------------------
    # Context manager support
    # ------------------------------------------------------------------

    def __enter__(self) -> ErrorTracker:
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> bool:
        # Do NOT suppress — always propagate
        return False

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @property
    def total_errors(self) -> int:
        """Total number of tracked entries."""
        with self._lock:
            return len(self._entries)

    @property
    def log_path(self) -> Optional[Path]:
        """Path to the JSONL log file, or ``None``."""
        return self._log_path


# ---------------------------------------------------------------------------
# Hash-based error ID (compatible with passport artifact-hash conventions)
# ---------------------------------------------------------------------------


def _make_error_id(stage: str, error_type: str, message: str, timestamp: str) -> str:
    """Generate a deterministic SHA-256 hex ID (first 12 chars).

    Uses the same SHA-256 hashing strategy as ``PaperPassport._compute_hash``
    to keep the ID scheme consistent across the project.
    """
    seed = f"{stage}:{error_type}:{message}:{timestamp}"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return digest[:12]


# ---------------------------------------------------------------------------
# error_tracker_context — dual-use context manager / decorator
# ---------------------------------------------------------------------------


class _ErrorTrackerContext:
    """Callable that serves as both a context manager and a decorator.

    **Context manager**::

        with error_tracker_context("my_stage") as tracker:
            ...

    **Decorator**::

        @error_tracker_context("my_stage")
        def my_func():
            ...

    When an exception propagates out of the managed block, it is automatically
    recorded via ``tracker.track()`` with the stage name provided at
    construction, then re-raised.
    """

    def __init__(
        self,
        stage_name: str,
        log_dir: Optional[Path] = None,
        passport: Any = None,
    ) -> None:
        self._stage_name = stage_name
        self._log_dir = log_dir
        self._passport = passport
        self._tracker: Optional[ErrorTracker] = None

    # --- Context manager protocol ---

    def __enter__(self) -> ErrorTracker:
        self._tracker = ErrorTracker(
            log_dir=self._log_dir,
            passport=self._passport,
        )
        return self._tracker

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> bool:
        if exc_type is not None and exc_val is not None and self._tracker is not None:
            self._tracker.track(
                stage=self._stage_name,
                error_type=exc_type.__name__,
                message=str(exc_val),
                severity="error",
            )
        # Never suppress — always propagate
        return False

    # --- Decorator protocol ---

    def __call__(self, func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return func(*args, **kwargs)

        # Attach a reference so callers can inspect the tracker after the fact
        # (useful when the function completes without raising)
        wrapper._error_tracker_context = self  # type: ignore[attr-defined]
        return wrapper


def error_tracker_context(
    stage_name: str,
    log_dir: Optional[Union[str, Path]] = None,
    passport: Any = None,
) -> _ErrorTrackerContext:
    """Create a dual-use context manager / decorator for error tracking.

    Parameters
    ----------
    stage_name : str
        Pipeline stage name used when auto-recording exceptions.
    log_dir : str or pathlib.Path, optional
        Directory for ``error_log.jsonl``.  In-memory only if ``None``.
    passport : PaperPassport, optional
        If supplied, CRITICAL errors also create integrity events.

    Returns
    -------
    _ErrorTrackerContext
        An object that can be used with ``with`` or as a ``@decorator``.

    Examples
    --------
    Context manager::

        with error_tracker_context("alignment", log_dir="./logs") as tracker:
            run_alignment()

    Decorator::

        @error_tracker_context("normalisation")
        def normalise(counts):
            ...
    """
    _log_dir = Path(log_dir) if log_dir else None
    return _ErrorTrackerContext(
        stage_name=stage_name,
        log_dir=_log_dir,
        passport=passport,
    )
