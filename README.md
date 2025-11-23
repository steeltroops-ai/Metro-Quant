# IMC Munich ETF Trading Bot

An adaptive algorithmic trading bot for the IMC Munich ETF Challenge at HackaTUM 2025. The bot discovers alpha in live Munich city data (weather, air quality, flights) and trades on IMC's simulated exchange with real-time regime detection and risk management.

## 🎯 Key Features

- **Novel Signal Discovery**: Creative feature engineering from Munich city data
- **Adaptive Strategy**: Real-time market regime detection and strategy adjustment
- **Robust Risk Management**: Position limits, drawdown monitoring, emergency shutdown
- **High Performance**: < 100ms latency from data to order execution
- **Clean Architecture**: Modular async-first design with comprehensive testing

## 📋 Requirements

- Python 3.10 or higher
- pip (Python package manager)
- Internet connection for API access

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd imc-trading-bot

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with your credentials:

```bash
# IMC Exchange (REQUIRED)
IMC_EXCHANGE_URL=http://ec2-52-31-108-187.eu-west-1.compute.amazonaws.com
IMC_USERNAME=inexia
IMC_PASSWORD=ma21GLA$

# OpenWeatherMap API (REQUIRED for Munich data)
OPENWEATHER_API_KEY=your_api_key_here

# OpenSky Network API (OPTIONAL - public access available)
OPENSKY_API_KEY=your_api_key_here
```

**Get API Keys:**
- OpenWeatherMap: https://openweathermap.org/api (free tier available)
- OpenSky Network: https://opensky-network.org/ (optional, public API works)

### 3. Test Exchange Connection

Before running the bot, test your exchange connection:

```bash
python scripts/test_exchange.py
```

This will verify:
- ✓ Authentication with IMC exchange
- ✓ Product fetching (all 8 instruments)
- ✓ Market data retrieval
- ✓ Order submission and cancellation
- ✓ Position tracking
- ✓ Error handling

### 4. Run the Trading Bot

```bash
# Paper trading mode (recommended for testing)
python src/main.py --mode paper

# Live trading mode (real money!)
python src/main.py --mode live

# With custom configuration
python src/main.py --mode live --config config.yaml --log-level DEBUG
```

## 📊 Monitoring

### Real-time Dashboard

While the bot is running, access the Streamlit dashboard:

```bash
streamlit run src/visualization/dashboard.py
```

Open http://localhost:8501 in your browser to see:
- Live PnL tracking
- Signal strength visualization
- Regime detection status
- Position overview
- Trade history

### Metrics API

The bot exposes real-time metrics on port 8080:

```bash
curl http://localhost:8080/metrics
```

Returns JSON with:
- Current PnL
- Sharpe ratio
- Maximum drawdown
- Win rate
- Active positions

### Logs

Logs are written to:
- Console (stdout)
- `logs/trading_bot_YYYY-MM-DD.log` (daily rotation)
- `logs/trades_YYYY-MM-DD.json` (structured trade logs)

## 🧪 Testing

### Run All Tests

```bash
# Unit tests
pytest tests/unit/ -v

# Property-based tests
pytest tests/property/ -v

# Integration tests
pytest tests/integration/ -v

# All tests with coverage
pytest tests/ -v --cov=src --cov-report=html
```

### Run Backtest

```bash
python scripts/run_backtest.py
```

Results are saved to `reports/backtest_results_TIMESTAMP.json`

## 📁 Project Structure

```
imc-trading-bot/
├── src/
│   ├── data/              # Data ingestion (weather, flights, air quality)
│   ├── signals/           # Feature engineering and signal generation
│   ├── strategy/          # Regime detection and adaptive strategy
│   ├── risk/              # Risk management and position limits
│   ├── exchange/          # IMC exchange client and order management
│   ├── monitoring/        # Logging, metrics, and reporting
│   ├── backtest/          # Backtesting engine
│   ├── visualization/     # Streamlit dashboard and charts
│   └── utils/             # Configuration, types, and helpers
├── tests/
│   ├── unit/              # Unit tests
│   ├── property/          # Property-based tests (Hypothesis)
│   └── integration/       # Integration tests
├── scripts/
│   ├── test_exchange.py   # Exchange integration test suite
│   ├── run_backtest.py    # Backtest execution script
│   └── generate_presentation.py  # Presentation materials
├── config.yaml            # Main configuration file
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

### Trading Strategy
```yaml
strategy:
  signal_threshold: 0.3      # Minimum signal strength to trade
  confidence_threshold: 0.5  # Minimum confidence to trade
```

### Risk Management
```yaml
risk:
  max_position_size: 0.20           # 20% per position
  max_total_exposure: 0.80          # 80% total
  drawdown_reduction_threshold: 0.15  # 15% triggers reduction
  drawdown_safe_mode_threshold: 0.25  # 25% triggers shutdown
```

### Data Sources
```yaml
data_sources:
  weather:
    update_interval: 60  # seconds
  air_quality:
    update_interval: 60
  flights:
    update_interval: 30
```

### Exchange Settings
```yaml
exchange:
  position_limits:
    min: -200  # Maximum short per instrument
    max: 200   # Maximum long per instrument
```

## 🎓 How It Works

### 1. Data Ingestion
- Fetches live Munich data from multiple sources concurrently
- Weather: temperature, humidity, wind, precipitation
- Air Quality: AQI, PM2.5, PM10, NO2, O3
- Flights: active flights, departures, arrivals, delays

### 2. Signal Generation
- Computes engineered features (momentum, trends, deltas)
- Applies Kalman filtering for noise reduction
- Generates signal strength scores [-1.0, 1.0]
- Combines signals with regime-specific weights

### 3. Regime Detection
- Classifies market state: trending, mean-reverting, high/low volatility
- Adapts strategy parameters based on regime
- Adjusts position sizing and signal weights

### 4. Risk Management
- Enforces position limits (20% per position, 80% total)
- Monitors drawdown (15% reduction, 25% shutdown)
- Scales positions by signal confidence

### 5. Order Execution
- Submits limit orders with < 50ms latency
- Tracks positions and PnL in real-time
- Handles rejections and reconnections gracefully

## 🔧 Troubleshooting

### Authentication Failed
```
Error: Authentication failed with status 401
```
**Solution**: Verify credentials in `.env` file match IMC exchange credentials

### API Rate Limits
```
Error: OpenWeatherMap API rate limit exceeded
```
**Solution**: Increase `update_interval` in `config.yaml` or upgrade API plan

### Connection Timeout
```
Error: Connection timeout to exchange
```
**Solution**: Check internet connection and exchange URL. Verify exchange is running.

### No Market Data
```
Warning: No market data available
```
**Solution**: Market may be closed. Check exchange trading hours.

### Position Limit Exceeded
```
Error: Order rejected - position limit exceeded
```
**Solution**: Reduce `max_position_size` in `config.yaml` or close existing positions

## 📈 Performance Targets

- **Latency**: < 100ms total (data → signal → order)
- **Sharpe Ratio**: > 1.5
- **Max Drawdown**: < 20%
- **Win Rate**: > 55%

## 🏆 Competition Strategy

### Signal Discovery (40%)
- Novel correlations between Munich data and ETF price
- Creative feature engineering (weather momentum, flight trends)
- Kalman filtering for noise reduction

### Adaptive Strategy (30%)
- Real-time regime detection
- Dynamic parameter adjustment
- Observable strategy changes

### Engineering Quality (30%)
- Clean async architecture
- Comprehensive error handling
- Property-based testing
- Performance optimization (Numba JIT)

## 📝 Production Checklist

Before switching to production exchange:

- [ ] Test all functionality with `scripts/test_exchange.py`
- [ ] Verify all 8 instruments are tradeable
- [ ] Confirm position limits (-200 to +200) are enforced
- [ ] Test error handling with injected failures
- [ ] Verify logging captures all trades with reasoning
- [ ] Run backtest to validate strategy performance
- [ ] Monitor test exchange for 1+ hours without crashes
- [ ] Update `IMC_EXCHANGE_URL` in `.env` to production URL
- [ ] Set `--mode live` when running bot
- [ ] Monitor leaderboard position

## 🚨 Emergency Procedures

### Stop Trading Immediately
```bash
# Press Ctrl+C in terminal running the bot
# Or send SIGTERM signal
kill -TERM <pid>
```

The bot will:
1. Cancel all pending orders
2. Generate final report
3. Close connections gracefully
4. Exit cleanly

### Safe Mode Activation
If drawdown exceeds 25%, the bot automatically:
- Halts all trading
- Cancels pending orders
- Logs emergency shutdown
- Waits for manual intervention

### Manual Position Close
```python
# In Python console
from src.exchange.imc_client import IMCExchangeClient
import asyncio

async def close_all():
    async with IMCExchangeClient(...) as client:
        positions = await client.get_positions()
        for symbol, pos in positions.items():
            # Submit closing orders
            ...

asyncio.run(close_all())
```

## 📞 Support

For issues or questions:
1. Check logs in `logs/` directory
2. Review configuration in `config.yaml`
3. Run test suite: `pytest tests/ -v`
4. Check exchange status at IMC URL

## 📄 License

This project is developed for the IMC Munich ETF Challenge at HackaTUM 2025.

## 🙏 Acknowledgments

- IMC Trading for hosting the challenge
- HackaTUM organizers
- OpenWeatherMap and OpenSky Network for data APIs

---

**Ready to trade? Run `python scripts/test_exchange.py` to verify your setup!**
