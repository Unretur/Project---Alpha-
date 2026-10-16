# Project Alpha

> **Current status: research application / model validation in progress.** The latest local evaluation reported on 2026-10-15 did not qualify any of the 5m, 15m, or 30m return models for deployment: all three failed the zero-return MAE gate on the held-out test split, and walk-forward results did not show consistent baseline improvement. Forecasts are exploratory only; model-driven paper-trading entries must remain disabled. A running dashboard or cloud deployment is not evidence of predictive skill or profitability. See [Model Readiness and Research-Only Operation](docs/model-readiness-and-research-mode.md).


## NIFTY 50 Short-Horizon Prediction & Autonomous Paper-Trading System

Project Alpha is a production-oriented machine learning system designed to investigate whether financial news, market data, derivatives data, macroeconomic variables, and global market information can provide predictive power for short-horizon NIFTY 50 returns.

The system uses **FinBERT** to extract financial sentiment from text and combines those signals with structured market and derivatives features to generate short-horizon predictions and autonomous trading decisions.

The system will first operate in **paper-trading mode for 1–2 months** before any consideration of real-money execution.

---

## Objective

At each decision point, Alpha uses only information that was available at that exact time to estimate the future return of the NIFTY 50 over three horizons:

* **5 minutes**
* **15 minutes**
* **30 minutes**

The predictions are then converted into trading signals.

The underlying being predicted is the **NIFTY 50**.

The execution instrument for the paper-trading system is the **near-ATM weekly NIFTY Call/Put option (CE/PE)**.

---

## Core Prediction Pipeline

```text
Market Data ───────────────┐
                           │
Derivatives Data ──────────┤
                           │
Macro Data ────────────────┤
                           ├──> Feature Engineering
Global Market Data ────────┤
                           │
Financial News ────────────┤
                           │
                           └──> FinBERT
                                  │
                                  ↓
                         Sentiment Probabilities
                                  │
                                  ↓
                           Alpha Prediction
                                  │
                    ┌─────────────┼─────────────┐
                    ↓             ↓             ↓
                   5m            15m           30m
                    │             │             │
                    └─────────────┼─────────────┘
                                  ↓
                            Signal Engine
                                  ↓
                         Risk / Position Logic
                                  ↓
                         Paper Trading Engine
                                  ↓
                           Trade & P&L Logs
                                  ↓
                              Dashboard
```

---

## Prediction Targets

For a decision timestamp (t), Alpha will estimate:

[
R_{5m,t} = \frac{P_{t+5}}{P_t} - 1
]

[
R_{15m,t} = \frac{P_{t+15}}{P_t} - 1
]

[
R_{30m,t} = \frac{P_{t+30}}{P_t} - 1
]

where (P_t) represents the NIFTY 50 price at the decision timestamp.

The model may later produce both expected returns and directional probabilities.

---

## Trading Decision

Predictions are converted into explicit autonomous decisions.

Possible system states include:

```text
BULLISH
BEARISH
FLAT
EXIT
```

For the options execution layer:

```text
Bullish NIFTY signal
        ↓
Near-ATM NIFTY CE

Bearish NIFTY signal
        ↓
Near-ATM NIFTY PE

Insufficient edge
        ↓
FLAT

Existing position + signal invalidated
        ↓
EXIT
```

The system is intended to make paper-trading decisions automatically rather than requiring manual trade execution.

---

## Data

Project Alpha will use multiple information sources:

### Market

* NIFTY 50 price data
* Returns
* Volatility
* Momentum
* Market microstructure features where available

### Derivatives

* NIFTY futures
* Options data
* Open interest
* Volume
* Implied volatility
* Greeks where available
* Near-ATM CE/PE information

### News

* Financial news
* News timestamps
* Headlines and relevant text

### Macro

Relevant Indian and international macroeconomic variables.

### Global

Relevant global indices, futures, commodities, currencies, and other market indicators.

The exact providers and APIs will be documented separately after the data-source evaluation.

---

## FinBERT

FinBERT is used to convert financial text into probability-based sentiment information.

Example output:

```text
Positive probability: 0.72
Neutral probability:  0.18
Negative probability: 0.10
```

These probabilities become features for the Alpha prediction system rather than being treated as the final trading signal by themselves.

---

## Backtesting

Before paper trading, Alpha will be evaluated on historical data.

The backtesting framework will evaluate:

* Returns
* Sharpe ratio
* Sortino ratio
* Maximum drawdown
* Volatility
* Win rate
* Turnover
* Transaction costs
* Slippage
* Benchmark performance

The system will be compared against appropriate baseline strategies.

Backtesting must prevent:

* Look-ahead bias
* Data leakage
* Survivorship bias where applicable
* Incorrect timestamp alignment
* Unrealistic execution assumptions

---

## Timestamp Integrity

Timestamp alignment is a core design requirement.

The system must distinguish between:

```text
Information publication time
            ↓
Information availability time
            ↓
Model decision time
            ↓
Trade execution time
            ↓
Future return
```

Alpha must never use information that was unavailable at the moment a prediction was generated.

This rule applies to both historical backtesting and live/paper trading.

---

## Paper Trading

After historical validation, Alpha will enter a **1–2 month paper-trading period**.

The paper-trading system will:

1. Receive live market and information data.
2. Generate predictions automatically.
3. Generate trading signals.
4. Select the appropriate near-ATM NIFTY CE/PE.
5. Simulate order execution.
6. Track positions.
7. Track P&L.
8. Record every prediction and decision.
9. Compare predicted and realized outcomes.

No real capital will be used during this phase.

The model and signal specification should be frozen before the paper-trading evaluation begins to avoid continuously optimizing against live results.

---

## Production Architecture

The intended production architecture includes:

```text
Data Sources
     ↓
Data Ingestion
     ↓
Data Validation
     ↓
Timestamp Alignment
     ↓
Feature Engineering
     ↓
FinBERT Inference
     ↓
Prediction Model
     ↓
Signal Engine
     ↓
Risk Management
     ↓
Paper Trading Engine
     ↓
Storage
     ↓
Monitoring / Dashboard
```

Cloud infrastructure will be built primarily on **AWS**, with services selected according to the requirements of the final implementation.

Potential components include:

* Amazon S3
* Amazon SageMaker
* CloudWatch
* IAM
* Compute/container infrastructure
* GitHub Actions
* Supabase
* Streamlit

The final AWS architecture will be documented separately.

---

## Project Architecture

```text
project-alpha/
│
├── README.md
│
├── docs/
│   ├── research-specification.md
│   ├── architecture.md
│   ├── data-contracts.md
│   ├── data-pipeline.md
│   ├── backtesting.md
│   ├── paper-trading.md
│   └── deployment.md
│
├── src/
│   ├── ingestion/
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   ├── signals/
│   ├── backtesting/
│   ├── paper_trading/
│   └── pipeline/
│
├── tests/
│
├── notebooks/
│   └── research/
│
├── dashboard/
│
├── infra/
│   └── aws/
│
├── .github/
│   └── workflows/
│
├── requirements.txt
│
└── .gitignore
```

---

## Development Philosophy

Project Alpha is being developed as an end-to-end ML/quantitative system rather than as a standalone notebook.

The system will prioritize:

* Reproducibility
* Data integrity
* Proper time-series validation
* Leakage prevention
* Modular architecture
* Automated testing
* Observability
* Reusable inference code
* Separation of research and production components
* Realistic execution assumptions

The historical backtest and paper-trading system should share the same core preprocessing, feature, prediction, and signal-generation logic wherever possible.

---

## Current Status

### Repository / Engineering Status

- [x] GitHub repository connected and active
- [x] GitHub repository: `Unretur/Project---Alpha-`
- [x] Main branch established
- [x] README created
- [x] Research specification created
- [x] Data contracts created
- [x] Provider research completed
- [x] Core Alpha scope locked
- [x] Upstox selected as the primary market-data API for V1 implementation
- [ ] Upstox developer app/authentication configured
- [ ] First successful NIFTY API response
- [ ] Historical market-data ingestion
- [ ] Derivatives/options ingestion
- [ ] Live WebSocket ingestion
- [ ] Macro/news integrations
- [ ] Feature pipeline
- [ ] FinBERT inference pipeline
- [ ] Prediction model
- [ ] Signal engine
- [ ] Backtesting engine
- [ ] Paper-trading engine
- [x] Temporary Docker/AWS dashboard smoke test completed (2026-10-16); public-IP access verified, then EC2 instance terminated
- [ ] Reproducible deployment configuration committed to GitHub
- [ ] Permanent dashboard hosting / live dashboard

### Current Phase

**Research application / model validation.** Market-data ingestion and model evaluation code are present, but the latest reported model evaluation (2026-10-15) did not qualify any horizon for model-driven entries.

The current 5m, 15m, and 30m Ridge models all failed to beat the zero-return MAE baseline on the held-out test set. Walk-forward evaluation did not establish consistent improvement. See [Model Readiness and Research-Only Operation](docs/model-readiness-and-research-mode.md) for the reported metrics and validation plan.

The dashboard may be deployed as a research interface, provided forecasts are clearly labelled exploratory and automated model-driven paper-trading entries remain disabled. On 2026-10-16, a temporary Docker image was pushed to Docker Hub, pulled onto an AWS EC2 test instance, and the dashboard was verified through a public URL. The EC2 instance was then terminated, the temporary inbound rule was removed, and the test URL is no longer a persistent deployment. This deployment was intentionally temporary: keeping cloud compute online can create recurring charges, which are not appropriate to incur continuously just to keep a student portfolio project publicly available. The goal is to demonstrate and document the end-to-end engineering workflow—not to claim that a paid cloud deployment must run 24/7. The test demonstrated containerizing the Streamlit dashboard, publishing and pulling an image through Docker Hub, running it on EC2, verifying public reachability, and cleaning up the cloud resources afterward. The dashboard Dockerfile and its build requirements used for that test are not yet committed in this repository, so the deployment is not currently reproducible from GitHub alone. Project Alpha is an end-to-end learning and engineering project spanning data science, machine learning, data pipelines, model evaluation, and DevOps/cloud deployment; individual components remain in progress and model readiness is still gated by validation. A successful Docker/AWS smoke test is an infrastructure milestone, not evidence of predictive skill or profitability.

### Next Steps

1. Preserve the deployment gate and research-only status.
2. Inspect fold-level walk-forward results and audit targets, feature timestamps, and train/validation/test boundaries.
3. Improve and validate models using training/validation data only; reserve an untouched period for final evaluation.
4. Build realistic strategy evaluation with option pricing/selection, transaction costs, spread, slippage, and risk controls.
5. Add and review the dashboard's Dockerfile, dashboard-specific requirements, and deployment instructions in GitHub so the tested image can be rebuilt reproducibly; keep credentials and `.env` files out of source control.
6. Choose a low-cost permanent hosting option for the research interface without enabling automated entries.
7. Reconsider paper-trading eligibility only after a documented validation review.

### Development Rule

The GitHub repository is the source of truth for tracked code. Keep credentials out of source control and use environment variables or a secrets manager. Local dashboard code not present in this repository must be committed separately before it can be reviewed or deployed from GitHub.

## Disclaimer

Project Alpha is an experimental research and engineering project. Historical backtest results and paper-trading results do not guarantee future performance. No real-money trading is performed during the initial validation phase.

## Local data-ingestion workflow

Run commands from the repository root in the same Python environment used for the project.

Create the environment and install the project's runtime dependencies (PowerShell):

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

1. Configure local credentials in `.env` (copy `.env.example` and use the variable names documented by `src/config/config.py`). Never commit `.env`.
2. Download FRED observations:
   ```powershell
   .\.venv\Scripts\python.exe -m src.ingestion.fred.download_macro
   ```
3. Download NIFTY 50 5-minute candles:
   ```powershell
   .\.venv\Scripts\python.exe -m src.ingestion.upstox.historical
   ```
4. Build the market + macro dataset:
   ```powershell
   .\.venv\Scripts\python.exe -m src.data_engineering.build_aligned_dataset
   ```
5. Fetch news and run FinBERT:
   ```powershell
   .\.venv\Scripts\python.exe -m src.ingestion.upstox.news
   .\.venv\Scripts\python.exe -m src.ingestion.upstox.run_finbert
   .\.venv\Scripts\python.exe -m src.data_engineering.news_features
   .\.venv\Scripts\python.exe -m src.data_engineering.align_news_with_market
   ```

### Important data-timing limitation

The news ingestion timestamp is when this pipeline retrieved an article, not a historical archive of when the provider first made the article available. Therefore, this news dataset is not sufficient on its own to claim a point-in-time-valid historical backtest. The alignment code generates rolling 5-, 15-, and 30-minute sentiment features from articles whose recorded availability time is no later than the decision candle, but that check does not recover original historical availability. Use timestamped historical news data before making backtest claims that depend on news.

FRED observation dates likewise are not publication timestamps. The current pipeline delays those observations to the next UTC midnight as a conservative same-day leakage guard. This is a provisional proxy, not exact release/vintage data; verify release timing or use point-in-time datasets before treating historical backtest performance as validated.

The RBI parser expects source PDFs under `data/raw/rbi/`. When parsed RBI CSVs are present, the dataset builder includes them automatically; otherwise it continues with market + FRED data. RBI dates are delayed to the next UTC midnight as a conservative guard, not an exact publication timestamp.

Current Upstox news ingestion is a prototype that queries Reliance Industries only. It does not yet represent the full NIFTY 50 news universe and should not be interpreted as market-wide news coverage.

Historical candle download dates can be overridden with `ALPHA_MARKET_FROM_DATE` and `ALPHA_MARKET_TO_DATE`. The start date defaults to `2026-01-01`; the end date defaults to yesterday, avoiding a potentially incomplete current-session download.

