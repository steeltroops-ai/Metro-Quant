#!/bin/bash
# IMC Trading Bot - Quick Setup Script

set -e  # Exit on error

echo "🚀 Setting up IMC Trading Bot - Turbo Stack"
echo "============================================"

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.10"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.10+ required. Found: $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo ""
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip setuptools wheel
echo "✅ Pip upgraded"

# Install requirements
echo ""
echo "📥 Installing turbo stack dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create directory structure
echo ""
echo "📁 Creating project structure..."
mkdir -p src/{data,signals,strategy,risk,exchange,monitoring,backtest,visualization,utils}
mkdir -p data/{raw,processed,historical,cache}
mkdir -p notebooks
mkdir -p tests/{unit,property,integration}
mkdir -p docs/{presentation,diagrams}
mkdir -p scripts

# Create __init__.py files
find src -type d -exec touch {}/__init__.py \;
find tests -type d -exec touch {}/__init__.py \;

echo "✅ Project structure created"

# Create .env template
echo ""
echo "🔐 Creating .env template..."
cat > .env << 'EOF'
# API Keys
OPENWEATHER_API_KEY=your_openweather_key_here
EXCHANGE_URL=wss://imc-exchange.com
EXCHANGE_API_KEY=your_exchange_key_here

# Configuration
LOG_LEVEL=INFO
CACHE_TTL=300
MAX_WORKERS=4
EOF
echo "✅ .env template created"

# Create config.yaml
echo ""
echo "⚙️  Creating config.yaml..."
cat > config.yaml << 'EOF'
# IMC Trading Bot Configuration

api:
  openweather:
    base_url: "https://api.openweathermap.org/data/2.5"
    timeout: 5
  opensky:
    base_url: "https://opensky-network.org/api"
    timeout: 10

strategy:
  signal_threshold: 0.3
  confidence_threshold: 0.5
  
  # Kalman Filter parameters
  kalman:
    process_variance: 0.01
    measurement_variance: 0.1
  
  # Order Book Imbalance
  obi:
    threshold: 0.3
    depth_levels: 5
  
  # Regime detection
  regime:
    volatility_window: 20
    trend_fast_ma: 10
    trend_slow_ma: 50

risk:
  max_position_size: 0.20      # 20% per position
  max_total_exposure: 0.80     # 80% total
  max_drawdown_warning: 0.15   # 15% warning
  max_drawdown_halt: 0.25      # 25% halt trading
  
  # Position sizing
  base_size: 0.10
  confidence_multiplier: 1.0

performance:
  target_sharpe: 1.5
  target_win_rate: 0.55
  max_acceptable_drawdown: 0.20

monitoring:
  log_level: INFO
  metrics_port: 8000
  dashboard_port: 8501
EOF
echo "✅ config.yaml created"

# Create .gitignore
echo ""
echo "🚫 Creating .gitignore..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Data
data/raw/*
data/cache/*
*.parquet
*.csv
*.json

# Secrets
.env
*.key
*.pem

# IDE
.vscode/
.idea/
*.swp
*.swo

# Jupyter
.ipynb_checkpoints/
*.ipynb

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Testing
.coverage
htmlcov/
.pytest_cache/

# Build
dist/
build/
*.egg-info/
EOF
echo "✅ .gitignore created"

# Create README
echo ""
echo "📝 Creating README.md..."
cat > README.md << 'EOF'
# 🚀 IMC Trading Bot - Munich ETF Challenge

High-performance algorithmic trading bot for the IMC Munich ETF Challenge.

## Features

- **Async Architecture**: Non-blocking I/O with asyncio
- **Turbo Stack**: Polars (10x faster), Numba JIT (100x faster)
- **Kalman Filters**: Zero-lag signal smoothing
- **Order Book Imbalance**: Microstructure alpha
- **HMM Regime Detection**: Adaptive strategy
- **Live Dashboard**: Real-time Streamlit visualization

## Quick Start

```bash
# Setup (5 minutes)
./setup.sh

# Activate environment
source venv/bin/activate

# Configure API keys
nano .env

# Run data exploration
jupyter notebook notebooks/01_data_exploration.ipynb

# Run backtest
python src/backtest/engine.py

# Launch live dashboard
streamlit run src/dashboard.py

# Run live bot
python src/main.py --mode live
```

## Tech Stack

- Python 3.10+
- Polars (data processing)
- Numba (JIT compilation)
- Kalman Filters (signal smoothing)
- HMM (regime detection)
- Streamlit (live dashboard)
- Hypothesis (property testing)

## Architecture

```
Data Sources → Async Clients → Kalman Filter → Signal Generator
                                                      ↓
                                              Regime Detector
                                                      ↓
                                            Adaptive Strategy + OBI
                                                      ↓
                                              Risk Manager
                                                      ↓
                                              Order Manager
                                                      ↓
                                          Exchange + Dashboard
```

## Performance Targets

- Latency: < 100ms (data → order)
- Sharpe Ratio: > 1.5
- Max Drawdown: < 20%
- Win Rate: > 55%

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run property tests only
pytest tests/property/ -v
```

## Team

Built for HackaTUM 2025 - IMC Munich ETF Challenge
EOF
echo "✅ README.md created"

echo ""
echo "============================================"
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Activate environment: source venv/bin/activate"
echo "2. Edit .env with your API keys"
echo "3. Start coding: code ."
echo ""
echo "Quick commands:"
echo "  - Run tests: pytest tests/ -v"
echo "  - Launch dashboard: streamlit run src/dashboard.py"
echo "  - Run bot: python src/main.py --mode live"
echo ""
echo "Good luck! 🚀"
