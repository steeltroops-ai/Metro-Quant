@echo off
REM IMC Trading Bot - Quick Setup Script (Windows)

echo 🚀 Setting up IMC Trading Bot - Turbo Stack
echo ============================================

REM Check Python version
echo 📋 Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ❌ Python not found. Please install Python 3.10+
    exit /b 1
)
echo ✅ Python detected

REM Create virtual environment
echo.
echo 📦 Creating virtual environment...
python -m venv venv
echo ✅ Virtual environment created

REM Activate virtual environment
echo.
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

REM Upgrade pip
echo.
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip setuptools wheel
echo ✅ Pip upgraded

REM Install requirements
echo.
echo 📥 Installing turbo stack dependencies...
pip install -r requirements.txt
echo ✅ Dependencies installed

REM Create directory structure
echo.
echo 📁 Creating project structure...
mkdir src\data src\signals src\strategy src\risk src\exchange src\monitoring src\backtest src\visualization src\utils 2>nul
mkdir data\raw data\processed data\historical data\cache 2>nul
mkdir notebooks 2>nul
mkdir tests\unit tests\property tests\integration 2>nul
mkdir docs\presentation docs\diagrams 2>nul
mkdir scripts 2>nul

REM Create __init__.py files
echo. > src\__init__.py
echo. > src\data\__init__.py
echo. > src\signals\__init__.py
echo. > src\strategy\__init__.py
echo. > src\risk\__init__.py
echo. > src\exchange\__init__.py
echo. > src\monitoring\__init__.py
echo. > src\backtest\__init__.py
echo. > src\visualization\__init__.py
echo. > src\utils\__init__.py
echo. > tests\__init__.py
echo. > tests\unit\__init__.py
echo. > tests\property\__init__.py
echo. > tests\integration\__init__.py

echo ✅ Project structure created

REM Create .env template
echo.
echo 🔐 Creating .env template...
(
echo # API Keys
echo OPENWEATHER_API_KEY=your_openweather_key_here
echo EXCHANGE_URL=wss://imc-exchange.com
echo EXCHANGE_API_KEY=your_exchange_key_here
echo.
echo # Configuration
echo LOG_LEVEL=INFO
echo CACHE_TTL=300
echo MAX_WORKERS=4
) > .env
echo ✅ .env template created

REM Create config.yaml
echo.
echo ⚙️  Creating config.yaml...
(
echo # IMC Trading Bot Configuration
echo.
echo api:
echo   openweather:
echo     base_url: "https://api.openweathermap.org/data/2.5"
echo     timeout: 5
echo   opensky:
echo     base_url: "https://opensky-network.org/api"
echo     timeout: 10
echo.
echo strategy:
echo   signal_threshold: 0.3
echo   confidence_threshold: 0.5
echo   kalman:
echo     process_variance: 0.01
echo     measurement_variance: 0.1
echo   obi:
echo     threshold: 0.3
echo     depth_levels: 5
echo.
echo risk:
echo   max_position_size: 0.20
echo   max_total_exposure: 0.80
echo   max_drawdown_warning: 0.15
echo   max_drawdown_halt: 0.25
) > config.yaml
echo ✅ config.yaml created

echo.
echo ============================================
echo ✅ Setup complete!
echo.
echo Next steps:
echo 1. Activate environment: venv\Scripts\activate.bat
echo 2. Edit .env with your API keys
echo 3. Start coding: code .
echo.
echo Quick commands:
echo   - Run tests: pytest tests/ -v
echo   - Launch dashboard: streamlit run src/dashboard.py
echo   - Run bot: python src/main.py --mode live
echo.
echo Good luck! 🚀

pause
