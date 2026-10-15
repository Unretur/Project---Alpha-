# Model Readiness and Research-Only Operation

## Current decision

Project Alpha's current short-horizon return models are **research-only**. None of the 5-, 15-, or 30-minute models passed the existing zero-return MAE deployment gate in the latest local evaluation reported on 2026-10-15.

The correct response is to preserve the gate, keep model-driven paper-trading entries disabled, and allow the application to display research forecasts and diagnostics with an explicit status. Do not describe these results as validated trading signals or evidence of profitability.

## Latest reported results

| Horizon | Test model MAE | Test zero-return MAE | Relative MAE improvement | Deployment eligible |
| --- | ---: | ---: | ---: | --- |
| 5m | 0.0004588011 | 0.0004341987 | -5.67% | No |
| 15m | 0.0008039832 | 0.0007417792 | -8.39% | No |
| 30m | 0.0011854365 | 0.0010428931 | -13.67% | No |

Negative improvement means the trained model's mean absolute error was higher than the zero-return baseline's error.

The reported expanding-window walk-forward evaluation also failed to establish consistent improvement:

| Horizon | Folds beating zero-return baseline | Aggregate model MAE | Aggregate baseline MAE | Relative MAE improvement |
| --- | ---: | ---: | ---: | ---: |
| 5m | 0/4 | 0.00041104 | 0.00040375 | -1.81% |
| 15m | 1/4 | 0.00071143 | 0.00069566 | -2.27% |
| 30m | 0/4 | 0.00100452 | 0.00097459 | -3.07% |

These values are from the user's local run and should be regenerated from the current dataset before being treated as a reproducible repository artifact.

## Research application requirements

The dashboard/application may be deployed for demonstration and research if it clearly communicates all of the following:

- Application status is separate from model eligibility. A running dashboard or successful AWS deployment does not validate the models.
- Forecasts from ineligible models are exploratory outputs only.
- Automated model-driven paper-trading entries remain disabled while the gate fails.
- No broker orders or real-money trades are sent.
- Display the evaluation date, model artifact/version where available, forecast timestamp, and stale-data status.
- Show the gate result for each horizon rather than implying all horizons have the same quality.
- Log prediction errors, missing/stale input data, model-loading errors, and application failures.
- Do not silently override or bypass `deployment_eligible`.

## Current model limitations

The training report currently documents that:

- Historical point-in-time news features are not included in the training pipeline.
- Macro availability timestamps are conservative proxies rather than exact release vintages.
- Predictive metrics do not establish profitability after transaction costs, slippage, option pricing, and execution effects.

The feature list in the current training report consists of lagged NIFTY returns/candle features and macro variables. FinBERT news sentiment is not among those 14 training features in that report. Do not claim that the current return model is using FinBERT sentiment unless the training data and feature pipeline are changed and verified.

## Next validation work

1. Re-run training and save the metrics report with the dataset/version and run timestamp.
2. Inspect walk-forward results per fold, not only aggregate MAE.
3. Verify target construction, timestamp ordering, feature availability, and train/validation/test boundaries for leakage or alignment defects.
4. Compare against simple, time-appropriate baselines and evaluate whether directional metrics are statistically meaningful. A zero predictor's sign accuracy is not a meaningful directional benchmark when its predictions are all zero.
5. Only after sound out-of-sample predictive evidence, build a trading simulator that includes option contract selection, transaction costs, spread, slippage, and realistic execution assumptions.
6. Keep paper trading disabled for model-driven entries until a documented review approves the relevant horizon/model.

## Research-only CLI

The prediction module supports an explicit research override for inspecting models that fail the deployment gate:

```powershell
.\.venv\Scripts\python.exe -m src.models.predict_latest --allow-research-model
```

This flag is for inspection only. It must not be wired to an automated trading path or used to change the saved eligibility status.
