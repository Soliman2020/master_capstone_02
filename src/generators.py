"""Deterministic synthetic generator for the surveillance and access datasets.

Produces two Parquet files in `data/raw/`:

  * ``surveillance_events.parquet``  — ~1,000 rows, one row per camera event.
  * ``access_logs.parquet``          — ~10,000 rows, one row per badge swipe.

Why synthetic? The capstone explicitly needs a reproducible substrate Synthetic data 
means reviewers can regenerate identical artifacts, and we don't ship anything that
resembles real PII.
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

# Local imports — we add the project root to sys.path so this file also
# works as a script (`python src/generators.py`) without packaging work.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.constants import (
    ACCESS_PARQUET,
    DATA_RAW,
    SEED,
    SURVEILLANCE_PARQUET,
    ensure_data_dirs,
)

# --- Generator configuration ---------------------------------------------------
# These constants are deliberately exposed at module level (not buried inside
# functions) so the notebook can import them and document them in markdown.

# Sample sizes
N_SURVEILLANCE_EVENTS: int = 1_000
N_ACCESS_LOGS: int = 10_000

# We deliberately inject ~5% bad rows so the cleaning notebook has signal
# to demonstrate. The exact 5% is not sacred — adjust if cleaning tests
# need more or less dirt to exercise edge cases.
DIRTY_RATE: float = 0.05

# Site metadata. Small enough to read end-to-end, large enough to make
# referential integrity checks meaningful.
SITES = ["SITE-001", "SITE-002", "SITE-003"]
ZONES_PER_SITE = ["ZONE-A", "ZONE-B", "ZONE-C", "ZONE-D"]  # 4 zones per site
RESTRICTED_ZONES = {"SITE-001::ZONE-D", "SITE-002::ZONE-D"}  # for intrusion rules
DEVICES_PER_ZONE = 2  # cameras / readers; keeps the FK graph small

# Event taxonomies.
SURVEILLANCE_EVENT_TYPES = [
    "intrusion",
    "loitering", # remaining in a secure area or near an entry point for an extended period without a valid purpose or authorization
    "object_left",
    "tailgating", #physical security breach where an unauthorized person follows an authorized person through a secure entry point without proper authentication.
    "normal_motion",
]
SURVEILLANCE_TYPE_WEIGHTS = [0.05, 0.10, 0.05, 0.05, 0.75]

ACCESS_OUTCOMES = ["granted", "denied", "invalid_credential", "tailgated"]
ACCESS_OUTCOME_WEIGHTS = [0.85, 0.10, 0.03, 0.02]

# Time window. 14 days, ending now-ish, so the dataset always feels
# "recent" but stays small. Anchored to a fixed end so SEED alone is enough
# to reproduce the exact same timestamps.
END_TIME = datetime(2025, 1, 14, 23, 59, 59, tzinfo=timezone.utc)
WINDOW_DAYS = 14


def _build_reference() -> pd.DataFrame:
    """Build a small reference table: (site, zone, device) tuples.

    Returned as a DataFrame so it's easy to inspect in the notebook, but
    the rows are pure strings — no synthetic PII.
    """
    rows = []
    device_seq = 1
    for site in SITES:
        for zone in ZONES_PER_SITE:
            for _ in range(DEVICES_PER_ZONE):
                rows.append(
                    {
                        "site_id": site,
                        "zone_id": f"{site}::{zone}",
                        "device_id": f"DEV-{device_seq:03d}",
                    }
                )
                device_seq += 1
    return pd.DataFrame(rows)


def _inject_dirt_surveillance(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Sprinkle known bad rows into a clean surveillance frame.

    We *intentionally* corrupt ~``DIRTY_RATE`` of rows so the cleaning
    notebook can demonstrate a fix. The corruption patterns are chosen to
    match what real access-control data looks like: missing timestamps,
    out-of-range confidence scores, and odd-cased zone IDs.
    """
    n_dirty = int(len(df) * DIRTY_RATE)
    if n_dirty == 0:
        return df

    idx = rng.choice(df.index, size=n_dirty, replace=False)
    for i in idx:
        # Pick a corruption style uniformly among the three options.
        style = rng.integers(0, 3)
        if style == 0:
            # Missing event_timestamp -> NaT. Common when a sensor drops
            # an event and only the device_id survives.
            df.at[i, "event_timestamp"] = pd.NaT
        elif style == 1:
            # Out-of-range confidence score. Real classifiers occasionally
            # emit values >1.0 due to calibration drift.
            df.at[i, "confidence_score"] = float(rng.uniform(1.01, 1.50))
        else:
            # Mixed-case zone_id, e.g. "site-001::zone-a". Trivial for
            # humans, lethal for joins.
            df.at[i, "zone_id"] = str(df.at[i, "zone_id"]).lower()
    return df


def _inject_dirt_access(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    """Sprinkle known bad rows into a clean access frame.

    Mirrors the surveillance dirt pattern: missing timestamps, bad badge
    formats, and unknown outcomes that should be coerced to NaN.
    """
    n_dirty = int(len(df) * DIRTY_RATE)
    if n_dirty == 0:
        return df

    idx = rng.choice(df.index, size=n_dirty, replace=False)
    for i in idx:
        style = rng.integers(0, 3)
        if style == 0:
            df.at[i, "log_timestamp"] = pd.NaT
        elif style == 1:
            # Malformed badge id: empty string. In real systems this is
            # how a mis-tapped card shows up.
            df.at[i, "badge_id"] = ""
        else:
            # Outcome not in the controlled vocabulary. Future schema
            # change or a buggy firmware revision.
            df.at[i, "outcome"] = "??unknown??"
    return df


def generate_surveillance_events(rng: np.random.Generator) -> pd.DataFrame:
    """Generate the surveillance_events DataFrame.

    Columns: ``event_id``, ``event_timestamp``, ``site_id``, ``zone_id``,
    ``device_id``, ``event_type``, ``confidence_score``.
    """
    ref = _build_reference()
    n = N_SURVEILLANCE_EVENTS

    # Sample (site, zone, device) with replacement. Real events don't
    # care whether the same device fires twice in a row.
    sampled = ref.sample(n=n, replace=True, random_state=rng).reset_index(drop=True)

    # Random timestamps uniformly across the window.
    start = END_TIME - timedelta(days=WINDOW_DAYS)
    seconds_offset = rng.integers(0, int((END_TIME - start).total_seconds()), size=n)
    timestamps = [start + timedelta(seconds=int(s)) for s in seconds_offset]

    # Event types drawn from the weighted distribution.
    types = rng.choice(
        SURVEILLANCE_EVENT_TYPES,
        size=n,
        p=SURVEILLANCE_TYPE_WEIGHTS,
    )

    # Confidence scores for non-normal events are higher on average; normal
    # motion events hover near 0.6 with more spread.
    confidence = np.where(
        types == "normal_motion",
        rng.normal(loc=0.60, scale=0.15, size=n),
        rng.normal(loc=0.85, scale=0.10, size=n),
    )
    confidence = np.clip(confidence, 0.0, 1.0)  # clean baseline; dirt may push past

    df = pd.DataFrame(
        {
            "event_id": [f"EVT-{i:06d}" for i in range(1, n + 1)],
            "event_timestamp": pd.to_datetime(timestamps, utc=True),
            "site_id": sampled["site_id"].values,
            "zone_id": sampled["zone_id"].values,
            "device_id": sampled["device_id"].values,
            "event_type": types,
            "confidence_score": confidence,
        }
    )
    return _inject_dirt_surveillance(df, rng)


def generate_access_logs(rng: np.random.Generator) -> pd.DataFrame:
    """Generate the access_logs DataFrame.

    Columns: ``log_id``, ``log_timestamp``, ``site_id``, ``zone_id``,
    ``device_id``, ``badge_id``, ``user_id``, ``outcome``.
    """
    ref = _build_reference()
    n = N_ACCESS_LOGS

    sampled = ref.sample(n=n, replace=True, random_state=rng).reset_index(drop=True)

    # A small badge pool: 200 badges. ~80% of logs reuse a badge, ~20%
    # introduce a new one — the long-tail access pattern you'd see in
    # practice.
    badge_pool = [f"BADGE-{i:05d}" for i in range(1, 201)]

    # Each badge maps to a stable user_id. We precompute the mapping so
    # the same badge always references the same user (referential sanity).
    badge_to_user = {b: f"USR-{i:04d}" for i, b in enumerate(badge_pool, start=1)}

    badge_choices = rng.choice(badge_pool, size=n, replace=True)
    user_ids = [badge_to_user[b] for b in badge_choices]

    # 1% of logs are from a user that has no badge — tailgating-like.
    no_badge_mask = rng.random(size=n) < 0.01
    badge_choices = ["" if m else b for m, b in zip(no_badge_mask, badge_choices)]
    user_ids = ["USR-0000" if m else u for m, u in zip(no_badge_mask, user_ids)]

    # Timestamps: roughly uniform, with a slight business-hours bias.
    # We keep it simple (uniform) for v1; the EDA notebook can show
    # the distribution and decide whether to upgrade later.
    start = END_TIME - timedelta(days=WINDOW_DAYS)
    seconds_offset = rng.integers(0, int((END_TIME - start).total_seconds()), size=n)
    timestamps = [start + timedelta(seconds=int(s)) for s in seconds_offset]

    outcomes = rng.choice(ACCESS_OUTCOMES, size=n, p=ACCESS_OUTCOME_WEIGHTS)

    df = pd.DataFrame(
        {
            "log_id": [f"LOG-{i:06d}" for i in range(1, n + 1)],
            "log_timestamp": pd.to_datetime(timestamps, utc=True),
            "site_id": sampled["site_id"].values,
            "zone_id": sampled["zone_id"].values,
            "device_id": sampled["device_id"].values,
            "badge_id": badge_choices,
            "user_id": user_ids,
            "outcome": outcomes,
        }
    )
    return _inject_dirt_access(df, rng)


def write_raw(
    surveillance: pd.DataFrame,
    access: pd.DataFrame,
    out_dir: Path = DATA_RAW,
) -> tuple[Path, Path]:
    """Write both frames to Parquet under ``out_dir``.

    Returns the two paths so the caller (notebook, CLI, tests) can log
    or assert on them.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    s_path = out_dir / SURVEILLANCE_PARQUET
    a_path = out_dir / ACCESS_PARQUET
    surveillance.to_parquet(s_path, index=False)
    surveillance.to_csv(s_path.with_suffix(".csv"), index=False)  # also write CSV for easy eyeballing
    access.to_parquet(a_path, index=False)
    access.to_csv(a_path.with_suffix(".csv"), index=False)  # also write CSV for easy eyeballing
    return s_path, a_path


def main() -> None:
    """Entry point for `python -m src.generators`."""
    ensure_data_dirs()
    rng = np.random.default_rng(SEED)
    surv = generate_surveillance_events(rng)
    acc = generate_access_logs(rng)
    s_path, a_path = write_raw(surv, acc)
    print(f"Wrote {len(surv):>5} surveillance rows -> {s_path}")
    print(f"Wrote {len(acc):>5} access rows      -> {a_path}")


if __name__ == "__main__":
    main()
