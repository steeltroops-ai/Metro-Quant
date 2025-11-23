"""Backtesting engine for strategy validation.

This module provides chronological data replay with realistic order fills.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from loguru import logger

from src.utils.types import MarketData, Signal, Order, Position
from src.strategy.regime import RegimeDetector
from src.strategy.adaptive import AdaptiveStrategy
from src.risk.limiter import PositionLimiter
from src.risk.drawdown import DrawdownMonitor


class BacktestOrder:
    """Simplified order for backtesting."""
    
    def __init__(
        self,
        order_id: str,
        symbol: str,
        side: str,
        size: float,
        limit_price: float,
        timestamp: datetime
    ):
        self.order_id = order_id
        self.symbol = symbol
        self.side = side
        self.size = size
        self.limit_price = limit_price
        self.timestamp = timestamp
        self.fill_price: Optional[float] = None
        self.filled = False


class BacktestPosition:
    """Position tracking for backtesting."""
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.size = 0.0
        self.entry_price = 0.0
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        
    def update(self, size_delta: float, price: float):
        """Update position with new fill."""
        if self.size == 0:
            # Opening new position
            self.size = size_delta
            self.entry_price = price
        elif (self.size > 0 and size_delta < 0) or (self.size < 0 and size_delta > 0):
            # Closing or reducing position
            close_size = min(abs(size_delta), abs(self.size))
            pnl_per_unit = (price - self.entry_price) if self.size > 0 else (self.entry_price - price)
            self.realized_pnl += close_size * pnl_per_unit
            
            self.size += size_delta
            if abs(self.size) < 1e-6:
                self.size = 0.0
                self.entry_price = 0.0
        else:
            # Adding to position
            # Calculate weighted average entry price
            total_size = abs(self.size) + abs(size_delta)
            self.entry_price = (
                (abs(self.size) * self.entry_price + abs(size_delta) * price) / total_size
            )
            self.size += size_delta
            
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL at current price."""
        if self.size == 0:
            return 0.0
        
        if self.size > 0:
            self.unrealized_pnl = self.size * (current_price - self.entry_price)
        else:
            self.unrealized_pnl = abs(self.size) * (self.entry_price - current_price)
            
        return self.unrealized_pnl


class Backtester:
    """
    Backtesting engine with chronological replay and realistic fills.
    
    Simulates trading strategy on historical data with:
    - Chronological data replay
    - Realistic order fill simulation with slippage
    - Performance metrics calculation
    - Regime-segmented analysis
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        slippage_bps: float = 5.0,  # 5 basis points default slippage
        commission_bps: float = 2.0,  # 2 basis points commission
    ):
        """
        Initialize backtester.
        
        Args:
            initial_capital: Starting capital
            slippage_bps: Slippage in basis points (1 bp = 0.01%)
            commission_bps: Commission in basis points
        """
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.slippage_bps = slippage_bps
        self.commission_bps = commission_bps
        
        # Strategy components
        self.regime_detector = RegimeDetector()
        self.adaptive_strategy = AdaptiveStrategy()
        self.position_limiter = PositionLimiter(max_position_pct=0.20, max_total_exposure_pct=0.80)
        self.drawdown_monitor = DrawdownMonitor(
            initial_capital=initial_capital,
            reduction_threshold=0.15,
            safe_mode_threshold=0.25
        )
        
        # Tracking
        self.positions: Dict[str, BacktestPosition] = {}
        self.pending_orders: List[BacktestOrder] = []
        self.filled_orders: List[BacktestOrder] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.trade_log: List[Dict[str, Any]] = []
        self.regime_changes: List[Tuple[datetime, str, str]] = []
        
        # Performance metrics by regime
        self.regime_metrics: Dict[str, Dict[str, Any]] = {
            'trending': {'trades': 0, 'pnl': 0.0, 'wins': 0},
            'mean-reverting': {'trades': 0, 'pnl': 0.0, 'wins': 0},
            'high-volatility': {'trades': 0, 'pnl': 0.0, 'wins': 0},
            'low-volatility': {'trades': 0, 'pnl': 0.0, 'wins': 0},
            'uncertain': {'trades': 0, 'pnl': 0.0, 'wins': 0},
        }
        
        self.current_regime = 'uncertain'
        
        logger.info(
            f"Backtester initialized: capital=${initial_capital:,.2f}, "
            f"slippage={slippage_bps}bps, commission={commission_bps}bps"
        )
    
    async def run(
        self,
        market_data: List[MarketData],
        signals: List[Signal],
        strategy_func: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run backtest on historical data.
        
        Args:
            market_data: List of MarketData objects in chronological order
            signals: List of Signal objects in chronological order
            strategy_func: Optional custom strategy function(signal, regime) -> order_size
            
        Returns:
            Dictionary of performance metrics
            
        Performance: Processes data chronologically with realistic fills
        """
        logger.info(f"Starting backtest with {len(market_data)} data points")
        
        # Validate chronological order
        if not self._validate_chronological_order(market_data):
            raise ValueError("Market data must be in chronological order")
        
        if signals and not self._validate_chronological_order(signals):
            raise ValueError("Signals must be in chronological order")
        
        # Create signal lookup by timestamp
        signal_map = {s.timestamp: s for s in signals} if signals else {}
        
        # Process each data point chronologically
        for i, data in enumerate(market_data):
            # Update regime detection
            if len(data.returns) >= 30:
                old_regime = self.current_regime
                self.current_regime = self.regime_detector.detect(data.returns)
                
                if old_regime != self.current_regime:
                    self.regime_changes.append((data.timestamp, old_regime, self.current_regime))
                    logger.debug(f"Regime change: {old_regime} -> {self.current_regime}")
            
            # Process pending orders (check for fills)
            await self._process_pending_orders(data)
            
            # Update positions with current prices
            self._update_positions(data)
            
            # Update drawdown monitor
            total_equity = self._calculate_total_equity(data)
            self.drawdown_monitor.update(total_equity)
            
            # Record equity
            self.equity_curve.append((data.timestamp, total_equity))
            
            # Check for signal at this timestamp
            signal = signal_map.get(data.timestamp)
            if signal and not self.drawdown_monitor.is_safe_mode():
                # Generate order based on signal
                order = await self._generate_order_from_signal(
                    signal, data, strategy_func
                )
                if order:
                    self.pending_orders.append(order)
        
        # Close all remaining positions at final prices
        if market_data:
            final_data = market_data[-1]
            await self._close_all_positions(final_data)
        
        # Calculate final metrics
        metrics = self._calculate_metrics()
        
        logger.info(
            f"Backtest complete: Final PnL=${metrics['total_pnl']:,.2f}, "
            f"Sharpe={metrics['sharpe_ratio']:.2f}, "
            f"Max DD={metrics['max_drawdown']:.2%}"
        )
        
        return metrics
    
    def _validate_chronological_order(self, data_list: List) -> bool:
        """Validate that data is in chronological order."""
        if len(data_list) < 2:
            return True
        
        for i in range(1, len(data_list)):
            if data_list[i].timestamp < data_list[i-1].timestamp:
                logger.error(
                    f"Data not in chronological order at index {i}: "
                    f"{data_list[i-1].timestamp} > {data_list[i].timestamp}"
                )
                return False
        
        return True
    
    async def _process_pending_orders(self, data: MarketData):
        """Process pending orders and simulate fills with slippage."""
        filled_indices = []
        
        for i, order in enumerate(self.pending_orders):
            if order.symbol != data.symbol:
                continue
            
            # Simulate fill with slippage
            fill_price = self._simulate_fill(order, data)
            
            if fill_price is not None:
                # Order filled
                order.fill_price = fill_price
                order.filled = True
                
                # Update position
                if order.symbol not in self.positions:
                    self.positions[order.symbol] = BacktestPosition(order.symbol)
                
                size_delta = order.size if order.side == 'BUY' else -order.size
                self.positions[order.symbol].update(size_delta, fill_price)
                
                # Calculate commission
                commission = abs(order.size) * fill_price * (self.commission_bps / 10000)
                self.capital -= commission
                
                # Log trade
                self.trade_log.append({
                    'timestamp': data.timestamp,
                    'symbol': order.symbol,
                    'side': order.side,
                    'size': order.size,
                    'price': fill_price,
                    'commission': commission,
                    'regime': self.current_regime
                })
                
                # Update regime metrics
                self.regime_metrics[self.current_regime]['trades'] += 1
                
                self.filled_orders.append(order)
                filled_indices.append(i)
        
        # Remove filled orders
        for i in reversed(filled_indices):
            self.pending_orders.pop(i)
    
    def _simulate_fill(
        self,
        order: BacktestOrder,
        data: MarketData
    ) -> Optional[float]:
        """
        Simulate order fill with realistic slippage.
        
        Args:
            order: Order to fill
            data: Current market data
            
        Returns:
            Fill price if order would fill, None otherwise
        """
        # Check if limit price would be hit
        if order.side == 'BUY':
            # Buy order fills if ask <= limit price
            if data.ask <= order.limit_price:
                # Apply slippage (pay more)
                slippage = data.ask * (self.slippage_bps / 10000)
                fill_price = data.ask + slippage
                return fill_price
        else:
            # Sell order fills if bid >= limit price
            if data.bid >= order.limit_price:
                # Apply slippage (receive less)
                slippage = data.bid * (self.slippage_bps / 10000)
                fill_price = data.bid - slippage
                return fill_price
        
        return None
    
    def _update_positions(self, data: MarketData):
        """Update all positions with current market prices."""
        for symbol, position in self.positions.items():
            if symbol == data.symbol:
                position.calculate_unrealized_pnl(data.price)
    
    def _calculate_total_equity(self, data: MarketData) -> float:
        """Calculate total equity (capital + unrealized PnL)."""
        total_pnl = sum(pos.realized_pnl + pos.unrealized_pnl 
                       for pos in self.positions.values())
        return self.capital + total_pnl
    
    async def _generate_order_from_signal(
        self,
        signal: Signal,
        data: MarketData,
        strategy_func: Optional[callable] = None
    ) -> Optional[BacktestOrder]:
        """Generate order from signal using strategy."""
        # Get regime-specific parameters
        params = self.adaptive_strategy.get_parameters(signal.regime)
        signal_threshold = params.get('signal_threshold', 0.3)
        
        # Check if signal is strong enough
        if abs(signal.strength) < signal_threshold:
            return None
        
        # Calculate position size
        if strategy_func:
            size = strategy_func(signal, signal.regime)
        else:
            # Default position sizing
            position_multiplier = params.get('position_multiplier', 1.0)
            
            # Apply drawdown multiplier
            drawdown_multiplier = self.drawdown_monitor.get_multiplier()
            
            # Base size on signal strength and confidence
            base_size = signal.strength * signal.confidence * 100  # 100 units max
            size = base_size * position_multiplier * drawdown_multiplier
        
        if abs(size) < 1:
            return None
        
        # Apply position limits
        current_position = self.positions.get(data.symbol, BacktestPosition(data.symbol)).size
        total_equity = self._calculate_total_equity(data)
        
        # Convert size to capital units (size * price)
        proposed_capital = abs(size) * data.price
        
        # Get all current positions in capital units
        current_positions_capital = {
            sym: abs(pos.size) * data.price  # Simplified: using current price for all
            for sym, pos in self.positions.items()
        }
        
        adjusted_capital = self.position_limiter.check_limit(
            proposed_size=proposed_capital if size > 0 else -proposed_capital,
            symbol=data.symbol,
            capital=total_equity,
            current_positions=current_positions_capital
        )
        
        # Convert back to units
        adjusted_size = (adjusted_capital / data.price) if data.price > 0 else 0
        if size < 0:
            adjusted_size = -adjusted_size
        
        if abs(adjusted_size) < 1:
            return None
        
        # Determine side and limit price
        side = 'BUY' if adjusted_size > 0 else 'SELL'
        
        # Set aggressive limit price to ensure fill in backtest
        if side == 'BUY':
            limit_price = data.ask * 1.01  # 1% above ask
        else:
            limit_price = data.bid * 0.99  # 1% below bid
        
        # Create order
        order_id = f"backtest_{len(self.filled_orders) + len(self.pending_orders)}"
        order = BacktestOrder(
            order_id=order_id,
            symbol=data.symbol,
            side=side,
            size=abs(adjusted_size),
            limit_price=limit_price,
            timestamp=data.timestamp
        )
        
        return order
    
    async def _close_all_positions(self, data: MarketData):
        """Close all positions at final prices."""
        for symbol, position in self.positions.items():
            if position.size != 0 and symbol == data.symbol:
                # Create closing order
                side = 'SELL' if position.size > 0 else 'BUY'
                order = BacktestOrder(
                    order_id=f"close_{symbol}",
                    symbol=symbol,
                    side=side,
                    size=abs(position.size),
                    limit_price=data.price,
                    timestamp=data.timestamp
                )
                
                # Fill at market price
                order.fill_price = data.price
                order.filled = True
                
                # Update position
                size_delta = -position.size
                position.update(size_delta, data.price)
                
                self.filled_orders.append(order)
                
                logger.debug(f"Closed position in {symbol}: {size_delta} @ {data.price}")
    
    def _calculate_metrics(self) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics."""
        if not self.equity_curve:
            return {}
        
        # Extract equity values
        timestamps, equity_values = zip(*self.equity_curve)
        equity_array = np.array(equity_values)
        
        # Total PnL
        total_pnl = equity_array[-1] - self.initial_capital
        total_return = total_pnl / self.initial_capital
        
        # Calculate returns
        returns = np.diff(equity_array) / equity_array[:-1]
        returns = returns[~np.isnan(returns)]  # Remove NaN values
        
        # Sharpe ratio (annualized, assuming daily data)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # Maximum drawdown
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = np.min(drawdown)
        
        # Win rate
        winning_trades = sum(1 for trade in self.trade_log 
                           if self._is_winning_trade(trade))
        total_trades = len(self.trade_log)
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0
        
        # Regime-specific metrics
        regime_breakdown = {}
        for regime, metrics in self.regime_metrics.items():
            if metrics['trades'] > 0:
                regime_breakdown[regime] = {
                    'trades': metrics['trades'],
                    'pnl': metrics['pnl'],
                    'win_rate': metrics['wins'] / metrics['trades']
                }
        
        return {
            'total_pnl': total_pnl,
            'total_return': total_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'total_trades': total_trades,
            'final_equity': equity_array[-1],
            'regime_breakdown': regime_breakdown,
            'equity_curve': self.equity_curve,
            'trade_log': self.trade_log,
            'regime_changes': self.regime_changes
        }
    
    def _is_winning_trade(self, trade: Dict[str, Any]) -> bool:
        """Determine if a trade was profitable."""
        # Look up position PnL at trade time
        # Simplified: assume trade is winning if it contributed to positive PnL
        # In practice, would need to track individual trade PnL
        return True  # Placeholder
    
    def compare_strategies(
        self,
        strategy_a_results: Dict[str, Any],
        strategy_b_results: Dict[str, Any],
        confidence_level: float = 0.95
    ) -> Dict[str, Any]:
        """
        Compare two strategies with statistical significance testing.
        
        Args:
            strategy_a_results: Results from strategy A
            strategy_b_results: Results from strategy B
            confidence_level: Confidence level for significance test
            
        Returns:
            Dictionary with comparison metrics and significance
        """
        # Extract returns from equity curves
        returns_a = self._extract_returns(strategy_a_results['equity_curve'])
        returns_b = self._extract_returns(strategy_b_results['equity_curve'])
        
        # Calculate mean difference
        mean_diff = np.mean(returns_a) - np.mean(returns_b)
        
        # Perform t-test
        from scipy import stats
        t_stat, p_value = stats.ttest_ind(returns_a, returns_b)
        
        # Determine significance
        is_significant = p_value < (1 - confidence_level)
        
        comparison = {
            'strategy_a_sharpe': strategy_a_results['sharpe_ratio'],
            'strategy_b_sharpe': strategy_b_results['sharpe_ratio'],
            'strategy_a_return': strategy_a_results['total_return'],
            'strategy_b_return': strategy_b_results['total_return'],
            'mean_return_diff': mean_diff,
            't_statistic': t_stat,
            'p_value': p_value,
            'is_significant': bool(is_significant),  # Convert numpy bool to Python bool
            'confidence_level': confidence_level,
            'winner': 'A' if strategy_a_results['sharpe_ratio'] > strategy_b_results['sharpe_ratio'] else 'B'
        }
        
        logger.info(
            f"Strategy comparison: Winner={comparison['winner']}, "
            f"Significant={is_significant}, p-value={p_value:.4f}"
        )
        
        return comparison
    
    def _extract_returns(self, equity_curve: List[Tuple[datetime, float]]) -> np.ndarray:
        """Extract returns from equity curve."""
        if not equity_curve:
            return np.array([])
        
        _, equity_values = zip(*equity_curve)
        equity_array = np.array(equity_values)
        returns = np.diff(equity_array) / equity_array[:-1]
        return returns[~np.isnan(returns)]
