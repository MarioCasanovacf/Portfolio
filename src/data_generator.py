"""
Nutanix GSO Synthetic Data Generator
=====================================
Generates realistic synthetic datasets for a Global Support Organization (GSO)
analytics portfolio, simulating Nutanix HCI support operations.

Datasets produced:
  1. support_tickets.csv   — 100,000 support tickets with TTR, priority, region, NPS
  2. pulse_telemetry.csv   — Time-series telemetry (IO latency, CPU, IOPS) per cluster
  3. migration_cohorts.csv — VMware-to-AHV migration wave tracking

Usage:
    python src/data_generator.py
    # or from a notebook:
    from src.data_generator import generate_all_datasets
    tickets, telemetry, migrations = generate_all_datasets()
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import random
import os

# ── Reproducibility ──────────────────────────────────────────────────────────
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

# ── Configuration ─────────────────────────────────────────────────────────────
N_TICKETS    = 100_000
N_CLUSTERS   = 500
START_DATE   = datetime(2022, 1, 1)
END_DATE     = datetime(2024, 12, 31)

# Nutanix AOS / AHV version cohorts (realistic naming)
AOS_VERSIONS = [
    "6.1.1", "6.1.2", "6.5", "6.5.1", "6.5.2",
    "6.7", "6.7.1", "6.8", "6.8.1", "6.8.2"
]
AHV_VERSIONS = [
    "20220304.342", "20220304.480", "20230302.100",
    "20230302.215", "20231004.10010", "20240304.100"
]

REGIONS = ["AMER-EAST", "AMER-WEST", "LATAM", "EMEA-WEST", "EMEA-EAST", "APAC-ANZ", "APAC-INDIA"]
PRIORITIES = ["P1", "P2", "P3", "P4"]
CUSTOMER_TIERS = ["Enterprise", "Mid-Market", "SMB", "Strategic"]
MIGRATION_TYPES = ["VMware-to-AHV", "Greenfield", "AOS-Upgrade", "Hardware-Refresh", "None"]
ESCALATION_REASONS = [
    "SLA Breach", "Customer Requested", "Revenue Risk", "Data Loss Risk",
    "Repeated Issue", "Executive Visibility", None, None, None, None  # weighted toward None
]

# SLA thresholds (hours) per priority
SLA_HOURS = {"P1": 0.5, "P2": 2.0, "P3": 4.0, "P4": 8.0}

# Mean TTR (hours) per priority — realistic distributions
TTR_PARAMS = {
    "P1": {"mean": 3.5,  "std": 2.1,  "min": 0.25},
    "P2": {"mean": 12.0, "std": 8.5,  "min": 1.0},
    "P3": {"mean": 36.0, "std": 24.0, "min": 4.0},
    "P4": {"mean": 96.0, "std": 48.0, "min": 8.0},
}

# Priority distribution (realistic GSO mix)
PRIORITY_WEIGHTS = [0.08, 0.22, 0.45, 0.25]  # P1, P2, P3, P4


def _random_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def _ttr_hours(priority: str, is_migrating: bool, aos_version: str) -> float:
    """Sample TTR with realistic modifiers for migration stress and older AOS."""
    p = TTR_PARAMS[priority]
    ttr = np.random.lognormal(
        mean=np.log(max(p["mean"], 0.1)),
        sigma=p["std"] / p["mean"]
    )
    ttr = max(ttr, p["min"])

    # Migration stress: tickets during active migrations take ~35% longer
    if is_migrating:
        ttr *= np.random.uniform(1.15, 1.55)

    # Older AOS versions have higher complexity → longer TTR
    version_index = AOS_VERSIONS.index(aos_version)
    if version_index < 3:  # oldest versions
        ttr *= np.random.uniform(1.10, 1.30)

    return round(ttr, 2)


def _nps_score(ttr: float, priority: str, escalated: bool) -> int | None:
    """Generate NPS score (0–10) inversely correlated with TTR breach and escalations."""
    sla = SLA_HOURS[priority]
    breach_ratio = ttr / sla  # 1.0 = exactly at SLA

    if breach_ratio <= 1.0:
        base_score = np.random.choice([9, 10], p=[0.35, 0.65])
    elif breach_ratio <= 2.0:
        base_score = np.random.choice([7, 8, 9], p=[0.25, 0.45, 0.30])
    elif breach_ratio <= 5.0:
        base_score = np.random.choice([5, 6, 7, 8], p=[0.20, 0.35, 0.30, 0.15])
    else:
        base_score = np.random.choice([0, 1, 2, 3, 4, 5, 6], p=[0.05, 0.08, 0.12, 0.20, 0.25, 0.20, 0.10])

    if escalated:
        base_score = max(0, base_score - np.random.randint(1, 4))

    # ~15% of tickets don't return NPS (customer didn't respond)
    if np.random.random() < 0.15:
        return None
    return int(base_score)


def generate_support_tickets(n: int = N_TICKETS) -> pd.DataFrame:
    """
    Generate synthetic support ticket dataset.

    Returns
    -------
    pd.DataFrame with columns:
        ticket_id, created_at, resolved_at, ttr_hours, priority,
        region, customer_tier, aos_version, ahv_version, cluster_id,
        migration_type, is_migrating, escalated, escalation_reason,
        sla_breached, nps_score, assigned_engineer
    """
    print(f"[data_generator] Generating {n:,} support tickets...")

    cluster_ids = [f"CL-{str(i).zfill(5)}" for i in range(N_CLUSTERS)]
    engineer_ids = [f"SRE-{str(i).zfill(3)}" for i in range(1, 81)]  # 80 SREs globally

    rows = []
    for i in range(n):
        priority = np.random.choice(PRIORITIES, p=PRIORITY_WEIGHTS)
        region = random.choice(REGIONS)
        customer_tier = random.choice(CUSTOMER_TIERS)
        aos_version = random.choice(AOS_VERSIONS)
        ahv_version = random.choice(AHV_VERSIONS)
        cluster_id = random.choice(cluster_ids)
        migration_type = np.random.choice(
            MIGRATION_TYPES,
            p=[0.28, 0.18, 0.22, 0.12, 0.20]  # VMware migration is dominant
        )
        is_migrating = migration_type != "None"

        created_at = _random_date(START_DATE, END_DATE)
        ttr = _ttr_hours(priority, is_migrating, aos_version)
        resolved_at = created_at + timedelta(hours=ttr)

        sla_breached = ttr > SLA_HOURS[priority]

        # Escalation: more likely for P1/P2 SLA breaches and strategic customers
        escalation_prob = 0.03
        if priority == "P1":
            escalation_prob = 0.22 if sla_breached else 0.05
        elif priority == "P2":
            escalation_prob = 0.12 if sla_breached else 0.02
        if customer_tier == "Strategic":
            escalation_prob *= 1.8

        escalated = np.random.random() < escalation_prob
        escalation_reason = random.choice(ESCALATION_REASONS) if escalated else None

        nps = _nps_score(ttr, priority, escalated)

        rows.append({
            "ticket_id":         f"TKT-{str(i + 1).zfill(7)}",
            "created_at":        created_at,
            "resolved_at":       resolved_at,
            "ttr_hours":         ttr,
            "priority":          priority,
            "region":            region,
            "customer_tier":     customer_tier,
            "aos_version":       aos_version,
            "ahv_version":       ahv_version,
            "cluster_id":        cluster_id,
            "migration_type":    migration_type,
            "is_migrating":      is_migrating,
            "escalated":         escalated,
            "escalation_reason": escalation_reason,
            "sla_breached":      sla_breached,
            "nps_score":         nps,
            "assigned_engineer": random.choice(engineer_ids),
        })

    df = pd.DataFrame(rows)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df["resolved_at"] = pd.to_datetime(df["resolved_at"])
    df = df.sort_values("created_at").reset_index(drop=True)

    print(f"[data_generator] ✓ Tickets generated. Shape: {df.shape}")
    return df


def generate_pulse_telemetry(cluster_ids: list | None = None,
                             days: int = 365 * 3) -> pd.DataFrame:
    """
    Generate synthetic Nutanix Pulse telemetry time series.

    One reading per cluster per hour for `days` days would be too large;
    instead we generate daily aggregates with hourly-resolution anomaly windows.

    Returns
    -------
    pd.DataFrame with columns:
        timestamp, cluster_id, avg_io_latency_usecs, cpu_usage_pct,
        memory_usage_pct, iops, network_throughput_mbps, anomaly_injected
    """
    if cluster_ids is None:
        cluster_ids = [f"CL-{str(i).zfill(5)}" for i in range(50)]  # 50 clusters for telemetry

    print(f"[data_generator] Generating Pulse telemetry for {len(cluster_ids)} clusters × {days} days...")

    date_range = pd.date_range(start=START_DATE, periods=days, freq="D")
    rows = []

    for cluster_id in cluster_ids:
        # Baseline characteristics vary per cluster
        base_latency = np.random.uniform(200, 800)   # usecs — healthy range
        base_cpu     = np.random.uniform(25, 60)     # %
        base_memory  = np.random.uniform(40, 75)     # %
        base_iops    = np.random.uniform(5000, 25000)
        base_net     = np.random.uniform(100, 500)   # MB/s

        # Inject anomaly windows (5% of days per cluster)
        n_anomaly_days = max(1, int(days * 0.05))
        anomaly_days = set(np.random.choice(range(days), size=n_anomaly_days, replace=False))

        for day_idx, ts in enumerate(date_range):
            is_anomaly = day_idx in anomaly_days

            # Seasonal weekly pattern: weekdays have higher load
            weekday_factor = 1.0 if ts.weekday() < 5 else 0.72

            if is_anomaly:
                # Anomaly: IO latency spikes 3–8× normal, often precedes a ticket
                latency_val = base_latency * np.random.uniform(3.0, 8.0)
                cpu_val     = min(99.0, base_cpu * np.random.uniform(1.5, 2.2) * weekday_factor)
                iops_val    = base_iops * np.random.uniform(1.8, 3.5) * weekday_factor
            else:
                latency_val = base_latency * np.random.uniform(0.85, 1.20) * weekday_factor
                cpu_val     = base_cpu * np.random.uniform(0.80, 1.25) * weekday_factor
                iops_val    = base_iops * np.random.uniform(0.75, 1.30) * weekday_factor

            rows.append({
                "timestamp":               ts,
                "cluster_id":              cluster_id,
                "avg_io_latency_usecs":    round(latency_val, 1),
                "cpu_usage_pct":           round(min(99.9, cpu_val), 2),
                "memory_usage_pct":        round(min(99.9, base_memory * np.random.uniform(0.90, 1.10)), 2),
                "iops":                    round(iops_val, 0),
                "network_throughput_mbps": round(base_net * np.random.uniform(0.80, 1.25) * weekday_factor, 1),
                "anomaly_injected":        is_anomaly,
            })

    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    print(f"[data_generator] ✓ Telemetry generated. Shape: {df.shape}")
    return df


def generate_migration_cohorts() -> pd.DataFrame:
    """
    Generate VMware-to-AHV migration cohort tracking data.
    Simulates wave-based migrations with start/completion dates and cluster counts.
    """
    print("[data_generator] Generating migration cohort data...")

    waves = []
    wave_start = datetime(2022, 6, 1)

    for i in range(1, 25):  # 24 migration waves
        duration_days = np.random.randint(45, 180)
        n_clusters = np.random.randint(10, 120)
        region = random.choice(REGIONS)
        customer_tier = random.choice(CUSTOMER_TIERS)
        start_date = wave_start + timedelta(days=np.random.randint(0, 30))
        end_date = start_date + timedelta(days=duration_days)

        waves.append({
            "wave_id":           f"WAVE-{str(i).zfill(3)}",
            "region":            region,
            "customer_tier":     customer_tier,
            "migration_start":   start_date,
            "migration_end":     end_date,
            "duration_days":     duration_days,
            "n_clusters":        n_clusters,
            "source_platform":   "VMware vSphere",
            "target_platform":   "Nutanix AHV",
            "aos_target_version": random.choice(AOS_VERSIONS[-4:]),  # always recent
            "status":            "Completed" if end_date < datetime.now() else "In Progress",
        })
        wave_start = wave_start + timedelta(days=np.random.randint(30, 90))

    df = pd.DataFrame(waves)
    df["migration_start"] = pd.to_datetime(df["migration_start"])
    df["migration_end"] = pd.to_datetime(df["migration_end"])
    print(f"[data_generator] ✓ Migration cohorts generated. Shape: {df.shape}")
    return df


def generate_all_datasets(output_dir: str = "data/synthetic") -> tuple:
    """
    Generate all three datasets and optionally save them to CSV.

    Parameters
    ----------
    output_dir : str
        Directory to save CSV files. Pass None to skip saving.

    Returns
    -------
    tuple: (tickets_df, telemetry_df, migrations_df)
    """
    tickets    = generate_support_tickets()
    telemetry  = generate_pulse_telemetry()
    migrations = generate_migration_cohorts()

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        tickets.to_csv(f"{output_dir}/support_tickets.csv", index=False)
        telemetry.to_csv(f"{output_dir}/pulse_telemetry.csv", index=False)
        migrations.to_csv(f"{output_dir}/migration_cohorts.csv", index=False)
        print(f"\n[data_generator] All datasets saved to '{output_dir}/'")
        print(f"  support_tickets.csv   → {len(tickets):,} rows")
        print(f"  pulse_telemetry.csv   → {len(telemetry):,} rows")
        print(f"  migration_cohorts.csv → {len(migrations):,} rows")

    return tickets, telemetry, migrations


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    generate_all_datasets()
