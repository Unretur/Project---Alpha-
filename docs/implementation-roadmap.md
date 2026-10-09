# Project Alpha — Implementation Roadmap

## Purpose
This document is the execution checklist for Project Alpha after research and repository setup.

The GitHub repository is the source of truth. Work proceeds component-by-component, with each integration tested before the next layer is built.

## Current State
- Research/specification: defined
- Repository: connected; use feature branches and pull requests for changes
- Primary market-data API for V1: Upstox
- Development phase: baseline model implementation and evaluation
- Trading mode: paper trading only
- Implemented: Upstox historical NIFTY candles, FRED ingestion, optional parsed RBI alignment, prototype Upstox news ingestion, FinBERT inference, rolling news features, automated tests, exact-timestamp forward-return target generation, and an initial leakage-conscious Ridge baseline
- Known limitations: news is currently Reliance-specific and has no overlap with the available historical market window; FRED/RBI availability timestamps are conservative proxies, not exact point-in-time release metadata; no validated historical trading backtest yet

## Phase 1 — Upstox API

### Step 1 — Authentication
- [ ] Create/configure Upstox developer app
- [ ] Configure redirect URI
- [ ] Obtain client credentials
- [ ] Implement OAuth/authentication flow
- [ ] Obtain access token securely
- [x] Store secrets outside Git

### Step 2 — First Market Data Call
- [x] Identify NIFTY instrument key
- [x] Validate authenticated Upstox profile request
- [x] Parse historical candle response
- [x] Normalize timestamps and remove duplicate candles
- [ ] Validate market-session coverage against an exchange calendar
- [ ] Add an authenticated integration test that can run with local credentials

### Step 3 — Historical Data
- [x] Historical NIFTY candles
- [ ] Historical futures data
- [ ] Historical options/option-chain data
- [ ] OI/IV/Greeks where available
- [ ] Global instruments required by Alpha
- [ ] Normalize to the Alpha data contract

### Step 4 — Live Data
- [ ] Configure Upstox WebSocket V3
- [ ] Stream required instruments
- [ ] Validate incoming messages
- [ ] Handle reconnects/errors
- [ ] Persist raw events

## Phase 2 — Data Pipeline
- [x] Local raw-data storage
- [x] Basic data validation
- [x] Timestamp normalization
- [x] Conservative availability-time guards
- [x] Rolling time-windowed news features
- [ ] Build and validate a versioned feature snapshot contract
- [ ] S3 storage

## Phase 3 — News + Macro + FinBERT
- [x] Implement prototype Upstox news ingestion (Reliance-only scope)
- [x] Implement FRED macro ingestion
- [x] Add optional parsed RBI CSV alignment
- [x] Add conservative publication/availability-time guards
- [x] Run FinBERT inference
- [x] Aggregate sentiment into 5m/15m/30m rolling features
- [ ] Select and integrate a historical point-in-time news source before news-based backtesting

## Phase 4 — ML
- [x] Implement exact-timestamp 5m/15m/30m forward-return target generation
- [x] Run target generation and inspect valid-target counts
- [x] Implement model feature construction that excludes targets and availability-time metadata
- [x] Implement chronological train/validation/test splitting with horizon purging
- [x] Implement initial Ridge regression baselines for 5m/15m/30m returns
- [ ] Run baseline locally on the current dataset and review metrics
- [ ] Compare model performance with zero-return baseline
- [ ] Improve/validate macro point-in-time assumptions
- [ ] Alpha prediction model
- [ ] Probability/calibration evaluation

## Phase 5 — Trading Research
- [ ] Signal engine
- [ ] Risk rules
- [ ] Option selection
- [ ] Backtesting
- [ ] Slippage/transaction-cost assumptions
- [ ] Out-of-sample validation

## Phase 6 — Paper Trading
- [ ] Live feature pipeline
- [ ] Live inference
- [ ] Autonomous paper signals
- [ ] Simulated fills
- [ ] Position/P&L tracking
- [ ] Immutable prediction/trade records

## Phase 7 — Deployment
- [ ] AWS infrastructure
- [ ] Secrets management
- [ ] Logging/monitoring
- [ ] FastAPI where required
- [ ] Streamlit dashboard
- [ ] Production-style health checks

## Git Workflow
Each component should follow:
```text
Implement on feature branch
  ↓
Add / update tests
  ↓
Run automated checks
  ↓
Review the diff
  ↓
Open pull request
  ↓
Merge to main after checks pass
```

Do not commit API keys, client secrets, access tokens, TOTP secrets, or other credentials.

## Immediate Next Action
Pull the baseline-modeling branch, run the baseline tests, then train/evaluate the three return-horizon baselines on the local training dataset. Review metrics against the zero-return baseline before starting trading backtests.
