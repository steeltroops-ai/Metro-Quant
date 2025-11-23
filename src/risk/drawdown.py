"""Drawdown monitoring and risk reduction.

This module tracks portfolio drawdown and triggers risk reduction measures.
"""

from typing import Optional
from datetime import datetime
from loguru import logger


class DrawdownMonitor:
    """
    Monitors portfolio drawdown and triggers risk reduction.
    
    Drawdown thresholds:
    - 15% drawdown: Reduce all position sizes by 50%
    - 25% drawdown: Enter safe mode (halt all trading)
    """
    
    def __init__(
        self,
        initial_capital: float,
        reduction_threshold: float = 0.15,
        safe_mode_threshold: float = 0.25
    ):
        """
        Initialize drawdown monitor.
        
        Args:
            initial_capital: Starting capital
            reduction_threshold: Drawdown % to trigger position reduction (default 15%)
            safe_mode_threshold: Drawdown % to trigger safe mode (default 25%)
        """
        self.initial_capital = initial_capital
        self.reduction_threshold = reduction_threshold
        self.safe_mode_threshold = safe_mode_threshold
        
        # Track peak capital and current capital
        self.peak_capital = initial_capital
        self.current_capital = initial_capital
        
        # Track drawdown state
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0
        self.in_safe_mode = False
        
        # Track when thresholds were crossed
        self.reduction_triggered_at: Optional[datetime] = None
        self.safe_mode_triggered_at: Optional[datetime] = None
        
        logger.info(
            f"DrawdownMonitor initialized: initial_capital={initial_capital:.2f}, "
            f"reduction_threshold={reduction_threshold:.1%}, "
            f"safe_mode_threshold={safe_mode_threshold:.1%}"
        )
    
    def update(self, current_capital: float) -> None:
        """
        Update drawdown tracking with current capital.
        
        Args:
            current_capital: Current portfolio capital
        """
        self.current_capital = current_capital
        
        # Update peak if we've reached a new high (or equal to peak)
        if current_capital >= self.peak_capital:
            if current_capital > self.peak_capital:
                logger.debug(f"New peak capital: {self.peak_capital:.2f}")
            self.peak_capital = current_capital
            
            # Reset reduction trigger if we've recovered
            if self.reduction_triggered_at is not None:
                logger.info("Recovered from drawdown, resetting reduction trigger")
                self.reduction_triggered_at = None
        
        # Calculate current drawdown from peak
        if self.peak_capital > 0:
            self.current_drawdown = (self.peak_capital - current_capital) / self.peak_capital
        else:
            self.current_drawdown = 0.0
        
        # Update max drawdown
        if self.current_drawdown > self.max_drawdown:
            self.max_drawdown = self.current_drawdown
            logger.warning(f"New maximum drawdown: {self.max_drawdown:.2%}")
        
        # Check for safe mode threshold (must be checked first)
        # Use small tolerance for floating point comparison
        if self.current_drawdown >= self.safe_mode_threshold - 1e-10:
            if not self.in_safe_mode:
                self.in_safe_mode = True
                self.safe_mode_triggered_at = datetime.now()
                logger.critical(
                    f"SAFE MODE ACTIVATED: Drawdown {self.current_drawdown:.2%} "
                    f"exceeds threshold {self.safe_mode_threshold:.1%}"
                )
        # Check for reduction threshold (only if not in safe mode)
        elif self.current_drawdown >= self.reduction_threshold - 1e-10 and not self.in_safe_mode:
            if self.reduction_triggered_at is None:
                self.reduction_triggered_at = datetime.now()
                logger.warning(
                    f"RISK REDUCTION TRIGGERED: Drawdown {self.current_drawdown:.2%} "
                    f"exceeds threshold {self.reduction_threshold:.1%}"
                )
        
        logger.debug(
            f"Drawdown update: capital={current_capital:.2f}, "
            f"peak={self.peak_capital:.2f}, "
            f"drawdown={self.current_drawdown:.2%}, "
            f"max_drawdown={self.max_drawdown:.2%}"
        )
    
    def get_multiplier(self) -> float:
        """
        Get position size multiplier based on drawdown state.
        
        Returns:
            Position size multiplier:
            - 1.0: Normal operation
            - 0.5: Risk reduction (15%+ drawdown)
            - 0.0: Safe mode (25%+ drawdown)
        """
        if self.in_safe_mode:
            return 0.0
        elif self.reduction_triggered_at is not None:
            return 0.5
        else:
            return 1.0
    
    def is_safe_mode(self) -> bool:
        """
        Check if safe mode is active.
        
        Returns:
            True if safe mode is active, False otherwise
        """
        return self.in_safe_mode
    
    def is_reduction_active(self) -> bool:
        """
        Check if risk reduction is active.
        
        Returns:
            True if risk reduction is active, False otherwise
        """
        return self.reduction_triggered_at is not None and not self.in_safe_mode
    
    def get_current_drawdown(self) -> float:
        """
        Get current drawdown percentage.
        
        Returns:
            Current drawdown as decimal (0.15 = 15%)
        """
        return self.current_drawdown
    
    def get_max_drawdown(self) -> float:
        """
        Get maximum drawdown experienced.
        
        Returns:
            Maximum drawdown as decimal (0.15 = 15%)
        """
        return self.max_drawdown
    
    def get_drawdown_from_initial(self) -> float:
        """
        Get drawdown from initial capital.
        
        Returns:
            Drawdown from initial capital as decimal
        """
        if self.initial_capital > 0:
            return (self.initial_capital - self.current_capital) / self.initial_capital
        return 0.0
    
    def reset_safe_mode(self) -> None:
        """
        Manually reset safe mode (use with caution).
        
        This should only be called after manual intervention or
        when starting a new trading session.
        """
        logger.warning("Manually resetting safe mode")
        self.in_safe_mode = False
        self.safe_mode_triggered_at = None
        self.reduction_triggered_at = None
    
    def get_status(self) -> dict:
        """
        Get comprehensive drawdown status.
        
        Returns:
            Dict with drawdown metrics and state
        """
        return {
            'current_capital': self.current_capital,
            'peak_capital': self.peak_capital,
            'initial_capital': self.initial_capital,
            'current_drawdown': self.current_drawdown,
            'max_drawdown': self.max_drawdown,
            'drawdown_from_initial': self.get_drawdown_from_initial(),
            'in_safe_mode': self.in_safe_mode,
            'risk_reduction_active': self.is_reduction_active(),
            'position_multiplier': self.get_multiplier(),
            'reduction_triggered_at': self.reduction_triggered_at,
            'safe_mode_triggered_at': self.safe_mode_triggered_at
        }
