# Project Alpha — Implementation Roadmap

## Purpose

This document is the execution checklist for Project Alpha after research and repository setup.

The GitHub repository is the source of truth. Work proceeds component-by-component, with each integration tested before the next layer is built.

## Current State

- Research/specification: defined
- Repository: connected; use feature branches and pull requests for changes
- Primary market-data API for V1: Upstox
- Development phase: data-ingestion and alignment validation
- Trading mode: paper trading only
- Implemented: Upstox authentication check, NIFTY 50 historical candles, FRED ingestion, optional parsed RBI alignment, Upstox news ingestion prototype, FinBERT inference, rolling news features, and basic automated unit tests
- Known limitations: news is currently Reliance-specific; FRED/RBI availability timestamps are conservative proxies, not exact point-in-time release metadata; no validated historical model/backtest yet

## Phase 1 — Upstox API

### Step 1 — Authentication
- [ ] Create/configure Upstox developer app
- [ ] Configure redirect URI
- [ ] Obtain client credentials
- [ ] Implement OAuth/authentication flow
- [ ] Obtain access token securely
- [ ] Store secrets outside Git

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

- [ ] Build training dataset
- [ ] Create 5m/15m/30m targets
- [ ] Time-series split
- [ ] Baseline models
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

**Create/configure the Upstox developer application and implement the authentication flow.**

The first success milestone is:

> Python authenticates successfully and retrieves real NIFTY market data from Upstox.
