# Technology Stack

## Primary Language

**Python 3.10+** - Superior for hackathons due to data science ecosystem. While IMC uses C++ for nanosecond execution, Python's rapid development and Munich signal analysis libraries make it the winning choice.

## Core Stack (Production-Grade)

### Concurrency & Async (NON-NEGOTIABLE)
- **asyncio**: Core async runtime for responsive bot
- **aiohttp**: Async HTTP client for API calls
- **websockets**: Real-time exchange communication

### Data Processing (Speed Matters)
- **Polars**: 10x faster than Pandas for large datasets (primary choice)
- **Pandas**: Fallback for compatibility with existing libraries
- **NumPy**: Vectorized operations, SIMD optimizations
- **Numba**: JIT compilation with @jit decorator - compiles Python to machine code

### Math & Statistics
- **NumPy**: Vector operations, linear algebra
- **SciPy**: Statistical functions, optimization
- **Statsmodels**: Time-series analysis, cointegration tests
- **pykalman**: Kalman Filter implementation (the "ghost" algo)

### Networking & APIs
- **aiohttp**: Async HTTP requests (weather, air quality, flights)
- **websockets**: Real-time market data streaming
- **requests**: Synchronous fallback if needed

### Visualization (The "Wow" Factor)
- **Streamlit**: Live dashboard showing real-time PnL, signal correlations, regime changes
- **Plotly**: Interactive charts for presentation
- **matplotlib/seaborn**: Static charts for documentation

### Testing
- **Hypothesis**: Property-based testing
- **pytest**: Unit testing framework
- **pytest-asyncio**: Async test support

## "Turbo" Stack Upgrades (Competitive Edge)

### 1. Kalman Filter (State Estimation)
**Why**: Unlike lagging rolling OLS, Kalman Filters estimate the "true" hidden state instantly
**Use Case**: Real-time signal filtering, noise reduction, trend estimation
**Library**: `pykalman` or `filterpy`
```python
from pykalman import KalmanFilter
# Estimates true price/signal from noisy observations
kf = KalmanFilter(transition_matrices=[1], observation_matrices=[1])
state_means, _ = kf.filter(noisy_observations)
```

### 2. Numba JIT Compilation
**Why**: Compiles Python loops to machine code (100x+ speedup)
**Use Case**: Feature engineering loops, signal calculations
```python
from numba import jit
@jit(nopython=True)
def fast_feature_calc(prices):
    # This runs at C speed
    return np.diff(prices) / prices[:-1]
```

### 3. Order Book Imbalance (OBI) - Microstructure Alpha
**Why**: Predicts price movement 1 second before it happens
**Use Case**: Front-run market moves using bid/ask depth
```python
def order_book_imbalance(bids, asks):
    bid_volume = sum(b['size'] for b in bids[:5])
    ask_volume = sum(a['size'] for a in asks[:5])
    return (bid_volume - ask_volume) / (bid_volume + ask_volume)
```

### 4. Advanced Regime Detection
- **Hidden Markov Models (HMM)**: Probabilistic regime classification
- **Change Point Detection**: Identify regime transitions instantly
- **Hurst Exponent**: Measure mean-reversion vs trending

## Architecture Principles

- **Async-first**: All I/O operations use asyncio
- **JIT-optimized**: Critical paths use Numba compilation
- **Real-time**: Sub-100ms latency for data → signal → order
- **Observable**: Live Streamlit dashboard for judges
- **Modular**: Clean separation of concerns
- **Type-safe**: Full type hints with mypy validation

## Performance Targets

- Data ingestion: < 50ms (async concurrent fetching)
- Feature engineering: < 20ms (Numba JIT)
- Signal generation: < 10ms (vectorized NumPy)
- Order submission: < 20ms (async websocket)
- **Total latency: < 100ms** (data → order)

## Development Workflow

### Hours 0-4: Setup & Data Pipeline
- Install turbo stack
- Set up async data clients
- Implement Kalman Filter for signal smoothing

### Hours 4-12: Signal Discovery
- Correlation analysis with Polars
- Kalman Filter for noise reduction
- OBI calculation from order book

### Hours 12-24: Core Trading Engine
- Numba-optimized feature engineering
- Regime detection with HMM
- Adaptive strategy with OBI signals

### Hours 24-36: Streamlit Dashboard
- Real-time PnL visualization
- Signal correlation heatmaps
- Regime transition timeline
- Order book imbalance chart

### Hours 36-42: Backtesting
- Vectorized backtest with Polars
- Performance metrics by regime
- Statistical validation

### Hours 42-48: Presentation Prep
- Polish Streamlit dashboard
- Generate static charts
- Architecture diagrams
- Practice demo

## Key Libraries (Complete List)

```txt
# Core
python>=3.10
asyncio
aiohttp>=3.9.0
websockets>=12.0

# Data Processing (Speed)
polars>=0.19.0
pandas>=2.0.0
numpy>=1.24.0
numba>=0.58.0

# Math & Stats
scipy>=1.11.0
statsmodels>=0.14.0
pykalman>=0.9.5
filterpy>=1.4.5

# Visualization (Wow Factor)
streamlit>=1.28.0
plotly>=5.17.0
matplotlib>=3.8.0
seaborn>=0.13.0

# Testing
hypothesis>=6.92.0
pytest>=7.4.0
pytest-asyncio>=0.21.0

# Utilities
pydantic>=2.5.0  # Data validation
python-dotenv>=1.0.0  # Config management
loguru>=0.7.0  # Better logging
```

## Common Commands

```bash
# Setup
pip install -r requirements.txt

# Run live bot
python src/main.py --mode live

# Run backtest
python src/backtest.py --data data/historical.parquet

# Launch dashboard (judges will love this)
streamlit run src/dashboard.py

# Run tests
pytest tests/ -v

# Type checking
mypy src/
```
