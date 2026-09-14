# Project Alpha — Research Specification

## 1. Research Objective

Project Alpha investigates whether information available in real time from financial news, market data, derivatives, macroeconomic variables, and global markets can provide predictive information about short-horizon NIFTY 50 returns.

The system is designed as an end-to-end quantitative ML pipeline:

```text
Live Information
      ↓
Feature Engineering
      ↓
FinBERT + Structured Features
      ↓
Return Prediction
      ↓
Trading Signal
      ↓
Risk Management
      ↓
Paper Trading
      ↓
Performance Evaluation
```

---

# 2. Underlying

## Primary Underlying

**NIFTY 50**

NIFTY 50 is the underlying asset whose future returns Alpha attempts to predict.

## Execution Instrument

The paper-trading layer will use:

**Near-ATM weekly NIFTY Call Options (CE)** for bullish exposure.

**Near-ATM weekly NIFTY Put Options (PE)** for bearish exposure.

The prediction target and execution instrument are intentionally separated.

```text
NIFTY 50
   ↓
Prediction Target

NIFTY Weekly CE/PE
   ↓
Execution Instrument
```

---

# 3. Prediction Horizons

Alpha will generate predictions for three forward horizons:

* 5 minutes
* 15 minutes
* 30 minutes

The initial decision frequency will be **5 minutes**.

Therefore, the system will generate a new prediction at each 5-minute decision point during the defined trading session.

Example:

```text
10:00 → prediction
10:05 → prediction
10:10 → prediction
10:15 → prediction
...
```

The system will not rely on running the prediction model every second.

Market and information data may be collected at higher frequency where available, but the initial Alpha decision cycle is 5 minutes.

---

# 4. Primary Prediction Targets

For decision timestamp `t`, Alpha will calculate forward NIFTY returns.

## 5-Minute Forward Return

```text
R_5(t) = P(t+5) / P(t) - 1
```

## 15-Minute Forward Return

```text
R_15(t) = P(t+15) / P(t) - 1
```

## 30-Minute Forward Return

```text
R_30(t) = P(t+30) / P(t) - 1
```

Where:

* `P(t)` = NIFTY price at decision time `t`
* `P(t+5)` = NIFTY price 5 minutes after `t`
* `P(t+15)` = NIFTY price 15 minutes after `t`
* `P(t+30)` = NIFTY price 30 minutes after `t`

These forward returns are historical labels used for model training and evaluation.

They are never available to the model during a live prediction.

---

# 5. Prediction Output

Alpha should eventually produce both expected return and directional probability for each horizon.

Conceptually:

```text
5-minute:
    Expected return
    P(UP)
    P(DOWN)

15-minute:
    Expected return
    P(UP)
    P(DOWN)

30-minute:
    Expected return
    P(UP)
    P(DOWN)
```

Example:

```text
Time: 10:00

NIFTY: 25,000

5m:
Expected return: +0.12%
P(UP): 68%

15m:
Expected return: +0.21%
P(UP): 73%

30m:
Expected return: +0.27%
P(UP): 76%
```

The values above are illustrative only.

They do not represent expected model performance.

---

# 6. Feature Universe

Alpha will initially investigate five major feature groups.

## 6.1 Market Features

Potential features include:

* NIFTY price
* Log returns
* Rolling returns
* Momentum
* Realized volatility
* High/low range
* Volume
* VWAP where available
* Market breadth
* Intraday price structure

The exact feature set will be determined through research and validation.

---

## 6.2 Derivatives Features

Potential features include:

* NIFTY futures price
* Futures basis
* Options open interest
* Options volume
* Implied volatility
* Put-call ratios
* Near-ATM option information
* Greeks where available
* Changes in open interest
* Futures positioning

The system must avoid using information that was not available at the decision timestamp.

---

## 6.3 Financial News

News will provide the primary unstructured-text input.

For each article/headline, the system should attempt to capture:

```text
article_id
publication_timestamp
source
headline
text where available
instrument relevance
```

News will be processed by FinBERT.

---

# 7. FinBERT Output

FinBERT will produce probability-based sentiment rather than only a categorical label.

For each relevant financial text item:

```text
P(positive)
P(neutral)
P(negative)
```

Example:

```text
Positive: 0.72
Neutral:  0.18
Negative: 0.10
```

These values will become features in the Alpha prediction system.

FinBERT sentiment is therefore an input to the predictive model, not the final trading decision.

---

# 8. Macro Features

Potential macroeconomic inputs include relevant:

* Indian macroeconomic indicators
* Interest-rate information
* Currency information
* Inflation-related information
* Economic event indicators
* Other scheduled macroeconomic releases

Macro features must include their actual release/availability timestamps.

A value released at time `t` cannot be used to generate a prediction for a timestamp before `t`.

---

# 9. Global Market Features

Potential global inputs include:

* Major global equity indices
* Global futures
* US market indicators
* Asian market indicators
* Currency markets
* Commodity markets
* Volatility indicators

The exact feature universe will be determined after evaluating data availability, latency, relevance, and cost.

---

# 10. Information Availability Rule

This is a fundamental rule of Project Alpha.

## Alpha may only use information available at the prediction timestamp.

For every feature:

```text
Feature timestamp
        ↓
Was the information available?
        ↓
YES → feature may be used
NO  → feature must be excluded
```

The historical dataset must reproduce the information set that Alpha would actually have had in live operation.

---

# 11. Timestamp Architecture

The system must distinguish:

```text
Publication Time
      ↓
Availability Time
      ↓
Decision Time
      ↓
Execution Time
      ↓
Future Price
```

For example:

```text
News published:       10:02:31
Decision point:        10:05:00
News available before: YES
                       ↓
                  Can be used
```

But:

```text
News published:       10:05:30
Decision point:        10:05:00
                       ↓
                  Cannot be used
```

This rule must be enforced in both historical backtesting and paper trading.

---

# 12. Signal Generation

The prediction model does not directly place a trade.

The architecture is:

```text
Predictions
    ↓
Confidence / Edge Evaluation
    ↓
Signal Engine
    ↓
Risk Management
    ↓
Execution Decision
```

Initial possible states:

```text
BULLISH
BEARISH
FLAT
EXIT
```

Execution mapping:

```text
BULLISH
   ↓
Near-ATM NIFTY CE

BEARISH
   ↓
Near-ATM NIFTY PE

FLAT
   ↓
No new position

EXIT
   ↓
Close existing position
```

The exact thresholds and position-sizing rules will be determined during model and strategy research rather than assumed in advance.

---

# 13. Paper Trading

Paper trading is a mandatory validation stage.

Duration:

**1–2 months**

The system will operate autonomously using live data but will not place real-money orders.

The paper-trading engine will:

1. Receive live data.
2. Construct the current feature set.
3. Run inference.
4. Generate predictions.
5. Generate a trading signal.
6. Select the appropriate near-ATM CE/PE.
7. Simulate execution.
8. Track positions.
9. Track P&L.
10. Store every prediction and trade.
11. Compare predictions with realized future returns.

The user will not manually execute trades during the paper-trading phase.

---

# 14. Paper Trading Records

Every decision should produce an immutable record containing, where applicable:

```text
decision_timestamp
NIFTY_price
model_version
feature_snapshot_id

prediction_5m
prediction_15m
prediction_30m

probability_up_5m
probability_up_15m
probability_up_30m

signal
selected_option
position
entry_price
exit_price

execution_timestamp
simulated_fill_price

transaction_cost
slippage
realized_pnl
```

This allows every decision to be reconstructed later.

---

# 15. Backtesting

Before paper trading, the strategy will be evaluated using historical data.

The backtester must model:

* Trading hours
* Position entry
* Position exit
* Transaction costs
* Slippage
* Option execution assumptions
* Position sizing
* Risk limits

Performance metrics will include:

* Total return
* CAGR where applicable
* Sharpe ratio
* Sortino ratio
* Maximum drawdown
* Volatility
* Win rate
* Profit factor
* Turnover
* Transaction costs

The strategy will be compared with appropriate baselines.

---

# 16. Time-Series Validation

Random train/test splitting will not be used for the primary evaluation.

The project will use time-ordered validation to prevent future information from entering the training process.

The eventual research design may include:

```text
Historical Period
        ↓
Training
        ↓
Validation
        ↓
Out-of-sample Test
        ↓
Paper Trading
```

Walk-forward validation may be introduced where appropriate.

---

# 17. Model Architecture

The initial conceptual architecture is:

```text
                    Financial News
                         ↓
                      FinBERT
                         ↓
              Sentiment Probabilities
                         │
                         │
Market ──────────────────┤
                         │
Derivatives ─────────────┤
                         │
Macro ───────────────────┤
                         │
Global ──────────────────┤
                         ↓
                Feature Engineering
                         ↓
                  Prediction Model
                         ↓
              ┌──────────┼──────────┐
              ↓          ↓          ↓
             5m         15m        30m
          prediction  prediction  prediction
              └──────────┼──────────┘
                         ↓
                   Signal Engine
                         ↓
                  Risk Management
                         ↓
                  Paper Execution
```

The final predictive architecture is intentionally not frozen until baseline experiments establish what provides meaningful predictive value.

---

# 18. Research Principle

Project Alpha is not designed to maximize historical backtest performance.

The primary objective is to determine whether the predictive relationship survives:

```text
Training
   ↓
Out-of-sample testing
   ↓
Unseen live data
   ↓
Paper trading
```

A simpler model with robust out-of-sample performance is preferable to a highly complex model that only performs well historically.

---

# 19. Production Requirement

The backtesting and paper-trading systems should share the same core:

```text
Preprocessing
      +
Feature Engineering
      +
Model Inference
      +
Signal Generation
```

The data source changes between historical and live operation, but the core logic should remain consistent.

This prevents divergence between the backtested strategy and the deployed strategy.

---

# 20. Validation Gate

Alpha should not automatically progress from backtesting to paper trading because a backtest looks profitable.

The transition should require predefined validation criteria.

Conceptually:

```text
Historical Backtest
        ↓
Out-of-Sample Evaluation
        ↓
Does the strategy satisfy predefined criteria?
        │
       YES
        ↓
1–2 Month Paper Trading
        ↓
Live Forward Evaluation
        ↓
Final Assessment
```

The exact acceptance criteria will be defined before the paper-trading period begins.

---

# 21. Current Decisions

| Decision                   | Status                      |
| -------------------------- | --------------------------- |
| Underlying                 | NIFTY 50                    |
| Prediction horizons        | 5m / 15m / 30m              |
| Initial decision frequency | 5 minutes                   |
| Execution instrument       | Near-ATM weekly NIFTY CE/PE |
| News sentiment model       | FinBERT                     |
| Market features            | Included                    |
| Derivatives features       | Included                    |
| Macro features             | Included                    |
| Global features            | Included                    |
| Historical backtesting     | Required                    |
| Paper trading              | Required                    |
| Paper-trading duration     | 1–2 months                  |
| Real-money trading         | Not part of initial project |
| Timestamp integrity        | Mandatory                   |
| Look-ahead prevention      | Mandatory                   |
| Time-series validation     | Mandatory                   |

---

# 22. Open Research Decisions

The following are intentionally not finalized yet:

* Exact historical market-data provider
* Exact options-data provider
* Exact news providers
* Exact macro data providers
* Exact global data providers
* Final feature list
* Exact prediction model architecture
* Regression vs. classification architecture
* Signal thresholds
* Position-sizing methodology
* Risk limits
* Option-selection algorithm
* Execution assumptions
* AWS architecture details

These decisions will be made through research and experiments rather than arbitrary assumptions.
