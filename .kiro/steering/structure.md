---
inclusion: always
---

# Project Structure & Architecture Patterns

## Directory Structure

When creating new files or organizing code, follow this modular structure:

```
src/
├── main.py                    # Entry point with async main loop
├── dashboard.py               # Streamlit dashboard
├── data/                      # Data ingestion (async clients)
│   ├── base.py               # Abstract DataClient interface
│   ├── weather.py            # Weather API client
│   ├── air_quality.py        # Air quality client
│   ├── flights.py            # Flight data client
│   └── cache.py              # Caching layer
├── signals/                   # Signal processing
│   ├── features.py           # Feature engineering (Numba-optimized)
│   ├── kalman.py             # Kalman Filter implementation
│   ├── generator.py          # Signal generation logic
│   └── combiner.py           # Signal aggregation
├── strategy/                  # Trading strategy
│   ├── regime.py             # Regime detection (HMM)
│   ├── adaptive.py           # Adaptive strategy logic
│   ├── position_sizer.py     # Position sizing
│   └── microstructure.py     # Order book imbalance
├── risk/                      # Risk management
│   ├── limiter.py            # Position limits
│   ├── drawdown.py           # Drawdown monitoring
│   └── safe_mode.py          # Emergency shutdown
├── exchange/                  # Exchange interaction
│   ├── client.py             # WebSocket client
│   ├── orders.py             # Order management
│   └── positions.py          # Position tracking
├── monitoring/                # Observability
│   ├── logger.py             # Structured logging
│   ├── metrics.py            # Performance metrics
│   └── reporter.py           # Reporting
├── backtest/                  # Backtesting
│   ├── engine.py             # Backtest engine (Polars)
│   ├── simulator.py          # Order simulation
│   └── analyzer.py           # Performance analysis
├── visualization/             # Charts & dashboards
│   ├── streamlit_app.py      # Dashboard components
│   ├── charts.py             # Chart generation
│   └── presentation.py       # Presentation materials
└── utils/                     # Shared utilities
    ├── config.py             # Configuration loader
    ├── types.py              # Type definitions (Pydantic)
    └── helpers.py            # Helper functions

data/                          # Data storage
├── raw/                      # Raw API responses
├── processed/                # Processed features (Parquet)
├── historical/               # Historical market data
└── cache/                    # Cached data

tests/                         # Tests
├── unit/                     # Unit tests
├── property/                 # Property-based tests (Hypothesis)
└── integration/              # Integration tests

docs/                          # Documentation
├── presentation/             # Presentation materials
└── diagrams/                 # Architecture diagrams
```

## Architecture Principles

### Async-First Design
- Use `asyncio` for all I/O operations (API calls, WebSocket, file I/O)
- Implement concurrent data fetching from multiple sources
- Non-blocking order submission and execution
- Example pattern:
```python
async def fetch_all_data():
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_weather(session),
            fetch_air_quality(session),
            fetch_flights(session)
        ]
        return await asyncio.gather(*tasks)
```

### Performance Optimization
- Use Polars for data processing (prefer over Pandas)
- Apply Numba `@jit` decorator to hot loops and feature calculations
- Vectorize operations with NumPy where possible
- Store processed data in Parquet format
- Target: < 100ms total latency (data → signal → order)

### Separation of Concerns
- Each module has single responsibility
- Clear interfaces between layers (data → signals → strategy → risk → exchange)
- Abstract base classes for extensibility (e.g., `DataClient`, `SignalGenerator`)
- Dependency injection for testability

### Type Safety
- Use Pydantic models for data validation and serialization
- Full type hints on all functions and methods
- Run mypy for type checking

## Naming Conventions

- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

## Import Organization

Always organize imports in this order with blank lines between groups:

```python
# 1. Standard library
import asyncio
from typing import Dict, List, Optional

# 2. Third-party packages
import numpy as np
import polars as pl
from numba import jit

# 3. Local imports
from src.signals.features import FeatureEngineer
from src.utils.types import Signal, MarketData
```

## Configuration Pattern

Use YAML for configuration with environment variable substitution:

```yaml
api_keys:
  openweather: ${OPENWEATHER_API_KEY}
  
exchange:
  url: wss://imc-exchange.com
  timeout: 5000
  
strategy:
  signal_threshold: 0.3
  position_limit: 0.2
```

Load with `src/utils/config.py` that handles env var expansion.

## Data Flow Architecture

Follow this pipeline pattern:

```
External APIs → Data Clients (async) → Cache → Feature Engineer (Numba)
                                                        ↓
                                                 Kalman Filter
                                                        ↓
                                                Signal Generator
                                                        ↓
                                          Regime Detector (HMM)
                                                        ↓
                                            Adaptive Strategy + OBI
                                                        ↓
                                              Position Sizer
                                                        ↓
                                              Risk Manager
                                                        ↓
                                            Order Manager (async)
                                                        ↓
                                              Exchange (WebSocket)
```

Each stage should be independently testable and have clear input/output contracts.

## Code Documentation

Every module should include:
- Module-level docstring explaining purpose
- Function/method docstrings with type hints
- Performance characteristics for critical paths
- Usage examples for complex APIs

Example:
```python
async def compute_signal(data: MarketData) -> Signal:
    """
    Compute trading signal from market data using Kalman filtering.
    
    Args:
        data: Market data with OHLCV and order book
        
    Returns:
        Signal with direction, confidence, and metadata
        
    Performance: ~10ms for typical input
    """
    pass
```

## Error Handling

- Use specific exceptions, not bare `except:`
- Log errors with context using loguru
- Implement graceful degradation (e.g., fallback to cached data)
- Risk management should trigger safe mode on critical errors

## Testing Strategy

- Unit tests for pure functions (signals, features, risk calculations)
- Property-based tests with Hypothesis for invariants
- Integration tests for full pipeline
- Mock external APIs in tests
- Target: > 80% coverage on critical paths

## File Creation Guidelines

When creating new files:
1. Place in appropriate module directory based on responsibility
2. Include `__init__.py` in new packages
3. Add module docstring at top
4. Follow import organization pattern
5. Use type hints throughout
6. Add corresponding test file in `tests/` with same structure
