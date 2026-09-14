# Project Alpha

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

**Phase 0 — Research Specification**

* [ ] NIFTY 50 selected as underlying
* [ ] 5-minute prediction horizon defined
* [ ] 15-minute prediction horizon defined
* [ ] 30-minute prediction horizon defined
* [ ] Near-ATM weekly NIFTY CE/PE selected as execution instrument
* [ ] Paper trading selected as the first live validation stage
* [ ] Final data providers selected
* [ ] Data contracts finalized
* [ ] Timestamp methodology finalized
* [ ] Prediction model architecture finalized
* [ ] Backtesting framework implemented
* [ ] Paper-trading engine implemented
* [ ] AWS deployment implemented
* [ ] Live dashboard implemented

---

## Disclaimer

Project Alpha is an experimental research and engineering project. Historical backtest results and paper-trading results do not guarantee future performance. No real-money trading is performed during the initial validation phase.
