"""Property-based tests for strategy layer.

Tests verify correctness properties for regime detection, adaptive strategy,
and position sizing.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta
import numpy as np
import time

from src.strategy.regime import RegimeDetector
from src.strategy.adaptive import AdaptiveStrategy
from src.strategy.position_sizer import PositionSizer


# Strategies for generating test data

@st.composite
def returns_strategy(draw, min_length=30, max_length=200):
    """Generate valid return series."""
    length = draw(st.integers(min_value=min_length, max_value=max_length))
    # Generate returns in reasonable range [-10%, +10%]
    returns = [draw(st.floats(min_value=-0.1, max_value=0.1)) for _ in range(length)]
    return returns


@st.composite
def signal_data_strategy(draw):
    """Generate valid signal data."""
    return {
        'strength': draw(st.floats(min_value=-1.0, max_value=1.0)),
        'confidence': draw(st.floats(min_value=0.0, max_value=1.0)),
        'regime': draw(st.sampled_from(['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']))
    }


# Feature: imc-trading-bot, Property 9: Valid regime classification
@given(returns=returns_strategy())
@settings(max_examples=100, deadline=None)
def test_valid_regime_classification(returns):
    """
    Property 9: Valid regime classification
    
    For any market data analyzed, the classified regime should be one of:
    trending, mean-reverting, high-volatility, low-volatility, or uncertain.
    
    Validates: Requirements 3.1
    """
    detector = RegimeDetector()
    
    # Detect regime
    regime = detector.detect(returns)
    
    # Verify regime is one of the valid values
    valid_regimes = {'trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain'}
    assert regime in valid_regimes, \
        f"Regime '{regime}' is not one of the valid regimes: {valid_regimes}"
    
    # Verify confidence is in valid range
    confidence = detector.get_confidence()
    assert 0.0 <= confidence <= 1.0, \
        f"Confidence {confidence} is outside [0, 1] range"
    
    # Verify current regime matches detected regime
    assert detector.get_current_regime() == regime, \
        "Current regime should match detected regime"


# Feature: imc-trading-bot, Property 10: Regime adaptation latency
@given(returns=returns_strategy(min_length=50, max_length=100))
@settings(max_examples=100, deadline=None)
def test_regime_adaptation_latency(returns):
    """
    Property 10: Regime adaptation latency
    
    For any detected regime change, strategy parameters should be updated within 1 second.
    
    Validates: Requirements 3.2
    """
    detector = RegimeDetector()
    strategy = AdaptiveStrategy()
    
    # Detect initial regime
    start_time = time.time()
    regime = detector.detect(returns)
    detection_time = time.time() - start_time
    
    # Get strategy parameters
    start_time = time.time()
    params = strategy.get_parameters(regime)
    weights = strategy.get_signal_weights(regime)
    adaptation_time = time.time() - start_time
    
    # Verify total time is under 1 second
    total_time = detection_time + adaptation_time
    assert total_time < 1.0, \
        f"Regime detection and adaptation took {total_time:.3f}s, exceeds 1 second limit"
    
    # Verify parameters were retrieved
    assert isinstance(params, dict), "Parameters should be a dictionary"
    assert isinstance(weights, dict), "Weights should be a dictionary"
    assert len(params) > 0, "Parameters should not be empty"


# Feature: imc-trading-bot, Property 11: Volatility-based position reduction
@given(
    returns=returns_strategy(min_length=50, max_length=100),
    signal_strength=st.floats(min_value=0.3, max_value=1.0),
    confidence=st.floats(min_value=0.5, max_value=1.0),
    capital=st.floats(min_value=10000, max_value=1000000)
)
@settings(max_examples=100, deadline=None)
def test_volatility_based_position_reduction(returns, signal_strength, confidence, capital):
    """
    Property 11: Volatility-based position reduction
    
    For any high-volatility regime, position sizes should be reduced by at least 50%
    compared to normal regime.
    
    Validates: Requirements 3.3
    """
    detector = RegimeDetector()
    strategy = AdaptiveStrategy()
    sizer = PositionSizer()
    
    # Detect regime
    regime = detector.detect(returns)
    
    # Get regime multiplier
    regime_multiplier = strategy.get_position_multiplier(regime)
    
    # Calculate position size
    position_size = sizer.calculate_size(
        signal_strength=signal_strength,
        confidence=confidence,
        regime=regime,
        capital=capital,
        regime_multiplier=regime_multiplier
    )
    
    # If regime is high-volatility, verify position is reduced
    if regime == 'high-volatility':
        # Get normal regime multiplier for comparison
        normal_multiplier = strategy.get_position_multiplier('low-volatility')
        
        # High volatility multiplier should be at most 50% of normal
        assert regime_multiplier <= normal_multiplier * 0.5, \
            f"High-volatility multiplier {regime_multiplier} should be <= 50% of normal {normal_multiplier}"
        
        # Verify position size respects the multiplier
        # (position size should be proportional to multiplier)
        assert abs(position_size) <= abs(capital * 0.2 * regime_multiplier), \
            f"Position size {position_size} exceeds expected maximum for high volatility"


# Feature: imc-trading-bot, Property 12: Regime-specific signal weighting
@given(
    returns=returns_strategy(min_length=50, max_length=100)
)
@settings(max_examples=100, deadline=None)
def test_regime_specific_weighting(returns):
    """
    Property 12: Regime-specific signal weighting
    
    For any trending regime, momentum signal weights should be higher than in other regimes.
    
    Validates: Requirements 3.4
    """
    detector = RegimeDetector()
    strategy = AdaptiveStrategy()
    
    # Detect regime
    regime = detector.detect(returns)
    
    # Get signal weights for detected regime
    weights = strategy.get_signal_weights(regime)
    
    # Verify weights is a dictionary
    assert isinstance(weights, dict), "Weights should be a dictionary"
    
    # If regime is trending, verify momentum signals have higher weights
    if regime == 'trending':
        # Get momentum-related signal names
        momentum_signals = ['temp_momentum', 'temp_trend', 'flights_trend', 'flight_volume_delta']
        
        # Get weights for other regimes for comparison
        other_regimes = ['mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']
        
        # Check that at least one momentum signal has higher weight in trending
        has_higher_momentum = False
        for signal_name in momentum_signals:
            if signal_name in weights:
                trending_weight = abs(weights[signal_name])
                
                # Compare with other regimes
                for other_regime in other_regimes:
                    other_weights = strategy.get_signal_weights(other_regime)
                    if signal_name in other_weights:
                        other_weight = abs(other_weights[signal_name])
                        if trending_weight > other_weight:
                            has_higher_momentum = True
                            break
                
                if has_higher_momentum:
                    break
        
        # At least one momentum signal should have higher weight in trending regime
        assert has_higher_momentum, \
            "Trending regime should emphasize momentum signals more than other regimes"


# Feature: imc-trading-bot, Property 13: Conservative fallback parameters
@given(
    signal_strength=st.floats(min_value=0.1, max_value=1.0),
    confidence=st.floats(min_value=0.1, max_value=1.0),
    capital=st.floats(min_value=10000, max_value=1000000)
)
@settings(max_examples=100, deadline=None)
def test_conservative_fallback_parameters(signal_strength, confidence, capital):
    """
    Property 13: Conservative fallback parameters
    
    For any uncertain regime classification, the system should use conservative
    default parameters.
    
    Validates: Requirements 3.5
    """
    strategy = AdaptiveStrategy()
    sizer = PositionSizer()
    
    # Get parameters for uncertain regime
    uncertain_params = strategy.get_parameters('uncertain')
    uncertain_multiplier = strategy.get_position_multiplier('uncertain')
    
    # Get parameters for other regimes
    other_regimes = ['trending', 'mean-reverting', 'high-volatility', 'low-volatility']
    
    # Verify uncertain regime has conservative parameters
    # 1. Position multiplier should be smaller than most other regimes
    smaller_count = 0
    for regime in other_regimes:
        other_multiplier = strategy.get_position_multiplier(regime)
        if uncertain_multiplier <= other_multiplier:
            smaller_count += 1
    
    assert smaller_count >= 3, \
        f"Uncertain regime multiplier {uncertain_multiplier} should be conservative " \
        f"(smaller than most other regimes)"
    
    # 2. Signal threshold should be higher (more conservative)
    uncertain_threshold = strategy.get_signal_threshold('uncertain')
    
    higher_threshold_count = 0
    for regime in other_regimes:
        other_threshold = strategy.get_signal_threshold(regime)
        if uncertain_threshold >= other_threshold:
            higher_threshold_count += 1
    
    assert higher_threshold_count >= 2, \
        f"Uncertain regime threshold {uncertain_threshold} should be conservative " \
        f"(higher than most other regimes)"
    
    # 3. Calculate position size and verify it's conservative
    position_size = sizer.calculate_size(
        signal_strength=signal_strength,
        confidence=confidence,
        regime='uncertain',
        capital=capital,
        regime_multiplier=uncertain_multiplier
    )
    
    # Position size should be relatively small
    position_pct = abs(position_size) / capital
    assert position_pct <= 0.1, \
        f"Uncertain regime position {position_pct:.1%} should be conservative (<= 10% of capital)"


# Additional property: Regime detection is deterministic
@given(returns=returns_strategy())
@settings(max_examples=50, deadline=None)
def test_regime_detection_deterministic(returns):
    """
    Verify that regime detection is deterministic.
    
    For any return series, detecting regime twice should yield identical results.
    """
    detector1 = RegimeDetector()
    detector2 = RegimeDetector()
    
    regime1 = detector1.detect(returns)
    regime2 = detector2.detect(returns)
    
    # Verify same regime
    assert regime1 == regime2, \
        f"Regime detection should be deterministic: {regime1} != {regime2}"
    
    # Verify same confidence
    confidence1 = detector1.get_confidence()
    confidence2 = detector2.get_confidence()
    
    assert abs(confidence1 - confidence2) < 1e-9, \
        f"Confidence should be deterministic: {confidence1} != {confidence2}"


# Additional property: Position size respects maximum limits
@given(
    signal_strength=st.floats(min_value=-1.0, max_value=1.0),
    confidence=st.floats(min_value=0.0, max_value=1.0),
    regime=st.sampled_from(['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']),
    capital=st.floats(min_value=1000, max_value=1000000),
    regime_multiplier=st.floats(min_value=0.1, max_value=2.0)
)
@settings(max_examples=100, deadline=None)
def test_position_size_respects_limits(signal_strength, confidence, regime, capital, regime_multiplier):
    """
    Verify that position sizes never exceed maximum limits.
    
    For any signal and capital, position size should not exceed 20% of capital.
    """
    sizer = PositionSizer(max_position_pct=0.2)
    
    position_size = sizer.calculate_size(
        signal_strength=signal_strength,
        confidence=confidence,
        regime=regime,
        capital=capital,
        regime_multiplier=regime_multiplier
    )
    
    # Verify position size doesn't exceed 20% of capital
    position_pct = abs(position_size) / capital
    assert position_pct <= 0.2, \
        f"Position size {position_pct:.1%} exceeds maximum 20% of capital"
    
    # Verify position size respects signal direction
    if signal_strength > 0:
        assert position_size >= 0, \
            f"Position should be long (positive) for positive signal"
    elif signal_strength < 0:
        assert position_size <= 0, \
            f"Position should be short (negative) for negative signal"


# Additional property: Position size scales with confidence
@given(
    signal_strength=st.floats(min_value=0.5, max_value=1.0),
    confidence_low=st.floats(min_value=0.3, max_value=0.5),
    confidence_high=st.floats(min_value=0.7, max_value=1.0),
    capital=st.floats(min_value=10000, max_value=100000)
)
@settings(max_examples=100, deadline=None)
def test_position_size_scales_with_confidence(signal_strength, confidence_low, confidence_high, capital):
    """
    Verify that position size increases with confidence.
    
    For any signal, higher confidence should result in larger position size.
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
    
    # Higher confidence should result in larger position (or equal if at max)
    assert abs(position_high) >= abs(position_low), \
        f"Higher confidence {confidence_high} should result in larger position than {confidence_low}"
