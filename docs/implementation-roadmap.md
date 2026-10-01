# Project Alpha — Implementation Roadmap

## Purpose

This document is the execution checklist for Project Alpha after research and repository setup.

The GitHub repository is the source of truth. Work proceeds component-by-component, with each integration tested before the next layer is built.

## Current State

- Research/specification: complete
- Repository: connected
- Branch: main
- Primary market-data API for V1: Upstox
- Development phase: API implementation
- Trading mode: paper trading only

## Phase 1 — Upstox API

### Step 1 — Authentication
- [ ] Create/configure Upstox developer app
- [ ] Configure redirect URI
- [ ] Obtain client credentials
- [ ] Implement OAuth/authentication flow
- [ ] Obtain access token securely
- [ ] Store secrets outside Git

### Step 2 — First Market Data Call
- [ ] Identify NIFTY instrument key
- [ ] Request NIFTY market data
- [ ] Parse response
- [ ] Validate timestamp and price fields
- [ ] Write a minimal integration test

### Step 3 — Historical Data
- [ ] Historical NIFTY candles
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

- [ ] Raw-data storage
- [ ] Data validation
- [ ] Timestamp normalization
- [ ] Availability-time handling
- [ ] Feature snapshots
- [ ] S3 storage

## Phase 3 — News + Macro + FinBERT

- [ ] Select free V1 news provider
- [ ] Implement news ingestion
- [ ] Implement macro ingestion
- [ ] Enforce publication/availability timestamps
- [ ] Run FinBERT
- [ ] Aggregate sentiment into time-aware features

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
Implement
  ↓
Test
  ↓
Review
  ↓
Commit
  ↓
Push to main
```

Do not commit API keys, client secrets, access tokens, TOTP secrets, or other credentials.

## Immediate Next Action

**Create/configure the Upstox developer application and implement the authentication flow.**

The first success milestone is:

> Python authenticates successfully and retrieves real NIFTY market data from Upstox.
