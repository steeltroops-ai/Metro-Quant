"""Position limit enforcement for risk management.

This module enforces per-position and total exposure limits.
"""

from typing import Dict, Optional
from loguru import logger


class PositionLimiter:
    """
    Enforces position size limits to manage risk.
    
    Limits enforced:
    - Per-position limit: 20% of total capital
    - Total exposure limit: 80% of total capital
    """
    
    def __init__(
        self,
        max_position_pct: float = 0.2,
        max_total_exposure_pct: float = 0.8
    ):
        """
        Initialize position limiter.
        
        Args:
            max_position_pct: Maximum position size as % of capital (default 20%)
            max_total_exposure_pct: Maximum total exposure as % of capital (default 80%)
        """
        self.max_position_pct = max_position_pct
        self.max_total_exposure_pct = max_total_exposure_pct
        
        logger.info(
            f"PositionLimiter initialized: max_position={max_position_pct:.1%}, "
            f"max_total_exposure={max_total_exposure_pct:.1%}"
        )
    
    def check_limit(
        self,
        proposed_size: float,
        symbol: str,
        capital: float,
        current_positions: Dict[str, float]
    ) -> float:
        """
        Check and adjust position size to respect limits.
        
        Args:
            proposed_size: Proposed position size in capital units
            symbol: Trading symbol for the position
            capital: Total available capital
            current_positions: Dict of {symbol: position_size} for existing positions
            
        Returns:
            Adjusted position size that respects all limits
        """
        if capital <= 0:
            logger.error(f"Invalid capital: {capital}")
            return 0.0
        
        # Calculate proposed position as percentage of capital
        proposed_pct = abs(proposed_size) / capital
        
        # Check per-position limit
        if proposed_pct > self.max_position_pct:
            logger.warning(
                f"Proposed position {proposed_pct:.1%} exceeds per-position limit "
                f"{self.max_position_pct:.1%}, reducing to limit"
            )
            # Reduce to maximum allowed
            adjusted_size = self.max_position_pct * capital
            # Preserve direction
            if proposed_size < 0:
                adjusted_size = -adjusted_size
            proposed_size = adjusted_size
            proposed_pct = self.max_position_pct
        
        # Calculate current total exposure (excluding the symbol we're trading)
        current_exposure = sum(
            abs(size) for sym, size in current_positions.items()
            if sym != symbol
        )
        current_exposure_pct = current_exposure / capital
        
        # Calculate what total exposure would be with this position
        total_exposure_pct = current_exposure_pct + proposed_pct
        
        # Check total exposure limit
        if total_exposure_pct > self.max_total_exposure_pct:
            # Calculate available exposure
            available_exposure_pct = self.max_total_exposure_pct - current_exposure_pct
            
            if available_exposure_pct <= 0:
                logger.warning(
                    f"Cannot take position: current exposure {current_exposure_pct:.1%} "
                    f"at or above limit {self.max_total_exposure_pct:.1%}"
                )
                return 0.0
            
            logger.warning(
                f"Proposed position would exceed total exposure limit "
                f"({total_exposure_pct:.1%} > {self.max_total_exposure_pct:.1%}), "
                f"reducing to available exposure {available_exposure_pct:.1%}"
            )
            
            # Reduce to available exposure
            adjusted_size = available_exposure_pct * capital
            # Preserve direction
            if proposed_size < 0:
                adjusted_size = -adjusted_size
            proposed_size = adjusted_size
        
        logger.debug(
            f"Position limit check for {symbol}: "
            f"proposed={proposed_size:.2f} ({proposed_pct:.1%}), "
            f"current_exposure={current_exposure_pct:.1%}, "
            f"total_would_be={total_exposure_pct:.1%}"
        )
        
        return float(proposed_size)
    
    def get_available_exposure(
        self,
        capital: float,
        current_positions: Dict[str, float]
    ) -> float:
        """
        Calculate available exposure capacity.
        
        Args:
            capital: Total available capital
            current_positions: Dict of {symbol: position_size}
            
        Returns:
            Available exposure in capital units
        """
        if capital <= 0:
            return 0.0
        
        # Calculate current total exposure
        current_exposure = sum(abs(size) for size in current_positions.values())
        current_exposure_pct = current_exposure / capital
        
        # Calculate available exposure
        available_pct = max(0.0, self.max_total_exposure_pct - current_exposure_pct)
        available_exposure = available_pct * capital
        
        return float(available_exposure)
    
    def is_within_limits(
        self,
        position_size: float,
        symbol: str,
        capital: float,
        current_positions: Dict[str, float]
    ) -> bool:
        """
        Check if a position size is within limits without adjusting.
        
        Args:
            position_size: Position size to check
            symbol: Trading symbol
            capital: Total available capital
            current_positions: Dict of {symbol: position_size}
            
        Returns:
            True if position is within limits, False otherwise
        """
        if capital <= 0:
            return False
        
        # Check per-position limit
        position_pct = abs(position_size) / capital
        if position_pct > self.max_position_pct:
            return False
        
        # Check total exposure limit
        current_exposure = sum(
            abs(size) for sym, size in current_positions.items()
            if sym != symbol
        )
        total_exposure = current_exposure + abs(position_size)
        total_exposure_pct = total_exposure / capital
        
        if total_exposure_pct > self.max_total_exposure_pct:
            return False
        
        return True
    
    def get_max_position_for_symbol(
        self,
        symbol: str,
        capital: float,
        current_positions: Dict[str, float]
    ) -> float:
        """
        Get maximum allowed position size for a symbol.
        
        Args:
            symbol: Trading symbol
            capital: Total available capital
            current_positions: Dict of {symbol: position_size}
            
        Returns:
            Maximum allowed position size
        """
        if capital <= 0:
            return 0.0
        
        # Maximum from per-position limit
        max_from_position_limit = self.max_position_pct * capital
        
        # Maximum from total exposure limit
        available_exposure = self.get_available_exposure(capital, current_positions)
        
        # Return the smaller of the two
        return float(min(max_from_position_limit, available_exposure))
