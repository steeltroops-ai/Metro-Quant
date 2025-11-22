"""Air quality data client for OpenWeatherMap Air Pollution API.

This module fetches air quality data from OpenWeatherMap Air Pollution API.
"""

from typing import Any, Dict, Optional

from loguru import logger

from src.data.base import DataClient
from src.utils.types import AirQualityData


class AirQualityClient(DataClient):
    """
    Client for fetching air quality data from OpenWeatherMap Air Pollution API.
    
    API Documentation: https://openweathermap.org/api/air-pollution
    """
    
    BASE_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
    
    def __init__(self, api_key: str, lat: float, lon: float, timeout: int = 10):
        """
        Initialize air quality client.
        
        Args:
            api_key: OpenWeatherMap API key
            lat: Latitude coordinate
            lon: Longitude coordinate
            timeout: Request timeout in seconds
        """
        super().__init__(api_key=api_key, timeout=timeout)
        self.lat = lat
        self.lon = lon
        logger.info(f"AirQualityClient initialized for coordinates: ({lat}, {lon})")
    
    async def fetch(self) -> Dict[str, Any]:
        """
        Fetch air quality data from OpenWeatherMap API.
        
        Returns:
            Dictionary containing air quality data with timestamp
            
        Raises:
            aiohttp.ClientError: If API request fails
            ValueError: If data validation fails
        """
        params = {
            'lat': self.lat,
            'lon': self.lon,
            'appid': self.api_key
        }
        
        try:
            logger.debug(f"Fetching air quality data for ({self.lat}, {self.lon})")
            raw_data = await self._get(self.BASE_URL, params=params)
            
            # Validate raw data
            if not self.validate(raw_data):
                raise ValueError("Air quality data validation failed")
            
            # Transform to our format
            data = self._transform(raw_data)
            
            # Add timestamp
            data = self._add_timestamp(data)
            
            logger.info(f"Air quality data fetched successfully: AQI={data.get('aqi', 'N/A')}")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch air quality data: {e}")
            raise
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate air quality data format.
        
        Args:
            data: Raw API response data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check list field exists and has data
            if 'list' not in data or not data['list']:
                logger.warning("Air quality data missing 'list' field or empty")
                return False
            
            # Get first entry (current data)
            entry = data['list'][0]
            
            # Check main AQI field
            if 'main' not in entry or 'aqi' not in entry['main']:
                logger.warning("Air quality data missing AQI")
                return False
            
            # Check components field
            if 'components' not in entry:
                logger.warning("Air quality data missing components")
                return False
            
            # Check required components
            components = entry['components']
            required_components = ['co', 'no2', 'o3', 'pm2_5', 'pm10']
            if not all(comp in components for comp in required_components):
                logger.warning(f"Air quality data missing required components: {required_components}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Air quality data validation error: {e}")
            return False
    
    def _transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw API response to our data format.
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Transformed data dictionary
        """
        # Get first entry (current data)
        entry = raw_data['list'][0]
        main = entry.get('main', {})
        components = entry.get('components', {})
        
        return {
            'aqi': main.get('aqi', 1),
            'co': components.get('co', 0.0),
            'no2': components.get('no2', 0.0),
            'o3': components.get('o3', 0.0),
            'pm2_5': components.get('pm2_5', 0.0),
            'pm10': components.get('pm10', 0.0),
        }
    
    def parse_to_model(self, data: Dict[str, Any]) -> AirQualityData:
        """
        Parse data dictionary to AirQualityData model.
        
        Args:
            data: Data dictionary (without timestamp)
            
        Returns:
            AirQualityData model instance
        """
        # Remove timestamp if present
        data_copy = {k: v for k, v in data.items() if k != 'timestamp'}
        return AirQualityData(**data_copy)
