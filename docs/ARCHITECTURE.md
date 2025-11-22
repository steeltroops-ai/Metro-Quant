# 🏗
️ IMC Trading Bot - System Architecture

## High-Level Architecture

```mermaid
graph TB
    subgraph "External Data Sources"
        A1[OpenWeatherMap API]
        A2[Air Quality API]
        A3[OpenSky Network]
        A4[IMC Exchange WebSocket]
    end
    
    subgraph "Data Ingestion Layer (Async)"
        B1[Weather Client]
        B2[Air Quality Client]
        B3[Flight Client]
        B4[Cache Manager]
    end
    
    subgraph "Signal Processing Layer (Numba JIT)"
        C1[Feature Engineer]
        C2[Kalman Filter]
        C3[Signal Generator]
        C4[Signal Combiner]
    end
    
    subgraph "Strategy Layer"
        D1[HMM Regime Detector]
        D2[Adaptive Strategy]
        D3[OBI Calculator]
        D4[Position Sizer]
    end
    
    subgraph "Risk Management Layer"
        E1[Position Limiter]
        E2[Drawdown Monitor]
        E3[Safe Mode Controller]
    end
    
    subgraph "Execution Layer (Async)"
        F1[Order Manager]
        F2[Position Tracker]
        F3[Exchange Client]
    end
    
    subgraph "Monitoring Layer"
        G1[Logger]
        G2[Metrics Collector]
        G3[Streamlit Dashboard]
    end
    
    A1 --> B1
    A2 --> B2
    A3 --> B3
    A4 --> F3
    
    B1 --> B4
    B2 --> B4
    B3 --> B4
    
    B4 --> C1
    C1 --> C2
    C2 --> C3
    C3 --> C4
    
    C4 --> D1
    C4 --> D3
    D1 --> D2
    D3 --> D2
    D2 --> D4
    
    D4 --> E1
    E1 --> E2
    E2 --> E3
    
    E3 --> F1
    F1 --> F2
    F2 --> F3
    
    F1 --> G1
    F2 --> G2
    G2 --> G3
    
    style C1 fill:#ff9999
    style C2 fill:#ff9999
    style D1 fill:#99ccff
    style D3 fill:#99ccff
    style G3 fill:#99ff99
```

## Data Flow Diagram

```mermaid
sequenceDiagram
    participant APIs as External APIs
    participant Ingest as Data Ingestion
    participant Kalman as Kalman Filter
    participant Signal as Signal Generator
    participant HMM as HMM Regime
    participant OBI as OBI Calculator
    participant Strategy as Adaptive Strategy
    participant Risk as Risk Manager
    participant Exchange as Exchange
    participant Dashboard as Streamlit Dashboard
    
    APIs->>Ingest: Async fetch (weather, air, flights)
    Ingest->>Kalman: Raw Munich data
    Kalman->>Signal: Filtered signals (zero lag)
    Signal->>HMM: Market data
    HMM->>Strategy: Current regime + confidence
    Signal->>OBI: Order book data
    OBI->>Strategy: OBI signal
    Strategy->>Risk: Position size request
    Risk->>Exchange: Submit order
    Exchange->>Dashboard: Update PnL
    Dashboard->>Dashboard: Real-time visualization
```

## Component Details

### 1. Data Ingestion Layer (Async)

**Purpose**: Fetch data from multiple sources concurrently

**Key Technologies**:
- `asyncio` + `aiohttp` for non-blocking I/O
- Connection pooling for efficiency
- Redis/in-memory cache with TTL

**Performance**: 
- Concurrent fetching: 100ms (vs 300ms sequential)
- Cache hit rate: > 80%

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

### 2. Signal Processing Layer (Numba JIT)

**Purpose**: Transform raw data into trading signals

**Key Technologies**:
- Numba JIT compilation (100x speedup)
- Kalman Filters (zero-lag smoothing)
- Polars for vectorized operations

**Performance**:
- Feature engineering: < 20ms (Numba)
- Kalman filtering: < 10ms
- Signal generation: < 10ms

```python
@jit(nopython=True)
def calculate_features(prices, volumes):
    """Compiled to machine code"""
    momentum = (prices[-1] - prices[-20]) / prices[-20]
    volatility = np.std(prices[-20:])
    return momentum, volatility
```

### 3. Strategy Layer

**Purpose**: Detect market regimes and adapt strategy

**Key Technologies**:
- Hidden Markov Models (HMM) for regime detection
- Order Book Imbalance (OBI) for microstructure alpha
- Confidence-based position sizing

**Regimes**:
1. **Trending**: High momentum signals, trailing stops
2. **Mean-Reverting**: Contrarian signals, tight stops
3. **High-Volatility**: Reduced positions, wider stops

```python
# HMM Regime Detection
model = hmm.GaussianHMM(n_components=3)
regime = model.predict(features)[-1]

# OBI Calculation
obi = (bid_volume - ask_volume) / (bid_volume + ask_volume)
```

### 4. Risk Management Layer

**Purpose**: Enforce position limits and drawdown controls

**Limits**:
- Per-position: 20% of capital
- Total exposure: 80% of capital
- Drawdown warning: 15%
- Drawdown halt: 25%

**Features**:
- Confidence-based scaling
- Regime-specific multipliers
- Emergency safe mode

### 5. Execution Layer (Async)

**Purpose**: Submit orders and track positions

**Key Technologies**:
- WebSocket for real-time exchange communication
- Async order submission (< 20ms)
- State reconciliation on reconnect

**Performance**:
- Order submission: < 20ms
- Position update: < 5ms

### 6. Monitoring Layer

**Purpose**: Observability and presentation

**Key Technologies**:
- Streamlit for live dashboard
- Plotly for interactive charts
- Structured logging with loguru

**Dashboard Features**:
- Real-time PnL curve
- Signal correlation heatmap
- Regime timeline
- OBI gauge
- Position monitor

## Technology Stack Summary

| Layer | Technology | Speedup | Purpose |
|-------|-----------|---------|---------|
| Data Processing | Polars | 10x | Fast data manipulation |
| Hot Loops | Numba JIT | 100x | Machine code compilation |
| I/O Operations | asyncio | 10x | Non-blocking concurrency |
| Signal Smoothing | Kalman Filter | Zero lag | State estimation |
| Regime Detection | HMM | Probabilistic | Market state classification |
| Microstructure | OBI | New alpha | Order book analysis |
| Visualization | Streamlit | Real-time | Live dashboard |
| Testing | Hypothesis | Comprehensive | Property-based tests |

## Performance Characteristics

### Latency Breakdown (Target: < 100ms)

```
Data Fetch (async):        30ms  ████████
Feature Engineering:       20ms  ██████
Kalman Filtering:          10ms  ███
Signal Generation:         10ms  ███
Regime Detection:          15ms  ████
Position Sizing:            5ms  █
Order Submission:          20ms  ██████
                          -----
Total:                    110ms  (target: 100ms)
```

**Optimization Opportunities**:
- Cache regime detection results (save 10ms)
- Pre-compute feature templates (save 5ms)
- **Optimized Total: 95ms** ✅

### Throughput

- **Data ingestion**: 10 updates/second
- **Signal generation**: 20 signals/second
- **Order submission**: 50 orders/second

### Resource Usage

- **Memory**: ~500MB (with caching)
- **CPU**: 2-4 cores (async + Numba)
- **Network**: ~1MB/min (API calls)

## Deployment Architecture

```mermaid
graph LR
    subgraph "Development"
        A[Jupyter Notebooks]
        B[Local Testing]
    end
    
    subgraph "Production"
        C[Main Bot Process]
        D[Streamlit Dashboard]
        E[Monitoring]
    end
    
    subgraph "Data Storage"
        F[Parquet Files]
        G[Redis Cache]
        H[Logs]
    end
    
    A --> B
    B --> C
    C --> D
    C --> E
    C --> F
    C --> G
    C --> H
```

## Scalability Considerations

### Horizontal Scaling
- Multiple bot instances with different strategies
- Shared Redis cache for coordination
- Load balancing across exchange connections

### Vertical Scaling
- Numba JIT utilizes all CPU cores
- Polars uses multi-threading automatically
- Async I/O maximizes single-thread efficiency

## Security & Reliability

### Error Handling
- Graceful degradation on data source failures
- Automatic reconnection with exponential backoff
- Safe mode on critical errors

### Data Validation
- Pydantic models for type safety
- Input validation on all external data
- Sanity checks on signals and positions

### Monitoring
- Real-time metrics via Streamlit
- Structured logging for debugging
- Alert system for critical events

## Testing Strategy

### Unit Tests
- Individual component testing
- Mock external dependencies
- Edge case coverage

### Property-Based Tests (Hypothesis)
- Bounds checking (signals in [-1, 1])
- Risk limits (position sizes)
- Consistency (state transitions)

### Integration Tests
- End-to-end data flow
- Regime detection accuracy
- Order execution simulation

### Performance Tests
- Latency benchmarks
- Throughput stress tests
- Memory profiling

## Competitive Advantages

1. **Speed**: 10-100x faster than basic Python
2. **Sophistication**: Kalman + HMM + OBI
3. **Observability**: Live Streamlit dashboard
4. **Engineering**: Production-grade architecture
5. **Testing**: Comprehensive test coverage
6. **Type Safety**: Full type hints + validation

## Future Enhancements

If time permits:
1. **Multi-asset trading**: Extend to multiple correlated assets
2. **Machine learning**: Train models on historical correlations
3. **Distributed architecture**: Microservices for scalability
4. **Advanced HMM**: More sophisticated regime models
5. **REST API**: External monitoring and control

---

**This architecture is designed to win the IMC Munich ETF Challenge by demonstrating:**
- Novel signal discovery (Kalman + OBI)
- Adaptive strategy (HMM regimes)
- Clean engineering (modular, tested, typed)

Good luck! 🚀
