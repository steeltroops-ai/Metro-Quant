"""Property-based tests for backtesting engine.

Tests verify correctness properties for backtest execution.
"""

import asyncio
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
import numpy as np
import pytest

from src.backtest.engine import Backtester
from src.utils.types import MarketData, Signal


# Strategies for generating test data

@st.composite
def market_data_strategy(draw, min_size=10, max_size=100):
    """Generate chronological market data."""
    size = draw(st.integers(min_value=min_size, max_value=max_size))
    base_time = datetime(2024, 1, 1, 10, 0, 0)
    symbol = draw(st.sampled_from(['EISBACH', 'WEATHER', 'FLIGHTS']))
    
    # Generate prices with random walk
    base_price = draw(st.floats(min_value=50.0, max_value=200.0))
    prices = [base_price]
    for _ in range(size - 1):
        change = draw(st.floats(min_value=-0.05, max_value=0.05))
        new_price = max(1.0, prices[-1] * (1 + change))
        prices.append(new_price)
    
    # Generate market data points
    data_points = []
    for i in range(size):
        timestamp = base_time + timedelta(minutes=i)
        price = prices[i]
        spread = price * 0.001  # 0.1% spread
        
        # Calculate returns
        if i > 0:
            returns = [(prices[j] - prices[j-1]) / prices[j-1] 
                      for j in range(1, i+1)]
        else:
            returns = []
        
        data = MarketData(
            timestamp=timestamp,
            symbol=symbol,
            price=price,
            volume=draw(st.floats(min_value=100, max_value=10000)),
            bid=price - spread/2,
            ask=price + spread/2,
            returns=returns
        )
        data_points.append(data)
    
    return data_points


@st.composite
def signal_strategy(draw, market_data):
    """Generate signals aligned with market data timestamps."""
    # Generate signals for subset of timestamps
    num_signals = draw(st.integers(min_value=0, max_value=len(market_data) // 2))
    
    if num_signals == 0:
        return []
    
    # Sample timestamps
    indices = draw(st.lists(
        st.integers(min_value=0, max_value=len(market_data)-1),
        min_size=num_signals,
        max_size=num_signals,
        unique=True
    ))
    indices.sort()  # Ensure chronological order
    
    signals = []
    for idx in indices:
        timestamp = market_data[idx].timestamp
        signal = Signal(
            timestamp=timestamp,
            strength=draw(st.floats(min_value=-1.0, max_value=1.0)),
            confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
            components={},
            regime=draw(st.sampled_from([
                'trending', 'mean-reverting', 'high-volatility', 
                'low-volatility', 'uncertain'
            ]))
        )
        signals.append(signal)
    
    return signals


# Feature: imc-trading-bot, Property 26: Chronological backtest replay
@given(market_data=market_data_strategy())
@settings(max_examples=50, deadline=5000)
def test_chronological_replay(market_data):
    """
    For any historical data provided to the backtesting engine,
    it should be replayed in chronological order.
    
    Validates: Requirements 7.1
    """
    backtester = Backtester(initial_capital=100000.0)
    
    # Run backtest
    results = asyncio.run(backtester.run(
        market_data=market_data,
        signals=[]
    ))
    
    # Verify equity curve is in chronological order
    equity_curve = results.get('equity_curve', [])
    
    if len(equity_curve) > 1:
        timestamps = [t for t, _ in equity_curve]
        
        # Check that timestamps are monotonically increasing
        for i in range(1, len(timestamps)):
            assert timestamps[i] >= timestamps[i-1], \
                f"Equity curve not chronological at index {i}: {timestamps[i-1]} > {timestamps[i]}"
    
    # Verify trade log is in chronological order
    trade_log = results.get('trade_log', [])
    
    if len(trade_log) > 1:
        trade_timestamps = [trade['timestamp'] for trade in trade_log]
        
        for i in range(1, len(trade_timestamps)):
            assert trade_timestamps[i] >= trade_timestamps[i-1], \
                f"Trade log not chronological at index {i}"


# Feature: imc-trading-bot, Property 27: Realistic slippage simulation
@given(
    market_data=market_data_strategy(min_size=20, max_size=50),
    slippage_bps=st.floats(min_value=1.0, max_value=20.0)
)
@settings(max_examples=30, deadline=5000)
def test_realistic_slippage(market_data, slippage_bps):
    """
    For any order filled during backtesting, the fill price should include
    realistic slippage relative to the limit price.
    
    Validates: Requirements 7.2
    """
    backtester = Backtester(
        initial_capital=100000.0,
        slippage_bps=slippage_bps
    )
    
    # Generate signals to trigger trades
    signals = []
    for i in range(0, len(market_data), 5):
        if i < len(market_data):
            signal = Signal(
                timestamp=market_data[i].timestamp,
                strength=0.5,  # Strong enough to trade
                confidence=0.8,
                components={},
                regime='trending'
            )
            signals.append(signal)
    
    # Run backtest
    results = asyncio.run(backtester.run(
        market_data=market_data,
        signals=signals
    ))
    
    # Verify slippage was applied to filled orders
    trade_log = results.get('trade_log', [])
    
    for trade in trade_log:
        # Find corresponding market data
        trade_time = trade['timestamp']
        matching_data = [d for d in market_data if d.timestamp == trade_time]
        
        if matching_data:
            data = matching_data[0]
            fill_price = trade['price']
            
            # Verify fill price includes slippage
            if trade['side'] == 'BUY':
                # Buy fills should be at or above ask (due to slippage)
                expected_min = data.ask
                expected_max = data.ask * (1 + slippage_bps / 10000 * 2)  # Allow some tolerance
                assert expected_min <= fill_price <= expected_max, \
                    f"Buy fill price {fill_price} outside expected range [{expected_min}, {expected_max}]"
            else:
                # Sell fills should be at or below bid (due to slippage)
                expected_min = data.bid * (1 - slippage_bps / 10000 * 2)  # Allow some tolerance
                expected_max = data.bid
                assert expected_min <= fill_price <= expected_max, \
                    f"Sell fill price {fill_price} outside expected range [{expected_min}, {expected_max}]"


# Feature: imc-trading-bot, Property 28: Regime-segmented backtest results
@given(market_data=market_data_strategy(min_size=50, max_size=100))
@settings(max_examples=30, deadline=5000)
def test_regime_segmented_results(market_data):
    """
    For any backtest across multiple market types, performance metrics
    should be broken down by regime.
    
    Validates: Requirements 7.4
    """
    backtester = Backtester(initial_capital=100000.0)
    
    # Generate signals across different regimes
    signals = []
    regimes = ['trending', 'mean-reverting', 'high-volatility', 'low-volatility']
    
    for i in range(0, len(market_data), 10):
        if i < len(market_data):
            regime = regimes[i % len(regimes)]
            signal = Signal(
                timestamp=market_data[i].timestamp,
                strength=0.6,
                confidence=0.7,
                components={},
                regime=regime
            )
            signals.append(signal)
    
    # Run backtest
    results = asyncio.run(backtester.run(
        market_data=market_data,
        signals=signals
    ))
    
    # Verify regime breakdown exists
    assert 'regime_breakdown' in results, "Results missing regime_breakdown"
    
    regime_breakdown = results['regime_breakdown']
    
    # Verify regime breakdown is a dictionary
    assert isinstance(regime_breakdown, dict), \
        "Regime breakdown should be a dictionary"
    
    # Verify each regime entry has required metrics
    for regime, metrics in regime_breakdown.items():
        assert 'trades' in metrics, f"Regime {regime} missing 'trades' metric"
        assert 'pnl' in metrics, f"Regime {regime} missing 'pnl' metric"
        assert 'win_rate' in metrics, f"Regime {regime} missing 'win_rate' metric"
        
        # Verify metrics are reasonable
        assert metrics['trades'] >= 0, f"Regime {regime} has negative trade count"
        assert 0.0 <= metrics['win_rate'] <= 1.0, \
            f"Regime {regime} win_rate {metrics['win_rate']} not in [0, 1]"


# Feature: imc-trading-bot, Property 29: Statistical A/B testing support
@given(
    market_data=market_data_strategy(min_size=50, max_size=100),
    strategy_a_multiplier=st.floats(min_value=0.5, max_value=1.5),
    strategy_b_multiplier=st.floats(min_value=0.5, max_value=1.5)
)
@settings(max_examples=20, deadline=10000)
def test_ab_testing_support(market_data, strategy_a_multiplier, strategy_b_multiplier):
    """
    For any comparison of multiple strategies, the backtesting engine
    should provide statistical significance measures.
    
    Validates: Requirements 7.5
    """
    # Strategy A: Conservative
    def strategy_a(signal, regime):
        return signal.strength * signal.confidence * 50 * strategy_a_multiplier
    
    # Strategy B: Aggressive
    def strategy_b(signal, regime):
        return signal.strength * signal.confidence * 100 * strategy_b_multiplier
    
    # Generate signals
    signals = []
    for i in range(0, len(market_data), 5):
        if i < len(market_data):
            signal = Signal(
                timestamp=market_data[i].timestamp,
                strength=0.5,
                confidence=0.7,
                components={},
                regime='trending'
            )
            signals.append(signal)
    
    # Run backtest for strategy A
    backtester_a = Backtester(initial_capital=100000.0)
    results_a = asyncio.run(backtester_a.run(
        market_data=market_data,
        signals=signals,
        strategy_func=strategy_a
    ))
    
    # Run backtest for strategy B
    backtester_b = Backtester(initial_capital=100000.0)
    results_b = asyncio.run(backtester_b.run(
        market_data=market_data,
        signals=signals,
        strategy_func=strategy_b
    ))
    
    # Compare strategies
    comparison = backtester_a.compare_strategies(
        strategy_a_results=results_a,
        strategy_b_results=results_b,
        confidence_level=0.95
    )
    
    # Verify comparison contains required fields
    assert 'strategy_a_sharpe' in comparison, "Missing strategy_a_sharpe"
    assert 'strategy_b_sharpe' in comparison, "Missing strategy_b_sharpe"
    assert 'strategy_a_return' in comparison, "Missing strategy_a_return"
    assert 'strategy_b_return' in comparison, "Missing strategy_b_return"
    assert 'p_value' in comparison, "Missing p_value"
    assert 'is_significant' in comparison, "Missing is_significant"
    assert 'winner' in comparison, "Missing winner"
    
    # Verify p_value is in valid range
    assert 0.0 <= comparison['p_value'] <= 1.0, \
        f"p_value {comparison['p_value']} not in [0, 1]"
    
    # Verify is_significant is boolean
    assert isinstance(comparison['is_significant'], bool), \
        "is_significant should be boolean"
    
    # Verify winner is either 'A' or 'B'
    assert comparison['winner'] in ['A', 'B'], \
        f"Winner '{comparison['winner']}' should be 'A' or 'B'"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
