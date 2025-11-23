"""Signal generation from engineered features.

This module converts normalized features into trading signal scores.
"""

from typing import Dict
import pandas as pd
import numpy as np
from loguru import logger


class SignalGenerator:
    """
    Converts engineered features into trading signal scores.
    
    Signal scores are in the range [-1.0, 1.0] where:
    - Positive values indicate bullish signals
    - Negative values indicate bearish signals
    - Magnitude indicates signal strength
    """
    
    def __init__(self, feature_weights: Dict[str, float] = None):
        """
        Initialize signal generator.
        
        Args:
            feature_weights: Optional custom weights for features
        """
        self.feature_weights = feature_weights or self._default_weights()
        logger.info(f"SignalGenerator initialized with {len(self.feature_weights)} feature weights")
    
    def _default_weights(self) -> Dict[str, float]:
        """
        Define default feature weights for signal generation.
        
        These weights are based on hypothesized correlations with Munich ETF price.
        Positive weights = feature increase suggests price increase
        Negative weights = feature increase suggests price decrease
        """
        return {
            # Weather signals
            'temp_momentum': 0.3,  # Rising temp = more activity
            'pressure_delta': -0.2,  # Falling pressure = bad weather coming
            'precipitation': -0.4,  # Rain/snow = reduced activity
            'wind_speed': -0.2,  # High wind = disruption
            
            # Air quality signals
            'aqi_delta': -0.3,  # Worsening air quality = concern
            'pm2_5_delta': -0.3,  # Particulate increase = pollution event
            
            # Flight signals
            'flight_volume_delta': 0.5,  # More flights = more activity
            'movements_delta': 0.4,  # More takeoffs/landings = busy airport
            'avg_delay': -0.3,  # Delays = operational issues
            
            # Cross signals
            'weather_flight_stress': -0.4,  # Bad weather + few flights = problem
            'temp_activity_factor': 0.2,  # Extreme temps with activity = resilience
            'temp_trend': 0.2,  # Warming trend = positive
            'flights_trend': 0.5,  # Increasing flights = growth
        }
    
    def generate(self, features: pd.DataFrame) -> Dict[str, float]:
        """
        Generate signal strength scores for each feature.
        
        Args:
            features: DataFrame with normalized features (values in [0, 1])
            
        Returns:
            Dictionary mapping feature names to signal scores [-1.0, 1.0]
        """
        signals = {}
        
        # Convert DataFrame to dict for easier access
        feature_dict = features.iloc[0].to_dict() if len(features) > 0 else {}
        
        for feature_name, feature_value in feature_dict.items():
            if feature_name in self.feature_weights:
                weight = self.feature_weights[feature_name]
                
                # Convert normalized feature [0, 1] to signal [-1, 1]
                # Center around 0.5 (neutral point)
                centered_value = (feature_value - 0.5) * 2.0  # Maps [0,1] to [-1,1]
                
                # Apply weight
                signal_score = centered_value * weight
                
                # Clip to [-1, 1] range
                signal_score = np.clip(signal_score, -1.0, 1.0)
                
                signals[feature_name] = float(signal_score)
            else:
                # Unknown feature, assign neutral signal
                signals[feature_name] = 0.0
        
        logger.debug(f"Generated {len(signals)} signals from features")
        return signals
    
    def update_weights(self, new_weights: Dict[str, float]):
        """
        Update feature weights (useful for regime adaptation).
        
        Args:
            new_weights: Dictionary of feature weights to update
        """
        self.feature_weights.update(new_weights)
        logger.info(f"Updated {len(new_weights)} feature weights")
    
    def get_weights(self) -> Dict[str, float]:
        """
        Get current feature weights.
        
        Returns:
            Dictionary of feature weights
        """
        return self.feature_weights.copy()
