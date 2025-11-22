# Design Document

## Overview

The IMC Trading Bot is a real-time algorithmic trading system designed to compete in the Munich ETF Challenge. The system ingests live Munich city data (weather, air quality, flight activity), generates trading signals through feature engineering, adapts to different market regimes, and executes trades on a simulated exchange with robust risk management.

The architecture prioritizes three key aspects valued by judges:
1. **Novel Signal Discovery (40%)**: Creative feature engineering from Munich data
2. **Adaptive Strategy (30%)**: Real-time regime detection and strategy adjustment
3. **Clean Engineering (30%)**: Modular design with clear separation of concerns

## Architecture

The system follows a layered architecture with clear data flow:

```
┌─────────────────────────────────────────────────────────────┐
│                     External Data Sources                    │
│  (Weather API, Air Quality API, Flight Data, Exchange API)  │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Data Ingestion Layer                       │
│  - API Clients (Weather, AirQuality, Flights)               │
│  - Data Validators                                           │
│  - Cache Manager                                             │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 Signal Processing Layer                      │
│  - Feature Engineer (compute derived features)              │
│  - Signal Generator (combine features → signals)            │
│  - Signal Combiner (weighted aggregation)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                  Strategy Layer                              │
│  - Regime Detector (classify market state)                  │
│  - Adaptive Strategy (regime-specific logic)                │
│  - Position Sizer (confidence-based sizing)                 │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Risk Management Layer                      │
│  - Position Limiter (enforce exposure limits)               │
│  - Drawdown Monitor (track losses)                          │
│  - Safe Mode Controller (emergency shutdown)                │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                   Execution Layer                            │
│  - Order Manager (submit/cancel orders)                     │
│  - Position Tracker (maintain state)                        │
│  - Exchange Client (API communication)                      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                 Monitoring & Logging Layer                   │
│  - Logger (structured logging)                              │
│  - Metrics Collector (PnL, Sharpe, etc.)                    │
│  - Report Generator (summary statistics)                    │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Modularity**: Each layer has a single responsibility and well-defined interfaces
2. **Testability**: Components can be tested in isolation with mock dependencies
3. **Observability**: Comprehensive logging at each layer for debugging and presentation
4. **Resilience**: Graceful degradation when data sources fail
5. **Performance**: Sub-100ms latency for data processing and order submission

## Components and Interfaces

### 1. Data Ingestion Layer

**Purpose**: Fetch and validate data from external sources

**Components**:

- `WeatherClient`: Fetches weather data from OpenWeatherMap API
- `AirQualityClient`: Fetches air quality data from OpenWeatherMap Air Pollution API
- `FlightClient`: Fetches flight data from OpenSky Network API
- `DataValidator`: Validates data format and rejects malformed inputs
- `CacheManager`: Stores recent data for fallback when sources are unavailable

**Interfaces**:

```python
class DataClient(ABC):
    @abstractmethod
    async def fetch(self) -> Dict[str, Any]:
        """Fetch data from external source"""
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """Validate data format"""
        pass

class CacheManager:
    def store(self, key: str, data: Dict[str, Any], ttl: int) -> None:
        """Store data with time-to-live"""
        pass
    
    def retrieve(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached data if available and fresh"""
        pass
```

### 2. Signal Processing Layer

**Purpose**: Transform raw data into actionable trading signals

**Components**:

- `FeatureEngineer`: Computes derived features from raw data
  - Weather momentum (temperature change rate)
  - Flight volume trends (moving averages, deltas)
  - Air quality deltas (rate of change)
  - Cross-signal indicators (multiple data sources aligned)
  
- `SignalGenerator`: Converts features into signal strength scores [-1.0, 1.0]
- `SignalCombiner`: Aggregates multiple signals with regime-specific weights

**Interfaces**:

```python
class FeatureEngineer:
    def compute_features(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Compute engineered features from raw data"""
        pass
    
    def normalize(self, features: pd.DataFrame) -> pd.DataFrame:
        """Normalize features to comparable scales"""
        pass

class SignalGenerator:
    def generate(self, features: pd.DataFrame) -> Dict[str, float]:
        """Generate signal strength scores for each feature"""
        pass

class SignalCombiner:
    def combine(self, signals: Dict[str, float], regime: str) -> float:
        """Combine signals with regime-specific weights"""
        pass
```

### 3. Strategy Layer

**Purpose**: Detect market regimes and adapt trading logic

**Components**:

- `RegimeDetector`: Classifies market state using volatility, trend, and mean-reversion metrics
  - Volatility: Rolling standard deviation of returns
  - Trend: Moving average crossover (fast MA vs slow MA)
  - Mean reversion: Autocorrelation of returns
  
- `AdaptiveStrategy`: Applies regime-specific trading logic
  - Trending: Momentum signals, trailing stops
  - Mean-reverting: Contrarian signals, tight stops
  - High-volatility: Reduced positions, wider stops
  - Low-volatility: Normal positions, standard stops
  
- `PositionSizer`: Calculates position size based on signal confidence and regime

**Interfaces**:

```python
class RegimeDetector:
    def detect(self, market_data: pd.DataFrame) -> str:
        """Classify current market regime"""
        pass
    
    def get_confidence(self) -> float:
        """Return confidence in regime classification"""
        pass

class AdaptiveStrategy:
    def get_signal_weights(self, regime: str) -> Dict[str, float]:
        """Return regime-specific signal weights"""
        pass
    
    def get_parameters(self, regime: str) -> Dict[str, Any]:
        """Return regime-specific strategy parameters"""
        pass

class PositionSizer:
    def calculate_size(self, signal: float, confidence: float, 
                      regime: str, capital: float) -> float:
        """Calculate position size based on signal and risk"""
        pass
```

### 4. Risk Management Layer

**Purpose**: Enforce position limits and drawdown controls

**Components**:

- `PositionLimiter`: Enforces per-position and total exposure limits
- `DrawdownMonitor`: Tracks cumulative losses and triggers risk reduction
- `SafeModeController`: Halts trading when drawdown exceeds critical threshold

**Interfaces**:

```python
class PositionLimiter:
    def check_limit(self, proposed_size: float, current_positions: Dict) -> float:
        """Return adjusted position size within limits"""
        pass

class DrawdownMonitor:
    def update(self, current_pnl: float) -> None:
        """Update drawdown tracking"""
        pass
    
    def get_multiplier(self) -> float:
        """Return position size multiplier based on drawdown"""
        pass
    
    def is_safe_mode(self) -> bool:
        """Check if safe mode should be activated"""
        pass
```

### 5. Execution Layer

**Purpose**: Submit orders and track positions

**Components**:

- `OrderManager`: Submits, cancels, and tracks orders
- `PositionTracker`: Maintains current position state
- `ExchangeClient`: Communicates with simulated exchange API

**Interfaces**:

```python
class OrderManager:
    def submit_order(self, symbol: str, size: float, 
                    limit_price: float) -> str:
        """Submit order and return order ID"""
        pass
    
    def cancel_order(self, order_id: str) -> bool:
        """Cancel unfilled order"""
        pass
    
    def get_order_status(self, order_id: str) -> str:
        """Get current order status"""
        pass

class PositionTracker:
    def update_position(self, symbol: str, size: float, price: float) -> None:
        """Update position after fill"""
        pass
    
    def get_position(self, symbol: str) -> float:
        """Get current position size"""
        pass
    
    def get_total_exposure(self) -> float:
        """Get total capital exposure"""
        pass
```

### 6. Monitoring & Logging Layer

**Purpose**: Track performance and provide observability

**Components**:

- `Logger`: Structured logging with context
- `MetricsCollector`: Tracks PnL, Sharpe ratio, drawdown, win rate
- `ReportGenerator`: Generates summary statistics and visualizations

**Interfaces**:

```python
class Logger:
    def log_trade(self, symbol: str, size: float, price: float, 
                 signal: float, regime: str, reasoning: str) -> None:
        """Log trade execution with context"""
        pass
    
    def log_regime_change(self, old_regime: str, new_regime: str, 
                         new_params: Dict) -> None:
        """Log regime transition"""
        pass

class MetricsCollector:
    def record_trade(self, pnl: float, timestamp: datetime) -> None:
        """Record trade result"""
        pass
    
    def get_sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""
        pass
    
    def get_max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        pass
```

## Data Models

### MunichData
```python
@dataclass
class MunichData:
    timestamp: datetime
    weather: WeatherData
    air_quality: AirQualityData
    flights: FlightData
```

### WeatherData
```python
@dataclass
class WeatherData:
    temperature: float  # Celsius
    feels_like: float
    humidity: float  # Percentage
    pressure: float  # hPa
    wind_speed: float  # m/s
    wind_direction: float  # degrees
    cloud_coverage: float  # Percentage
    rain_volume: float  # mm
    snow_volume: float  # mm
```

### AirQualityData
```python
@dataclass
class AirQualityData:
    aqi: int  # Air Quality Index (1-5)
    co: float  # Carbon monoxide (μg/m³)
    no2: float  # Nitrogen dioxide (μg/m³)
    o3: float  # Ozone (μg/m³)
    pm2_5: float  # Fine particulate matter (μg/m³)
    pm10: float  # Coarse particulate matter (μg/m³)
```

### FlightData
```python
@dataclass
class FlightData:
    active_flights: int  # Number of flights in Munich airspace
    departures: int  # Departures from MUC in last hour
    arrivals: int  # Arrivals to MUC in last hour
    avg_delay: float  # Average delay in minutes
```

### MarketData
```python
@dataclass
class MarketData:
    timestamp: datetime
    symbol: str
    price: float
    volume: float
    bid: float
    ask: float
    returns: List[float]  # Historical returns for regime detection
```

### Signal
```python
@dataclass
class Signal:
    timestamp: datetime
    strength: float  # [-1.0, 1.0]
    confidence: float  # [0.0, 1.0]
    components: Dict[str, float]  # Individual signal contributions
    regime: str
```

### Position
```python
@dataclass
class Position:
    symbol: str
    size: float  # Positive for long, negative for short
    entry_price: float
    current_price: float
    unrealized_pnl: float
```

### Order
```python
@dataclass
class Order:
    order_id: str
    symbol: str
    size: float
    limit_price: float
    status: str  # 'pending', 'filled', 'cancelled', 'rejected'
    timestamp: datetime
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, several properties can be consolidated:
- Properties 1.2 and 4.1 both test latency requirements and can be combined into a general latency property
- Properties 5.1 and 5.5 both test exposure limits and can be combined into a comprehensive risk limits property
- Properties 2.2 and 2.3 both test output bounds and can be combined into a bounds checking property

### Core Properties

**Property 1: Data processing latency bounds**
*For any* incoming data from Munich sources, the system should process and store it within 100 milliseconds, and when a trading signal exceeds threshold, the system should submit an order within 50 milliseconds.
**Validates: Requirements 1.2, 4.1**

**Property 2: Resilient operation with fallback**
*For any* data source failure, the system should continue operating using cached data and log the failure without crashing.
**Validates: Requirements 1.3**

**Property 3: Input validation rejects malformed data**
*For any* malformed data input, the system should reject it, and for any valid data input, the system should accept and process it.
**Validates: Requirements 1.4**

**Property 4: Chronological processing order**
*For any* set of timestamped data points arriving simultaneously, the system should process them in chronological order by timestamp.
**Validates: Requirements 1.5**

**Property 5: Feature computation completeness**
*For any* Munich data input, the system should compute at least 5 engineered features.
**Validates: Requirements 2.1**

**Property 6: Output bounds enforcement**
*For any* computed features, all normalized values should fall within comparable scales, and for any generated signal, the strength score should be between -1.0 and 1.0.
**Validates: Requirements 2.2, 2.3**

**Property 7: Signal combination consistency**
*For any* set of conflicting signals, the combined output should be a weighted aggregation of the inputs.
**Validates: Requirements 2.4**

**Property 8: Confidence-based trading abstention**
*For any* signal with confidence below threshold, no trade should be executed.
**Validates: Requirements 2.5**

**Property 9: Valid regime classification**
*For any* market data analyzed, the classified regime should be one of: trending, mean-reverting, high-volatility, or low-volatility.
**Validates: Requirements 3.1**

**Property 10: Regime adaptation latency**
*For any* detected regime change, strategy parameters should be updated within 1 second.
**Validates: Requirements 3.2**

**Property 11: Volatility-based position reduction**
*For any* high-volatility regime, position sizes should be reduced by at least 50% compared to normal regime.
**Validates: Requirements 3.3**

**Property 12: Regime-specific signal weighting**
*For any* trending regime, momentum signal weights should be higher than in other regimes.
**Validates: Requirements 3.4**

**Property 13: Conservative fallback parameters**
*For any* uncertain regime classification, the system should use conservative default parameters.
**Validates: Requirements 3.5**

**Property 14: Order limit price inclusion**
*For any* submitted order, a limit price should be included.
**Validates: Requirements 4.2**

**Property 15: Position tracking consistency**
*For any* filled order, the internal position state should be immediately updated to reflect the fill.
**Validates: Requirements 4.3**

**Property 16: Order rejection handling**
*For any* rejected order, the system should log the rejection reason and adjust future order parameters.
**Validates: Requirements 4.4**

**Property 17: Rapid market change response**
*For any* rapid market condition change, unfilled orders should be cancelled and positions reassessed.
**Validates: Requirements 4.5**

**Property 18: Comprehensive risk limits**
*For any* position calculation, the exposure should not exceed 20% of total capital per position, and for any portfolio state, total exposure should not exceed 80% of capital.
**Validates: Requirements 5.1, 5.5**

**Property 19: Drawdown-triggered risk reduction**
*For any* portfolio state where drawdown exceeds 15%, all position sizes should be reduced by 50%.
**Validates: Requirements 5.2**

**Property 20: Emergency safe mode activation**
*For any* portfolio state where drawdown exceeds 25%, all trading should halt and safe mode should be activated.
**Validates: Requirements 5.3**

**Property 21: Confidence-proportional position sizing**
*For any* signal with varying confidence, position size should scale proportionally to confidence level.
**Validates: Requirements 5.4**

**Property 22: Trade logging completeness**
*For any* executed trade, the log should contain signal strength, regime, position size, and reasoning.
**Validates: Requirements 6.1**

**Property 23: Regime change logging**
*For any* regime transition, the log should contain the old regime, new regime, and updated parameters.
**Validates: Requirements 6.2**

**Property 24: Error resilience without crashes**
*For any* error that occurs, the system should log the stack trace and context while continuing to operate.
**Validates: Requirements 6.3**

**Property 25: Continuous metrics availability**
*For any* point in time while running, the monitoring interface should expose current real-time metrics.
**Validates: Requirements 6.5**

**Property 26: Chronological backtest replay**
*For any* historical data provided to the backtesting engine, it should be replayed in chronological order.
**Validates: Requirements 7.1**

**Property 27: Realistic slippage simulation**
*For any* order filled during backtesting, the fill price should include realistic slippage relative to the limit price.
**Validates: Requirements 7.2**

**Property 28: Regime-segmented backtest results**
*For any* backtest across multiple market types, performance metrics should be broken down by regime.
**Validates: Requirements 7.4**

**Property 29: Statistical A/B testing support**
*For any* comparison of multiple strategies, the backtesting engine should provide statistical significance measures.
**Validates: Requirements 7.5**

**Property 30: Performance visualization by market type**
*For any* performance display, PnL curves should be shown separately for different market types.
**Validates: Requirements 8.2**

**Property 31: Adaptation visualization completeness**
*For any* adaptation explanation, visualizations should include regime transition markers and corresponding strategy adjustments.
**Validates: Requirements 8.3**

**Property 32: Consistency metric prominence**
*For any* results presentation, consistency metrics (Sharpe ratio, max drawdown) should be highlighted more prominently than peak PnL.
**Validates: Requirements 8.5**

**Property 33: Graceful error handling with messages**
*For any* error scenario, the system should handle it gracefully and provide informative error messages.
**Validates: Requirements 9.4**

## Error Handling

### Data Source Failures

**Strategy**: Graceful degradation with cached data

- Each data client maintains a local cache with TTL (time-to-live)
- When a data source is unavailable, the system uses the most recent cached value
- Failures are logged with severity level and timestamp
- If cache is stale (> 5 minutes), the system reduces confidence in signals derived from that source
- If all data sources fail, the system enters safe mode and closes positions

### Invalid Data

**Strategy**: Validation and rejection

- All incoming data is validated against expected schemas
- Malformed data is rejected and logged
- The system continues operating with the last valid data point
- Repeated validation failures trigger alerts

### Order Rejections

**Strategy**: Adaptive retry with parameter adjustment

- Order rejections are logged with exchange-provided reason codes
- The system analyzes rejection reasons (e.g., insufficient capital, invalid price)
- Future orders are adjusted based on rejection patterns
- After 3 consecutive rejections, the system pauses trading for 60 seconds

### Regime Detection Uncertainty

**Strategy**: Conservative fallback

- When regime classification confidence is below 70%, use conservative default parameters
- Default parameters: reduced position sizes, wider stops, lower signal weights
- Log uncertainty events for post-analysis

### Exchange Connectivity Issues

**Strategy**: Reconnection with state preservation

- Maintain local position state independent of exchange connection
- On disconnect, attempt reconnection with exponential backoff
- On reconnect, reconcile local state with exchange state
- If reconciliation fails, enter safe mode

### Extreme Market Conditions

**Strategy**: Circuit breakers

- If volatility exceeds 3x historical average, reduce all positions by 75%
- If price moves > 10% in 1 minute, cancel all orders and reassess
- If multiple circuit breakers trigger within 5 minutes, enter safe mode

## Testing Strategy

### Unit Testing

Unit tests will verify specific examples and edge cases for individual components:

**Data Ingestion Layer**:
- Test successful data fetch from each API
- Test handling of API rate limits
- Test cache hit/miss scenarios
- Test validation of malformed data

**Signal Processing Layer**:
- Test feature engineering with known inputs
- Test normalization edge cases (zero values, extreme values)
- Test signal combination with conflicting inputs
- Test signal generation at boundary conditions

**Strategy Layer**:
- Test regime detection with synthetic market data
- Test parameter switching on regime changes
- Test position sizing with various confidence levels
- Test edge cases (zero confidence, maximum confidence)

**Risk Management Layer**:
- Test position limits at boundaries (19%, 20%, 21% exposure)
- Test drawdown monitoring with simulated losses
- Test safe mode activation at 25% drawdown
- Test total exposure calculation with multiple positions

**Execution Layer**:
- Test order submission with mock exchange
- Test position tracking after fills
- Test order cancellation
- Test state reconciliation after reconnection

### Property-Based Testing

Property-based tests will verify universal properties across all inputs using **Hypothesis** (Python PBT library):

**Configuration**: Each property test will run a minimum of 100 iterations to ensure statistical coverage.

**Test Organization**: Each property-based test will be tagged with a comment explicitly referencing the correctness property from this design document using the format: `# Feature: imc-trading-bot, Property {number}: {property_text}`

**Key Properties to Test**:

1. **Latency properties**: Generate random data payloads and verify processing times
2. **Bounds properties**: Generate random inputs and verify outputs stay within bounds
3. **Risk limit properties**: Generate random signals and verify position sizes respect limits
4. **Ordering properties**: Generate random timestamp sequences and verify chronological processing
5. **Resilience properties**: Inject random failures and verify graceful handling
6. **Consistency properties**: Generate random state transitions and verify state consistency

**Example Property Test Structure**:
```python
from hypothesis import given, strategies as st

# Feature: imc-trading-bot, Property 6: Output bounds enforcement
@given(st.floats(min_value=-1000, max_value=1000))
def test_signal_strength_bounds(raw_signal):
    """For any raw signal value, normalized signal should be in [-1.0, 1.0]"""
    normalized = signal_generator.normalize(raw_signal)
    assert -1.0 <= normalized <= 1.0
```

### Integration Testing

Integration tests will verify component interactions:

- End-to-end data flow: API → features → signals → orders
- Regime detection → strategy adaptation → position sizing
- Order execution → position tracking → PnL calculation
- Error injection → fallback behavior → recovery

### Backtesting Validation

Backtest the strategy on historical data to validate:

- Performance across different market regimes
- Risk management effectiveness (drawdown limits)
- Signal quality (win rate, Sharpe ratio)
- Adaptation effectiveness (regime-specific performance)

**Backtest Metrics**:
- Sharpe Ratio (target: > 1.5)
- Maximum Drawdown (target: < 20%)
- Win Rate (target: > 55%)
- Consistency across regimes (positive PnL in all regimes)

### Performance Testing

Verify latency requirements:

- Data processing: < 100ms (99th percentile)
- Order submission: < 50ms (99th percentile)
- Regime detection: < 1s (99th percentile)

### Presentation Testing

Verify visualization generation:

- Signal discovery charts render correctly
- PnL curves show regime breakdowns
- Architecture diagrams are complete
- Consistency metrics are highlighted

## Implementation Notes

### Technology Choices

**Language**: Python 3.11+ for rapid development and rich ecosystem

**Key Libraries**:
- `pandas` + `numpy`: Data processing and feature engineering
- `scikit-learn`: Simple, interpretable ML models for regime detection
- `requests` + `aiohttp`: Synchronous and asynchronous HTTP clients
- `websockets`: Real-time exchange communication
- `hypothesis`: Property-based testing
- `pytest`: Unit testing framework
- `matplotlib` + `seaborn`: Visualization
- `dataclasses`: Type-safe data models

### Performance Optimizations

- Use `asyncio` for concurrent data fetching from multiple sources
- Cache computed features to avoid redundant calculations
- Use `numpy` vectorized operations for feature engineering
- Maintain in-memory position state for fast lookups
- Use connection pooling for exchange API calls

### Observability

- Structured logging with JSON format for easy parsing
- Log levels: DEBUG (development), INFO (production), ERROR (failures)
- Metrics exposed via simple HTTP endpoint for monitoring
- Trade logs include full context for post-analysis

### Deployment

For the hackathon, the system will run as a single Python process:

```bash
python src/main.py --mode live --config config.yaml
```

Configuration file includes:
- API keys for data sources
- Exchange connection details
- Risk parameters (position limits, drawdown thresholds)
- Strategy parameters (signal weights, regime thresholds)
- Logging configuration

### Future Enhancements

If time permits after core implementation:

1. **Advanced regime detection**: Use Hidden Markov Models for more sophisticated regime classification
2. **Multi-asset trading**: Extend to trade multiple correlated assets
3. **Machine learning signals**: Train models on historical Munich data correlations
4. **Real-time dashboard**: Web-based monitoring interface with live charts
5. **Distributed architecture**: Separate data ingestion, strategy, and execution into microservices
