"""Position sizing based on signal confidence and regime.

This module calculates appropriate position sizes for risk management.
"""

from typing import Optional
import numpy as np
from loguru import logger


class PositionSizer:
    """
    Calculates position sizes based on signal strength, confidence, and regime.
    
    Position sizing considers:
    - Signal strength (stronger signals = larger positions)
    - Signal confidence (higher confidence = larger positions)
    - Market regime (volatile regimes = smaller positions)
    - Available capital
    - Risk limits
    """
    
    def __init__(
        self,
        base_position_pct: float = 0.1,
        max_position_pct: float = 0.2,
        min_confidence: float = 0.3
    ):
        """
        Initialize position sizer.
        
        Args:
            base_position_pct: Base position size as % of capital (0.1 = 10%)
            max_position_pct: Maximum position size as % of capital (0.2 = 20%)
            min_confidence: Minimum confidence to take any position
        """
        self.base_position_pct = base_position_pct
        self.max_position_pct = max_position_pct
        self.min_confidence = min_confidence
        
        logger.info(
            f"PositionSizer initialized: base={base_position_pct:.1%}, "
            f"max={max_position_pct:.1%}, min_confidence={min_confidence:.2f}"
        )
    
    def calculate_size(
        self,
        signal_strength: float,
        confidence: float,
        regime: str,
        capital: float,
        regime_multiplier: float = 1.0,
        current_exposure: float = 0.0
    ) -> float:
        """
        Calculate position size based on signal and risk parameters.
        
        Args:
            signal_strength: Signal strength [-1.0, 1.0]
            confidence: Signal confidence [0.0, 1.0]
            regime: Current market regime
            capital: Available capital
            regime_multiplier: Regime-specific position multiplier
            current_exposure: Current total exposure as % of capital
            
        Returns:
            Position size in capital units (positive for long, negative for short)
        """
        # Check minimum confidence
        if confidence < self.min_confidence:
            logger.debug(
                f"Confidence {confidence:.3f} below minimum {self.min_confidence:.3f}, "
                "position size = 0"
            )
            return 0.0
        
        # Check signal strength
        if abs(signal_strength) < 0.01:
            logger.debug("Signal strength near zero, position size = 0")
            return 0.0
        
        # Calculate base size from signal strength
        # Stronger signals get larger positions
        strength_factor = abs(signal_strength)
        
        # Scale by confidence
        # Higher confidence gets larger positions
        confidence_factor = confidence
        
        # Calculate position percentage
        position_pct = (
            self.base_position_pct *
            strength_factor *
            confidence_factor *
            regime_multiplier
        )
        
        # Apply maximum limit
        position_pct = min(position_pct, self.max_position_pct)
        
        # Check if adding this position would exceed total exposure limit (80%)
        MAX_TOTAL_EXPOSURE = 0.8
        if current_exposure + position_pct > MAX_TOTAL_EXPOSURE:
            # Reduce position to stay within limit
            available_exposure = MAX_TOTAL_EXPOSURE - current_exposure
            if available_exposure > 0:
                position_pct = available_exposure
                logger.warning(
                    f"Reducing position from {position_pct:.1%} to {available_exposure:.1%} "
                    f"to stay within total exposure limit"
                )
            else:
                logger.warning(
                    f"Cannot take position: current exposure {current_exposure:.1%} "
                    f"at or above limit {MAX_TOTAL_EXPOSURE:.1%}"
                )
                return 0.0
        
        # Calculate position size in capital units
        position_size = position_pct * capital
        
        # Apply signal direction (positive = long, negative = short)
        if signal_strength < 0:
            position_size = -position_size
        
        logger.info(
            f"Position size calculated: {position_size:.2f} "
            f"({position_pct:.1%} of capital) "
            f"[strength={signal_strength:.3f}, confidence={confidence:.3f}, "
            f"regime={regime}, multiplier={regime_multiplier:.2f}]"
        )
        
        return float(position_size)
    
    def calculate_size_with_kelly(
        self,
        signal_strength: float,
        confidence: float,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
        capital: float,
        regime_multiplier: float = 1.0
    ) -> float:
        """
        Calculate position size using Kelly Criterion.
        
        Kelly Criterion optimally sizes positions based on edge and odds.
        Formula: f = (p * b - q) / b
        where:
        - f = fraction of capital to bet
        - p = probability of win
        - q = probability of loss (1 - p)
        - b = ratio of win to loss
        
        Args:
            signal_strength: Signal strength [-1.0, 1.0]
            confidence: Signal confidence [0.0, 1.0]
            win_rate: Historical win rate [0.0, 1.0]
            avg_win: Average win amount
            avg_loss: Average loss amount (positive value)
            capital: Available capital
            regime_multiplier: Regime-specific multiplier
            
        Returns:
            Position size in capital units
        """
        # Check minimum confidence
        if confidence < self.min_confidence:
            return 0.0
        
        # Calculate Kelly fraction
        if avg_loss > 0:
            b = avg_win / avg_loss  # Win/loss ratio
        else:
            b = 2.0  # Default 2:1 ratio
        
        p = win_rate
        q = 1 - p
        
        kelly_fraction = (p * b - q) / b
        
        # Apply fractional Kelly (half Kelly for safety)
        kelly_fraction = kelly_fraction * 0.5
        
        # Ensure non-negative
        kelly_fraction = max(kelly_fraction, 0.0)
        
        # Scale by signal strength and confidence
        kelly_fraction = kelly_fraction * abs(signal_strength) * confidence
        
        # Apply regime multiplier
        kelly_fraction = kelly_fraction * regime_multiplier
        
        # Apply maximum limit
        kelly_fraction = min(kelly_fraction, self.max_position_pct)
        
        # Calculate position size
        position_size = kelly_fraction * capital
        
        # Apply signal direction
        if signal_strength < 0:
            position_size = -position_size
        
        logger.debug(
            f"Kelly position size: {position_size:.2f} "
            f"(kelly_fraction={kelly_fraction:.3f}, win_rate={win_rate:.2f})"
        )
        
        return float(position_size)
    
    def adjust_for_volatility(
        self,
        base_size: float,
        current_volatility: float,
        target_volatility: float = 0.15
    ) -> float:
        """
        Adjust position size based on volatility targeting.
        
        Higher volatility = smaller positions to maintain constant risk.
        
        Args:
            base_size: Base position size
            current_volatility: Current market volatility
            target_volatility: Target volatility level
            
        Returns:
            Adjusted position size
        """
        if current_volatility <= 0:
            return base_size
        
        # Calculate volatility adjustment factor
        vol_adjustment = target_volatility / current_volatility
        
        # Cap adjustment to reasonable range [0.25, 2.0]
        vol_adjustment = np.clip(vol_adjustment, 0.25, 2.0)
        
        adjusted_size = base_size * vol_adjustment
        
        logger.debug(
            f"Volatility adjustment: {base_size:.2f} -> {adjusted_size:.2f} "
            f"(vol={current_volatility:.3f}, target={target_volatility:.3f})"
        )
        
        return float(adjusted_size)
    
    def get_max_position_size(self, capital: float) -> float:
        """
        Get maximum allowed position size.
        
        Args:
            capital: Available capital
            
        Returns:
            Maximum position size
        """
        return self.max_position_pct * capital
    
    def get_min_position_size(self, capital: float) -> float:
        """
        Get minimum meaningful position size.
        
        Args:
            capital: Available capital
            
        Returns:
            Minimum position size (1% of capital)
        """
        return 0.01 * capital
