"""Signal combination with weighted aggregation.

This module combines multiple signals into a single trading signal.
"""

from typing import Dict
import numpy as np
from loguru import logger

from src.utils.types import Signal
from datetime import datetime


class SignalCombiner:
    """
    Combines multiple signals using weighted aggregation.
    
    Supports regime-specific weighting for adaptive strategy.
    """
    
    def __init__(self, confidence_threshold: float = 0.3):
        """
        Initialize signal combiner.
        
        Args:
            confidence_threshold: Minimum confidence to generate trading signal
        """
        self.confidence_threshold = confidence_threshold
        self.regime_weights = self._default_regime_weights()
        logger.info(f"SignalCombiner initialized with confidence_threshold={confidence_threshold}")
    
    def _default_regime_weights(self) -> Dict[str, Dict[str, float]]:
        """
        Define default regime-specific signal weights.
        
        Different market regimes emphasize different signal types.
        """
        return {
            'trending': {
                'temp_momentum': 0.4,
                'temp_trend': 0.5,
                'flights_trend': 0.6,
                'flight_volume_delta': 0.5,
                'movements_delta': 0.4,
            },
            'mean-reverting': {
                'temp_momentum': -0.3,  # Fade momentum
                'pressure_delta': 0.4,
                'aqi_delta': 0.3,
                'weather_flight_stress': 0.5,
            },
            'high-volatility': {
                # In high volatility, trust stable indicators
                'precipitation': 0.5,
                'avg_delay': 0.4,
                'weather_flight_stress': 0.6,
            },
            'low-volatility': {
                # In low volatility, trust all signals equally
                'temp_momentum': 0.3,
                'flight_volume_delta': 0.4,
                'movements_delta': 0.3,
                'temp_trend': 0.3,
                'flights_trend': 0.4,
            },
            'uncertain': {
                # Conservative: only trust strong, stable signals
                'precipitation': 0.4,
                'flight_volume_delta': 0.3,
                'movements_delta': 0.3,
            }
        }
    
    def combine(
        self,
        signals: Dict[str, float],
        regime: str = 'uncertain',
        base_confidence: float = 0.5
    ) -> Signal:
        """
        Combine multiple signals into a single trading signal.
        
        Args:
            signals: Dictionary of signal scores [-1.0, 1.0]
            regime: Current market regime
            base_confidence: Base confidence level [0.0, 1.0]
            
        Returns:
            Combined Signal object with strength and confidence
        """
        # Get regime-specific weights
        weights = self.regime_weights.get(regime, self.regime_weights['uncertain'])
        
        # Compute weighted average of signals
        weighted_sum = 0.0
        total_weight = 0.0
        signal_components = {}
        
        for signal_name, signal_value in signals.items():
            # Get weight for this signal in current regime
            weight = weights.get(signal_name, 0.1)  # Default small weight
            
            weighted_sum += signal_value * weight
            total_weight += abs(weight)
            
            # Store component for transparency
            signal_components[signal_name] = signal_value
        
        # Normalize by total weight
        if total_weight > 0:
            combined_strength = weighted_sum / total_weight
        else:
            combined_strength = 0.0
        
        # Clip to [-1, 1] range
        combined_strength = np.clip(combined_strength, -1.0, 1.0)
        
        # Calculate confidence based on signal agreement
        confidence = self._calculate_confidence(
            signals,
            weights,
            combined_strength,
            base_confidence
        )
        
        # Create Signal object
        signal = Signal(
            timestamp=datetime.now(),
            strength=float(combined_strength),
            confidence=float(confidence),
            components=signal_components,
            regime=regime
        )
        
        logger.debug(
            f"Combined signal: strength={signal.strength:.3f}, "
            f"confidence={signal.confidence:.3f}, regime={regime}"
        )
        
        return signal
    
    def _calculate_confidence(
        self,
        signals: Dict[str, float],
        weights: Dict[str, float],
        combined_strength: float,
        base_confidence: float
    ) -> float:
        """
        Calculate confidence in the combined signal.
        
        Confidence is higher when:
        - Signals agree in direction
        - Signal magnitudes are strong
        - More signals are available
        
        Args:
            signals: Individual signal scores
            weights: Signal weights for current regime
            combined_strength: Combined signal strength
            base_confidence: Base confidence level
            
        Returns:
            Confidence score [0.0, 1.0]
        """
        if not signals:
            return 0.0
        
        # Calculate signal agreement
        # Signals that agree with combined direction increase confidence
        agreement_scores = []
        for signal_name, signal_value in signals.items():
            if signal_name in weights:
                # Check if signal agrees with combined direction
                if np.sign(signal_value) == np.sign(combined_strength):
                    agreement_scores.append(abs(signal_value))
                else:
                    agreement_scores.append(-abs(signal_value))
        
        if agreement_scores:
            # Average agreement (positive = agreement, negative = disagreement)
            avg_agreement = np.mean(agreement_scores)
            # Map to [0, 1] range
            agreement_factor = (avg_agreement + 1.0) / 2.0
        else:
            agreement_factor = 0.5
        
        # Calculate signal strength factor
        # Stronger signals increase confidence
        signal_strengths = [abs(v) for v in signals.values()]
        avg_strength = np.mean(signal_strengths) if signal_strengths else 0.0
        
        # Calculate coverage factor
        # More signals increase confidence
        num_signals = len(signals)
        coverage_factor = min(num_signals / 10.0, 1.0)  # Cap at 10 signals
        
        # Combine factors
        confidence = (
            base_confidence * 0.3 +
            agreement_factor * 0.4 +
            avg_strength * 0.2 +
            coverage_factor * 0.1
        )
        
        # Clip to [0, 1] range
        confidence = np.clip(confidence, 0.0, 1.0)
        
        return float(confidence)
    
    def should_trade(self, signal: Signal) -> bool:
        """
        Determine if signal confidence exceeds threshold for trading.
        
        Args:
            signal: Combined signal
            
        Returns:
            True if should trade, False if should abstain
        """
        should_trade = signal.confidence >= self.confidence_threshold
        
        if not should_trade:
            logger.info(
                f"Abstaining from trade: confidence {signal.confidence:.3f} "
                f"< threshold {self.confidence_threshold:.3f}"
            )
        
        return should_trade
    
    def update_regime_weights(self, regime: str, new_weights: Dict[str, float]):
        """
        Update weights for a specific regime.
        
        Args:
            regime: Regime name
            new_weights: New weights to apply
        """
        if regime not in self.regime_weights:
            self.regime_weights[regime] = {}
        
        self.regime_weights[regime].update(new_weights)
        logger.info(f"Updated {len(new_weights)} weights for regime '{regime}'")
    
    def get_regime_weights(self, regime: str) -> Dict[str, float]:
        """
        Get weights for a specific regime.
        
        Args:
            regime: Regime name
            
        Returns:
            Dictionary of signal weights
        """
        return self.regime_weights.get(regime, {}).copy()
