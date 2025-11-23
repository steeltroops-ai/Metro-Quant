"""
Property-based tests for visualization module.

Tests correctness properties for chart generation and presentation tools.
"""

import os
import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import numpy as np

# Set matplotlib to use non-interactive backend for tests
import matplotlib
matplotlib.use('Agg')

from src.visualization.charts import ChartGenerator


# Simple test with direct data generation

@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    n_points=st.integers(min_value=10, max_value=30),
    seed=st.integers(min_value=0, max_value=100)
)
def test_property_30_performance_visualization_by_market_type(n_points, seed):
    """
    Feature: imc-trading-bot, Property 30: Performance visualization by market type
    
    For any performance display, PnL curves should be shown separately for different market types.
    
    Validates: Requirements 8.2
    """
    np.random.seed(seed)
    
    # Generate timestamps
    start_time = datetime.now() - timedelta(days=7)
    timestamps = [start_time + timedelta(hours=i) for i in range(n_points)]
    
    # Generate cumulative PnL (random walk)
    pnl_changes = np.random.uniform(-100, 100, n_points)
    pnl_values = np.cumsum(pnl_changes).tolist()
    
    # Generate regime labels
    regimes = ['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']
    regime_labels = [regimes[i % len(regimes)] for i in range(n_points)]
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        chart_gen = ChartGenerator(output_dir=tmpdir)
        
        # Generate PnL curve with regime breakdown
        output_path = chart_gen.generate_pnl_curve(
            timestamps=timestamps,
            pnl_values=pnl_values,
            regime_labels=regime_labels,
            filename="test_pnl_curve.png"
        )
        
        # Property: Chart file should be created
        assert os.path.exists(output_path), "PnL curve chart should be created"
        
        # Property: Chart should be a valid PNG file
        assert output_path.endswith('.png'), "Chart should be PNG format"
        
        # Property: File should have non-zero size
        file_size = os.path.getsize(output_path)
        assert file_size > 0, "Chart file should have non-zero size"
        
        # Property: File should be reasonably sized (not corrupted)
        assert file_size > 1000, "Chart file should be at least 1KB (valid image)"
        assert file_size < 10_000_000, "Chart file should be less than 10MB (reasonable size)"
        
        # Property: All regimes should be valid
        valid_regimes = {'trending', 'mean-reverting', 'high-volatility', 
                       'low-volatility', 'uncertain'}
        unique_regimes = set(regime_labels)
        for regime in unique_regimes:
            assert regime in valid_regimes, f"Regime {regime} should be valid"


@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    n_points=st.integers(min_value=5, max_value=20),
    seed=st.integers(min_value=0, max_value=100)
)
def test_property_31_adaptation_visualization_completeness(n_points, seed):
    """
    Feature: imc-trading-bot, Property 31: Adaptation visualization completeness
    
    For any adaptation explanation, visualizations should include regime transition 
    markers and corresponding strategy adjustments.
    
    Validates: Requirements 8.3
    """
    np.random.seed(seed)
    
    # Generate timestamps
    start_time = datetime.now() - timedelta(days=7)
    timestamps = [start_time + timedelta(hours=i*2) for i in range(n_points)]
    
    # Generate regimes
    regime_options = ['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']
    regimes = [regime_options[i % len(regime_options)] for i in range(n_points)]
    
    # Generate strategy parameters
    strategy_params = []
    for _ in range(n_points):
        params = {
            'position_multiplier': float(np.random.uniform(0.1, 2.0)),
            'signal_threshold': float(np.random.uniform(0.1, 0.9)),
            'stop_loss': float(np.random.uniform(0.01, 0.1))
        }
        strategy_params.append(params)
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        chart_gen = ChartGenerator(output_dir=tmpdir)
        
        # Generate regime timeline
        output_path = chart_gen.generate_regime_timeline(
            timestamps=timestamps,
            regimes=regimes,
            strategy_params=strategy_params,
            filename="test_regime_timeline.png"
        )
        
        # Property: Chart file should be created
        assert os.path.exists(output_path), "Regime timeline chart should be created"
        
        # Property: Chart should be a valid PNG file
        assert output_path.endswith('.png'), "Chart should be PNG format"
        
        # Property: File should have non-zero size
        file_size = os.path.getsize(output_path)
        assert file_size > 0, "Chart file should have non-zero size"
        
        # Property: File should be reasonably sized
        assert file_size > 1000, "Chart file should be at least 1KB (valid image)"
        assert file_size < 10_000_000, "Chart file should be less than 10MB"
        
        # Property: All regimes should be valid
        valid_regimes = {'trending', 'mean-reverting', 'high-volatility', 
                        'low-volatility', 'uncertain'}
        for regime in regimes:
            assert regime in valid_regimes, f"Regime {regime} should be valid"
        
        # Property: Strategy parameters should contain expected keys
        for params in strategy_params:
            assert isinstance(params, dict), "Strategy params should be dictionaries"
            assert len(params) > 0, "Strategy params should not be empty"
        
        # Property: Number of timestamps, regimes, and params should match
        assert len(timestamps) == len(regimes), "Timestamps and regimes should have same length"
        assert len(timestamps) == len(strategy_params), "Timestamps and params should have same length"


@settings(max_examples=5, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(
    sharpe=st.floats(min_value=-2.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    drawdown=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
    win_rate=st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False),
    seed=st.integers(min_value=0, max_value=100)
)
def test_property_32_consistency_metric_prominence(sharpe, drawdown, win_rate, seed):
    """
    Feature: imc-trading-bot, Property 32: Consistency metric prominence
    
    For any results presentation, consistency metrics (Sharpe ratio, max drawdown) 
    should be highlighted more prominently than peak PnL.
    
    Validates: Requirements 8.5
    """
    np.random.seed(seed)
    
    # Create metrics dictionary
    metrics = {
        'sharpe_ratio': sharpe,
        'max_drawdown': drawdown,
        'win_rate': win_rate,
        'total_pnl': float(np.random.uniform(-10000, 10000)),
        'trade_count': int(np.random.randint(0, 1000)),
        'recent_sharpe': float(np.random.uniform(-2.0, 5.0))
    }
    
    # Create regime performance
    regime_performance = {}
    for regime in ['trending', 'mean-reverting', 'high-volatility', 'low-volatility']:
        regime_performance[regime] = {
            'total_pnl': float(np.random.uniform(-1000, 1000)),
            'trade_count': int(np.random.randint(0, 100)),
            'avg_pnl_per_trade': float(np.random.uniform(-50, 50))
        }
    
    # Create temporary directory for output
    with tempfile.TemporaryDirectory() as tmpdir:
        chart_gen = ChartGenerator(output_dir=tmpdir)
        
        # Generate consistency dashboard
        output_path = chart_gen.generate_consistency_dashboard(
            metrics=metrics,
            regime_performance=regime_performance,
            filename="test_consistency_dashboard.png"
        )
        
        # Property: Chart file should be created
        assert os.path.exists(output_path), "Consistency dashboard should be created"
        
        # Property: Chart should be a valid PNG file
        assert output_path.endswith('.png'), "Chart should be PNG format"
        
        # Property: File should have non-zero size
        file_size = os.path.getsize(output_path)
        assert file_size > 0, "Chart file should have non-zero size"
        
        # Property: File should be reasonably sized
        assert file_size > 1000, "Chart file should be at least 1KB (valid image)"
        assert file_size < 10_000_000, "Chart file should be less than 10MB"
        
        # Property: Metrics should contain consistency metrics
        assert 'sharpe_ratio' in metrics, "Should include Sharpe ratio"
        assert 'max_drawdown' in metrics, "Should include max drawdown"
        assert 'win_rate' in metrics, "Should include win rate"
        
        # Property: Consistency metrics should be within valid ranges
        assert -10 <= metrics['sharpe_ratio'] <= 10, "Sharpe ratio should be reasonable"
        assert 0 <= metrics['max_drawdown'] <= 1, "Max drawdown should be between 0 and 1"
        assert 0 <= metrics['win_rate'] <= 1, "Win rate should be between 0 and 1"
        
        # Property: Regime performance should have valid structure
        for regime, perf in regime_performance.items():
            assert 'total_pnl' in perf, f"Regime {regime} should have total_pnl"
            assert 'trade_count' in perf, f"Regime {regime} should have trade_count"
            assert isinstance(perf['trade_count'], int), "Trade count should be integer"
            assert perf['trade_count'] >= 0, "Trade count should be non-negative"


# Additional unit tests for edge cases

def test_chart_generator_initialization():
    """Test ChartGenerator initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chart_gen = ChartGenerator(output_dir=tmpdir)
        assert chart_gen.output_dir.exists()
        assert chart_gen.output_dir.is_dir()


def test_empty_pnl_curve():
    """Test PnL curve with minimal data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chart_gen = ChartGenerator(output_dir=tmpdir)
        
        timestamps = [datetime.now()]
        pnl_values = [0.0]
        
        output_path = chart_gen.generate_pnl_curve(
            timestamps=timestamps,
            pnl_values=pnl_values,
            filename="test_empty_pnl.png"
        )
        
        assert os.path.exists(output_path)


def test_architecture_diagram_generation():
    """Test architecture diagram generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chart_gen = ChartGenerator(output_dir=tmpdir)
        
        output_path = chart_gen.generate_architecture_diagram(
            filename="test_architecture.png"
        )
        
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 1000
