"""
Run comprehensive backtest and validate strategy performance.

This script:
1. Generates synthetic historical market data with realistic characteristics
2. Generates corresponding signals based on the strategy
3. Runs backtest with the implemented strategy
4. Validates performance against targets
5. Generates detailed report with regime breakdown
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
import numpy as np
from loguru import logger

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.types import MarketData, Signal
from src.backtest.engine import Backtester
from src.signals.generator import SignalGenerator
from src.signals.features import FeatureEngineer
from src.strategy.regime import RegimeDetector
from src.utils.config import load_config


class HistoricalDataGenerator:
    """Generate realistic synthetic historical market data."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with random seed for reproducibility."""
        np.random.seed(seed)
        self.regime_detector = RegimeDetector()
    
    def generate_market_data(
        self,
        symbol: str,
        num_days: int = 90,
        initial_price: float = 100.0,
        volatility: float = 0.02
    ) -> List[MarketData]:
        """
        Generate synthetic market data with regime changes.
        
        Args:
            symbol: Instrument symbol
            num_days: Number of days to generate
            initial_price: Starting price
            volatility: Base volatility (daily)
            
        Returns:
            List of MarketData objects in chronological order
        """
        logger.info(f"Generating {num_days} days of market data for {symbol}")
        
        # Generate timestamps (hourly data)
        start_time = datetime.now() - timedelta(days=num_days)
        timestamps = [start_time + timedelta(hours=i) for i in range(num_days * 24)]
        
        # Generate price series with regime changes
        prices = self._generate_price_series(
            initial_price, len(timestamps), volatility
        )
        
        # Generate market data objects
        market_data = []
        returns_history = []
        
        for i, (timestamp, price) in enumerate(zip(timestamps, prices)):
            # Calculate return
            if i > 0:
                ret = (price - prices[i-1]) / prices[i-1]
                returns_history.append(ret)
            
            # Generate bid-ask spread (0.1% of price)
            spread = price * 0.001
            bid = price - spread / 2
            ask = price + spread / 2
            
            # Generate volume (random with some correlation to volatility)
            volume = np.random.lognormal(10, 1)
            
            # Create market data
            data = MarketData(
                timestamp=timestamp,
                symbol=symbol,
                price=price,
                volume=volume,
                bid=bid,
                ask=ask,
                returns=returns_history[-100:] if len(returns_history) >= 100 else returns_history.copy()
            )
            
            market_data.append(data)
        
        logger.info(f"Generated {len(market_data)} market data points")
        return market_data
    
    def _generate_price_series(
        self,
        initial_price: float,
        num_points: int,
        base_volatility: float
    ) -> np.ndarray:
        """
        Generate price series with multiple market regimes.
        
        Creates realistic price movements with:
        - Trending periods
        - Mean-reverting periods
        - High/low volatility periods
        """
        prices = np.zeros(num_points)
        prices[0] = initial_price
        
        # Define regime periods (each regime lasts ~20% of total period)
        regime_length = num_points // 5
        
        # Regime 1: Trending up with low volatility
        for i in range(1, min(regime_length, num_points)):
            drift = 0.0002  # Positive drift
            vol = base_volatility * 0.5  # Low volatility
            prices[i] = prices[i-1] * (1 + drift + np.random.normal(0, vol))
        
        # Regime 2: Mean-reverting with normal volatility
        mean_price = prices[regime_length - 1] if regime_length < num_points else initial_price
        for i in range(regime_length, min(2 * regime_length, num_points)):
            mean_reversion = 0.05 * (mean_price - prices[i-1]) / mean_price
            vol = base_volatility
            prices[i] = prices[i-1] * (1 + mean_reversion + np.random.normal(0, vol))
        
        # Regime 3: High volatility, no clear trend
        for i in range(2 * regime_length, min(3 * regime_length, num_points)):
            vol = base_volatility * 2.0  # High volatility
            prices[i] = prices[i-1] * (1 + np.random.normal(0, vol))
        
        # Regime 4: Trending down with normal volatility
        for i in range(3 * regime_length, min(4 * regime_length, num_points)):
            drift = -0.0001  # Negative drift
            vol = base_volatility
            prices[i] = prices[i-1] * (1 + drift + np.random.normal(0, vol))
        
        # Regime 5: Low volatility, slight uptrend
        for i in range(4 * regime_length, num_points):
            drift = 0.0001
            vol = base_volatility * 0.3  # Very low volatility
            prices[i] = prices[i-1] * (1 + drift + np.random.normal(0, vol))
        
        return prices
    
    def generate_munich_data(
        self,
        timestamps: List[datetime]
    ) -> List[Dict[str, Any]]:
        """
        Generate synthetic Munich city data (weather, air quality, flights).
        
        Args:
            timestamps: List of timestamps to generate data for
            
        Returns:
            List of Munich data dictionaries
        """
        logger.info(f"Generating Munich data for {len(timestamps)} timestamps")
        
        munich_data = []
        
        for timestamp in timestamps:
            # Generate weather data with daily and seasonal patterns
            hour = timestamp.hour
            day_of_year = timestamp.timetuple().tm_yday
            
            # Temperature: seasonal + daily variation
            base_temp = 10 + 15 * np.sin(2 * np.pi * day_of_year / 365)  # Seasonal
            daily_variation = 5 * np.sin(2 * np.pi * hour / 24)  # Daily
            temperature = base_temp + daily_variation + np.random.normal(0, 2)
            
            # Weather data
            weather = {
                'temperature': temperature,
                'feels_like': temperature - 2,
                'humidity': max(0.0, min(100.0, 50 + np.random.normal(0, 15))),
                'pressure': max(900.0, 1013 + np.random.normal(0, 10)),
                'wind_speed': max(0.0, 5 + np.random.normal(0, 3)),
                'wind_direction': np.random.uniform(0, 360),
                'cloud_coverage': max(0.0, min(100.0, 50 + np.random.normal(0, 30))),
                'rain_volume': max(0.0, np.random.exponential(0.5)),
                'snow_volume': 0.0
            }
            
            # Air quality data
            air_quality = {
                'aqi': np.random.randint(1, 6),  # 1-5 scale (randint is exclusive of upper bound)
                'co': max(0.0, 200 + np.random.normal(0, 50)),
                'no2': max(0.0, 30 + np.random.normal(0, 10)),
                'o3': max(0.0, 50 + np.random.normal(0, 15)),
                'pm2_5': max(0.0, 15 + np.random.normal(0, 5)),
                'pm10': max(0.0, 25 + np.random.normal(0, 8))
            }
            
            # Flight data (more flights during day, fewer at night)
            if 6 <= hour <= 22:
                base_flights = 50
            else:
                base_flights = 10
            
            flights = {
                'active_flights': int(max(0, base_flights + np.random.normal(0, 10))),
                'departures': int(max(0, 5 + np.random.normal(0, 3))),
                'arrivals': int(max(0, 5 + np.random.normal(0, 3))),
                'avg_delay': max(0.0, np.random.exponential(5))
            }
            
            munich_data.append({
                'timestamp': timestamp,
                'weather': weather,
                'air_quality': air_quality,
                'flights': flights
            })
        
        return munich_data


async def generate_signals_from_data(
    market_data: List[MarketData],
    munich_data: List[Dict[str, Any]],
    config: Dict[str, Any]
) -> List[Signal]:
    """
    Generate trading signals from market and Munich data.
    
    Args:
        market_data: Historical market data
        munich_data: Historical Munich city data
        config: Configuration dictionary
        
    Returns:
        List of Signal objects
    """
    from src.utils.types import CityData, WeatherData, AirQualityData, FlightData
    from src.signals.combiner import SignalCombiner
    
    logger.info("Generating signals from historical data")
    
    # Initialize components with correct parameters
    feature_engineer = FeatureEngineer(window_size=config['features']['weather_momentum_period'])
    signal_generator = SignalGenerator()  # Uses default weights
    signal_combiner = SignalCombiner(config)
    regime_detector = RegimeDetector()
    
    signals = []
    
    for i, (mkt_data, mun_data) in enumerate(zip(market_data, munich_data)):
        # Skip first few points (need history for features)
        if i < 30:
            continue
        
        # Detect regime
        if len(mkt_data.returns) >= 30:
            regime = regime_detector.detect(mkt_data.returns)
        else:
            regime = 'uncertain'
        
        # Convert dict to CityData object
        city_data = CityData(
            timestamp=mun_data['timestamp'],
            location='Munich,DE',
            weather=WeatherData(**mun_data['weather']),
            air_quality=AirQualityData(**mun_data['air_quality']),
            flights=FlightData(**mun_data['flights'])
        )
        
        # Compute features
        features = feature_engineer.compute_features(city_data)
        
        # Generate individual signals
        individual_signals = signal_generator.generate(features)
        
        # Combine signals based on regime (returns a Signal object)
        signal = signal_combiner.combine(individual_signals, regime)
        
        # Update timestamp to match market data
        signal.timestamp = mkt_data.timestamp
        
        signals.append(signal)
    
    logger.info(f"Generated {len(signals)} signals")
    return signals


async def run_backtest_validation():
    """Run comprehensive backtest and validate performance."""
    logger.info("=" * 80)
    logger.info("BACKTEST VALIDATION - IMC Trading Bot")
    logger.info("=" * 80)
    
    # Load configuration
    config = load_config()
    
    # Initialize data generator
    data_gen = HistoricalDataGenerator(seed=42)
    
    # Generate historical market data (90 days, hourly)
    logger.info("\n[1/5] Generating historical market data...")
    market_data = data_gen.generate_market_data(
        symbol='7_ETF',  # Munich ETF
        num_days=90,
        initial_price=100.0,
        volatility=0.02
    )
    
    # Generate Munich city data
    logger.info("\n[2/5] Generating Munich city data...")
    timestamps = [data.timestamp for data in market_data]
    munich_data = data_gen.generate_munich_data(timestamps)
    
    # Generate signals
    logger.info("\n[3/5] Generating trading signals...")
    signals = await generate_signals_from_data(market_data, munich_data, config)
    
    # Run backtest
    logger.info("\n[4/5] Running backtest...")
    backtester = Backtester(
        initial_capital=config['backtest']['initial_capital'],
        slippage_bps=config['backtest']['slippage'] * 10000,
        commission_bps=config['backtest']['commission'] * 10000
    )
    
    results = await backtester.run(market_data, signals)
    
    # Validate performance
    logger.info("\n[5/5] Validating performance targets...")
    validation_results = validate_performance(results, config['targets'])
    
    # Print detailed report
    print_backtest_report(results, validation_results)
    
    # Save results
    save_backtest_results(results, validation_results)
    
    return results, validation_results


def validate_performance(
    results: Dict[str, Any],
    targets: Dict[str, float]
) -> Dict[str, bool]:
    """
    Validate backtest results against performance targets.
    
    Args:
        results: Backtest results
        targets: Performance targets from config
        
    Returns:
        Dictionary of validation results
    """
    validation = {
        'sharpe_ratio': results['sharpe_ratio'] >= targets['sharpe_ratio'],
        'max_drawdown': abs(results['max_drawdown']) <= targets['max_drawdown'],
        'win_rate': results['win_rate'] >= targets['win_rate'],
        'positive_pnl': results['total_pnl'] > 0,
        'all_regimes_positive': True  # Will check below
    }
    
    # Check if all regimes have positive PnL
    for regime, metrics in results.get('regime_breakdown', {}).items():
        if metrics['pnl'] <= 0:
            validation['all_regimes_positive'] = False
            logger.warning(f"Regime '{regime}' has negative PnL: ${metrics['pnl']:.2f}")
    
    # Overall validation
    validation['passed'] = all([
        validation['sharpe_ratio'],
        validation['max_drawdown'],
        validation['win_rate'],
        validation['positive_pnl']
    ])
    
    return validation


def print_backtest_report(
    results: Dict[str, Any],
    validation: Dict[str, bool]
):
    """Print comprehensive backtest report."""
    print("\n" + "=" * 80)
    print("BACKTEST RESULTS")
    print("=" * 80)
    
    # Overall Performance
    print("\n[OVERALL PERFORMANCE]")
    print("-" * 80)
    print(f"Total PnL:           ${results['total_pnl']:>15,.2f}")
    print(f"Total Return:        {results['total_return']:>15.2%}")
    print(f"Sharpe Ratio:        {results['sharpe_ratio']:>15.2f}  {'[PASS]' if validation['sharpe_ratio'] else '[FAIL]'}")
    print(f"Max Drawdown:        {results['max_drawdown']:>15.2%}  {'[PASS]' if validation['max_drawdown'] else '[FAIL]'}")
    print(f"Win Rate:            {results['win_rate']:>15.2%}  {'[PASS]' if validation['win_rate'] else '[FAIL]'}")
    print(f"Total Trades:        {results['total_trades']:>15,}")
    print(f"Final Equity:        ${results['final_equity']:>15,.2f}")
    
    # Regime Breakdown
    print("\n[PERFORMANCE BY REGIME]")
    print("-" * 80)
    print(f"{'Regime':<20} {'Trades':>10} {'PnL':>15} {'Win Rate':>12}")
    print("-" * 80)
    
    for regime, metrics in results.get('regime_breakdown', {}).items():
        pnl_str = f"${metrics['pnl']:,.2f}"
        win_rate_str = f"{metrics['win_rate']:.1%}"
        status = '[+]' if metrics['pnl'] > 0 else '[-]'
        print(f"{regime:<20} {metrics['trades']:>10} {pnl_str:>15} {win_rate_str:>12} {status}")
    
    # Validation Summary
    print("\n[VALIDATION SUMMARY]")
    print("-" * 80)
    print(f"Sharpe Ratio Target:     {'PASS' if validation['sharpe_ratio'] else 'FAIL'}")
    print(f"Max Drawdown Target:     {'PASS' if validation['max_drawdown'] else 'FAIL'}")
    print(f"Win Rate Target:         {'PASS' if validation['win_rate'] else 'FAIL'}")
    print(f"Positive PnL:            {'PASS' if validation['positive_pnl'] else 'FAIL'}")
    print(f"All Regimes Positive:    {'PASS' if validation['all_regimes_positive'] else 'FAIL'}")
    print("-" * 80)
    print(f"OVERALL:                 {'PASS' if validation['passed'] else 'FAIL'}")
    
    # Regime Changes
    if results.get('regime_changes'):
        print(f"\n[REGIME CHANGES]: {len(results['regime_changes'])} transitions")
        print("-" * 80)
        for timestamp, old_regime, new_regime in results['regime_changes'][:10]:
            print(f"{timestamp.strftime('%Y-%m-%d %H:%M')} | {old_regime:>15} -> {new_regime:<15}")
        if len(results['regime_changes']) > 10:
            print(f"... and {len(results['regime_changes']) - 10} more")
    
    print("\n" + "=" * 80)


def save_backtest_results(
    results: Dict[str, Any],
    validation: Dict[str, bool]
):
    """Save backtest results to file."""
    import json
    from pathlib import Path
    
    # Create reports directory if it doesn't exist
    reports_dir = Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    # Prepare results for JSON serialization
    serializable_results = {
        'timestamp': datetime.now().isoformat(),
        'performance': {
            'total_pnl': float(results['total_pnl']),
            'total_return': float(results['total_return']),
            'sharpe_ratio': float(results['sharpe_ratio']),
            'max_drawdown': float(results['max_drawdown']),
            'win_rate': float(results['win_rate']),
            'total_trades': int(results['total_trades']),
            'final_equity': float(results['final_equity'])
        },
        'regime_breakdown': {
            regime: {
                'trades': int(metrics['trades']),
                'pnl': float(metrics['pnl']),
                'win_rate': float(metrics['win_rate'])
            }
            for regime, metrics in results.get('regime_breakdown', {}).items()
        },
        'validation': {k: bool(v) for k, v in validation.items()},
        'regime_changes_count': len(results.get('regime_changes', []))
    }
    
    # Save to file
    output_file = reports_dir / f"backtest_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(serializable_results, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")


if __name__ == '__main__':
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # Run backtest
    try:
        results, validation = asyncio.run(run_backtest_validation())
        
        # Exit with appropriate code
        if validation['passed']:
            logger.success("✅ Backtest validation PASSED!")
            sys.exit(0)
        else:
            logger.error("❌ Backtest validation FAILED!")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Backtest failed with error: {e}")
        sys.exit(1)
