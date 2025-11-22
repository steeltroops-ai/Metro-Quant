# IMC Munich ETF Trading Bot

An adaptive algorithmic trading bot for the IMC Munich ETF Challenge at HackaTUM 2025.

## Features

- **Real-time Munich data ingestion**: Weather, air quality, and flight activity
- **Adaptive strategy**: Regime detection with HMM and dynamic parameter adjustment
- **Advanced signal processing**: Kalman filtering and order book imbalance analysis
- **Robust risk management**: Position limits, drawdown controls, and safe mode
- **Live monitoring**: Streamlit dashboard with real-time metrics
- **High performance**: Sub-100ms latency with async architecture and Numba JIT

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
cp .env.template .env

# Edit .env and add your API keys
# Get OpenWeatherMap API key: https://openweathermap.org/api
```

### 3. Run the Bot

```bash
# Run in live trading mode
python src/main.py --mode live --config config.yaml

# Run backtest
python src/backtest.py --data data/historical/market_data.parquet

# Launch monitoring dashboard
streamlit run src/dashboard.py
```

## Project Structure

```
src/
├── data/           # Data ingestion (async API clients)
├── signals/        # Signal processing and feature engineering
├── strategy/       # Regime detection and adaptive strategy
├── risk/           # Risk management and position limits
├── exchange/       # Order execution and position tracking
├── monitoring/     # Logging and metrics
├── backtest/       # Backtesting engine
├── visualization/  # Charts and dashboards
└── utils/          # Configuration and utilities

data/
├── raw/           # Raw API responses
├── processed/     # Processed features
├── historical/    # Historical market data
└── cache/         # Cached data

tests/
├── unit/          # Unit tests
├── property/      # Property-based tests (Hypothesis)
└── integration/   # Integration tests
```

## Architecture

The bot follows a layered architecture with clear separation of concerns:

1. **Data Ingestion Layer**: Async API clients for Munich data sources
2. **Signal Processing Layer**: Feature engineering with Kalman filtering
3. **Strategy Layer**: Regime detection and adaptive parameter selection
4. **Risk Management Layer**: Position limits and drawdown controls
5. **Execution Layer**: Order management and exchange communication
6. **Monitoring Layer**: Structured logging and metrics collection

## Configuration

Edit `config.yaml` to customize:

- API endpoints and update intervals
- Strategy parameters and signal weights
- Risk management thresholds
- Regime detection parameters
- Feature engineering settings

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only
pytest tests/unit/ -v

# Run property-based tests
pytest tests/property/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Performance Targets

- **Sharpe Ratio**: > 1.5
- **Max Drawdown**: < 20%
- **Win Rate**: > 55%
- **Latency**: < 100ms (data → signal → order)

## Development

### Code Style

- Follow PEP 8 style guide
- Use type hints throughout
- Document all public functions
- Keep functions focused and testable

### Adding New Features

1. Create module in appropriate `src/` subdirectory
2. Add corresponding tests in `tests/`
3. Update configuration if needed
4. Document in module docstring

## License

MIT License - See LICENSE file for details

## Authors

HackaTUM 2025 Team
