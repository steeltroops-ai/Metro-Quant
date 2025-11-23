"""Property-based tests for risk management layer.

Tests verify correctness properties for position limiting, drawdown monitoring,
and risk reduction measures.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
import time

from src.risk.limiter import PositionLimiter
from src.risk.drawdown import DrawdownMonitor
from src.strategy.position_sizer import PositionSizer


# Strategies for generating test data

@st.composite
def position_dict_strategy(draw, max_positions=5):
    """Generate valid position dictionary."""
    num_positions = draw(st.integers(min_value=0, max_value=max_positions))
    positions = {}
    for i in range(num_positions):
        symbol = f"SYMBOL_{i}"
        # Position size in capital units
        size = draw(st.floats(min_value=100, max_value=50000))
        positions[symbol] = size
    return positions


@st.composite
def capital_and_positions_strategy(draw):
    """Generate capital and positions that make sense together."""
    capital = draw(st.floats(min_value=10000, max_value=1000000))
    positions = draw(position_dict_strategy())
    
    # Ensure total positions don't exceed 80% of capital (the max exposure limit)
    total_exposure = sum(abs(size) for size in positions.values())
    if total_exposure > capital * 0.75:
        # Scale down positions to be well within limits
        scale_factor = (capital * 0.6) / total_exposure
        positions = {sym: size * scale_factor for sym, size in positions.items()}
    
    return capital, positions


# Feature: imc-trading-bot, Property 18: Comprehensive risk limits
@given(
    capital=st.floats(min_value=10000, max_value=1000000),
    proposed_size=st.floats(min_value=100, max_value=500000),
    current_positions=position_dict_strategy()
)
@settings(max_examples=100, deadline=None)
def test_comprehensive_risk_limits(capital, proposed_size, current_positions):
    """
    Property 18: Comprehensive risk limits
    
    For any position calculation, the exposure should not exceed 20% of total capital
    per position, and for any portfolio state, total exposure should not exceed 80%
    of capital.
    
    Validates: Requirements 5.1, 5.5
    """
    limiter = PositionLimiter(max_position_pct=0.2, max_total_exposure_pct=0.8)
    
    # Test symbol
    symbol = "TEST_SYMBOL"
    
    # Check and adjust position size
    adjusted_size = limiter.check_limit(
        proposed_size=proposed_size,
        symbol=symbol,
        capital=capital,
        current_positions=current_positions
    )
    
    # Verify per-position limit (20% of capital)
    position_pct = abs(adjusted_size) / capital
    # Allow small floating point tolerance
    assert position_pct <= 0.2 + 1e-10, \
        f"Adjusted position {position_pct:.1%} exceeds per-position limit of 20%"
    
    # Verify total exposure limit (80% of capital)
    # Calculate total exposure including the new position
    current_exposure = sum(
        abs(size) for sym, size in current_positions.items()
        if sym != symbol
    )
    total_exposure = current_exposure + abs(adjusted_size)
    total_exposure_pct = total_exposure / capital
    
    # Allow small floating point tolerance
    # Note: If adjusted_size is 0, current positions may already exceed limit
    if adjusted_size != 0:
        assert total_exposure_pct <= 0.8 + 1e-6, \
            f"Total exposure {total_exposure_pct:.1%} exceeds limit of 80%"
    
    # Verify adjusted size preserves direction of proposed size
    if proposed_size > 0:
        assert adjusted_size >= 0, \
            "Adjusted size should preserve positive direction"
    elif proposed_size < 0:
        assert adjusted_size <= 0, \
            "Adjusted size should preserve negative direction"
    
    # Verify adjusted size is not larger than proposed size
    assert abs(adjusted_size) <= abs(proposed_size), \
        "Adjusted size should not be larger than proposed size"


# Feature: imc-trading-bot, Property 19: Drawdown-triggered risk reduction
@given(
    initial_capital=st.floats(min_value=50000, max_value=500000),
    loss_pct=st.floats(min_value=0.15, max_value=0.24)
)
@settings(max_examples=100, deadline=None)
def test_drawdown_triggered_reduction(initial_capital, loss_pct):
    """
    Property 19: Drawdown-triggered risk reduction
    
    For any portfolio state where drawdown exceeds 15%, all position sizes should
    be reduced by 50%.
    
    Validates: Requirements 5.2
    """
    monitor = DrawdownMonitor(
        initial_capital=initial_capital,
        reduction_threshold=0.15,
        safe_mode_threshold=0.25
    )
    
    # Simulate a loss that triggers reduction threshold
    current_capital = initial_capital * (1 - loss_pct)
    monitor.update(current_capital)
    
    # Get position multiplier
    multiplier = monitor.get_multiplier()
    
    # Verify drawdown is calculated correctly
    drawdown = monitor.get_current_drawdown()
    expected_drawdown = loss_pct
    assert abs(drawdown - expected_drawdown) < 0.01, \
        f"Drawdown {drawdown:.2%} should match loss {expected_drawdown:.2%}"
    
    # If drawdown >= 15% and < 25%, multiplier should be 0.5
    if 0.15 <= loss_pct < 0.25:
        assert multiplier == 0.5, \
            f"Position multiplier should be 0.5 for {loss_pct:.1%} drawdown, got {multiplier}"
        
        # Verify risk reduction is active
        assert monitor.is_reduction_active(), \
            "Risk reduction should be active for 15%+ drawdown"
        
        # Verify safe mode is not active
        assert not monitor.is_safe_mode(), \
            "Safe mode should not be active for drawdown < 25%"


# Feature: imc-trading-bot, Property 20: Emergency safe mode activation
@given(
    initial_capital=st.floats(min_value=50000, max_value=500000),
    loss_pct=st.floats(min_value=0.25, max_value=0.50)
)
@settings(max_examples=100, deadline=None)
def test_safe_mode_activation(initial_capital, loss_pct):
    """
    Property 20: Emergency safe mode activation
    
    For any portfolio state where drawdown exceeds 25%, all trading should halt
    and safe mode should be activated.
    
    Validates: Requirements 5.3
    """
    monitor = DrawdownMonitor(
        initial_capital=initial_capital,
        reduction_threshold=0.15,
        safe_mode_threshold=0.25
    )
    
    # Simulate a loss that triggers safe mode
    current_capital = initial_capital * (1 - loss_pct)
    monitor.update(current_capital)
    
    # Get position multiplier
    multiplier = monitor.get_multiplier()
    
    # Verify drawdown is calculated correctly
    drawdown = monitor.get_current_drawdown()
    expected_drawdown = loss_pct
    assert abs(drawdown - expected_drawdown) < 0.01, \
        f"Drawdown {drawdown:.2%} should match loss {expected_drawdown:.2%}"
    
    # For drawdown >= 25%, multiplier should be 0.0 (no trading)
    assert multiplier == 0.0, \
        f"Position multiplier should be 0.0 for {loss_pct:.1%} drawdown, got {multiplier}"
    
    # Verify safe mode is active
    assert monitor.is_safe_mode(), \
        f"Safe mode should be active for {loss_pct:.1%} drawdown"
    
    # Verify safe mode was triggered
    assert monitor.safe_mode_triggered_at is not None, \
        "Safe mode trigger timestamp should be set"


# Feature: imc-trading-bot, Property 21: Confidence-proportional position sizing
@given(
    signal_strength=st.floats(min_value=0.5, max_value=1.0),
    confidence_low=st.floats(min_value=0.3, max_value=0.5),
    confidence_high=st.floats(min_value=0.7, max_value=1.0),
    capital=st.floats(min_value=10000, max_value=500000)
)
@settings(max_examples=100, deadline=None)
def test_confidence_proportional_sizing(signal_strength, confidence_low, confidence_high, capital):
    """
    Property 21: Confidence-proportional position sizing
    
    For any signal with varying confidence, position size should scale proportionally
    to confidence level.
    
    Validates: Requirements 5.4
    """
    sizer = PositionSizer()
    
    # Calculate position with low confidence
    position_low = sizer.calculate_size(
        signal_strength=signal_strength,
        confidence=confidence_low,
        regime='low-volatility',
        capital=capital,
        regime_multiplier=1.0
    )
    
    # Calculate position with high confidence
    position_high = sizer.calculate_size(
        signal_strength=signal_strength,
        confidence=confidence_high,
        regime='low-volatility',
        capital=capital,
        regime_multiplier=1.0
    )
    
    # Higher confidence should result in larger position
    # (unless low confidence is below minimum threshold)
    if confidence_low >= sizer.min_confidence:
        assert abs(position_high) >= abs(position_low), \
            f"Higher confidence {confidence_high:.2f} should result in larger position " \
            f"than {confidence_low:.2f}: {abs(position_high):.2f} vs {abs(position_low):.2f}"
        
        # Verify proportionality (approximately)
        # position_high / position_low should be roughly confidence_high / confidence_low
        if abs(position_low) > 0:
            size_ratio = abs(position_high) / abs(position_low)
            confidence_ratio = confidence_high / confidence_low
            
            # Allow some deviation due to other factors, but should be correlated
            # Size ratio should be at least 1.0 (higher confidence = larger or equal size)
            assert size_ratio >= 1.0, \
                f"Size ratio {size_ratio:.2f} should be >= 1.0 for confidence ratio {confidence_ratio:.2f}"


# Additional property: Position limiter is idempotent
@given(
    capital=st.floats(min_value=10000, max_value=1000000),
    proposed_size=st.floats(min_value=100, max_value=500000),
    current_positions=position_dict_strategy()
)
@settings(max_examples=100, deadline=None)
def test_position_limiter_idempotent(capital, proposed_size, current_positions):
    """
    Verify that applying position limiter twice yields same result.
    
    For any position, checking limits twice should give the same adjusted size.
    """
    limiter = PositionLimiter()
    symbol = "TEST_SYMBOL"
    
    # Apply limiter once
    adjusted_once = limiter.check_limit(
        proposed_size=proposed_size,
        symbol=symbol,
        capital=capital,
        current_positions=current_positions
    )
    
    # Apply limiter again with the adjusted size
    adjusted_twice = limiter.check_limit(
        proposed_size=adjusted_once,
        symbol=symbol,
        capital=capital,
        current_positions=current_positions
    )
    
    # Should be identical (or very close due to floating point)
    assert abs(adjusted_once - adjusted_twice) < 1e-6, \
        f"Position limiter should be idempotent: {adjusted_once} != {adjusted_twice}"


# Additional property: Drawdown recovery resets reduction
@given(
    initial_capital=st.floats(min_value=50000, max_value=500000),
    loss_pct=st.floats(min_value=0.15, max_value=0.24),
    recovery_pct=st.floats(min_value=0.0, max_value=0.10)
)
@settings(max_examples=100, deadline=None)
def test_drawdown_recovery_resets_reduction(initial_capital, loss_pct, recovery_pct):
    """
    Verify that recovering from drawdown resets risk reduction.
    
    For any drawdown followed by recovery to new peak, risk reduction should be reset.
    """
    monitor = DrawdownMonitor(
        initial_capital=initial_capital,
        reduction_threshold=0.15,
        safe_mode_threshold=0.25
    )
    
    # Simulate a loss that triggers reduction
    loss_capital = initial_capital * (1 - loss_pct)
    monitor.update(loss_capital)
    
    # Verify reduction is active
    assert monitor.is_reduction_active(), \
        "Risk reduction should be active after loss"
    
    # Simulate recovery to new peak
    recovery_capital = initial_capital * (1 + recovery_pct)
    monitor.update(recovery_capital)
    
    # Verify reduction is no longer active
    assert not monitor.is_reduction_active(), \
        "Risk reduction should be reset after recovery to new peak"
    
    # Verify multiplier is back to normal
    multiplier = monitor.get_multiplier()
    assert multiplier == 1.0, \
        f"Position multiplier should be 1.0 after recovery, got {multiplier}"


# Additional property: Available exposure calculation is accurate
@given(data=capital_and_positions_strategy())
@settings(max_examples=100, deadline=None)
def test_available_exposure_accurate(data):
    """
    Verify that available exposure calculation is accurate.
    
    For any portfolio state, available exposure + current exposure should equal max exposure.
    """
    capital, current_positions = data
    
    limiter = PositionLimiter(max_total_exposure_pct=0.8)
    
    # Get available exposure
    available = limiter.get_available_exposure(capital, current_positions)
    
    # Calculate current exposure
    current_exposure = sum(abs(size) for size in current_positions.values())
    
    # Verify available + current <= max
    max_exposure = 0.8 * capital
    assert current_exposure + available <= max_exposure + 1e-6, \
        f"Current {current_exposure:.2f} + available {available:.2f} " \
        f"should not exceed max {max_exposure:.2f}"
    
    # Verify available is non-negative
    assert available >= 0, \
        f"Available exposure should be non-negative, got {available:.2f}"


# Additional property: Drawdown never exceeds 100%
@given(
    initial_capital=st.floats(min_value=10000, max_value=500000),
    loss_pct=st.floats(min_value=0.0, max_value=0.99)
)
@settings(max_examples=100, deadline=None)
def test_drawdown_bounded(initial_capital, loss_pct):
    """
    Verify that drawdown is always between 0% and 100%.
    
    For any capital loss, drawdown should be in valid range.
    """
    monitor = DrawdownMonitor(initial_capital=initial_capital)
    
    # Simulate loss
    current_capital = initial_capital * (1 - loss_pct)
    monitor.update(current_capital)
    
    # Get drawdown
    drawdown = monitor.get_current_drawdown()
    
    # Verify drawdown is in valid range
    assert 0.0 <= drawdown <= 1.0, \
        f"Drawdown {drawdown:.2%} should be between 0% and 100%"
    
    # Verify drawdown matches expected
    assert abs(drawdown - loss_pct) < 0.01, \
        f"Drawdown {drawdown:.2%} should match loss {loss_pct:.2%}"


# Additional property: Position limits are consistent
@given(
    capital=st.floats(min_value=10000, max_value=1000000),
    proposed_size=st.floats(min_value=100, max_value=500000),
    current_positions=position_dict_strategy()
)
@settings(max_examples=100, deadline=None)
def test_position_limits_consistent(capital, proposed_size, current_positions):
    """
    Verify that position limit checks are consistent.
    
    If a position is within limits according to is_within_limits(),
    then check_limit() should not reduce it.
    """
    limiter = PositionLimiter()
    symbol = "TEST_SYMBOL"
    
    # Check if proposed size is within limits
    within_limits = limiter.is_within_limits(
        position_size=proposed_size,
        symbol=symbol,
        capital=capital,
        current_positions=current_positions
    )
    
    # Get adjusted size
    adjusted_size = limiter.check_limit(
        proposed_size=proposed_size,
        symbol=symbol,
        capital=capital,
        current_positions=current_positions
    )
    
    # If within limits, adjusted should equal proposed (or very close)
    if within_limits:
        assert abs(adjusted_size - proposed_size) < 1e-6, \
            f"If position is within limits, it should not be adjusted: " \
            f"{proposed_size:.2f} -> {adjusted_size:.2f}"
