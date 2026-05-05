import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

# Determinism
np.random.seed(42)


def generate_saas_hardware_data(output_dir="../data", n_users=5000):
    """
    Generate a relational model simulating the data warehouse of an IoT company
    with hardware lines (Security Cameras vs. Smart Doorbells), subscription
    logs (SaaS), and usage telemetry for cohort analysis.
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
    time_between_dates = end_date - start_date
    days_between_dates = time_between_dates.days

    purchase_dates = [
        start_date + timedelta(days=np.random.randint(0, days_between_dates))
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
    # Cameras convert better (higher attach rate); the variant onboarding also
    # improves conversion.
    subscriptions = []

    for _, user in users_df.iterrows():
        base_conv_prob = 0.35 if user["DeviceType"] == "Security Camera" else 0.20
        # A/B test effect on conversion
        if user["OnboardingVersion"] == "Variant":
            base_conv_prob += 0.15

        converts_to_sub = np.random.rand() < base_conv_prob

        if converts_to_sub:
            sub_start = user["PurchaseDate"] + timedelta(days=np.random.randint(1, 14))

            # Churn probability based on cohort and device type
            churn_prob = 0.4 if user["DeviceType"] == "Smart Doorbell" else 0.2
            if user["OnboardingVersion"] == "Variant":
                churn_prob -= 0.05  # Slightly better retention with the new onboarding

            churns = np.random.rand() < churn_prob

            if churns:
                # Random duration before churn (1 to 8 months)
                sub_end = sub_start + timedelta(days=np.random.randint(30, 240))
                is_active = False
            else:
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
    # Generate condensed daily logs for one sample month (March 2023) only,
    # to avoid blowing up memory while still simulating active users.
    telemetry_records = []
    sample_month_start = datetime(2023, 3, 1)

    # Only users who purchased before March 2023
    active_users = users_df[users_df["PurchaseDate"] < sample_month_start]

    for _, user in active_users.iterrows():  # random sample to simulate real MAU vs total MAU
        # Did they show up that month?
        if np.random.rand() < 0.8:  # 80% MAU
            # How many active days? (DAU)
            # Cameras have higher stickiness than doorbells.
            mean_days = 20 if user["DeviceType"] == "Security Camera" else 8
            active_days = np.clip(np.random.normal(mean_days, 5), 1, 31).astype(int)

            # Generate logs for those days
            days_selected = np.random.choice(range(1, 32), size=active_days, replace=False)
            for day in days_selected:
                telemetry_records.append(
                    {
                        "UserID": user["UserID"],
                        "LogDate": datetime(2023, 3, day),
                        "AppOpens": np.random.randint(1, 10),
                        "MinutesActive": round(np.random.uniform(2.0, 45.0), 1),
                    }
                )

    telemetry_df = pd.DataFrame(telemetry_records)

    # Export to CSV
    users_df.to_csv(os.path.join(output_dir, "hardware_users.csv"), index=False)
    subs_df.to_csv(os.path.join(output_dir, "subscriptions.csv"), index=False)
    telemetry_df.to_csv(os.path.join(output_dir, "telemetry_logs_202303.csv"), index=False)

    print(
        f"[+] Synthetic DWH generated: {len(users_df)} users, {len(subs_df)} subscriptions, "
        f"{len(telemetry_df)} telemetry logs."
    )
    print(
        f"    Paths: {output_dir}/ hardware_users.csv | subscriptions.csv | telemetry_logs.csv"
    )


if __name__ == "__main__":
    print("[*] Generating analytical datasets for Subscription Economics...")
    generate_saas_hardware_data()
