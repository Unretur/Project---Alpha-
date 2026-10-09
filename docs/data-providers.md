# Project Alpha — Data Provider Specification

## 1. Purpose

This document defines the external data providers used by Project Alpha.

Project Alpha requires multiple data sources because no single provider is expected to reliably provide all required market, derivatives, news, macroeconomic, and global-market information.

Each provider must be evaluated for:

- Historical data availability
- Real-time data availability
- Timestamp precision
- Data completeness
- API reliability
- Rate limits
- Cost
- Licensing/usage restrictions
- Ability to support reproducible research
- Compatibility with the historical and live Alpha pipelines

The provider architecture must preserve the information-availability rule defined in `research-specification.md`.

---

# 2. Data Provider Architecture

Project Alpha will use specialized providers for different categories of information.

```text
                         PROJECT ALPHA
                              |
        ------------------------------------------------
        |              |              |               |
        v              v              v               v
    Market/Data      News          Macro           Global
        |              |              |               |
    Upstox (V1)  Upstox prototype  FRED / RBI*       TBD
        |              |              |               |
        ----------------- Data Layer -----------------
                              |
                              v
                     Timestamp Alignment
                              |
                              v
                      Feature Engineering
                              |
                              v
                           FinBERT
                              |
                              v
                       Prediction Model

# 3. Current Implementation Status

| Data category | Current integration | Scope / limitation |
| --- | --- | --- |
| NIFTY 50 candles | Upstox V3 | 5-minute historical downloader is implemented. Confirm candle coverage and trading-calendar validity before training. |
| Options contracts | Upstox V2 | Contract lookup and ATM pair selection are implemented; weekly expiry selection is guarded by contract metadata. |
| News | Upstox News API | Prototype currently queries Reliance Industries only; it is not a market-wide NIFTY news feed. |
| Financial sentiment | ProsusAI/FinBERT | Produces positive, neutral, and negative probabilities locally. |
| Macro | FRED | VIXCLS, DGS10, DFF, and DEXINUS downloaders are implemented. Observation date is delayed to the next UTC midnight as a provisional leakage guard, not exact release metadata. |
| Indian macro / FX | RBI parsed CSVs | Automatically included when parsed CSVs exist under `data/raw/rbi/`. The effective/observation dates are conservatively delayed one UTC day; this is not a verified historical release timestamp. |
| Global market data | Not implemented | Provider and instruments remain undecided. |
| Alpha Vantage | Client only | The client is available, but no Alpha Vantage data series is currently integrated into the training pipeline. |

`*` FRED and RBI timing guards are provisional proxies. Before making validated historical-backtest claims, replace them with point-in-time release/vintage data where required and verify the timestamps against source documentation.
