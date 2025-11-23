---
inclusion: always
---

# Technology Stack & Implementation Patterns

## Language & Core Requirements

**Python 3.10+** with full type hints. All async I/O operations are mandatory for performance.

## Critical Libraries & Usage Patterns

### Async Operations (MANDATORY)
```python
# Use asyncio for all I/O - never blocking calls
import asyncio
import aiohttp
from websockets import connect

# Pattern: Concurrent data fetching
async def fetch_all_data():
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_weather(session),
            fetch_air_quality(session),
            fetch_flights(session)
        ]
        return await asyncio.gather(*tasks)
```

### Data Processing Stack
- **Polars**: Primary choice for data processing (10x faster than Pandas)
- **NumPy**: Vectorized operations, use for all array math
- **Numba**: Apply `@jit(nopython=True)` to hot loops and feature calculations

```python
from numba import jit
import numpy as np

@jit(nopython=True)
def compute_returns(prices: np.ndarray) -> np.ndarray:
    """JIT-compiled for C-level performance."""
    return np.diff(prices) / prices[:-1]
```

### Signal Processing
- **pykalman** or **filterpy**: Kalman Filter for real-time state estimation
- **scipy**: Statistical functions, optimization
- **statsmodels**: Time-series analysis, cointegration

```python
from pykalman import KalmanFilter

# Pattern: Noise reduction in signals
kf = KalmanFilter(transition_matrices=[1], observation_matrices=[1])
filtered_signal, _ = kf.filter(noisy_observations)
```

### Data Validation & Types
```python
from pydantic import BaseModel, Field
from typing import Optional

class Signal(BaseModel):
    """Use Pydantic for all data models."""
    direction: int = Field(..., ge=-1, le=1)  # -1, 0, 1
    confidence: float = Field(..., ge=0.0, le=1.0)
    metadata: Optional[dict] = None
```

### Testing
- **Hypothesis**: Property-based testing for invariants
- **pytest**: Unit tests
- **pytest-asyncio**: Async test support

```python
from hypothesis import given, strategies as st

@given(st.lists(st.floats(min_value=0, max_value=1000), min_size=10))
def test_signal_properties(prices):
    """Property: Signal confidence must be in [0, 1]."""
    signal = generate_signal(prices)
    assert 0 <= signal.confidence <= 1
```

## Performance Optimization Rules

### Latency Targets (ENFORCE)
- Total pipeline: < 100ms (data → signal → order)
- Data ingestion: < 50ms (use async concurrent fetching)
- Feature engineering: < 20ms (use Numba JIT)
- Signal generation: < 10ms (vectorize with NumPy)
- Order submission: < 20ms (async WebSocket)

### Optimization Checklist
1. **Use Polars over Pandas** for data processing
2. **Apply `@jit(nopython=True)`** to loops and feature calculations
3. **Vectorize with NumPy** - avoid Python loops on arrays
4. **Async all I/O** - never use blocking requests/file operations
5. **Cache expensive computations** - especially API calls

```python
# BAD: Blocking I/O
import requests
data = requests.get(url).json()  # Blocks event loop

# GOOD: Async I/O
async with aiohttp.ClientSession() as session:
    async with session.get(url) as resp:
        data = await resp.json()
```

## Advanced Techniques (Competitive Edge)

### Order Book Imbalance (OBI)
```python
def order_book_imbalance(bids: list, asks: list, depth: int = 5) -> float:
    """
    Microstructure signal: predicts short-term price movement.
    Returns value in [-1, 1] indicating buy/sell pressure.
    """
    bid_vol = sum(b['size'] for b in bids[:depth])
    ask_vol = sum(a['size'] for a in asks[:depth])
    return (bid_vol - ask_vol) / (bid_vol + ask_vol + 1e-10)
```

### Regime Detection
- Use Hidden Markov Models (HMM) for probabilistic regime classification
- Implement change point detection for regime transitions
- Calculate Hurst exponent to measure mean-reversion vs trending

## Error Handling Patterns

```python
from loguru import logger

# Pattern: Graceful degradation
try:
    data = await fetch_external_data()
except aiohttp.ClientError as e:
    logger.warning(f"API failed, using cached data: {e}")
    data = load_from_cache()
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise  # Re-raise critical errors
```

## Configuration Management

```python
# Use config.yaml with environment variable substitution
# Pattern: ${VAR_NAME:default_value}

# config.yaml:
# api_keys:
#   openweather: ${OPENWEATHER_API_KEY}
# exchange:
#   url: ${EXCHANGE_URL:wss://default-url.com}

# Load via src/utils/config.py
from src.utils.config import load_config
config = load_config()
```

## Common Anti-Patterns to Avoid

1. **Blocking I/O in async functions** - Use aiohttp, not requests
2. **Missing type hints** - All functions must have full type annotations
3. **Hardcoded values** - Use config.yaml for all parameters
4. **Bare except clauses** - Always catch specific exceptions
5. **Python loops on NumPy arrays** - Vectorize or use Numba
6. **Missing error handling in async code** - Wrap in try/except with logging

## Key Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run live trading bot
python src/main.py --mode live

# Run backtest
python src/backtest.py --data data/historical.parquet

# Launch Streamlit dashboard
streamlit run src/visualization/dashboard.py

# Run tests with coverage
pytest tests/ -v --cov=src

# Type checking
mypy src/
```

## Import Organization

```python
# 1. Standard library (alphabetical)
import asyncio
from typing import Dict, List, Optional

# 2. Third-party packages (alphabetical)
import numpy as np
import polars as pl
from numba import jit
from pydantic import BaseModel

# 3. Local imports (alphabetical)
from src.data.base import DataClient
from src.signals.features import FeatureEngineer
from src.utils.types import Signal, MarketData
```
