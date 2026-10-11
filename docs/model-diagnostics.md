# Baseline and data diagnostics

Run these commands from the repository root using the project's virtual environment. The scripts read `data/processed/nifty_training_dataset.csv`; the diagnostic scripts do not overwrite the dataset.

## Commands (PowerShell)

```powershell
.\.venv\Scripts\python.exe -m src.models.raw_data_audit
.\.venv\Scripts\python.exe -m src.models.target_diagnostics
.\.venv\Scripts\python.exe -m src.models.feature_diagnostics
.\.venv\Scripts\python.exe -m src.models.evaluation_diagnostics
.\.venv\Scripts\python.exe -m unittest src.models.test_baseline src.models.test_evaluation_diagnostics
```

Run the target-building pipeline first if the processed dataset does not exist:

```powershell
.\.venv\Scripts\python.exe -m src.data_engineering.create_targets
```

## What to inspect

- **Raw-data audit:** missingness, variability, and numeric ranges for market and available macro columns.
- **Target diagnostics:** return distribution and missing-target counts for the 5-, 15-, and 30-minute horizons.
- **Feature diagnostics:** feature missingness/variability, Pearson association with targets, and chronological train/test distribution shifts.
- **Evaluation diagnostics:** Ridge regression errors compared with a zero-return predictor, plus directional coverage. A high sign-accuracy figure is not by itself evidence of tradable edge.

## Research safeguards

- Predictors are lagged and the baseline uses chronological splits with a 30-minute purge.
- Constant-volume-derived features are omitted because they contain no variation.
- Correlation and baseline metrics are exploratory diagnostics, not a claim of profitability.
- Historical news point-in-time availability is not currently established, so these diagnostics do not validate a news-driven historical backtest.
