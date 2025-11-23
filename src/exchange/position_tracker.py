"""Position tracking and reconciliation.

This module maintains local position state and reconciles with exchange.
"""

from datetime import datetime
from typing import Dict, Optional
from loguru import logger

from src.exchange.imc_client import IMCExchangeClient
from src.utils.types import Position


class PositionTracker:
    """Tracks positions across all instruments with reconciliation.
    
    Maintains local state independent of exchange connection and
    periodically reconciles with exchange data.
    """
    
    def __init__(self, exchange_client: IMCExchangeClient):
        """Initialize position tracker.
        
        Args:
            exchange_client: Authenticated IMC exchange client
        """
        self.client = exchange_client
        self.positions: Dict[str, Position] = {}
        self.last_reconciliation: Optional[datetime] = None
        
    def update_position(
        self,
        symbol: str,
        size: float,
        price: float,
        is_fill: bool = True
    ) -> None:
        """Update position after order fill or manual adjustment.
        
        Args:
            symbol: Product symbol
            size: Size change (positive for buy, negative for sell)
            price: Fill price
            is_fill: True if this is from an order fill, False for manual adjustment
        """
        if symbol not in self.positions:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol,
                size=size,
                entry_price=price,
                current_price=price,
                unrealized_pnl=0.0
            )
            logger.info(f"New position opened: {symbol} size={size} @ {price}")
        else:
            # Update existing position
            pos = self.positions[symbol]
            old_size = pos.size
            new_size = old_size + size
            
            if new_size == 0:
                # Position closed
                realized_pnl = -old_size * (price - pos.entry_price)
                logger.info(f"Position closed: {symbol} realized PnL={realized_pnl:.2f}")
                del self.positions[symbol]
            elif (old_size > 0 and new_size > 0) or (old_size < 0 and new_size < 0):
                # Adding to position - update average entry price
                total_cost = old_size * pos.entry_price + size * price
                pos.size = new_size
                pos.entry_price = total_cost / new_size
                pos.current_price = price
                pos.unrealized_pnl = new_size * (price - pos.entry_price)
                logger.info(f"Position increased: {symbol} size={old_size}->{new_size} "
                          f"avg_entry={pos.entry_price:.2f}")
            else:
                # Reducing position or flipping
                if abs(new_size) < abs(old_size):
                    # Partial close
                    realized_pnl = -size * (price - pos.entry_price)
                    pos.size = new_size
                    pos.current_price = price
                    pos.unrealized_pnl = new_size * (price - pos.entry_price)
                    logger.info(f"Position reduced: {symbol} size={old_size}->{new_size} "
                              f"realized_pnl={realized_pnl:.2f}")
                else:
                    # Flipping position
                    realized_pnl = -old_size * (price - pos.entry_price)
                    pos.size = new_size
                    pos.entry_price = price
                    pos.current_price = price
                    pos.unrealized_pnl = 0.0
                    logger.info(f"Position flipped: {symbol} size={old_size}->{new_size} "
                              f"realized_pnl={realized_pnl:.2f}")
    
    def update_market_price(self, symbol: str, price: float) -> None:
        """Update current market price for position PnL calculation.
        
        Args:
            symbol: Product symbol
            price: Current market price
        """
        if symbol in self.positions:
            pos = self.positions[symbol]
            pos.current_price = price
            pos.unrealized_pnl = pos.size * (price - pos.entry_price)
            
    def get_position(self, symbol: str) -> float:
        """Get current position size for a symbol.
        
        Args:
            symbol: Product symbol
            
        Returns:
            Position size (0 if no position)
        """
        if symbol in self.positions:
            return self.positions[symbol].size
        return 0.0
        
    def get_position_details(self, symbol: str) -> Optional[Position]:
        """Get full position details for a symbol.
        
        Args:
            symbol: Product symbol
            
        Returns:
            Position object or None if no position
        """
        return self.positions.get(symbol)
        
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all current positions.
        
        Returns:
            Dictionary mapping symbol to Position
        """
        return self.positions.copy()
        
    def get_total_exposure(self, prices: Optional[Dict[str, float]] = None) -> float:
        """Calculate total capital exposure across all positions.
        
        Args:
            prices: Optional dict of current prices (uses position prices if not provided)
            
        Returns:
            Total exposure as sum of abs(size * price)
        """
        total = 0.0
        for symbol, pos in self.positions.items():
            price = prices.get(symbol, pos.current_price) if prices else pos.current_price
            total += abs(pos.size * price)
        return total
        
    def get_total_unrealized_pnl(self) -> float:
        """Calculate total unrealized PnL across all positions.
        
        Returns:
            Sum of unrealized PnL for all positions
        """
        return sum(pos.unrealized_pnl for pos in self.positions.values())
        
    async def reconcile_with_exchange(self) -> bool:
        """Reconcile local positions with exchange state.
        
        Fetches positions from exchange and updates local state.
        Logs any discrepancies for investigation.
        
        Returns:
            True if reconciliation successful
        """
        try:
            exchange_positions = await self.client.get_positions()
            
            # Check for discrepancies
            local_symbols = set(self.positions.keys())
            exchange_symbols = set(exchange_positions.keys())
            
            # Symbols only in local state
            only_local = local_symbols - exchange_symbols
            if only_local:
                logger.warning(f"Positions in local state but not on exchange: {only_local}")
                
            # Symbols only on exchange
            only_exchange = exchange_symbols - local_symbols
            if only_exchange:
                logger.warning(f"Positions on exchange but not in local state: {only_exchange}")
                
            # Check size discrepancies for common symbols
            for symbol in local_symbols & exchange_symbols:
                local_size = self.positions[symbol].size
                exchange_size = exchange_positions[symbol].size
                
                if abs(local_size - exchange_size) > 0.01:  # Allow small rounding errors
                    logger.error(f"Position size mismatch for {symbol}: "
                               f"local={local_size}, exchange={exchange_size}")
            
            # Update local state from exchange (exchange is source of truth)
            self.positions = exchange_positions
            self.last_reconciliation = datetime.now()
            
            logger.info(f"Position reconciliation complete: {len(self.positions)} positions")
            return True
            
        except Exception as e:
            logger.error(f"Error during position reconciliation: {e}", exc_info=True)
            return False
            
    def get_position_limit_remaining(self, symbol: str, max_position: int = 200) -> tuple[float, float]:
        """Get remaining capacity before hitting position limits.
        
        Args:
            symbol: Product symbol
            max_position: Maximum position size (default 200)
            
        Returns:
            Tuple of (buy_capacity, sell_capacity)
        """
        current_size = self.get_position(symbol)
        buy_capacity = max_position - current_size
        sell_capacity = current_size - (-max_position)
        return (buy_capacity, sell_capacity)
        
    def can_trade(self, symbol: str, size: float, max_position: int = 200) -> bool:
        """Check if a trade would violate position limits.
        
        Args:
            symbol: Product symbol
            size: Proposed trade size (positive for buy, negative for sell)
            max_position: Maximum position size (default 200)
            
        Returns:
            True if trade is within limits
        """
        current_size = self.get_position(symbol)
        projected_size = current_size + size
        return -max_position <= projected_size <= max_position
