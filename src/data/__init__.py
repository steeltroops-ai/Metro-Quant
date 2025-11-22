"""Data ingestion layer for fetching external data sources.

This module provides async clients for weather, air quality, and flight data,
along with caching support for resilient operation.
"""

from src.data.base import DataClient
from src.data.cache import CacheManager
from src.data.weather import WeatherClient
from src.data.air_quality import AirQualityClient
from src.data.flights import FlightClient

__all__ = [
    'DataClient',
    'CacheManager',
    'WeatherClient',
    'AirQualityClient',
    'FlightClient',
]
