
# Project Alpha — Data Contracts

## 1. Purpose

This document defines the structure, timing rules, and data requirements for Project Alpha.

The purpose is to ensure that historical training data and live inference data follow the same contract.

The most important requirement is:

> **No feature may contain information that was unavailable at the model's decision timestamp.**

---

# 2. Alpha Decision Event

Alpha operates on a 5-minute decision cycle.

Each decision is represented by a unique:

```text
decision_timestamp
```

Example:

```text
2026-09-15 10:00:00+05:30
```

At this timestamp, Alpha constructs a complete feature snapshot using only information available by that time.

---

# 3. Core Data Flow

```text
                    Decision Timestamp t
                            │
          ┌─────────────────┼─────────────────┐
          ↓                 ↓                 ↓
        Market          Derivatives          News
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ↓
                      Macro + Global
                            │
                            ↓
                    Feature Snapshot
                            │
                            ↓
                       Alpha Model
                            │
                ┌───────────┼───────────┐
                ↓           ↓           ↓
              5-min       15-min      30-min
              target       target      target
```

---

# 4. Market Data Contract

## Required Concept

NIFTY 50 market information available at the decision timestamp.

### Core fields

```text
decision_timestamp
nifty_open
nifty_high
nifty_low
nifty_close
nifty_volume
```

### Derived fields

Potential derived features include:

```text
return_1m
return_5m
return_15m
return_30m

volatility_5m
volatility_15m
volatility_30m

high_low_range
distance_from_day_open
distance_from_day_high
distance_from_day_low
```

The final feature list will be determined through research.

---

# 5. Derivatives Data Contract

The derivatives layer provides information about the NIFTY futures and options market.

## Futures

Potential fields:

```text
futures_price
futures_volume
futures_open_interest
futures_basis
futures_return
```

## Options

For relevant strikes and expiries:

```text
timestamp
expiry
strike
option_type
last_price
volume
open_interest
implied_volatility
delta
gamma
theta
vega
```

Not every field is guaranteed to be available from every provider.

The final schema will depend on the selected data source.

---

# 6. Near-ATM Option Contract

For paper trading, Alpha will select a near-ATM weekly NIFTY CE or PE.

The option-selection layer must record:

```text
decision_timestamp
underlying_price
expiry
strike
option_type
option_price
option_volume
option_open_interest
implied_volatility
```

The exact definition of:

```text
"near-ATM"
```

will be finalized before paper trading.

The selection algorithm must be deterministic and reproducible.

---

# 7. News Data Contract

Each news item should contain, where available:

```text
article_id
source
publication_timestamp
availability_timestamp
headline
body
url
```

The distinction between:

```text
publication_timestamp
```

and:

```text
availability_timestamp
```

is important.

If an article was published after the Alpha decision timestamp, it cannot be used for that decision.

---

# 8. News Aggregation

News is not directly inserted into the model as an unlimited collection of articles.

News will first be transformed into time-aware features.

For example:

```text
decision_timestamp = 10:00

Eligible news:

09:51
09:55
09:57
09:59

Ineligible:

10:01
10:03
```

Potential aggregated features:

```text
news_count
news_count_5m
news_count_15m
news_count_30m

finbert_positive_mean
finbert_negative_mean
finbert_neutral_mean

finbert_positive_weighted
finbert_negative_weighted

sentiment_score
sentiment_dispersion
```

The aggregation methodology will be finalized during feature engineering.

---

# 9. FinBERT Contract

For each eligible financial-text item, FinBERT produces:

```text
positive_probability
neutral_probability
negative_probability
```

Example:

```text
positive_probability = 0.72
neutral_probability  = 0.18
negative_probability = 0.10
```

The inference timestamp must be recorded.

FinBERT inference must only process news eligible for the relevant decision timestamp.

---

# 10. Macro Data Contract

Macro data must contain both the observed value and its information timing.

Conceptually:

```text
indicator
value
release_timestamp
availability_timestamp
revision_timestamp
```

Where available.

A macro value cannot be used before its public release.

Historical revisions must be handled carefully to avoid using information that was not known at the time.

---

# 11. Global Market Data Contract

Potential global features include:

```text
instrument
timestamp
price
return
volume
```

Examples of potential categories:

```text
Global equity indices
US futures
Asian indices
Currencies
Commodities
Volatility indicators
```

The exact instruments will be selected based on their relevance to NIFTY and data availability.

---

# 12. Feature Snapshot

At every Alpha decision timestamp, all eligible information is transformed into a single feature snapshot.

Conceptually:

```text
alpha_feature_snapshot

decision_timestamp

MARKET
├── nifty_price
├── returns
├── volatility
└── market features

DERIVATIVES
├── futures
├── open interest
├── options
├── IV
└── derivatives features

NEWS
├── news_count
├── sentiment
└── FinBERT probabilities

MACRO
└── macro features

GLOBAL
└── global features
```

This snapshot represents the information set available to Alpha at time `t`.

---

# 13. Prediction Targets

The targets are deliberately separated from the feature snapshot.

```text
feature_timestamp = t

target_5m
target_15m
target_30m
```

They are calculated using future NIFTY prices.

```text
target_5m  = P(t+5)  / P(t) - 1
target_15m = P(t+15) / P(t) - 1
target_30m = P(t+30) / P(t) - 1
```

These fields are only used for historical training and evaluation.

They must never enter the live feature set.

---

# 14. Training Dataset Contract

A training observation conceptually contains:

```text
decision_timestamp

MARKET FEATURES
DERIVATIVES FEATURES
NEWS FEATURES
FINBERT FEATURES
MACRO FEATURES
GLOBAL FEATURES

TARGET_5M
TARGET_15M
TARGET_30M
```

The feature portion represents information available at `t`.

The target portion represents what happened after `t`.

---

# 15. Live Prediction Contract

During live operation:

```text
decision_timestamp
        ↓
Collect available information
        ↓
Validate timestamps
        ↓
Create feature snapshot
        ↓
Run model
        ↓
Generate:
    prediction_5m
    prediction_15m
    prediction_30m
        ↓
Signal Engine
```

Future target values are obviously unavailable during this process.

---

# 16. Prediction Record

Every live/paper prediction should be stored.

Conceptual schema:

```text
prediction_id
decision_timestamp
model_version

prediction_5m
prediction_15m
prediction_30m

probability_up_5m
probability_up_15m
probability_up_30m

signal
```

---

# 17. Paper Trade Record

Every paper trade should be stored separately from predictions.

Conceptual schema:

```text
trade_id
prediction_id

decision_timestamp
execution_timestamp

underlying
option_type
expiry
strike

entry_price
exit_price

quantity

simulated_fill_price
transaction_cost
slippage

realized_pnl
```

---

# 18. Data Quality Requirements

Every data source must be checked for:

* Missing timestamps
* Duplicate records
* Invalid prices
* Missing values
* Out-of-order timestamps
* Unexpected gaps
* Incorrect timezone
* Incorrect trading dates
* Corporate/calendar effects where relevant
* Provider outages

Invalid records should not silently enter the model.

---

# 19. Timezone

Project Alpha will use:

```text
Asia/Kolkata
```

for the canonical market decision timestamp.

Internal storage may use UTC if required by infrastructure, but conversions must be deterministic and timezone-aware.

Naive timestamps should not be used in the production pipeline.

---

# 20. Data Lineage

Every production feature should be traceable to its source.

Conceptually:

```text
Source
   ↓
Raw Data
   ↓
Validated Data
   ↓
Processed Data
   ↓
Feature
   ↓
Model Prediction
   ↓
Trading Signal
   ↓
Paper Trade
```

The system should make it possible to investigate why a particular prediction or trade occurred.

---

# 21. Historical vs Live Consistency

The historical and live systems should use the same feature definitions.

```text
Historical Data
      ↓
Same preprocessing
      ↓
Same feature engineering
      ↓
Same model
      ↓
Backtest
```

and:

```text
Live Data
      ↓
Same preprocessing
      ↓
Same feature engineering
      ↓
Same model
      ↓
Paper Trading
```

Only the source of the data changes.

---

# 22. Current Status

## Defined

* NIFTY 50 underlying
* 5-minute decision cycle
* 5-minute target
* 15-minute target
* 30-minute target
* Market data
* Derivatives data
* News data
* FinBERT features
* Macro data
* Global data
* Paper-trading records
* Timestamp integrity requirements

## Not Yet Finalized

* Historical market-data provider
* Historical options-data provider
* Historical news provider
* Macro providers
* Global-data providers
* Exact feature list
* Exact option-selection methodology
* Exact signal thresholds
* Exact risk-management rules
* Data retention/storage implementation
