import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Determinism
np.random.seed(42)

# --- Data-extraction snapshot -------------------------------------------------
# The whole warehouse is "as of" this date. Subscriptions still active at the
# snapshot are right-censored (SubscriptionEnd = NaT); churns are observed only
# up to here. Cohort/LTV/telemetry logic all read against this single date.
SNAPSHOT = datetime(2023, 5, 31)


def generate_saas_hardware_data(output_dir="../data", n_users=5000, ab_conversion_lift=0.0185):
    """
    Generate a relational model simulating the data warehouse of an IoT company
    with hardware lines (Security Cameras vs. Smart Doorbells), subscription
    logs (SaaS), and usage telemetry for cohort analysis.

    Design notes (why this DGP, not the obvious one)
    -------------------------------------------------
    Churn is simulated as a *constant monthly hazard* (a geometric survival
    process), NOT as a one-shot "fraction who ever churn." That distinction is
    the whole point of the LTV notebook:

      * Under a constant monthly hazard ``h``, expected lifetime is ``1/h``
        months and the textbook identity ``LTV = ARPU * margin / h`` is *exactly*
        correct -- so an analyst who estimates ``h`` properly (churn events per
        subscriber-month of exposure) recovers a finite, meaningful LTV.

      * The naive shortcut -- dividing by the *cumulative* share who cancelled
        during the observation window -- is dimensionally wrong (a window-length-
        and censoring-dependent proportion, not a per-period rate) and gives a
        very different number. The notebook contrasts the two on purpose.

    Cameras are planted with a lower monthly hazard than Doorbells (better
    retention) and a higher ARPU, so the "Cameras out-earn Doorbells over a
    lifetime" conclusion is real once the math is done correctly. The A/B variant
    carries a *modest, realistic* conversion lift (~3pp) -- large enough to detect
    with N~5000, small enough that the hypothesis test actually earns its keep.
    """
    os.makedirs(output_dir, exist_ok=True)

    # 1. Hardware sales & onboarding (A/B test)
    user_ids = np.arange(10000, 10000 + n_users)
    device_types = np.random.choice(
        ["Security Camera", "Smart Doorbell"], size=n_users, p=[0.4, 0.6]
    )

    # Acquisition spread across the past year (monthly cohorts)
    start_date = datetime(2022, 1, 1)
    end_date = datetime(2022, 12, 31)
    days_between_dates = (end_date - start_date).days

    purchase_dates = [
        start_date + timedelta(days=int(np.random.randint(0, days_between_dates)))
        for _ in range(n_users)
    ]

    # A/B testing: Control (classic flow) vs Variant (optimized flow)
    onboarding_version = np.random.choice(["Control", "Variant"], size=n_users, p=[0.5, 0.5])

    users_df = pd.DataFrame(
        {
            "UserID": user_ids,
            "DeviceType": device_types,
            "PurchaseDate": purchase_dates,
            "OnboardingVersion": onboarding_version,
        }
    )

    users_df["PurchaseDate"] = pd.to_datetime(users_df["PurchaseDate"])
    users_df["CohortMonth"] = users_df["PurchaseDate"].dt.to_period("M").astype(str)

    # 2. Subscriptions fact table.
    # Cameras convert better (higher attach rate). The variant onboarding adds a
    # modest, realistic conversion lift.
    AB_CONVERSION_LIFT = ab_conversion_lift  # planted Variant lift; tuned small so the OBSERVED
    #                                          result is borderline (sig one-sided, not two-sided)

    # Constant *monthly* churn hazards (the geometric survival process). Cameras
    # retain markedly better than Doorbells; the variant shaves the hazard a bit.
    BASE_MONTHLY_HAZARD = {"Security Camera": 0.040, "Smart Doorbell": 0.075}
    AB_HAZARD_MULTIPLIER = 0.90  # Variant retains slightly better

    subscriptions = []

    for _, user in users_df.iterrows():
        base_conv_prob = 0.35 if user["DeviceType"] == "Security Camera" else 0.20
        if user["OnboardingVersion"] == "Variant":
            base_conv_prob += AB_CONVERSION_LIFT

        converts_to_sub = np.random.rand() < base_conv_prob
        if not converts_to_sub:
            continue

        sub_start = user["PurchaseDate"] + timedelta(days=int(np.random.randint(1, 14)))

        # Monthly-hazard survival: each whole month the subscriber is alive, they
        # churn with probability h. We march forward month by month until either
        # a churn fires or we hit the snapshot (right-censoring).
        h = BASE_MONTHLY_HAZARD[user["DeviceType"]]
        if user["OnboardingVersion"] == "Variant":
            h *= AB_HAZARD_MULTIPLIER

        months_to_snapshot = (
            (SNAPSHOT.year - sub_start.year) * 12 + (SNAPSHOT.month - sub_start.month)
        )
        months_to_snapshot = max(months_to_snapshot, 0)

        tenure_months = None
        for m in range(1, months_to_snapshot + 1):
            if np.random.rand() < h:
                tenure_months = m
                break

        if tenure_months is not None:
            # Observed churn: place the end *inside* month m (centred), so the
            # observed tenure spans [m-1, m] months and exposure isn't inflated.
            sub_end = sub_start + timedelta(
                days=int(30 * (tenure_months - 1) + np.random.randint(1, 31))
            )
            sub_end = min(sub_end, SNAPSHOT)
            is_active = False
        else:
            # Survived to the snapshot -> right-censored, still active.
            sub_end = pd.NaT
            is_active = True

        subscriptions.append(
            {
                "UserID": user["UserID"],
                "PlanName": "Premium Cloud Storage",
                "MonthlyFee": 14.99 if user["DeviceType"] == "Security Camera" else 9.99,
                "SubscriptionStart": sub_start,
                "SubscriptionEnd": sub_end,
                "IsActive": is_active,
            }
        )

    subs_df = pd.DataFrame(subscriptions)

    # 3. Telemetry logs (DAU/MAU stickiness).
    # Condensed daily logs for one sample month (March 2023). Engagement depends
    # on DeviceType (cameras are stickier) and is generated INDEPENDENTLY of the
    # churn process -- so March-2023 telemetry is a deliberately weak predictor of
    # the churn label (most churns happen on a different timeline). That is the
    # honest-null story the churn-prediction notebook tells.
    telemetry_records = []
    sample_month_start = datetime(2023, 3, 1)
    active_users = users_df[users_df["PurchaseDate"] < sample_month_start]

    for _, user in active_users.iterrows():
        if np.random.rand() < 0.8:  # 80% MAU
            mean_days = 20 if user["DeviceType"] == "Security Camera" else 8
            active_days = int(np.clip(np.random.normal(mean_days, 5), 1, 31))
            days_selected = np.random.choice(range(1, 32), size=active_days, replace=False)
            for day in days_selected:
                telemetry_records.append(
                    {
                        "UserID": user["UserID"],
                        "LogDate": datetime(2023, 3, day),
                        "AppOpens": int(np.random.randint(1, 10)),
                        "MinutesActive": round(np.random.uniform(2.0, 45.0), 1),
                    }
                )

    telemetry_df = pd.DataFrame(telemetry_records)

    # Export to CSV
    users_df.to_csv(os.path.join(output_dir, "hardware_users.csv"), index=False)
    subs_df.to_csv(os.path.join(output_dir, "subscriptions.csv"), index=False)
    telemetry_df.to_csv(os.path.join(output_dir, "telemetry_logs_202303.csv"), index=False)

    # Quick diagnostics (so the generator self-reports the planted truth).
    churned = subs_df[~subs_df["IsActive"].astype(bool)].copy()
    active = subs_df[subs_df["IsActive"].astype(bool)].copy()
    end_for_exposure = subs_df["SubscriptionEnd"].fillna(pd.Timestamp(SNAPSHOT))
    exposure_months = (
        (end_for_exposure - subs_df["SubscriptionStart"]).dt.days / 30.44
    ).clip(lower=0.0)

    print(
        f"[+] Synthetic DWH generated: {len(users_df)} users, {len(subs_df)} subscriptions, "
        f"{len(telemetry_df)} telemetry logs."
    )
    print(
        f"    Planted monthly hazards -> Camera {BASE_MONTHLY_HAZARD['Security Camera']:.3f}, "
        f"Doorbell {BASE_MONTHLY_HAZARD['Smart Doorbell']:.3f}"
    )
    print(
        f"    Observed churn events: {len(churned)} | still-active (censored): {len(active)} "
        f"| total exposure: {exposure_months.sum():,.0f} subscriber-months"
    )
    print(
        f"    Paths: {output_dir}/ hardware_users.csv | subscriptions.csv | telemetry_logs.csv"
    )


if __name__ == "__main__":
    print("[*] Generating analytical datasets for Subscription Economics...")
    generate_saas_hardware_data()
