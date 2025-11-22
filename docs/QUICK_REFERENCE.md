# 🚀 IMC Trading Bot - Quick Reference Cheat Sheet

## Setup (5 Minutes)

```bash
# Linux/Mac
chmod +x setup.sh && ./setup.sh
source venv/bin/activate

# Windows
setup.bat
venv\Scripts\activate.bat

# Edit API keys
nano .env
```

## Essential Commands

```bash
# Development
jupyter notebook notebooks/          # Data exploration
streamlit run src/dashboard.py      # Live dashboard
python src/main.py --mode live       # Run live bot
python src/backtest/engine.py        # Run backtest

# Testing
pytest tests/ -v                     # All tests
pytest tests/property/ -v            # Property tests only
pytest --cov=src --cov-report=html   # With coverage

# Code quality
black src/                           # Format code
ruff src/                            # Lint code
mypy src/                            # Type check
```

## Turbo Stack Quick Reference

### 1. Async Everything

```python
import asyncio
import aiohttp

async def fetch_all_data():
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_weather(session),
            fetch_air_quality(session),
            fetch_flights(session)
        ]
        return await asyncio.gather(*tasks)

# Run async function
data = asyncio.run(fetch_all_data())
```

### 2. Polars (10x Faster)

```python
import polars as pl

# Read data (lazy)
df = pl.scan_parquet("data/market_data.parquet")

# Process (vectorized)
result = (
    df
    .filter(pl.col("timestamp") > start_time)
    .with_columns([
        (pl.col("close") - pl.col("open")).alias("return"),
        pl.col("volume").rolling_mean(20).alias("vol_ma")
    ])
    .collect()  # Execute
)

# 10x faster than Pandas equivalent
```

### 3. Numba JIT (100x Speedup)

```python
from numba import jit
import numpy as np

@jit(nopython=True)
def calculate_momentum(prices, window=20):
    """Compiles to machine code"""
    n = len(prices)
    momentum = np.zeros(n)
    for i in range(window, n):
        momentum[i] = (prices[i] - prices[i-window]) / prices[i-window]
    return momentum

# First call: ~100ms (compilation)
# Subsequent: ~1ms (100x faster)
```

### 4. Kalman Filter (Zero Lag)

```python
from pykalman import KalmanFilter

kf = KalmanFilter(
    transition_matrices=[1],
    observation_matrices=[1],
    initial_state_mean=0,
    initial_state_covariance=1,
    observation_covariance=1,
    transition_covariance=0.01
)

# Filter noisy signal
filtered, _ = kf.filter(noisy_signal)
# No lag like moving averages!
```

### 5. Order Book Imbalance (OBI)

```python
def calculate_obi(order_book):
    """Predicts price 1s ahead"""
    bid_vol = sum(b['size'] for b in order_book['bids'][:5])
    ask_vol = sum(a['size'] for a in order_book['asks'][:5])
    return (bid_vol - ask_vol) / (bid_vol + ask_vol)

# OBI > 0.3: Buy pressure (price will rise)
# OBI < -0.3: Sell pressure (price will fall)
```

### 6. HMM Regime Detection

```python
from hmmlearn import hmm

# Train on historical data
model = hmm.GaussianHMM(n_components=3)
model.fit(historical_features)

# Predict current regime
regime = model.predict(current_features)[-1]
confidence = model.predict_proba(current_features)[-1]

# Regimes: 0=trending, 1=mean-reverting, 2=high-vol
```

### 7. Streamlit Dashboard

```python
import streamlit as st
import plotly.graph_objects as go

st.title("🚀 IMC Trading Bot")

# Real-time PnL
fig = go.Figure()
fig.add_trace(go.Scatter(x=times, y=pnl, name='PnL'))
st.plotly_chart(fig)

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("PnL", f"${pnl:.2f}", delta=pnl_change)
col2.metric("Regime", regime, delta=confidence)
col3.metric("OBI", f"{obi:.3f}", delta=obi_change)

# Run: streamlit run src/dashboard.py
```

## Data Sources (Free APIs)

### Weather (OpenWeatherMap)
```python
url = f"https://api.openweathermap.org/data/2.5/weather"
params = {"q": "Munich", "appid": API_KEY}
response = await session.get(url, params=params)
```

### Air Quality (OpenWeatherMap)
```python
url = f"http://api.openweathermap.org/data/2.5/air_pollution"
params = {"lat": 48.1351, "lon": 11.5820, "appid": API_KEY}
response = await session.get(url, params=params)
```

### Flights (OpenSky Network - No Key!)
```python
url = "https://opensky-network.org/api/states/all"
params = {
    "lamin": 47.9, "lomin": 11.3,
    "lamax": 48.3, "lomax": 11.8
}
response = await session.get(url, params=params)
```

## Performance Optimization Checklist

- [ ] Use `asyncio` for all I/O operations
- [ ] Use Polars instead of Pandas
- [ ] Add `@jit` to hot loops with Numba
- [ ] Vectorize with NumPy (no Python loops)
- [ ] Use Parquet format for data storage
- [ ] Cache expensive computations
- [ ] Profile with `pytest-benchmark`

## Common Patterns

### Async Data Fetching
```python
async def fetch_munich_data():
    async with aiohttp.ClientSession() as session:
        weather, air, flights = await asyncio.gather(
            fetch_weather(session),
            fetch_air_quality(session),
            fetch_flights(session)
        )
    return {"weather": weather, "air": air, "flights": flights}
```

### Feature Engineering (Numba)
```python
@jit(nopython=True)
def engineer_features(prices, volumes):
    returns = np.diff(prices) / prices[:-1]
    volatility = np.std(returns[-20:])
    momentum = (prices[-1] - prices[-20]) / prices[-20]
    return returns, volatility, momentum
```

### Signal Combination
```python
def combine_signals(signals, regime, weights):
    """Weighted signal combination"""
    regime_weights = weights[regime]
    combined = sum(s * w for s, w in zip(signals, regime_weights))
    return np.clip(combined, -1.0, 1.0)
```

### Risk Management
```python
def calculate_position_size(signal, confidence, capital, regime):
    """Confidence-based position sizing"""
    base_size = 0.10  # 10% base
    regime_multiplier = {
        "trending": 1.0,
        "mean_reverting": 0.8,
        "high_volatility": 0.5
    }[regime]
    
    size = base_size * abs(signal) * confidence * regime_multiplier
    return min(size, 0.20)  # Max 20% per position
```

## Debugging Tips

### Check Async Issues
```python
# Enable asyncio debug mode
import asyncio
asyncio.run(main(), debug=True)
```

### Profile Performance
```python
# Time critical sections
import time
start = time.perf_counter()
result = expensive_function()
print(f"Took {time.perf_counter() - start:.3f}s")
```

### Numba Debugging
```python
# Disable JIT for debugging
from numba import jit

@jit(nopython=True, debug=True)
def my_function(x):
    # Set breakpoint here
    return x * 2
```

## Presentation Checklist

- [ ] Streamlit dashboard running
- [ ] Signal correlation heatmap ready
- [ ] Regime timeline visualization
- [ ] Architecture diagram prepared
- [ ] Backtest results documented
- [ ] Code is clean and commented
- [ ] Demo script practiced

## Key Metrics to Show Judges

1. **Sharpe Ratio**: > 1.5 (risk-adjusted returns)
2. **Max Drawdown**: < 20% (risk management)
3. **Win Rate**: > 55% (signal quality)
4. **Latency**: < 100ms (data → order)
5. **Consistency**: Positive across all regimes

## Emergency Fixes

### Async Not Working
```python
# Use asyncio.run() not loop.run_until_complete()
asyncio.run(main())
```

### Numba Compilation Error
```python
# Remove @jit temporarily
# @jit(nopython=True)
def my_function(x):
    return x * 2
```

### Polars Import Error
```python
# Fallback to Pandas
try:
    import polars as pl
except ImportError:
    import pandas as pd
```

### Streamlit Not Loading
```bash
# Kill existing process
pkill -f streamlit
# Restart
streamlit run src/dashboard.py --server.port 8502
```

## Resources

- **Polars Docs**: https://pola-rs.github.io/polars/
- **Numba Docs**: https://numba.pydata.org/
- **Kalman Filter**: https://pykalman.github.io/
- **Streamlit Docs**: https://docs.streamlit.io/
- **HMM Learn**: https://hmmlearn.readthedocs.io/

## Final Checklist Before Demo

- [ ] All tests passing
- [ ] Dashboard launches without errors
- [ ] API keys configured
- [ ] Backtest results look good
- [ ] Code is formatted (black)
- [ ] README is updated
- [ ] Presentation slides ready
- [ ] Demo script practiced

Good luck! 🚀
