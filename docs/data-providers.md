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
    Angel One       TBD          FRED/RBI          TBD
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
