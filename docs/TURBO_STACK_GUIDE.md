# 🚀 IMC Trading Bot - Turbo Stack Implementation Guide

## Why This Stack Wins

While IMC uses C++ for nanosecond execution in production, **Python 3.10+ is the superior hackathon choice** because:
1. Munich signal analysis requires data science libraries
2. Rapid development (48 hours is tight)
3. Rich ecosystem for quant finance
4. Judges understand Python better than C++

## The Turbo Stack (Competitive Edge)

### 1. Async Everything (Non-Negotiable)

**Why**: Responsive bot that doesn't block on I/O
**Impact**: 10x throughput vs synchronous code

```python
import asyncio
import aiohttp

async def fetch_all_data():
    async with aiohttp.ClientSession() as session:
        # Fetch weather, air quality, flights CONCURRENTLY
        tasks = [
            fetch_weather(session),
            fetch_air_quality(session),
            fetch_flights(session)
        ]
        results = await asyncio.gather(*tasks)
    return results

# This takes 100ms instead of 300ms (sequential)
```

### 2. Polars > Pandas (10x Faster)

**Why**: Written in Rust, uses all CPU cores, lazy evaluation
**Impact**: Process 1M rows in 100ms vs 1s with Pandas

```python
import polars as pl

# Lazy evaluation - only computes when needed
df = (
    pl.scan_parquet("data/market_data.parquet")
    .filter(pl.col("timestamp") > start_time)
    .with_columns([
        (pl.col("close") - pl.col("open")).alias("return"),
        pl.col("volume").rolling_mean(20).alias("vol_ma")
    ])
    .collect()  # Execute the query plan
)

# This is 10x faster than Pandas equivalent
```

### 3. Numba JIT (100x Speedup)

**Why**: Compiles Python to machine code
**Impact**: Feature engineering runs at C speed

```python
from numba import jit
import numpy as np

@jit(nopython=True)
def calculate_momentum(prices, window=20):
    """Numba compiles this to machine code"""
    n = len(prices)
    momentum = np.zeros(n)
    for i in range(window, n):
        momentum[i] = (prices[i] - prices[i-window]) / prices[i-window]
    return momentum

# First call: ~100ms (compilation)
# Subsequent calls: ~1ms (100x faster than pure Python)
```

### 4. Kalman Filter (The "Ghost" Algo)

**Why**: Estimates true hidden state instantly (no lag like rolling OLS)
**Impact**: Cleaner signals, faster reaction to regime changes

```python
from pykalman import KalmanFilter

# Initialize Kalman Filter
kf = KalmanFilter(
    transition_matrices=[1],      # State transition
    observation_matrices=[1],     # Observation model
    initial_state_mean=0,
    initial_state_covariance=1,
    observation_covariance=1,     # Measurement noise
    transition_covariance=0.01    # Process noise
)

# Filter noisy price data
noisy_prices = fetch_market_data()
filtered_prices, _ = kf.filter(noisy_prices)

# filtered_prices has NO LAG - it's the "true" price estimate
```

**Use Cases**:
- Signal smoothing (remove noise without lag)
- Trend estimation (better than moving averages)
- Regime detection (detect changes instantly)
- Pairs trading (estimate spread mean)

### 5. Order Book Imbalance (OBI) - Microstructure Alpha

**Why**: Predicts price movement 1 second before it happens
**Impact**: Front-run the market legally

```python
def calculate_obi(order_book):
    """Order Book Imbalance - predicts next price move"""
    # Top 5 levels of bid/ask
    bid_volume = sum(level['size'] for level in order_book['bids'][:5])
    ask_volume = sum(level['size'] for level in order_book['asks'][:5])
    
    # OBI ranges from -1 (sell pressure) to +1 (buy pressure)
    obi = (bid_volume - ask_volume) / (bid_volume + ask_volume)
    
    return obi

# If OBI > 0.3: Price likely to go UP (buy pressure)
# If OBI < -0.3: Price likely to go DOWN (sell pressure)
```

**Why This Works**:
- Large buy orders → bid side heavy → price will rise
- Large sell orders → ask side heavy → price will fall
- You see this BEFORE the price moves

### 6. Streamlit Dashboard (The "Wow" Factor)

**Why**: Judges see your bot thinking in real-time
**Impact**: Instant credibility, shows engineering skill

```python
import streamlit as st
import plotly.graph_objects as go

st.title("🚀 IMC Trading Bot - Live Dashboard")

# Real-time PnL chart
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=timestamps,
    y=pnl_values,
    mode='lines',
    name='PnL',
    line=dict(color='green', width=2)
))
st.plotly_chart(fig)

# Signal correlation heatmap
st.subheader("Munich Signal Correlations")
st.plotly_chart(create_correlation_heatmap(signals))

# Current regime
st.metric("Current Regime", current_regime, delta=regime_confidence)

# Order book imbalance
st.metric("OBI", f"{obi:.3f}", delta=obi_change)
```

**Dashboard Sections**:
1. Real-time PnL curve
2. Signal correlation heatmap
3. Regime timeline (trending/mean-reverting/volatile)
4. Order book imbalance gauge
5. Position sizes and exposure
6. Recent trades with reasoning

## Advanced Techniques

### 7. Hidden Markov Models (HMM) for Regime Detection

**Why**: Probabilistic regime classification (better than simple volatility)
**Impact**: Smoother regime transitions, higher confidence

```python
from hmmlearn import hmm
import numpy as np

# Train HMM on historical returns
returns = calculate_returns(historical_prices)
features = np.column_stack([
    returns,
    rolling_volatility(returns, 20),
    rolling_autocorr(returns, 20)
])

# 3 hidden states: trending, mean-reverting, high-volatility
model = hmm.GaussianHMM(n_components=3, covariance_type="full")
model.fit(features)

# Predict current regime
current_regime = model.predict(current_features)[-1]
regime_probs = model.predict_proba(current_features)[-1]

# regime_probs = [0.1, 0.8, 0.1] → 80% confident in regime 1
```

### 8. Change Point Detection

**Why**: Detect regime changes instantly (not after 20 bars)
**Impact**: Adapt faster than competitors

```python
import ruptures as rpt

# Detect change points in price series
algo = rpt.Pelt(model="rbf").fit(prices)
change_points = algo.predict(pen=10)

# If change point detected in last 5 bars → regime changed
if len(change_points) > 0 and change_points[-1] > len(prices) - 5:
    print("REGIME CHANGE DETECTED!")
    adapt_strategy()
```

### 9. Cointegration for Pairs Trading

**Why**: Find assets that move together (Munich ETF + weather signals)
**Impact**: More robust signals

```python
from statsmodels.tsa.stattools import coint

# Test if Munich ETF is cointegrated with weather index
weather_index = create_weather_index(temp, humidity, pressure)
score, pvalue, _ = coint(munich_etf_prices, weather_index)

if pvalue < 0.05:
    print("Cointegrated! Use pairs trading strategy")
    spread = munich_etf_prices - beta * weather_index
    signal = -spread  # Mean reversion signal
```

## Performance Optimization Checklist

### Data Processing
- [ ] Use Polars instead of Pandas (10x faster)
- [ ] Use Parquet format for data storage (compressed, columnar)
- [ ] Lazy evaluation with `pl.scan_parquet()` (only load what you need)
- [ ] Vectorized operations with NumPy (no Python loops)

### Computation
- [ ] Numba @jit on hot loops (100x speedup)
- [ ] Vectorize with NumPy (SIMD instructions)
- [ ] Cache expensive computations (Kalman Filter state)
- [ ] Use float32 instead of float64 where precision allows

### I/O
- [ ] Async everything with asyncio (concurrent API calls)
- [ ] Connection pooling for HTTP requests
- [ ] WebSocket for real-time exchange data
- [ ] Redis for distributed caching (if multi-process)

### Memory
- [ ] Use generators for large datasets (yield instead of return)
- [ ] Delete unused DataFrames explicitly
- [ ] Use `pl.scan_*` for out-of-core processing
- [ ] Profile with `memory_profiler`

## Complete Requirements.txt

```txt
# Python 3.10+
python>=3.10

# Async & Networking
asyncio
aiohttp>=3.9.0
websockets>=12.0
aiofiles>=23.2.0

# Data Processing (Speed)
polars>=0.19.0
pandas>=2.0.0
numpy>=1.24.0
numba>=0.58.0
pyarrow>=14.0.0  # For Parquet

# Math & Stats
scipy>=1.11.0
statsmodels>=0.14.0
scikit-learn>=1.3.0

# Kalman Filter
pykalman>=0.9.5
filterpy>=1.4.5

# Regime Detection
hmmlearn>=0.3.0
ruptures>=1.1.9  # Change point detection

# Visualization (Wow Factor)
streamlit>=1.28.0
plotly>=5.17.0
matplotlib>=3.8.0
seaborn>=0.13.0

# Testing
hypothesis>=6.92.0
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# Utilities
pydantic>=2.5.0
python-dotenv>=1.0.0
loguru>=0.7.0
click>=8.1.0  # CLI
rich>=13.7.0  # Pretty terminal output

# Development
mypy>=1.7.0
black>=23.12.0
ruff>=0.1.8
```

## Project Setup (5 Minutes)

```bash
# Create project
mkdir imc-trading-bot
cd imc-trading-bot

# Virtual environment
python3.10 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install turbo stack
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
OPENWEATHER_API_KEY=your_key_here
EXCHANGE_URL=wss://imc-exchange.com
EXCHANGE_API_KEY=your_key_here
EOF

# Create config
cat > config.yaml << EOF
strategy:
  signal_threshold: 0.3
  kalman_process_variance: 0.01
  obi_threshold: 0.3
  
risk:
  max_position_size: 0.2
  max_total_exposure: 0.8
  max_drawdown: 0.25
EOF

# Run tests
pytest tests/ -v

# Launch dashboard
streamlit run src/dashboard.py

# Run live bot
python src/main.py --mode live
```

## Winning Implementation Timeline

### Hours 0-4: Turbo Setup
- Install stack
- Set up async data clients
- Implement Kalman Filter
- Test OBI calculation

### Hours 4-12: Signal Discovery
- Fetch Munich data (weather, flights, air quality)
- Correlation analysis with Polars
- Kalman Filter smoothing
- Identify 3-5 strong signals

### Hours 12-20: Core Engine
- Numba-optimized feature engineering
- HMM regime detection
- Adaptive strategy with OBI
- Risk management

### Hours 20-28: Backtesting
- Vectorized backtest with Polars
- Performance by regime
- Validate Sharpe > 1.5, drawdown < 20%

### Hours 28-36: Streamlit Dashboard
- Real-time PnL chart
- Signal correlations
- Regime timeline
- OBI gauge
- Position monitor

### Hours 36-42: Testing & Refinement
- Property-based tests
- Integration tests
- Performance profiling
- Bug fixes

### Hours 42-48: Presentation
- Polish dashboard
- Generate static charts
- Architecture diagram
- Practice demo

## Demo Script for Judges

**Slide 1: The Insight** (30 seconds)
"We discovered that flight delays + weather create a Kalman-filtered leading indicator for Munich ETF movements. Here's the correlation heatmap..."

**Slide 2: The Architecture** (30 seconds)
"Async Python with Polars for speed, Numba JIT for hot loops, Kalman Filters for signal smoothing, and Order Book Imbalance for microstructure alpha."

**Slide 3: Live Dashboard** (60 seconds)
[Open Streamlit dashboard]
"This is our bot trading live. You can see:
- Real-time PnL (green line)
- Current regime: Trending (HMM detected)
- OBI: +0.45 (strong buy pressure)
- Our signals: Weather momentum, flight volume, air quality delta
- Position: Long 15% (scaled by confidence)"

**Slide 4: The Adaptation** (30 seconds)
"When volatility spikes, our HMM detects it instantly, and we reduce positions by 50%. When trending, we increase momentum signal weights. This regime timeline shows our adaptations."

**Slide 5: The Results** (30 seconds)
"Sharpe ratio: 1.8, Max drawdown: 12%, Win rate: 62%. Positive across all regimes. Clean code, full test coverage, production-ready."

## Why This Wins

**Novel Signals (40%)**:
- Kalman-filtered Munich data
- OBI microstructure alpha
- Cointegration analysis
- Documented discovery process

**Adaptation (30%)**:
- HMM regime detection
- Change point detection
- Regime-specific strategies
- Live dashboard showing adaptation

**Engineering (30%)**:
- Async architecture
- Numba optimization
- Clean modular design
- Comprehensive tests
- Type safety

Judges are quant traders. They value:
- **Speed**: Numba, Polars, async
- **Sophistication**: Kalman, HMM, OBI
- **Observability**: Streamlit dashboard
- **Engineering**: Clean code, tests, types

You're not just building a bot. You're building a **production-grade trading system** in 48 hours.

Good luck! 🚀
