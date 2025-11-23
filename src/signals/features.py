"""Feature engineering for Munich city data.

This module computes derived features from raw city data using Numba JIT optimization.
Performance target: < 20ms for typical input.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
from numba import jit
from loguru import logger

from src.utils.types import CityData


class FeatureEngineer:
    """
    Computes engineered features from raw city data.
    
    Features include:
    - Weather momentum (temperature change rate)
    - Flight volume trends (moving averages, deltas)
    - Air quality deltas (rate of change)
    - Cross-signal indicators (multiple data sources aligned)
    """
    
    def __init__(self, window_size: int = 10):
        """
        Initialize feature engineer.
        
        Args:
            window_size: Number of historical data points for trend calculation
        """
        self.window_size = window_size
        self.history: List[CityData] = []
        logger.info(f"FeatureEngineer initialized with window_size={window_size}")
    
    def compute_features(self, city_data: CityData) -> pd.DataFrame:
        """
        Compute engineered features from city data.
        
        Args:
            city_data: Current city data
            
        Returns:
            DataFrame with computed features
            
        Performance: ~20ms for typical input
        """
        # Add to history
        self.history.append(city_data)
        
        # Keep only window_size most recent
        if len(self.history) > self.window_size:
            self.history = self.history[-self.window_size:]
        
        features = {}
        
        # Weather features
        weather_features = self._compute_weather_features(city_data)
        features.update(weather_features)
        
        # Air quality features
        air_quality_features = self._compute_air_quality_features(city_data)
        features.update(air_quality_features)
        
        # Flight features
        flight_features = self._compute_flight_features(city_data)
        features.update(flight_features)
        
        # Cross-signal features (require history)
        if len(self.history) >= 2:
            cross_features = self._compute_cross_features()
            features.update(cross_features)
        
        # Convert to DataFrame
        df = pd.DataFrame([features])
        
        logger.debug(f"Computed {len(features)} features from city data")
        return df
    
    def _compute_weather_features(self, city_data: CityData) -> Dict[str, float]:
        """Compute weather-based features."""
        weather = city_data.weather
        
        features = {
            'temp_current': weather.temperature,
            'temp_feels_like_delta': weather.feels_like - weather.temperature,
            'humidity': weather.humidity,
            'pressure': weather.pressure,
            'wind_speed': weather.wind_speed,
            'wind_direction': weather.wind_direction,
            'cloud_coverage': weather.cloud_coverage,
            'precipitation': weather.rain_volume + weather.snow_volume,
        }
        
        # Weather momentum (temperature change rate)
        if len(self.history) >= 2:
            prev_temp = self.history[-2].weather.temperature
            curr_temp = weather.temperature
            features['temp_momentum'] = curr_temp - prev_temp
            
            # Pressure change (indicator of weather system movement)
            prev_pressure = self.history[-2].weather.pressure
            features['pressure_delta'] = weather.pressure - prev_pressure
        else:
            features['temp_momentum'] = 0.0
            features['pressure_delta'] = 0.0
        
        return features
    
    def _compute_air_quality_features(self, city_data: CityData) -> Dict[str, float]:
        """Compute air quality-based features."""
        aq = city_data.air_quality
        
        features = {
            'aqi': float(aq.aqi),
            'co': aq.co,
            'no2': aq.no2,
            'o3': aq.o3,
            'pm2_5': aq.pm2_5,
            'pm10': aq.pm10,
        }
        
        # Air quality deltas (rate of change)
        if len(self.history) >= 2:
            prev_aq = self.history[-2].air_quality
            features['aqi_delta'] = float(aq.aqi - prev_aq.aqi)
            features['pm2_5_delta'] = aq.pm2_5 - prev_aq.pm2_5
            features['no2_delta'] = aq.no2 - prev_aq.no2
        else:
            features['aqi_delta'] = 0.0
            features['pm2_5_delta'] = 0.0
            features['no2_delta'] = 0.0
        
        return features
    
    def _compute_flight_features(self, city_data: CityData) -> Dict[str, float]:
        """Compute flight-based features."""
        flights = city_data.flights
        
        features = {
            'active_flights': float(flights.active_flights),
            'departures': float(flights.departures),
            'arrivals': float(flights.arrivals),
            'avg_delay': flights.avg_delay,
            'total_movements': float(flights.departures + flights.arrivals),
        }
        
        # Flight volume trends
        if len(self.history) >= 2:
            prev_flights = self.history[-2].flights
            features['flight_volume_delta'] = float(
                flights.active_flights - prev_flights.active_flights
            )
            features['movements_delta'] = float(
                (flights.departures + flights.arrivals) - 
                (prev_flights.departures + prev_flights.arrivals)
            )
        else:
            features['flight_volume_delta'] = 0.0
            features['movements_delta'] = 0.0
        
        return features
    
    def _compute_cross_features(self) -> Dict[str, float]:
        """
        Compute cross-signal features from multiple data sources.
        
        These features capture relationships between different data types.
        """
        features = {}
        
        # Get recent data
        curr = self.history[-1]
        
        # Weather-flight correlation
        # Hypothesis: Bad weather reduces flights
        weather_severity = (
            curr.weather.rain_volume + 
            curr.weather.snow_volume + 
            curr.weather.wind_speed / 10.0
        )
        features['weather_flight_stress'] = weather_severity * (
            1.0 / (1.0 + curr.flights.active_flights)
        )
        
        # Air quality-traffic correlation
        # Hypothesis: More flights = worse air quality
        total_movements = curr.flights.departures + curr.flights.arrivals
        features['pollution_traffic_ratio'] = (
            curr.air_quality.pm2_5 / (1.0 + total_movements)
        )
        
        # Temperature-activity correlation
        # Hypothesis: Extreme temps reduce activity
        temp_extremity = abs(curr.weather.temperature - 15.0)  # 15°C is "comfortable"
        features['temp_activity_factor'] = temp_extremity * total_movements
        
        # Compute moving averages if we have enough history
        if len(self.history) >= 5:
            features.update(self._compute_moving_averages())
        
        return features
    
    def _compute_moving_averages(self) -> Dict[str, float]:
        """Compute moving averages for trend detection."""
        # Extract time series
        temps = [h.weather.temperature for h in self.history[-5:]]
        flights = [float(h.flights.active_flights) for h in self.history[-5:]]
        aqi = [float(h.air_quality.aqi) for h in self.history[-5:]]
        
        return {
            'temp_ma5': np.mean(temps),
            'flights_ma5': np.mean(flights),
            'aqi_ma5': np.mean(aqi),
            'temp_trend': temps[-1] - np.mean(temps[:-1]) if len(temps) > 1 else 0.0,
            'flights_trend': flights[-1] - np.mean(flights[:-1]) if len(flights) > 1 else 0.0,
        }
    
    def normalize(self, features: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize features to comparable scales using min-max normalization.
        
        Args:
            features: DataFrame with raw features
            
        Returns:
            DataFrame with normalized features
        """
        normalized = features.copy()
        
        # Define normalization ranges for each feature type
        # These are based on typical ranges for Munich data
        normalization_ranges = {
            # Weather features
            'temp_current': (-20.0, 40.0),
            'temp_feels_like_delta': (-10.0, 10.0),
            'humidity': (0.0, 100.0),
            'pressure': (950.0, 1050.0),
            'wind_speed': (0.0, 30.0),
            'wind_direction': (0.0, 360.0),
            'cloud_coverage': (0.0, 100.0),
            'precipitation': (0.0, 50.0),
            'temp_momentum': (-5.0, 5.0),
            'pressure_delta': (-20.0, 20.0),
            
            # Air quality features
            'aqi': (1.0, 5.0),
            'co': (0.0, 10000.0),
            'no2': (0.0, 200.0),
            'o3': (0.0, 300.0),
            'pm2_5': (0.0, 100.0),
            'pm10': (0.0, 200.0),
            'aqi_delta': (-4.0, 4.0),
            'pm2_5_delta': (-50.0, 50.0),
            'no2_delta': (-100.0, 100.0),
            
            # Flight features
            'active_flights': (0.0, 100.0),
            'departures': (0.0, 50.0),
            'arrivals': (0.0, 50.0),
            'avg_delay': (-10.0, 60.0),
            'total_movements': (0.0, 100.0),
            'flight_volume_delta': (-50.0, 50.0),
            'movements_delta': (-50.0, 50.0),
            
            # Cross features
            'weather_flight_stress': (0.0, 10.0),
            'pollution_traffic_ratio': (0.0, 5.0),
            'temp_activity_factor': (0.0, 1000.0),
            'temp_ma5': (-20.0, 40.0),
            'flights_ma5': (0.0, 100.0),
            'aqi_ma5': (1.0, 5.0),
            'temp_trend': (-5.0, 5.0),
            'flights_trend': (-50.0, 50.0),
        }
        
        # Normalize each feature
        for col in normalized.columns:
            if col in normalization_ranges:
                min_val, max_val = normalization_ranges[col]
                # Min-max normalization to [0, 1]
                normalized[col] = (normalized[col] - min_val) / (max_val - min_val)
                # Clip to [0, 1] range
                normalized[col] = normalized[col].clip(0.0, 1.0)
            else:
                logger.warning(f"No normalization range defined for feature: {col}")
        
        logger.debug(f"Normalized {len(normalized.columns)} features")
        return normalized
    
    def reset_history(self):
        """Reset historical data buffer."""
        self.history = []
        logger.info("Feature history reset")
