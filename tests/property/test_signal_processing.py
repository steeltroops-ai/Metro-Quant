"""Property-based tests for signal processing layer.

Tests verify correctness properties for feature engineering, signal generation,
and signal combination.
"""

import pytest
from hypothesis import given, strategies as st, settings
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from src.signals.features import FeatureEngineer
from src.signals.generator import SignalGenerator
from src.signals.combiner import SignalCombiner
from src.utils.types import CityData, WeatherData, AirQualityData, FlightData


# Strategies for generating test data

@st.composite
def weather_data_strategy(draw):
    """Generate valid WeatherData."""
    return WeatherData(
        temperature=draw(st.floats(min_value=-50, max_value=50)),
        feels_like=draw(st.floats(min_value=-50, max_value=50)),
        humidity=draw(st.floats(min_value=0, max_value=100)),
        pressure=draw(st.floats(min_value=900, max_value=1100)),
        wind_speed=draw(st.floats(min_value=0, max_value=50)),
        wind_direction=draw(st.floats(min_value=0, max_value=359)),
        cloud_coverage=draw(st.floats(min_value=0, max_value=100)),
        rain_volume=draw(st.floats(min_value=0, max_value=100)),
        snow_volume=draw(st.floats(min_value=0, max_value=100))
    )


@st.composite
def air_quality_data_strategy(draw):
    """Generate valid AirQualityData."""
    return AirQualityData(
        aqi=draw(st.integers(min_value=1, max_value=5)),
        co=draw(st.floats(min_value=0, max_value=20000)),
        no2=draw(st.floats(min_value=0, max_value=400)),
        o3=draw(st.floats(min_value=0, max_value=500)),
        pm2_5=draw(st.floats(min_value=0, max_value=200)),
        pm10=draw(st.floats(min_value=0, max_value=400))
    )


@st.composite
def flight_data_strategy(draw):
    """Generate valid FlightData."""
    return FlightData(
        active_flights=draw(st.integers(min_value=0, max_value=200)),
        departures=draw(st.integers(min_value=0, max_value=100)),
        arrivals=draw(st.integers(min_value=0, max_value=100)),
        avg_delay=draw(st.floats(min_value=-20, max_value=120))
    )


@st.composite
def city_data_strategy(draw):
    """Generate valid CityData."""
    return CityData(
        timestamp=datetime.now() - timedelta(seconds=draw(st.integers(min_value=0, max_value=3600))),
        location=draw(st.sampled_from(["Munich,DE", "London,UK", "Paris,FR"])),
        weather=draw(weather_data_strategy()),
        air_quality=draw(air_quality_data_strategy()),
        flights=draw(flight_data_strategy())
    )


# Feature: imc-trading-bot, Property 5: Feature computation completeness
@given(city_data=city_data_strategy())
@settings(max_examples=100, deadline=None)
def test_feature_computation_completeness(city_data):
    """
    Property 5: Feature computation completeness
    
    For any Munich data input, the system should compute at least 5 engineered features.
    
    Validates: Requirements 2.1
    """
    engineer = FeatureEngineer(window_size=10)
    
    # Compute features
    features = engineer.compute_features(city_data)
    
    # Verify we have a DataFrame
    assert isinstance(features, pd.DataFrame), "Features should be returned as DataFrame"
    
    # Verify we have at least 5 features
    num_features = len(features.columns)
    assert num_features >= 5, f"Expected at least 5 features, got {num_features}"
    
    # Verify all feature values are numeric
    for col in features.columns:
        assert pd.api.types.is_numeric_dtype(features[col]), f"Feature {col} should be numeric"
    
    # Verify no NaN values
    assert not features.isnull().any().any(), "Features should not contain NaN values"


# Feature: imc-trading-bot, Property 6: Output bounds enforcement
@given(city_data=city_data_strategy())
@settings(max_examples=100, deadline=None)
def test_output_bounds_enforcement(city_data):
    """
    Property 6: Output bounds enforcement
    
    For any computed features, all normalized values should fall within comparable scales,
    and for any generated signal, the strength score should be between -1.0 and 1.0.
    
    Validates: Requirements 2.2, 2.3
    """
    engineer = FeatureEngineer(window_size=10)
    generator = SignalGenerator()
    
    # Compute and normalize features
    features = engineer.compute_features(city_data)
    normalized_features = engineer.normalize(features)
    
    # Verify normalized features are in [0, 1] range
    for col in normalized_features.columns:
        values = normalized_features[col].values
        assert np.all(values >= 0.0), f"Normalized feature {col} has values < 0"
        assert np.all(values <= 1.0), f"Normalized feature {col} has values > 1"
    
    # Generate signals
    signals = generator.generate(normalized_features)
    
    # Verify all signals are in [-1, 1] range
    for signal_name, signal_value in signals.items():
        assert -1.0 <= signal_value <= 1.0, \
            f"Signal {signal_name} = {signal_value} is outside [-1, 1] range"


# Feature: imc-trading-bot, Property 7: Signal combination consistency
@given(
    num_signals=st.integers(min_value=1, max_value=20),
    regime=st.sampled_from(['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain'])
)
@settings(max_examples=100, deadline=None)
def test_signal_combination_consistency(num_signals, regime):
    """
    Property 7: Signal combination consistency
    
    For any set of conflicting signals, the combined output should be a weighted
    aggregation of the inputs.
    
    Validates: Requirements 2.4
    """
    combiner = SignalCombiner(confidence_threshold=0.3)
    
    # Generate random signals in [-1, 1] range
    signal_names = [f"signal_{i}" for i in range(num_signals)]
    signals = {
        name: np.random.uniform(-1.0, 1.0)
        for name in signal_names
    }
    
    # Combine signals
    combined_signal = combiner.combine(signals, regime=regime)
    
    # Verify combined signal strength is in [-1, 1] range
    assert -1.0 <= combined_signal.strength <= 1.0, \
        f"Combined signal strength {combined_signal.strength} is outside [-1, 1] range"
    
    # Verify confidence is in [0, 1] range
    assert 0.0 <= combined_signal.confidence <= 1.0, \
        f"Combined signal confidence {combined_signal.confidence} is outside [0, 1] range"
    
    # Verify regime is preserved
    assert combined_signal.regime == regime, \
        f"Expected regime {regime}, got {combined_signal.regime}"
    
    # Verify components are stored
    assert len(combined_signal.components) == num_signals, \
        f"Expected {num_signals} components, got {len(combined_signal.components)}"
    
    # Verify combined signal is influenced by inputs
    # If all signals are positive, combined should be positive (or zero)
    if all(v > 0 for v in signals.values()):
        assert combined_signal.strength >= 0, \
            "Combined signal should be non-negative when all inputs are positive"
    
    # If all signals are negative, combined should be negative (or zero)
    if all(v < 0 for v in signals.values()):
        assert combined_signal.strength <= 0, \
            "Combined signal should be non-positive when all inputs are negative"


# Feature: imc-trading-bot, Property 8: Confidence-based trading abstention
@given(
    confidence=st.floats(min_value=0.0, max_value=1.0),
    threshold=st.floats(min_value=0.0, max_value=1.0)
)
@settings(max_examples=100, deadline=None)
def test_confidence_based_abstention(confidence, threshold):
    """
    Property 8: Confidence-based trading abstention
    
    For any signal with confidence below threshold, no trade should be executed.
    
    Validates: Requirements 2.5
    """
    combiner = SignalCombiner(confidence_threshold=threshold)
    
    # Create a signal with specific confidence
    from src.utils.types import Signal
    signal = Signal(
        timestamp=datetime.now(),
        strength=0.5,  # Arbitrary strength
        confidence=confidence,
        components={},
        regime='uncertain'
    )
    
    # Check if should trade
    should_trade = combiner.should_trade(signal)
    
    # Verify abstention logic
    if confidence < threshold:
        assert not should_trade, \
            f"Should abstain when confidence {confidence} < threshold {threshold}"
    else:
        assert should_trade, \
            f"Should trade when confidence {confidence} >= threshold {threshold}"


# Additional property: Feature computation is deterministic
@given(city_data=city_data_strategy())
@settings(max_examples=50, deadline=None)
def test_feature_computation_deterministic(city_data):
    """
    Verify that feature computation is deterministic.
    
    For any city data, computing features twice should yield identical results.
    """
    engineer1 = FeatureEngineer(window_size=10)
    engineer2 = FeatureEngineer(window_size=10)
    
    features1 = engineer1.compute_features(city_data)
    features2 = engineer2.compute_features(city_data)
    
    # Verify same columns
    assert set(features1.columns) == set(features2.columns), \
        "Feature columns should be identical"
    
    # Verify same values (within floating point tolerance)
    for col in features1.columns:
        assert np.allclose(features1[col].values, features2[col].values, rtol=1e-9), \
            f"Feature {col} values differ between computations"


# Additional property: Feature computation is deterministic (already tested above)
