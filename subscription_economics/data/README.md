# Data

## Files

### `hardware_users.csv`
Synthetic user-level table for an IoT company, representing 5,000 hardware purchasers across two device types with A/B test onboarding variants. Used for cohort analysis and subscription attach-rate modeling.

| Column | Type | Description |
|--------|------|-------------|
| UserID | int | Unique user identifier (10000-14999) |
| DeviceType | str | Hardware product purchased: "Security Camera" or "Smart Doorbell" |
| PurchaseDate | date | Date of hardware purchase (2022-01-01 to 2022-12-31) |
| OnboardingVersion | str | A/B test group: "Control" (classic flow) or "Variant" (optimized flow) |
| CohortMonth | str | Year-month cohort derived from PurchaseDate (e.g., "2022-03") |

### `subscriptions.csv`
Subscription fact table. Each row is one SaaS subscription tied to a user. Conversion probability depends on device type and onboarding variant. Churn probability varies by device and onboarding group.

| Column | Type | Description |
|--------|------|-------------|
| UserID | int | Foreign key to hardware_users |
| PlanName | str | Subscription plan name (always "Premium Cloud Storage") |
| MonthlyFee | float | Monthly subscription fee (14.99 for cameras, 9.99 for doorbells) |
| SubscriptionStart | date | Date the subscription began |
| SubscriptionEnd | date | Date the subscription ended (empty if still active) |
| IsActive | bool | Whether the subscription is currently active |

### `telemetry_logs_202303.csv`
Daily condensed telemetry logs for March 2023, recording app engagement for users who purchased before that month. Approximately 80% of eligible users appear (MAU simulation).

| Column | Type | Description |
|--------|------|-------------|
| UserID | int | Foreign key to hardware_users |
| LogDate | date | Date of the telemetry log entry (March 2023) |
| AppOpens | int | Number of app opens on that day (1-9) |
| MinutesActive | float | Total minutes of active usage on that day (2.0-45.0) |

## Regeneration

To regenerate the data files, run from the `src/` directory:

```bash
python data_generator.py
```

All files are generated deterministically with `np.random.seed(42)`.
