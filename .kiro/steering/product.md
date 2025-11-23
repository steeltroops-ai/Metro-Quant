---
inclusion: always
---

# Product Context: IMC Munich ETF Trading Challenge

## Project Overview

**Type**: 48-hour hackathon submission for IMC Munich ETF Challenge at HackaTUM (November 2025)

**Core Mission**: Build an adaptive trading bot for IMC's simulated exchange that discovers alpha in Munich city data (weather, air quality, flights) to trade the Munich ETF and other asset types.

**Critical Constraint**: Live judging with real-time demonstration - the bot must work flawlessly during the demo.

## Decision-Making Framework

When implementing features or making architectural choices, prioritize in this order:

1. **Reliability** - Will it work during the live demo?
2. **Explainability** - Can judges understand it in 5 minutes?
3. **Signal novelty** - Does it use Munich data creatively?
4. **Performance** - Is it fast enough (< 100ms latency)?
5. **Robustness** - Does it handle regime changes?

## What Judges Care About (Ranked)

1. **Novel signal discovery** - Creative correlation between Munich data and ETF price movements
2. **Real-time adaptation** - Observable strategy adjustments during live trading
3. **Engineering quality** - Clean async architecture, proper error handling, performance optimization
4. **Cross-market applicability** - Strategy works on multiple asset types, not just Munich ETF
5. **Demonstrable edge** - Clear explanation of why the approach generates alpha

## Core Product Requirements

### Must-Have Features
- Multi-source async data ingestion (weather, air quality, flights, order book)
- Real-time signal generation with Kalman filtering for noise reduction
- Adaptive position sizing based on signal confidence and market regime
- Live Streamlit dashboard showing decision-making process
- Robust risk management (drawdown limits, position limits, emergency shutdown)

### Nice-to-Have Features
- Order Book Imbalance (OBI) for microstructure alpha
- Hidden Markov Model (HMM) regime detection
- Historical backtest visualization
- Signal correlation heatmaps

### Out of Scope
- Complex ML models without interpretability
- Over-optimized strategies that memorize historical patterns
- Features that can't be explained to judges quickly

## Key Differentiators

When implementing or explaining features, emphasize these competitive advantages:

- **Kalman Filter smoothing**: Real-time state estimation vs lagging moving averages
- **Async-first architecture**: Concurrent data fetching, non-blocking execution
- **Regime-aware adaptation**: Strategy parameters adjust to market conditions
- **Microstructure signals**: Order book imbalance for short-term edge
- **Numba JIT optimization**: Near-C performance for critical paths

## Performance Targets

All code should aim for these benchmarks:

- **Total latency**: < 100ms (data ingestion → signal → order)
- **Data ingestion**: < 50ms (async concurrent fetching)
- **Feature engineering**: < 20ms (Numba JIT-optimized)
- **Signal generation**: < 10ms (vectorized NumPy)
- **Order submission**: < 20ms (async WebSocket)

## Risk Management Philosophy

**Non-negotiable**: Risk management must prevent catastrophic losses during live demo.

- Max drawdown limit: 25% (hard stop)
- Position limits: 20% of portfolio per asset
- Emergency shutdown on critical errors
- Graceful degradation when data sources fail

## Code Quality Standards

### Prioritize for Hackathon Context
- **Reliability over cleverness**: Simple, working code beats complex, buggy code
- **Observability**: Log all decisions for debugging and demonstration
- **Type safety**: Use type hints and Pydantic models to catch errors early
- **Async correctness**: Proper error handling in async code (no silent failures)

### Acceptable Trade-offs
- Less test coverage on non-critical paths (focus on risk management and signal generation)
- Simpler algorithms if they're more explainable
- Some code duplication if it improves clarity

### Unacceptable Shortcuts
- Skipping error handling in async code
- No risk limits or position sizing
- Hardcoded values that should be configurable
- Blocking I/O in async functions

## Presentation Strategy

When implementing features, consider how they'll be demonstrated:

- **Live dashboard**: Every major decision should be visible in real-time
- **Signal visualization**: Charts showing Munich data → signal → trade flow
- **Regime indicators**: Visual markers when strategy adapts
- **PnL tracking**: Real-time performance metrics

## Common Pitfalls to Avoid

- **Over-optimization**: Don't fit to historical data; judges will test on unseen periods
- **Black-box models**: Avoid unexplainable ML models
- **Ignoring latency**: Slow execution misses opportunities
- **Complex explanations**: If you can't explain it in 5 minutes, simplify it
- **Single point of failure**: One bad trade or data source failure shouldn't crash the bot

## Success Criteria

The project succeeds if:

1. Bot runs reliably during live demo without crashes
2. Judges understand the strategy and why it works
3. Clear correlation between Munich data signals and trades
4. Sharpe ratio > 1.5 with max drawdown < 25%
5. Strategy adapts observably to regime changes

## Development Priorities by Phase

### Phase 1: Foundation (Hours 0-12)
- Async data clients for all sources
- Basic signal generation with Kalman filtering
- Risk management framework
- Simple execution engine

### Phase 2: Alpha Discovery (Hours 12-24)
- Correlation analysis between Munich data and ETF
- Feature engineering with Numba optimization
- Regime detection implementation
- Adaptive position sizing

### Phase 3: Polish & Demo (Hours 24-36)
- Streamlit dashboard with live visualization
- Backtest validation
- Error handling and graceful degradation
- Documentation and architecture diagrams

### Phase 4: Presentation (Hours 36-48)
- Practice demo and explanation
- Generate presentation charts
- Prepare for judge questions
- Final testing and bug fixes

## Configuration Philosophy

All strategy parameters should be:
- Configurable via `config.yaml` (not hardcoded)
- Documented with rationale
- Testable with different values
- Observable in the dashboard

## When to Ask for Clarification

If implementing a feature that:
- Adds > 50ms latency to critical path
- Requires external data source not in approved list
- Can't be explained to judges in < 5 minutes
- Significantly increases complexity without clear benefit

Then discuss trade-offs before proceeding.
