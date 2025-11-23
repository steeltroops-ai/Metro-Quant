---
inclusion: always
---

# Project Structure & Architecture

## Module Organization

Place files in the appropriate module based on responsibility:

- `src/data/` - Async data clients (inherit from `DataClient` base class)
- `src/signals/` - Feature engineering (Numba-optimized) and signal generation
- `src/strategy/` - Trading logic, regime detection, position sizing
- `src/risk/` - Risk limits, drawdown monitoring, emergency shutdown
- `src/exchange/` - WebSocket client, order/position management
- `src/monitoring/` - Logging, metrics, reporting
- `src/backtest/` - Backtesting engine (Polars-based)
- `src/visualization/` - Streamlit dashboard and charts
- `src/utils/` - Config loader, type definitions (Pydantic), helpers

## Async-First Architecture

**All I/O operations MUST be async** (API calls, WebSocket, file operations):

```python
# Concurrent data fetching pattern
async def fetch_all_data():
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_weather(session),
            fetch_air_quality(session),
            fetch_flights(session)
        ]
        return await asyncio.gather(*tasks)
```

**Critical**: Never use blocking I/O in async functions. Use `aiohttp` for HTTP, `aiofiles` for file I/O.

## Data Flow Pipeline

Follow this strict pipeline order:

```
External APIs → Data Clients (async) → Cache → Feature Engineer (Numba)
    ↓
Kalman Filter → Signal Generator → Regime Detector
    ↓
Adaptive Strategy + OBI → Position Sizer → Risk Manager
    ↓
Order Manager (async) → Exchange (WebSocket)
```

Each stage must:
- Have clear input/output contracts (Pydantic models)
- Be independently testable
- Handle errors gracefully with fallback behavior

## Performance Requirements

**Target latency: < 100ms** (data → signal → order)

- Data ingestion: < 50ms (async concurrent)
- Feature engineering: < 20ms (use `@jit` from Numba)
- Signal generation: < 10ms (vectorized NumPy)
- Order submission: < 20ms (async WebSocket)

**Optimization rules**:
- Use Polars over Pandas for data processing
- Apply `@jit(nopython=True)` to hot loops and feature calculations
- Vectorize with NumPy where possible
- Store processed data in Parquet format

## Code Style

**Naming conventions**:
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions/methods: `snake_case()`
- Constants: `UPPER_SNAKE_CASE`
- Private members: `_leading_underscore`

**Import order** (with blank lines between groups):
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

## Type Safety

**Required**:
- Full type hints on all functions and methods
- Pydantic models for data validation and serialization
- Use `Optional[T]` for nullable values, not `T | None`

```python
from pydantic import BaseModel
from typing import Optional

class Signal(BaseModel):
    direction: int  # -1, 0, 1
    confidence: float  # 0.0 to 1.0
    metadata: Optional[dict] = None
```

## Configuration

Use `config.yaml` with environment variable substitution:

```yaml
api_keys:
  openweather: ${OPENWEATHER_API_KEY}
  
exchange:
  url: ${EXCHANGE_URL:wss://imc-exchange.com}  # Default value after colon
  timeout: 5000
```

Load via `src/utils/config.py` which handles `${VAR}` expansion.

**Never hardcode** strategy parameters, API keys, or URLs.

## Error Handling

**Required patterns**:
- Use specific exceptions, never bare `except:`
- Log errors with context using loguru: `logger.error(f"Failed to fetch {source}", exc_info=True)`
- Implement graceful degradation (fallback to cached data)
- Risk manager triggers safe mode on critical errors

```python
try:
    data = await fetch_data()
except aiohttp.ClientError as e:
    logger.warning(f"API failed, using cache: {e}")
    data = load_from_cache()
```

## Documentation

**Every module must include**:
- Module-level docstring explaining purpose
- Function docstrings with Args/Returns/Performance notes
- Type hints (not just in docstrings)

```python
async def compute_signal(data: MarketData) -> Signal:
    """
    Compute trading signal using Kalman filtering.
    
    Args:
        data: Market data with OHLCV and order book
        
    Returns:
        Signal with direction (-1/0/1), confidence (0-1), metadata
        
    Performance: ~10ms for typical input
    """
```

## Testing

**Test organization**:
- `tests/unit/` - Pure functions (signals, features, risk)
- `tests/property/` - Hypothesis property-based tests for invariants
- `tests/integration/` - Full pipeline tests

**Rules**:
- Mock external APIs in tests (use `aioresponses` for aiohttp)
- Test file structure mirrors `src/` structure
- Target > 80% coverage on critical paths (risk, signals, strategy)

## File Creation Checklist

When creating new files:
1. ✓ Place in correct module directory
2. ✓ Add `__init__.py` if creating new package
3. ✓ Module docstring at top
4. ✓ Follow import organization (stdlib → third-party → local)
5. ✓ Full type hints on all functions
6. ✓ Create corresponding test file in `tests/`

## Common Patterns

**Abstract base class for extensibility**:
```python
from abc import ABC, abstractmethod

class DataClient(ABC):
    @abstractmethod
    async def fetch(self) -> dict:
        """Fetch data from source."""
        pass
```

**Dependency injection for testability**:
```python
class Strategy:
    def __init__(self, signal_generator: SignalGenerator, risk_manager: RiskManager):
        self.signal_gen = signal_generator
        self.risk_mgr = risk_manager
```

**Numba optimization for hot paths**:
```python
from numba import jit

@jit(nopython=True)
def compute_features(prices: np.ndarray) -> np.ndarray:
    """Compute features at C speed."""
    return np.diff(prices) / prices[:-1]
```
