"""Weather data client for OpenWeatherMap API.

This module fetches weather data from OpenWeatherMap API.
"""

from typing import Any, Dict, Optional

from loguru import logger

from src.data.base import DataClient
from src.utils.types import WeatherData


class WeatherClient(DataClient):
    """
    Client for fetching weather data from OpenWeatherMap API.
    
    API Documentation: https://openweathermap.org/current
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
    
    def __init__(self, api_key: str, location: str, timeout: int = 10):
        """
        Initialize weather client.
        
        Args:
            api_key: OpenWeatherMap API key
            location: Location string (e.g., "Munich,DE")
            timeout: Request timeout in seconds
        """
        super().__init__(api_key=api_key, timeout=timeout)
        self.location = location
        logger.info(f"WeatherClient initialized for location: {location}")
    
    async def fetch(self) -> Dict[str, Any]:
        """
        Fetch weather data from OpenWeatherMap API.
        
        Returns:
            Dictionary containing weather data with timestamp
            
        Raises:
            aiohttp.ClientError: If API request fails
            ValueError: If data validation fails
        """
        params = {
            'q': self.location,
            'appid': self.api_key,
            'units': 'metric'  # Use Celsius
        }
        
        try:
            logger.debug(f"Fetching weather data for {self.location}")
            raw_data = await self._get(self.BASE_URL, params=params)
            
            # Validate raw data
            if not self.validate(raw_data):
                raise ValueError("Weather data validation failed")
            
            # Transform to our format
            data = self._transform(raw_data)
            
            # Add timestamp
            data = self._add_timestamp(data)
            
            logger.info(f"Weather data fetched successfully: {data.get('temperature', 'N/A')}°C")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch weather data: {e}")
            raise
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate weather data format.
        
        Args:
            data: Raw API response data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check required fields exist
            required_fields = ['main', 'wind', 'clouds']
            if not all(field in data for field in required_fields):
                logger.warning(f"Weather data missing required fields: {required_fields}")
                return False
            
            # Check main weather data
            main = data.get('main', {})
            required_main = ['temp', 'feels_like', 'humidity', 'pressure']
            if not all(field in main for field in required_main):
                logger.warning(f"Weather main data missing required fields: {required_main}")
                return False
            
            # Check wind data
            wind = data.get('wind', {})
            if 'speed' not in wind:
                logger.warning("Weather data missing wind speed")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Weather data validation error: {e}")
            return False
    
    def _transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw API response to our data format.
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Transformed data dictionary
        """
        main = raw_data.get('main', {})
        wind = raw_data.get('wind', {})
        clouds = raw_data.get('clouds', {})
        rain = raw_data.get('rain', {})
        snow = raw_data.get('snow', {})
        
        return {
            'temperature': main.get('temp', 0.0),
            'feels_like': main.get('feels_like', 0.0),
            'humidity': main.get('humidity', 0.0),
            'pressure': main.get('pressure', 1013.0),
            'wind_speed': wind.get('speed', 0.0),
            'wind_direction': wind.get('deg', 0.0),
            'cloud_coverage': clouds.get('all', 0.0),
            'rain_volume': rain.get('1h', 0.0),  # Rain volume in last hour
            'snow_volume': snow.get('1h', 0.0),  # Snow volume in last hour
        }
    
    def parse_to_model(self, data: Dict[str, Any]) -> WeatherData:
        """
        Parse data dictionary to WeatherData model.
        
        Args:
            data: Data dictionary (without timestamp)
            
        Returns:
            WeatherData model instance
        """
        # Remove timestamp if present
        data_copy = {k: v for k, v in data.items() if k != 'timestamp'}
        return WeatherData(**data_copy)
