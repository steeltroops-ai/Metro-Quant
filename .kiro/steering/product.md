---
inclusion: always
---

# Product Context: IMC Munich ETF Trading Challenge

## Project Type
Hackathon submission for IMC Munich ETF Challenge at HackaTUM (November 2025). Time-constrained development (48 hours) with live judging and demonstration.

## Core Objective
Build an adaptive trading bot for IMC's simulated exchange that trades multiple asset types, with emphasis on the Munich ETF - a synthetic instrument whose value correlates with real-time Munich city data (weather, air quality, flight activity).

## What Judges Evaluate (Priority Order)
1. **Novel signal discovery** - Creative use of Munich city data to generate trading signals
2. **Real-time adaptation** - Strategy learns and adjusts to market microstructure during live trading
3. **Engineering quality** - Clean architecture, proper async patterns, performance optimization
4. **Cross-market consistency** - Strategy performs across different market types (not just Munich ETF)
5. **Demonstrable edge** - Clear explanation of why the approach works, not just PnL numbers

## Product Philosophy
- **Show, don't just tell**: Live Streamlit dashboard demonstrating real-time decision-making
- **Explainability over black-box**: Judges must understand the strategy logic
- **Robustness over overfitting**: Strategy should adapt to regime changes, not memorize patterns
- **Speed matters**: Sub-100ms latency from data ingestion to order execution

## Key Product Features (Must-Haves)
1. **Multi-source data ingestion**: Weather, air quality, flights, order book data
2. **Real-time signal generation**: Kalman filtering, correlation analysis, regime detection
3. **Adaptive execution**: Position sizing based on signal confidence and market regime
4. **Live monitoring dashboard**: Visual proof of strategy thinking for judges
5. **Risk management**: Drawdown limits, position limits, emergency shutdown

## Competitive Advantages to Emphasize
- **Kalman Filter smoothing**: Reduces noise in Munich data signals (vs lagging moving averages)
- **Order Book Imbalance (OBI)**: Microstructure alpha from bid/ask depth analysis
- **Regime detection**: HMM-based market state classification with adaptive parameters
- **Numba JIT optimization**: Near-C performance for feature engineering loops
- **Async architecture**: Concurrent data fetching, non-blocking order execution

## Development Constraints
- **Time limit**: 48 hours total (prioritize core features over polish)
- **Live demo**: Strategy must run reliably during judging session
- **No external data**: Only approved APIs (OpenWeatherMap, OpenSky, etc.)
- **Simulated exchange**: Must handle exchange-specific quirks and latency

## Success Metrics (What to Optimize For)
- **Sharpe ratio** > 1.5 (risk-adjusted returns)
- **Max drawdown** < 25% (risk management)
- **Signal-to-noise ratio**: Clear correlation between Munich data and trades
- **Adaptation speed**: How quickly strategy adjusts to regime changes
- **Judge comprehension**: Can judges understand the strategy in 10 minutes?

## Anti-Patterns to Avoid
- Over-optimization on historical data (judges will test on unseen periods)
- Black-box ML models without interpretability
- Ignoring risk management (one bad trade can ruin demo)
- Complex strategies that can't be explained clearly
- Slow execution (missing opportunities due to latency)

## Presentation Requirements
- Architecture diagram showing data flow
- Live dashboard with real-time PnL, signals, and regime indicators
- Signal discovery charts proving Munich data correlation
- Clear explanation of edge and why it works
- Backtest results showing consistency across regimes
