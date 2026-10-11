# Model training, evaluation, and inference

Run commands from the repository root in the project's Python 3.11 virtual environment.

## Build the training dataset

~~~powershell
.\.venv\Scripts\python.exe -m src.data_engineering.build_aligned_dataset
.\.venv\Scripts\python.exe -m src.data_engineering.create_targets
~~~

The aligned dataset requires the configured raw NIFTY and FRED files; RBI files are optional. Do not invent or fill missing market observations to force training to run.

## Train, compare, and evaluate

~~~powershell
.\.venv\Scripts\python.exe -m src.models.train_model
~~~

For each 5-, 15-, and 30-minute return target, this compares a scaled Ridge model with a constrained histogram gradient-boosting regressor. Candidate selection uses validation MAE only. The selected candidate is refit on train+validation and evaluated once on the chronological test segment. A zero-return predictor is reported on both validation and test.

Outputs:
- models/artifacts/nifty_return_5m.joblib
- models/artifacts/nifty_return_15m.joblib
- models/artifacts/nifty_return_30m.joblib
- data/processed/model_training_metrics.json

Model artifacts and processed data are local outputs and are excluded from Git.

## Generate latest predictions

~~~powershell
.\.venv\Scripts\python.exe -m src.models.predict_latest
~~~

The command checks the model's stored feature list and deployment gate. It refuses to emit default predictions if a model failed to beat the zero-return MAE benchmark on both validation and test. To inspect experimental output only:

~~~powershell
.\.venv\Scripts\python.exe -m src.models.predict_latest --allow-research-model
~~~

The research override is not approval for live or automated trading. The printed timestamp is the timestamp of the latest row with complete features; verify it is recent enough for the intended use.

## Tests

~~~powershell
.\.venv\Scripts\python.exe -m unittest src.models.test_baseline src.models.test_evaluation_diagnostics src.models.test_train_predict_pipeline
~~~

## Interpretation and limits

- MAE/RMSE measure return-prediction error; sign accuracy alone is not evidence of trading edge.
- Passing the zero-return error benchmark is only a minimum model-quality gate, not a profitability guarantee. Backtesting still needs realistic fees, slippage, fill assumptions, and risk controls.
- Predictors are lagged and chronological splits purge the maximum 30-minute target horizon.
- Macro availability times are conservative proxies rather than exact historical release vintages.
- Historical point-in-time news features are not included until their historical availability can be established.
- Keep execution in paper-trading mode until the data, inference, and backtest path has been independently verified.
