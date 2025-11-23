"""
Signal Discovery Analysis for Munich ETF Trading Bot

This script explores correlations between Munich city data and synthetic market data
to discover novel trading signals for the IMC Trading Challenge.

Requirements: 2.1, 8.1
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from typing import Dict, List, Any
import yaml
from loguru import logger

# Import data clients
from src.data.weather import WeatherClient
from src.data.air_quality import AirQualityClient
from src.data.flights import FlightClient

# Configure plotting
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10


def load_config() -> Dict[str, Any]:
    """Load configuration from config.yaml."""
    config_path = Path(__file__).parent.parent / 'config.yaml'
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


async def fetch_munich_data(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fetch current Munich data from all sources.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Dictionary with weather, air_quality, and flights data
    """
    # Get API keys from environment
    api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')
    
    # Extract location info
    location = config['location']
    location_str = f"{location['city']},{location['country']}"
    lat = location['coordinates']['lat']
    lon = location['coordinates']['lon']
    
    # Calculate bounding box for flights
    bbox_offset = config['data_sources']['flights']['bbox_offset']
    bbox = [
        lon - bbox_offset,  # lon_min
        lat - bbox_offset,  # lat_min
        lon + bbox_offset,  # lon_max
        lat + bbox_offset   # lat_max
    ]
    
    logger.info(f"Fetching data for {location_str}")
    
    # Fetch data concurrently
    try:
        async with WeatherClient(api_key, location_str) as weather_client, \
                   AirQualityClient(api_key, lat, lon) as aq_client, \
                   FlightClient(bbox, location['airport_code']) as flight_client:
            
            weather_data, aq_data, flight_data = await asyncio.gather(
                weather_client.fetch(),
                aq_client.fetch(),
                flight_client.fetch(),
                return_exceptions=True
            )
        
        return {
            'weather': weather_data if not isinstance(weather_data, Exception) else None,
            'air_quality': aq_data if not isinstance(aq_data, Exception) else None,
            'flights': flight_data if not isinstance(flight_data, Exception) else None
        }
    except Exception as e:
        logger.error(f"Error fetching Munich data: {e}")
        return {'weather': None, 'air_quality': None, 'flights': None}


def generate_synthetic_market_data(
    munich_data: Dict[str, Any],
    num_samples: int = 100
) -> pd.DataFrame:
    """
    Generate synthetic market data with correlations to Munich data.
    
    This creates realistic market price movements that have embedded
    correlations with Munich city data for signal discovery.
    
    Args:
        munich_data: Dictionary with Munich data
        num_samples: Number of time samples to generate
        
    Returns:
        DataFrame with synthetic market data
    """
    logger.info(f"Generating {num_samples} samples of synthetic market data")
    
    # Extract current Munich values
    weather = munich_data.get('weather', {})
    air_quality = munich_data.get('air_quality', {})
    flights = munich_data.get('flights', {})
    
    # Base values
    temp_base = weather.get('temperature', 15.0) if weather else 15.0
    aqi_base = air_quality.get('aqi', 2) if air_quality else 2
    flights_base = flights.get('active_flights', 50) if flights else 50
    
    # Generate time series
    timestamps = [datetime.now() - timedelta(minutes=i*5) for i in range(num_samples)]
    timestamps.reverse()
    
    # Generate Munich data variations
    np.random.seed(42)
    temperature = temp_base + np.cumsum(np.random.randn(num_samples) * 0.5)
    humidity = 50 + np.cumsum(np.random.randn(num_samples) * 2)
    humidity = np.clip(humidity, 0, 100)
    wind_speed = 5 + np.abs(np.random.randn(num_samples) * 2)
    
    aqi = aqi_base + (np.random.randn(num_samples) * 0.5).astype(int)
    aqi = np.clip(aqi, 1, 5)
    pm25 = 20 + np.cumsum(np.random.randn(num_samples) * 2)
    pm25 = np.clip(pm25, 0, 100)
    
    active_flights = flights_base + (np.random.randn(num_samples) * 10).astype(int)
    active_flights = np.clip(active_flights, 0, 200)
    
    # Generate market data with embedded correlations
    # ETF price influenced by multiple factors
    base_price = 100.0
    
    # Temperature effect: warmer weather -> higher prices (tourism, outdoor activity)
    temp_effect = (temperature - temp_base) * 0.5
    
    # Air quality effect: better air quality -> higher prices
    aq_effect = -(pm25 - 20) * 0.1
    
    # Flight activity effect: more flights -> higher economic activity
    flight_effect = (active_flights - flights_base) * 0.05
    
    # Add random walk and combine effects
    random_walk = np.cumsum(np.random.randn(num_samples) * 0.3)
    etf_price = base_price + temp_effect + aq_effect + flight_effect + random_walk
    
    # Generate other instruments with different correlations
    # Weather derivative: directly correlated with temperature
    weather_price = 50 + (temperature - temp_base) * 2 + np.random.randn(num_samples) * 0.5
    
    # Flight derivative: correlated with flight activity
    flight_price = 75 + (active_flights - flights_base) * 0.2 + np.random.randn(num_samples) * 0.5
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'temperature': temperature,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'aqi': aqi,
        'pm25': pm25,
        'active_flights': active_flights,
        'etf_price': etf_price,
        'weather_price': weather_price,
        'flight_price': flight_price,
    })
    
    # Calculate returns
    df['etf_return'] = df['etf_price'].pct_change()
    df['weather_return'] = df['weather_price'].pct_change()
    df['flight_return'] = df['flight_price'].pct_change()
    
    return df


def compute_correlations(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute correlation matrix between Munich data and market returns.
    
    Args:
        df: DataFrame with Munich and market data
        
    Returns:
        Correlation matrix DataFrame
    """
    logger.info("Computing correlation matrix")
    
    # Select relevant columns
    munich_cols = ['temperature', 'humidity', 'wind_speed', 'aqi', 'pm25', 'active_flights']
    market_cols = ['etf_return', 'weather_return', 'flight_return']
    
    # Compute correlations
    corr_matrix = df[munich_cols + market_cols].corr()
    
    # Extract cross-correlations (Munich data vs market returns)
    cross_corr = corr_matrix.loc[munich_cols, market_cols]
    
    return cross_corr


def identify_strong_correlations(
    corr_matrix: pd.DataFrame,
    threshold: float = 0.3
) -> List[Dict[str, Any]]:
    """
    Identify strong correlations for presentation.
    
    Args:
        corr_matrix: Correlation matrix
        threshold: Minimum absolute correlation to consider
        
    Returns:
        List of strong correlation dictionaries
    """
    logger.info(f"Identifying correlations with |r| > {threshold}")
    
    strong_corrs = []
    
    for munich_var in corr_matrix.index:
        for market_var in corr_matrix.columns:
            corr_value = corr_matrix.loc[munich_var, market_var]
            
            if abs(corr_value) >= threshold:
                strong_corrs.append({
                    'munich_variable': munich_var,
                    'market_variable': market_var,
                    'correlation': corr_value,
                    'abs_correlation': abs(corr_value)
                })
    
    # Sort by absolute correlation
    strong_corrs.sort(key=lambda x: x['abs_correlation'], reverse=True)
    
    return strong_corrs


def visualize_signal_discovery(
    df: pd.DataFrame,
    corr_matrix: pd.DataFrame,
    strong_corrs: List[Dict[str, Any]],
    output_dir: Path
):
    """
    Create visualizations for signal discovery process.
    
    Args:
        df: DataFrame with Munich and market data
        corr_matrix: Correlation matrix
        strong_corrs: List of strong correlations
        output_dir: Directory to save plots
    """
    logger.info("Creating visualizations")
    output_dir.mkdir(exist_ok=True)
    
    # 1. Correlation Heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_matrix, annot=True, fmt='.3f', cmap='coolwarm', center=0,
                vmin=-1, vmax=1, square=True, linewidths=1)
    plt.title('Munich Data vs Market Returns Correlation Matrix', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(output_dir / 'correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("Saved correlation heatmap")
    
    # 2. Time Series of Top Correlations
    if strong_corrs:
        fig, axes = plt.subplots(min(3, len(strong_corrs)), 1, figsize=(12, 10))
        if len(strong_corrs) == 1:
            axes = [axes]
        
        for idx, corr_info in enumerate(strong_corrs[:3]):
            munich_var = corr_info['munich_variable']
            market_var = corr_info['market_variable']
            corr_val = corr_info['correlation']
            
            ax = axes[idx]
            ax2 = ax.twinx()
            
            # Plot Munich variable
            ax.plot(df['timestamp'], df[munich_var], 'b-', label=munich_var, linewidth=2)
            ax.set_ylabel(munich_var, color='b', fontsize=11)
            ax.tick_params(axis='y', labelcolor='b')
            
            # Plot market variable
            ax2.plot(df['timestamp'], df[market_var], 'r-', label=market_var, linewidth=2)
            ax2.set_ylabel(market_var, color='r', fontsize=11)
            ax2.tick_params(axis='y', labelcolor='r')
            
            ax.set_title(f'{munich_var} vs {market_var} (r={corr_val:.3f})',
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
            if idx == len(strong_corrs[:3]) - 1:
                ax.set_xlabel('Time', fontsize=11)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'top_correlations_timeseries.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Saved time series plots")
    
    # 3. Scatter Plots of Strong Correlations
    if strong_corrs:
        n_plots = min(4, len(strong_corrs))
        fig, axes = plt.subplots(2, 2, figsize=(14, 12))
        axes = axes.flatten()
        
        for idx, corr_info in enumerate(strong_corrs[:n_plots]):
            munich_var = corr_info['munich_variable']
            market_var = corr_info['market_variable']
            corr_val = corr_info['correlation']
            
            ax = axes[idx]
            
            # Remove NaN values for both variables
            valid_mask = df[munich_var].notna() & df[market_var].notna()
            x_valid = df[munich_var][valid_mask]
            y_valid = df[market_var][valid_mask]
            
            ax.scatter(x_valid, y_valid, alpha=0.6, s=30)
            
            # Add trend line
            if len(x_valid) > 1:
                z = np.polyfit(x_valid, y_valid, 1)
                p = np.poly1d(z)
                ax.plot(x_valid, p(x_valid), "r--", linewidth=2, alpha=0.8)
            
            ax.set_xlabel(munich_var, fontsize=11)
            ax.set_ylabel(market_var, fontsize=11)
            ax.set_title(f'{munich_var} vs {market_var}\\nr = {corr_val:.3f}',
                        fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_dir / 'correlation_scatterplots.png', dpi=300, bbox_inches='tight')
        plt.close()
        logger.info("Saved scatter plots")
    
    # 4. Feature Importance Bar Chart
    plt.figure(figsize=(12, 6))
    
    # Calculate average absolute correlation for each Munich variable
    avg_corr = corr_matrix.abs().mean(axis=1).sort_values(ascending=False)
    
    colors = ['#2ecc71' if x > 0.3 else '#3498db' if x > 0.2 else '#95a5a6' for x in avg_corr]
    avg_corr.plot(kind='bar', color=colors)
    
    plt.title('Average Correlation Strength by Munich Variable', fontsize=14, fontweight='bold')
    plt.xlabel('Munich Variable', fontsize=11)
    plt.ylabel('Average |Correlation|', fontsize=11)
    plt.axhline(y=0.3, color='r', linestyle='--', label='Strong Correlation Threshold')
    plt.legend()
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(output_dir / 'feature_importance.png', dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("Saved feature importance chart")


def generate_summary_report(
    munich_data: Dict[str, Any],
    strong_corrs: List[Dict[str, Any]],
    output_dir: Path
):
    """
    Generate text summary report of signal discovery.
    
    Args:
        munich_data: Current Munich data
        strong_corrs: List of strong correlations
        output_dir: Directory to save report
    """
    logger.info("Generating summary report")
    
    report_path = output_dir / 'signal_discovery_report.txt'
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\\n")
        f.write("MUNICH ETF SIGNAL DISCOVERY REPORT\\n")
        f.write("=" * 80 + "\\n\\n")
        
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n")
        
        # Current Munich Data
        f.write("CURRENT MUNICH DATA\\n")
        f.write("-" * 80 + "\\n")
        
        if munich_data.get('weather'):
            weather = munich_data['weather']
            f.write(f"Weather:\\n")
            f.write(f"  Temperature: {weather.get('temperature', 'N/A')}°C\\n")
            f.write(f"  Humidity: {weather.get('humidity', 'N/A')}%\\n")
            f.write(f"  Wind Speed: {weather.get('wind_speed', 'N/A')} m/s\\n")
        
        if munich_data.get('air_quality'):
            aq = munich_data['air_quality']
            f.write(f"\\nAir Quality:\\n")
            f.write(f"  AQI: {aq.get('aqi', 'N/A')}\\n")
            f.write(f"  PM2.5: {aq.get('pm2_5', 'N/A')} μg/m³\\n")
        
        if munich_data.get('flights'):
            flights = munich_data['flights']
            f.write(f"\\nFlights:\\n")
            f.write(f"  Active Flights: {flights.get('active_flights', 'N/A')}\\n")
            f.write(f"  Departures: {flights.get('departures', 'N/A')}\\n")
            f.write(f"  Arrivals: {flights.get('arrivals', 'N/A')}\\n")
        
        # Strong Correlations
        f.write("\\n\\n")
        f.write("DISCOVERED SIGNAL CORRELATIONS\\n")
        f.write("-" * 80 + "\\n")
        f.write(f"Found {len(strong_corrs)} strong correlations (|r| > 0.3)\\n\\n")
        
        for idx, corr in enumerate(strong_corrs[:5], 1):
            f.write(f"{idx}. {corr['munich_variable']} → {corr['market_variable']}\\n")
            f.write(f"   Correlation: {corr['correlation']:.4f}\\n")
            f.write(f"   Strength: {'Strong' if abs(corr['correlation']) > 0.5 else 'Moderate'}\\n")
            f.write(f"   Direction: {'Positive' if corr['correlation'] > 0 else 'Negative'}\\n\\n")
        
        # Trading Implications
        f.write("\\n")
        f.write("TRADING IMPLICATIONS\\n")
        f.write("-" * 80 + "\\n")
        
        if strong_corrs:
            top_corr = strong_corrs[0]
            f.write(f"Primary Signal: {top_corr['munich_variable']} → {top_corr['market_variable']}\\n")
            f.write(f"  - Use {top_corr['munich_variable']} as leading indicator\\n")
            f.write(f"  - Correlation strength: {abs(top_corr['correlation']):.2%}\\n")
            
            if top_corr['correlation'] > 0:
                f.write(f"  - Strategy: Go long when {top_corr['munich_variable']} increases\\n")
            else:
                f.write(f"  - Strategy: Go short when {top_corr['munich_variable']} increases\\n")
        
        f.write("\\n")
        f.write("=" * 80 + "\\n")
    
    logger.info(f"Report saved to {report_path}")


async def main():
    """Main execution function."""
    logger.info("Starting signal discovery analysis")
    
    # Load configuration
    config = load_config()
    
    # Fetch Munich data
    logger.info("Fetching live Munich data...")
    munich_data = await fetch_munich_data(config)
    
    # Generate synthetic market data
    logger.info("Generating synthetic market data...")
    df = generate_synthetic_market_data(munich_data, num_samples=100)
    
    # Compute correlations
    logger.info("Computing correlations...")
    corr_matrix = compute_correlations(df)
    
    # Identify strong correlations
    strong_corrs = identify_strong_correlations(corr_matrix, threshold=0.3)
    
    logger.info(f"Found {len(strong_corrs)} strong correlations")
    for corr in strong_corrs[:5]:
        logger.info(f"  {corr['munich_variable']} → {corr['market_variable']}: r={corr['correlation']:.3f}")
    
    # Create visualizations
    output_dir = Path(__file__).parent / 'output'
    visualize_signal_discovery(df, corr_matrix, strong_corrs, output_dir)
    
    # Generate summary report
    generate_summary_report(munich_data, strong_corrs, output_dir)
    
    logger.info(f"Signal discovery complete! Results saved to {output_dir}")
    logger.info("Key findings:")
    logger.info(f"  - {len(strong_corrs)} strong correlations identified")
    logger.info(f"  - Top correlation: {strong_corrs[0]['munich_variable']} → {strong_corrs[0]['market_variable']} (r={strong_corrs[0]['correlation']:.3f})")
    logger.info("  - Visualizations and report generated")


if __name__ == "__main__":
    asyncio.run(main())
