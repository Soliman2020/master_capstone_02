"""Project-wide constants and path helpers.

Centralising these here keeps the SEED value in one place 
and gives every other module the same view of where files live on disk.
"""
from __future__ import annotations

from pathlib import Path

# Single source of randomness for the whole project. Every generator,
# shuffler, and train/test split that wants reproducibility reads this.
SEED: int = 42

# Schema version. Bump when column names or types change so downstream
# consumers can detect stale data.
SCHEMA_VERSION: str = "1.0.0"

# Project root
PROJECT_ROOT: Path = Path(__file__).resolve().parents[1]

# Standard data layout. Keeping them as Path objects (not strings) means
# callers don't have to think about OS separators.
DATA_RAW: Path = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED: Path = PROJECT_ROOT / "data" / "processed"
REPORTS: Path = PROJECT_ROOT / "reports"

# Default file names for the synthetic datasets written by generators.py.
SURVEILLANCE_PARQUET: str = "surveillance_events.parquet"
ACCESS_PARQUET: str = "access_logs.parquet"


def ensure_data_dirs() -> None:
    """Create the data/ subdirs if they don't exist.

    Cheap, idempotent, and safe to call from a notebook before the first
    write. Only the dirs that this project actually uses are created
    """
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
