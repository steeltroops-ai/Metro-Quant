"""
Performance metrics collection and calculation.

Tracks PnL, Sharpe ratio, drawdown, win rate, and other trading metrics.
"""

import numpy as np
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class MetricsCollector:
    """
    Collects and calculates trading performance metrics.
    
    Tracks all trades and computes real-time statistics including:
    - Total PnL and returns
    - Sharpe ratio
    - Maximum drawdown
    - Win rate
    - Average trade size
    - Regime-specific performance
    """
    
    def __init__(self, risk_free_rate: float = 0.0):
        """
        Initialize metrics collector.
        
        Args:
            risk_free_rate: Annual risk-free rate for Sharpe calculation (default 0%)
        """
        self.risk_free_rate = risk_free_rate
        
        # Trade history
        self.trades: List[Dict] = []
        self.returns: List[float] = []
        self.timestamps: List[datetime] = []
        
        # Running metrics
        self.total_pnl: float = 0.0
        self.peak_value: float = 10000.0  # Starting capital
        self.max_drawdown: float = 0.0
        self.current_drawdown: float = 0.0
        
        # Regime-specific tracking
        self.regime_pnl: Dict[str, float] = {}
        self.regime_trades: Dict[str, int] = {}
        
        # Win/loss tracking
        self.winning_trades: int = 0
        self.losing_trades: int = 0
        
        # Rolling window for recent performance
        self.recent_returns = deque(maxlen=100)
    
    def record_trade(
        self,
        pnl: float,
        timestamp: datetime,
        regime: Optional[str] = None,
        size: Optional[float] = None,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Record a completed trade.
        
        Args:
            pnl: Profit/loss from the trade
            timestamp: Trade execution time
            regime: Market regime during trade
            size: Position size
            metadata: Additional trade information
        
        Performance: ~0.5ms
        """
        # Record trade
        trade_record = {
            "pnl": pnl,
            "timestamp": timestamp,
            "regime": regime,
            "size": size,
            "metadata": metadata or {}
        }
        self.trades.append(trade_record)
        self.timestamps.append(timestamp)
        
        # Update PnL
        self.total_pnl += pnl
        
        # Update peak and drawdown
        # Peak is based on capital, not just PnL
        starting_capital = 10000.0
        current_capital = starting_capital + self.total_pnl
        
        if current_capital > self.peak_value:
            self.peak_value = current_capital
            self.current_drawdown = 0.0
        else:
            # Drawdown as percentage of peak capital
            self.current_drawdown = (self.peak_value - current_capital) / max(self.peak_value, 1.0)
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Calculate return
        previous_capital = current_capital - pnl
        trade_return = pnl / max(abs(previous_capital), 1.0)
        self.returns.append(trade_return)
        self.recent_returns.append(trade_return)
        
        # Update win/loss counts
        if pnl > 0:
            self.winning_trades += 1
        elif pnl < 0:
            self.losing_trades += 1
        
        # Update regime-specific metrics
        if regime:
            self.regime_pnl[regime] = self.regime_pnl.get(regime, 0.0) + pnl
            self.regime_trades[regime] = self.regime_trades.get(regime, 0) + 1
    
    def get_sharpe_ratio(self, annualization_factor: float = 252.0) -> float:
        """
        Calculate Sharpe ratio.
        
        Args:
            annualization_factor: Factor to annualize returns (252 for daily, 1 for already annualized)
        
        Returns:
            Sharpe ratio (annualized)
        
        Performance: ~1ms
        """
        if len(self.returns) < 2:
            return 0.0
        
        returns_array = np.array(self.returns)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Annualize
        annualized_return = mean_return * annualization_factor
        annualized_std = std_return * np.sqrt(annualization_factor)
        
        sharpe = (annualized_return - self.risk_free_rate) / annualized_std
        return sharpe
    
    def get_max_drawdown(self) -> float:
        """
        Get maximum drawdown as a percentage.
        
        Returns:
            Maximum drawdown (0.0 to 1.0)
        
        Performance: ~0.1ms
        """
        return self.max_drawdown
    
    def get_current_drawdown(self) -> float:
        """
        Get current drawdown as a percentage.
        
        Returns:
            Current drawdown (0.0 to 1.0)
        
        Performance: ~0.1ms
        """
        return self.current_drawdown
    
    def get_win_rate(self) -> float:
        """
        Calculate win rate.
        
        Returns:
            Win rate (0.0 to 1.0)
        
        Performance: ~0.1ms
        """
        total_trades = self.winning_trades + self.losing_trades
        if total_trades == 0:
            return 0.0
        return self.winning_trades / total_trades
    
    def get_total_pnl(self) -> float:
        """Get total profit/loss."""
        return self.total_pnl
    
    def get_trade_count(self) -> int:
        """Get total number of trades."""
        return len(self.trades)
    
    def get_regime_performance(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance breakdown by regime.
        
        Returns:
            Dictionary mapping regime to performance metrics
        
        Performance: ~1ms
        """
        regime_stats = {}
        
        for regime in self.regime_pnl.keys():
            pnl = self.regime_pnl[regime]
            trade_count = self.regime_trades[regime]
            avg_pnl = pnl / trade_count if trade_count > 0 else 0.0
            
            regime_stats[regime] = {
                "total_pnl": pnl,
                "trade_count": trade_count,
                "avg_pnl_per_trade": avg_pnl
            }
        
        return regime_stats
    
    def get_recent_sharpe(self, window: int = 20) -> float:
        """
        Calculate Sharpe ratio over recent trades.
        
        Args:
            window: Number of recent trades to consider
        
        Returns:
            Recent Sharpe ratio
        
        Performance: ~1ms
        """
        if len(self.recent_returns) < 2:
            return 0.0
        
        recent = list(self.recent_returns)[-window:]
        if len(recent) < 2:
            return 0.0
        
        returns_array = np.array(recent)
        mean_return = np.mean(returns_array)
        std_return = np.std(returns_array, ddof=1)
        
        if std_return == 0:
            return 0.0
        
        # Annualize assuming daily returns
        annualized_return = mean_return * 252
        annualized_std = std_return * np.sqrt(252)
        
        sharpe = (annualized_return - self.risk_free_rate) / annualized_std
        return sharpe
    
    def get_summary(self) -> Dict[str, any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Dictionary with all key metrics
        
        Performance: ~2ms
        """
        return {
            "total_pnl": self.total_pnl,
            "trade_count": len(self.trades),
            "sharpe_ratio": self.get_sharpe_ratio(),
            "max_drawdown": self.max_drawdown,
            "current_drawdown": self.current_drawdown,
            "win_rate": self.get_win_rate(),
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "recent_sharpe": self.get_recent_sharpe(),
            "regime_performance": self.get_regime_performance()
        }
