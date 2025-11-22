"""Property-based tests for data model validation.

Feature: imc-trading-bot, Property 3: Input validation rejects malformed data
Validates: Requirements 1.4
"""

from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings
from pydantic import ValidationError
import pytest

from src.utils.types import (
    WeatherData,
    AirQualityData,
    FlightData,
    MunichData,
    MarketData,
    Signal,
    Position,
    Order,
)


# Strategies for generating valid data

@st.composite
def valid_weather_data(draw):
    """Generate valid weather data."""
    return {
        "temperature": draw(st.floats(min_value=-50, max_value=50)),
        "feels_like": draw(st.floats(min_value=-50, max_value=50)),
        "humidity": draw(st.floats(min_value=0, max_value=100)),
        "pressure": draw(st.floats(min_value=900, max_value=1100)),
        "wind_speed": draw(st.floats(min_value=0, max_value=50)),
        "wind_direction": draw(st.floats(min_value=0, max_value=359.99)),
        "cloud_coverage": draw(st.floats(min_value=0, max_value=100)),
        "rain_volume": draw(st.floats(min_value=0, max_value=100)),
        "snow_volume": draw(st.floats(min_value=0, max_value=100)),
    }


@st.composite
def valid_air_quality_data(draw):
    """Generate valid air quality data."""
    return {
        "aqi": draw(st.integers(min_value=1, max_value=5)),
        "co": draw(st.floats(min_value=0, max_value=10000)),
        "no2": draw(st.floats(min_value=0, max_value=1000)),
        "o3": draw(st.floats(min_value=0, max_value=500)),
        "pm2_5": draw(st.floats(min_value=0, max_value=500)),
        "pm10": draw(st.floats(min_value=0, max_value=1000)),
    }


@st.composite
def valid_flight_data(draw):
    """Generate valid flight data."""
    return {
        "active_flights": draw(st.integers(min_value=0, max_value=1000)),
        "departures": draw(st.integers(min_value=0, max_value=500)),
        "arrivals": draw(st.integers(min_value=0, max_value=500)),
        "avg_delay": draw(st.floats(min_value=-30, max_value=300)),
    }


@st.composite
def valid_market_data(draw):
    """Generate valid market data."""
    price = draw(st.floats(min_value=0.01, max_value=10000))
    spread = draw(st.floats(min_value=0.001, max_value=price * 0.1))
    bid = price - spread / 2
    ask = price + spread / 2
    
    return {
        "timestamp": datetime.now() - timedelta(seconds=draw(st.integers(min_value=0, max_value=3600))),
        "symbol": draw(st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll')))),
        "price": price,
        "volume": draw(st.floats(min_value=0, max_value=1000000)),
        "bid": bid,
        "ask": ask,
        "returns": draw(st.lists(st.floats(min_value=-0.5, max_value=0.5), max_size=100)),
    }


@st.composite
def valid_signal(draw):
    """Generate valid signal data."""
    valid_regimes = ['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']
    return {
        "timestamp": datetime.now() - timedelta(seconds=draw(st.integers(min_value=0, max_value=3600))),
        "strength": draw(st.floats(min_value=-1.0, max_value=1.0)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0)),
        "components": draw(st.dictionaries(st.text(min_size=1, max_size=20), st.floats(min_value=-1, max_value=1), max_size=10)),
        "regime": draw(st.sampled_from(valid_regimes)),
    }


# Property 3: Input validation rejects malformed data
# For any malformed data input, the system should reject it

@given(st.floats(min_value=-200, max_value=-101) | st.floats(min_value=61, max_value=200))
@settings(max_examples=100)
def test_weather_rejects_extreme_temperatures(temp):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        WeatherData(
            temperature=temp,
            feels_like=20,
            humidity=50,
            pressure=1013,
            wind_speed=5,
            wind_direction=180,
            cloud_coverage=50,
        )


@given(st.floats(min_value=-1000, max_value=-0.01) | st.floats(min_value=101, max_value=1000))
@settings(max_examples=100)
def test_weather_rejects_invalid_humidity(humidity):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        WeatherData(
            temperature=20,
            feels_like=20,
            humidity=humidity,
            pressure=1013,
            wind_speed=5,
            wind_direction=180,
            cloud_coverage=50,
        )


@given(st.integers(min_value=-100, max_value=0) | st.integers(min_value=6, max_value=100))
@settings(max_examples=100)
def test_air_quality_rejects_invalid_aqi(aqi):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        AirQualityData(
            aqi=aqi,
            co=100,
            no2=50,
            o3=80,
            pm2_5=25,
            pm10=50,
        )


@given(st.floats(min_value=-1000, max_value=-0.01))
@settings(max_examples=100)
def test_air_quality_rejects_negative_pollutants(value):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        AirQualityData(
            aqi=3,
            co=value,
            no2=50,
            o3=80,
            pm2_5=25,
            pm10=50,
        )


@given(st.integers(min_value=-1000, max_value=-1))
@settings(max_examples=100)
def test_flight_rejects_negative_counts(count):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        FlightData(
            active_flights=count,
            departures=10,
            arrivals=10,
            avg_delay=5,
        )


@given(st.floats(min_value=-1000, max_value=0) | st.floats(allow_nan=True, allow_infinity=True))
@settings(max_examples=100)
def test_market_data_rejects_invalid_prices(price):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    if price <= 0 or not (price == price):  # Check for NaN
        with pytest.raises(ValidationError):
            MarketData(
                timestamp=datetime.now(),
                symbol="TEST",
                price=price,
                volume=1000,
                bid=price * 0.99 if price > 0 else 1,
                ask=price * 1.01 if price > 0 else 1,
            )


@given(st.floats(min_value=-2.0, max_value=-1.01) | st.floats(min_value=1.01, max_value=2.0))
@settings(max_examples=100)
def test_signal_rejects_out_of_bounds_strength(strength):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        Signal(
            timestamp=datetime.now(),
            strength=strength,
            confidence=0.8,
            components={},
            regime="trending",
        )


@given(st.text(min_size=1, max_size=20).filter(lambda x: x not in ['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']))
@settings(max_examples=100)
def test_signal_rejects_invalid_regime(regime):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        Signal(
            timestamp=datetime.now(),
            strength=0.5,
            confidence=0.8,
            components={},
            regime=regime,
        )


@given(st.text(min_size=1, max_size=20).filter(lambda x: x not in ['pending', 'filled', 'cancelled', 'rejected']))
@settings(max_examples=100)
def test_order_rejects_invalid_status(status):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        Order(
            order_id="ORDER123",
            symbol="TEST",
            size=100,
            limit_price=50.0,
            status=status,
            timestamp=datetime.now(),
        )


@given(st.just(0.0))
@settings(max_examples=100)
def test_order_rejects_zero_size(size):
    """Feature: imc-trading-bot, Property 3: Input validation rejects malformed data"""
    with pytest.raises(ValidationError):
        Order(
            order_id="ORDER123",
            symbol="TEST",
            size=size,
            limit_price=50.0,
            status="pending",
            timestamp=datetime.now(),
        )


# Property 3: Input validation accepts valid data
# For any valid data input, the system should accept and process it

@given(valid_weather_data())
@settings(max_examples=100)
def test_weather_accepts_valid_data(data):
    """Feature: imc-trading-bot, Property 3: Input validation accepts valid data"""
    weather = WeatherData(**data)
    assert weather.temperature == data["temperature"]
    assert weather.humidity >= 0 and weather.humidity <= 100


@given(valid_air_quality_data())
@settings(max_examples=100)
def test_air_quality_accepts_valid_data(data):
    """Feature: imc-trading-bot, Property 3: Input validation accepts valid data"""
    air_quality = AirQualityData(**data)
    assert air_quality.aqi >= 1 and air_quality.aqi <= 5
    assert air_quality.co >= 0


@given(valid_flight_data())
@settings(max_examples=100)
def test_flight_accepts_valid_data(data):
    """Feature: imc-trading-bot, Property 3: Input validation accepts valid data"""
    flight = FlightData(**data)
    assert flight.active_flights >= 0
    assert flight.departures >= 0


@given(valid_market_data())
@settings(max_examples=100)
def test_market_data_accepts_valid_data(data):
    """Feature: imc-trading-bot, Property 3: Input validation accepts valid data"""
    market = MarketData(**data)
    assert market.price > 0
    assert market.bid > 0
    assert market.ask > 0
    assert market.bid <= market.ask


@given(valid_signal())
@settings(max_examples=100)
def test_signal_accepts_valid_data(data):
    """Feature: imc-trading-bot, Property 3: Input validation accepts valid data"""
    signal = Signal(**data)
    assert signal.strength >= -1.0 and signal.strength <= 1.0
    assert signal.confidence >= 0.0 and signal.confidence <= 1.0
    assert signal.regime in ['trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain']