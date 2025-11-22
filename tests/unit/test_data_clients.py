"""Unit tests for data client implementations.

Tests verify that data clients correctly transform and validate API responses.
"""

import pytest
from datetime import datetime

from src.data.weather import WeatherClient
from src.data.air_quality import AirQualityClient
from src.data.flights import FlightClient


class TestWeatherClient:
    """Test WeatherClient validation and transformation."""
    
    def test_validate_valid_data(self):
        """Test validation accepts valid weather data."""
        client = WeatherClient(api_key="test_key", location="Munich,DE")
        
        valid_data = {
            'main': {
                'temp': 20.0,
                'feels_like': 18.0,
                'humidity': 60,
                'pressure': 1013
            },
            'wind': {
                'speed': 5.0,
                'deg': 180
            },
            'clouds': {
                'all': 50
            }
        }
        
        assert client.validate(valid_data) is True
    
    def test_validate_missing_fields(self):
        """Test validation rejects data with missing fields."""
        client = WeatherClient(api_key="test_key", location="Munich,DE")
        
        invalid_data = {
            'main': {
                'temp': 20.0
                # Missing other required fields
            }
        }
        
        assert client.validate(invalid_data) is False
    
    def test_transform_data(self):
        """Test data transformation to internal format."""
        client = WeatherClient(api_key="test_key", location="Munich,DE")
        
        raw_data = {
            'main': {
                'temp': 20.0,
                'feels_like': 18.0,
                'humidity': 60,
                'pressure': 1013
            },
            'wind': {
                'speed': 5.0,
                'deg': 180
            },
            'clouds': {
                'all': 50
            },
            'rain': {
                '1h': 2.5
            }
        }
        
        transformed = client._transform(raw_data)
        
        assert transformed['temperature'] == 20.0
        assert transformed['feels_like'] == 18.0
        assert transformed['humidity'] == 60
        assert transformed['pressure'] == 1013
        assert transformed['wind_speed'] == 5.0
        assert transformed['wind_direction'] == 180
        assert transformed['cloud_coverage'] == 50
        assert transformed['rain_volume'] == 2.5
        assert transformed['snow_volume'] == 0.0


class TestAirQualityClient:
    """Test AirQualityClient validation and transformation."""
    
    def test_validate_valid_data(self):
        """Test validation accepts valid air quality data."""
        client = AirQualityClient(api_key="test_key", lat=48.1351, lon=11.5820)
        
        valid_data = {
            'list': [
                {
                    'main': {
                        'aqi': 2
                    },
                    'components': {
                        'co': 250.0,
                        'no2': 30.0,
                        'o3': 50.0,
                        'pm2_5': 15.0,
                        'pm10': 25.0
                    }
                }
            ]
        }
        
        assert client.validate(valid_data) is True
    
    def test_validate_empty_list(self):
        """Test validation rejects empty data list."""
        client = AirQualityClient(api_key="test_key", lat=48.1351, lon=11.5820)
        
        invalid_data = {
            'list': []
        }
        
        assert client.validate(invalid_data) is False
    
    def test_transform_data(self):
        """Test data transformation to internal format."""
        client = AirQualityClient(api_key="test_key", lat=48.1351, lon=11.5820)
        
        raw_data = {
            'list': [
                {
                    'main': {
                        'aqi': 2
                    },
                    'components': {
                        'co': 250.0,
                        'no2': 30.0,
                        'o3': 50.0,
                        'pm2_5': 15.0,
                        'pm10': 25.0
                    }
                }
            ]
        }
        
        transformed = client._transform(raw_data)
        
        assert transformed['aqi'] == 2
        assert transformed['co'] == 250.0
        assert transformed['no2'] == 30.0
        assert transformed['o3'] == 50.0
        assert transformed['pm2_5'] == 15.0
        assert transformed['pm10'] == 25.0


class TestFlightClient:
    """Test FlightClient validation and transformation."""
    
    def test_validate_valid_data(self):
        """Test validation accepts valid flight data."""
        bbox = [11.0, 47.5, 12.0, 48.5]
        client = FlightClient(bbox=bbox, airport_code="MUC")
        
        valid_data = {
            'states': [
                ['abc123', 'LH123', 'Germany', 1234567890, 1234567890,
                 11.5, 48.1, 1000, False, 250, 90, 0, None, 1000, None, False, 0]
            ]
        }
        
        assert client.validate(valid_data) is True
    
    def test_validate_no_flights(self):
        """Test validation accepts None states (no flights)."""
        bbox = [11.0, 47.5, 12.0, 48.5]
        client = FlightClient(bbox=bbox, airport_code="MUC")
        
        valid_data = {
            'states': None
        }
        
        assert client.validate(valid_data) is True
    
    def test_transform_data_with_flights(self):
        """Test data transformation with active flights."""
        bbox = [11.0, 47.5, 12.0, 48.5]
        client = FlightClient(bbox=bbox, airport_code="MUC")
        
        raw_data = {
            'states': [
                ['abc123', 'LH123', 'Germany', 1234567890, 1234567890,
                 11.5, 48.1, 500, False, 250, 90, 0, None, 500, None, False, 0],
                ['def456', 'LH456', 'Germany', 1234567890, 1234567890,
                 11.6, 48.2, 800, False, 200, 180, 0, None, 800, None, False, 0]
            ]
        }
        
        transformed = client._transform(raw_data)
        
        assert transformed['active_flights'] == 2
        assert transformed['departures'] >= 0
        assert transformed['arrivals'] >= 0
        assert transformed['avg_delay'] == 0.0
    
    def test_transform_data_no_flights(self):
        """Test data transformation with no flights."""
        bbox = [11.0, 47.5, 12.0, 48.5]
        client = FlightClient(bbox=bbox, airport_code="MUC")
        
        raw_data = {
            'states': None
        }
        
        transformed = client._transform(raw_data)
        
        assert transformed['active_flights'] == 0
        assert transformed['departures'] == 0
        assert transformed['arrivals'] == 0
        assert transformed['avg_delay'] == 0.0
