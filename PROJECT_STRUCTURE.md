# IMC Trading Bot - Project Structure

## Essential Files

### Configuration
- `config.yaml` - Main configuration (strategy, risk, data sources)
- `.env` - Environment variables (API keys, credentials)
- `.env.template` - Template for environment setup

### Documentation
- `README.md` - Setup instructions and usage guide
- `PRODUCTION_READY.md` - Production deployment checklist
- `PROJECT_STRUCTURE.md` - This file

### Core Directories
```
src/
├── data/           # Data ingestion (weather, flights, air quality)
├── signals/        # Feature engineering and signal generation
├── strategy/       # Regime detection and adaptive strategy
├── risk/           # Risk management and position limits
├── exchange/       # IMC exchange client and order management
├── monitoring/     # Logging, metrics, and reporting
├── backtest/       # Backtesting engine
├── visualization/  # Streamlit dashboard
└── utils/          # Configuration, types, helpers

tests/
├── unit/           # Unit tests
├── property/       # Property-based tests (Hypothesis)
└── integration/    # Integration tests

scripts/
├── test_exchange.py          # Exchange integration test suite
├── run_backtest.py           # Backtest execution
└── generate_presentation.py  # Presentation materials

docs/
├── ARCHITECTURE.md           # System architecture
├── QUICK_REFERENCE.md        # Quick command reference
├── START_HERE.md             # Getting started guide
├── WINNING_STRATEGY.md       # Strategy explanation
├── hackathon.md              # Hackathon context
└── presentation/             # Presentation materials
```

## Quick Commands

```bash
# Setup
pip install -r requirements.txt

# Test exchange connection
python scripts/test_exchange.py

# Run bot
python src/main.py --mode live

# Run backtest
python scripts/run_backtest.py

# Launch dashboard
streamlit run src/visualization/dashboard.py

# Run tests
pytest tests/ -v
```

## Key Configuration Files

### config.yaml
- Strategy parameters (signal thresholds, regime weights)
- Risk management (position limits, drawdown thresholds)
- Data sources (update intervals, API endpoints)
- Exchange settings (instruments, position limits)

### .env
- `IMC_EXCHANGE_URL` - Exchange URL
- `IMC_USERNAME` - Team username
- `IMC_PASSWORD` - Team password
- `OPENWEATHER_API_KEY` - Weather data API key

## Production Deployment

See `PRODUCTION_READY.md` for complete checklist.

Quick steps:
1. Update `.env` with production URL
2. Run `python scripts/test_exchange.py`
3. Start bot: `python src/main.py --mode live`
4. Monitor: `streamlit run src/visualization/dashboard.py`
