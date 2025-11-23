"""Adaptive strategy with regime-specific parameters.

This module provides regime-specific trading logic and signal weights.
"""

from typing import Dict, Any
from loguru import logger


class AdaptiveStrategy:
    """
    Adaptive trading strategy that adjusts parameters based on market regime.
    
    Different regimes require different approaches:
    - Trending: Follow momentum, use trailing stops
    - Mean-reverting: Fade moves, use tight stops
    - High-volatility: Reduce size, widen stops
    - Low-volatility: Normal size, standard stops
    """
    
    def __init__(self):
        """Initialize adaptive strategy with regime-specific configurations."""
        self.regime_configs = self._initialize_regime_configs()
        logger.info("AdaptiveStrategy initialized with regime-specific configurations")
    
    def _initialize_regime_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        Initialize regime-specific strategy configurations.
        
        Returns:
            Dictionary mapping regime names to configuration dictionaries
        """
        return {
            'trending': {
                'signal_weights': {
                    'temp_momentum': 0.5,
                    'temp_trend': 0.6,
                    'flights_trend': 0.7,
                    'flight_volume_delta': 0.6,
                    'movements_delta': 0.5,
                    'precipitation': -0.3,
                    'avg_delay': -0.2,
                },
                'position_multiplier': 1.0,  # Normal position size
                'stop_loss_pct': 0.02,  # 2% stop loss
                'take_profit_pct': 0.05,  # 5% take profit
                'signal_threshold': 0.3,  # Lower threshold in trending markets
                'max_holding_period': 3600,  # 1 hour max hold
            },
            'mean-reverting': {
                'signal_weights': {
                    'temp_momentum': -0.4,  # Fade momentum
                    'pressure_delta': 0.5,
                    'aqi_delta': 0.4,
                    'weather_flight_stress': 0.6,
                    'precipitation': 0.4,
                    'flight_volume_delta': -0.3,  # Fade volume spikes
                },
                'position_multiplier': 0.8,  # Slightly smaller positions
                'stop_loss_pct': 0.015,  # 1.5% tight stop
                'take_profit_pct': 0.03,  # 3% quick profit target
                'signal_threshold': 0.4,  # Higher threshold for mean reversion
                'max_holding_period': 1800,  # 30 min max hold
            },
            'high-volatility': {
                'signal_weights': {
                    # Trust stable, observable indicators
                    'precipitation': 0.6,
                    'avg_delay': 0.5,
                    'weather_flight_stress': 0.7,
                    'wind_speed': -0.4,
                    'aqi_delta': 0.3,
                },
                'position_multiplier': 0.5,  # Half size in volatile markets
                'stop_loss_pct': 0.04,  # 4% wider stop
                'take_profit_pct': 0.08,  # 8% wider target
                'signal_threshold': 0.5,  # Higher threshold for safety
                'max_holding_period': 900,  # 15 min max hold
            },
            'low-volatility': {
                'signal_weights': {
                    # Trust all signals in stable markets
                    'temp_momentum': 0.4,
                    'flight_volume_delta': 0.5,
                    'movements_delta': 0.4,
                    'temp_trend': 0.4,
                    'flights_trend': 0.5,
                    'pressure_delta': -0.3,
                    'aqi_delta': -0.3,
                },
                'position_multiplier': 1.2,  # Larger positions in stable markets
                'stop_loss_pct': 0.01,  # 1% tight stop
                'take_profit_pct': 0.025,  # 2.5% target
                'signal_threshold': 0.25,  # Lower threshold in stable markets
                'max_holding_period': 7200,  # 2 hour max hold
            },
            'uncertain': {
                'signal_weights': {
                    # Conservative: only strong, stable signals
                    'precipitation': 0.5,
                    'flight_volume_delta': 0.4,
                    'movements_delta': 0.4,
                    'weather_flight_stress': 0.5,
                },
                'position_multiplier': 0.3,  # Very small positions
                'stop_loss_pct': 0.02,  # 2% stop
                'take_profit_pct': 0.04,  # 4% target
                'signal_threshold': 0.6,  # High threshold for safety
                'max_holding_period': 600,  # 10 min max hold
            }
        }
    
    def get_signal_weights(self, regime: str) -> Dict[str, float]:
        """
        Get regime-specific signal weights.
        
        Args:
            regime: Current market regime
            
        Returns:
            Dictionary of signal weights for the regime
        """
        config = self.regime_configs.get(regime, self.regime_configs['uncertain'])
        weights = config['signal_weights'].copy()
        
        logger.debug(f"Retrieved {len(weights)} signal weights for regime '{regime}'")
        return weights
    
    def get_parameters(self, regime: str) -> Dict[str, Any]:
        """
        Get regime-specific strategy parameters.
        
        Args:
            regime: Current market regime
            
        Returns:
            Dictionary of strategy parameters
        """
        config = self.regime_configs.get(regime, self.regime_configs['uncertain'])
        
        # Return all parameters except signal_weights
        params = {k: v for k, v in config.items() if k != 'signal_weights'}
        
        logger.debug(f"Retrieved parameters for regime '{regime}': {params}")
        return params
    
    def get_position_multiplier(self, regime: str) -> float:
        """
        Get position size multiplier for regime.
        
        Args:
            regime: Current market regime
            
        Returns:
            Position multiplier (1.0 = normal size)
        """
        params = self.get_parameters(regime)
        return params.get('position_multiplier', 0.5)
    
    def get_signal_threshold(self, regime: str) -> float:
        """
        Get signal threshold for regime.
        
        Args:
            regime: Current market regime
            
        Returns:
            Minimum signal strength to trade
        """
        params = self.get_parameters(regime)
        return params.get('signal_threshold', 0.5)
    
    def update_regime_config(
        self,
        regime: str,
        updates: Dict[str, Any]
    ):
        """
        Update configuration for a specific regime.
        
        Args:
            regime: Regime to update
            updates: Dictionary of parameters to update
        """
        if regime not in self.regime_configs:
            logger.warning(f"Unknown regime '{regime}', creating new config")
            self.regime_configs[regime] = {}
        
        self.regime_configs[regime].update(updates)
        logger.info(f"Updated {len(updates)} parameters for regime '{regime}'")
    
    def get_all_regimes(self) -> list:
        """
        Get list of all configured regimes.
        
        Returns:
            List of regime names
        """
        return list(self.regime_configs.keys())
