"""Type definitions and data models for the trading bot.

This module defines all core data structures using Pydantic for validation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


# Munich Data Models

class WeatherData(BaseModel):
    """Weather data from OpenWeatherMap API."""
    
    temperature: float = Field(..., description="Temperature in Celsius")
    feels_like: float = Field(..., description="Feels like temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    pressure: float = Field(..., gt=0, description="Atmospheric pressure in hPa")
    wind_speed: float = Field(..., ge=0, description="Wind speed in m/s")
    wind_direction: float = Field(..., ge=0, lt=360, description="Wind direction in degrees")
    cloud_coverage: float = Field(..., ge=0, le=100, description="Cloud coverage percentage")
    rain_volume: float = Field(default=0.0, ge=0, description="Rain volume in mm")
    snow_volume: float = Field(default=0.0, ge=0, description="Snow volume in mm")
    
    @field_validator('temperature', 'feels_like')
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        """Validate temperature is within reasonable bounds."""
        if v < -100 or v > 60:
            raise ValueError(f"Temperature {v}°C is outside reasonable bounds [-100, 60]")
        return v


class AirQualityData(BaseModel):
    """Air quality data from OpenWeatherMap Air Pollution API."""
    
    aqi: int = Field(..., ge=1, le=5, description="Air Quality Index (1-5)")
    co: float = Field(..., ge=0, description="Carbon monoxide in μg/m³")
    no2: float = Field(..., ge=0, description="Nitrogen dioxide in μg/m³")
    o3: float = Field(..., ge=0, description="Ozone in μg/m³")
    pm2_5: float = Field(..., ge=0, description="Fine particulate matter in μg/m³")
    pm10: float = Field(..., ge=0, description="Coarse particulate matter in μg/m³")


class FlightData(BaseModel):
    """Flight data from OpenSky Network API."""
    
    active_flights: int = Field(..., ge=0, description="Number of flights in Munich airspace")
    departures: int = Field(..., ge=0, description="Departures from MUC in last hour")
    arrivals: int = Field(..., ge=0, description="Arrivals to MUC in last hour")
    avg_delay: float = Field(..., description="Average delay in minutes")


class CityData(BaseModel):
    """Combined city data (location-agnostic)."""
    
    timestamp: datetime = Field(..., description="Data timestamp")
    location: str = Field(..., description="City location (e.g., 'Munich,DE', 'London,UK')")
    weather: WeatherData
    air_quality: AirQualityData
    flights: FlightData
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        """Validate timestamp is not in the future."""
        if v > datetime.now():
            raise ValueError("Timestamp cannot be in the future")
        return v


# Backward compatibility alias
MunichData = CityData


# Market Data Models

class MarketData(BaseModel):
    """Market data for trading instruments."""
    
    timestamp: datetime = Field(..., description="Market data timestamp")
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    price: float = Field(..., gt=0, description="Current price")
    volume: float = Field(..., ge=0, description="Trading volume")
    bid: float = Field(..., gt=0, description="Best bid price")
    ask: float = Field(..., gt=0, description="Best ask price")
    returns: List[float] = Field(default_factory=list, description="Historical returns for regime detection")
    
    @field_validator('bid', 'ask')
    @classmethod
    def validate_bid_ask(cls, v: float, info) -> float:
        """Validate bid/ask spread is reasonable."""
        if 'bid' in info.data and 'ask' in info.data:
            bid = info.data.get('bid', 0)
            ask = info.data.get('ask', 0)
            if bid > 0 and ask > 0 and bid > ask:
                raise ValueError(f"Bid {bid} cannot be greater than ask {ask}")
        return v


class Signal(BaseModel):
    """Trading signal with metadata."""
    
    timestamp: datetime = Field(..., description="Signal generation timestamp")
    strength: float = Field(..., ge=-1.0, le=1.0, description="Signal strength [-1.0, 1.0]")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Signal confidence [0.0, 1.0]")
    components: Dict[str, float] = Field(default_factory=dict, description="Individual signal contributions")
    regime: str = Field(..., description="Current market regime")
    
    @field_validator('regime')
    @classmethod
    def validate_regime(cls, v: str) -> str:
        """Validate regime is one of the expected values."""
        valid_regimes = {'trending', 'mean-reverting', 'high-volatility', 'low-volatility', 'uncertain'}
        if v not in valid_regimes:
            raise ValueError(f"Regime '{v}' must be one of {valid_regimes}")
        return v


class Position(BaseModel):
    """Trading position."""
    
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    size: float = Field(..., description="Position size (positive for long, negative for short)")
    entry_price: float = Field(..., gt=0, description="Entry price")
    current_price: float = Field(..., gt=0, description="Current market price")
    unrealized_pnl: float = Field(..., description="Unrealized profit/loss")
    
    @field_validator('unrealized_pnl')
    @classmethod
    def calculate_pnl(cls, v: float, info) -> float:
        """Calculate unrealized PnL if not provided."""
        if 'size' in info.data and 'entry_price' in info.data and 'current_price' in info.data:
            size = info.data['size']
            entry = info.data['entry_price']
            current = info.data['current_price']
            calculated_pnl = size * (current - entry)
            # Allow provided value or calculate
            return v if v != 0 else calculated_pnl
        return v


class Order(BaseModel):
    """Trading order."""
    
    order_id: str = Field(..., min_length=1, description="Unique order identifier")
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    size: float = Field(..., description="Order size (positive for buy, negative for sell)")
    limit_price: float = Field(..., gt=0, description="Limit price")
    status: str = Field(..., description="Order status")
    timestamp: datetime = Field(..., description="Order creation timestamp")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate order status is one of the expected values."""
        valid_statuses = {'pending', 'filled', 'cancelled', 'rejected'}
        if v not in valid_statuses:
            raise ValueError(f"Status '{v}' must be one of {valid_statuses}")
        return v
    
    @field_validator('size')
    @classmethod
    def validate_size(cls, v: float) -> float:
        """Validate order size is non-zero."""
        if v == 0:
            raise ValueError("Order size cannot be zero")
        return v
