"""Constants and location presets for easy configuration.

This module provides predefined location configurations that can be easily
selected by changing a single constant. Perfect for quickly switching between
cities without editing the full config.yaml file.
"""

from typing import Dict, Any


# ============================================================================
# LOCATION PRESETS - Change ACTIVE_LOCATION to switch cities instantly
# ============================================================================

ACTIVE_LOCATION = "MUNICH"  # Change this to switch locations!


# Predefined location configurations
LOCATIONS: Dict[str, Dict[str, Any]] = {
    "MUNICH": {
        "city": "Munich",
        "country": "DE",
        "coordinates": {"lat": 48.1351, "lon": 11.5820},
        "airport_code": "MUC",
        "timezone": "Europe/Berlin",
    },
    "LONDON": {
        "city": "London",
        "country": "UK",
        "coordinates": {"lat": 51.5074, "lon": -0.1278},
        "airport_code": "LHR",
        "timezone": "Europe/London",
    },
    "NEW_YORK": {
        "city": "New York",
        "country": "US",
        "coordinates": {"lat": 40.7128, "lon": -74.0060},
        "airport_code": "JFK",
        "timezone": "America/New_York",
    },
    "TOKYO": {
        "city": "Tokyo",
        "country": "JP",
        "coordinates": {"lat": 35.6762, "lon": 139.6503},
        "airport_code": "NRT",
        "timezone": "Asia/Tokyo",
    },
    "SINGAPORE": {
        "city": "Singapore",
        "country": "SG",
        "coordinates": {"lat": 1.3521, "lon": 103.8198},
        "airport_code": "SIN",
        "timezone": "Asia/Singapore",
    },
    "PARIS": {
        "city": "Paris",
        "country": "FR",
        "coordinates": {"lat": 48.8566, "lon": 2.3522},
        "airport_code": "CDG",
        "timezone": "Europe/Paris",
    },
    "HONG_KONG": {
        "city": "Hong Kong",
        "country": "HK",
        "coordinates": {"lat": 22.3193, "lon": 114.1694},
        "airport_code": "HKG",
        "timezone": "Asia/Hong_Kong",
    },
    "SYDNEY": {
        "city": "Sydney",
        "country": "AU",
        "coordinates": {"lat": -33.8688, "lon": 151.2093},
        "airport_code": "SYD",
        "timezone": "Australia/Sydney",
    },
}


def get_active_location() -> Dict[str, Any]:
    """
    Get the currently active location configuration.
    
    Returns:
        Location configuration dictionary
        
    Raises:
        ValueError: If ACTIVE_LOCATION is not found in LOCATIONS
        
    Example:
        >>> location = get_active_location()
        >>> print(f"Trading with data from {location['city']}")
    """
    if ACTIVE_LOCATION not in LOCATIONS:
        raise ValueError(
            f"Unknown location: {ACTIVE_LOCATION}. "
            f"Available locations: {', '.join(LOCATIONS.keys())}"
        )
    
    return LOCATIONS[ACTIVE_LOCATION].copy()


def get_location_string() -> str:
    """
    Get location string in format 'City,Country' for API calls.
    
    Returns:
        Location string (e.g., 'Munich,DE')
    """
    location = get_active_location()
    return f"{location['city']},{location['country']}"


def get_coordinates() -> tuple[float, float]:
    """
    Get coordinates as (latitude, longitude) tuple.
    
    Returns:
        Tuple of (lat, lon)
    """
    location = get_active_location()
    coords = location['coordinates']
    return coords['lat'], coords['lon']


def get_bounding_box(offset: float = 0.5) -> list[float]:
    """
    Get bounding box for flight data around the location.
    
    Args:
        offset: Degrees to extend in each direction (default: 0.5)
        
    Returns:
        Bounding box as [lon_min, lat_min, lon_max, lat_max]
    """
    lat, lon = get_coordinates()
    return [
        lon - offset,  # lon_min
        lat - offset,  # lat_min
        lon + offset,  # lon_max
        lat + offset,  # lat_max
    ]


# ============================================================================
# API ENDPOINTS
# ============================================================================

API_ENDPOINTS = {
    "weather": "https://api.openweathermap.org/data/2.5/weather",
    "air_quality": "https://api.openweathermap.org/data/2.5/air_pollution",
    "flights": "https://opensky-network.org/api/states/all",
}


# ============================================================================
# TRADING CONSTANTS
# ============================================================================

# Signal thresholds
MIN_SIGNAL_STRENGTH = 0.3
MIN_CONFIDENCE = 0.5

# Risk limits
MAX_POSITION_SIZE = 0.20  # 20% per position
MAX_TOTAL_EXPOSURE = 0.80  # 80% total
DRAWDOWN_REDUCTION_THRESHOLD = 0.15  # 15%
DRAWDOWN_SAFE_MODE_THRESHOLD = 0.25  # 25%

# Performance targets
TARGET_SHARPE_RATIO = 1.5
TARGET_MAX_DRAWDOWN = 0.20
TARGET_WIN_RATE = 0.55

# Latency targets (milliseconds)
MAX_DATA_PROCESSING_LATENCY = 100
MAX_ORDER_SUBMISSION_LATENCY = 50
MAX_REGIME_DETECTION_LATENCY = 1000
