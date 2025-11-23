"""Order management with retry logic and rejection handling.

This module provides high-level order management on top of the exchange client.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger

from src.exchange.imc_client import IMCExchangeClient
from src.utils.types import Order


class OrderManager:
    """Manages order submission, cancellation, and status tracking.
    
    Provides retry logic for rejected orders and tracks order lifecycle.
    """
    
    # Position limits per instrument (IMC exchange rules)
    MIN_POSITION = -200
    MAX_POSITION = 200
    
    def __init__(self, exchange_client: IMCExchangeClient):
        """Initialize order manager.
        
        Args:
            exchange_client: Authenticated IMC exchange client
        """
        self.client = exchange_client
        self.active_orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        self.rejection_count: Dict[str, int] = {}  # Track rejections per symbol
        
    async def submit_order(
        self,
        symbol: str,
        size: float,
        limit_price: float,
        current_position: float = 0.0,
        max_retries: int = 3
    ) -> Optional[Order]:
        """Submit order with position limit validation and retry logic.
        
        Args:
            symbol: Product symbol
            size: Order size (positive for buy, negative for sell)
            limit_price: Limit price
            current_position: Current position in this symbol
            max_retries: Maximum retry attempts on rejection
            
        Returns:
            Order object if successful, None otherwise
            
        Performance: Target < 50ms for submission
        """
        # Validate position limits
        projected_position = current_position + size
        if projected_position > self.MAX_POSITION:
            logger.warning(f"Order would exceed max position limit: "
                         f"{projected_position} > {self.MAX_POSITION}")
            # Adjust size to stay within limits
            size = self.MAX_POSITION - current_position
            if size <= 0:
                logger.error(f"Cannot buy more {symbol}, already at max position")
                return None
                
        elif projected_position < self.MIN_POSITION:
            logger.warning(f"Order would exceed min position limit: "
                         f"{projected_position} < {self.MIN_POSITION}")
            # Adjust size to stay within limits
            size = self.MIN_POSITION - current_position
            if size >= 0:
                logger.error(f"Cannot sell more {symbol}, already at min position")
                return None
        
        # Determine side
        side = 'BUY' if size > 0 else 'SELL'
        volume = abs(int(size))
        
        if volume == 0:
            logger.warning(f"Order size is zero after rounding, skipping")
            return None
        
        # Attempt submission with retries
        for attempt in range(max_retries):
            try:
                order = await self.client.submit_order(
                    symbol=symbol,
                    side=side,
                    price=limit_price,
                    volume=volume
                )
                
                if order:
                    # Track active order
                    self.active_orders[order.order_id] = order
                    self.order_history.append(order)
                    
                    # Reset rejection count on success
                    self.rejection_count[symbol] = 0
                    
                    logger.info(f"Order submitted successfully: {order.order_id}")
                    return order
                else:
                    # Order rejected
                    self.rejection_count[symbol] = self.rejection_count.get(symbol, 0) + 1
                    
                    if attempt < max_retries - 1:
                        # Adjust price slightly and retry
                        if side == 'BUY':
                            limit_price *= 1.001  # Increase buy price by 0.1%
                        else:
                            limit_price *= 0.999  # Decrease sell price by 0.1%
                        
                        logger.warning(f"Order rejected (attempt {attempt + 1}/{max_retries}), "
                                     f"adjusting price to {limit_price:.2f} and retrying")
                        await asyncio.sleep(0.1)  # Brief delay before retry
                    else:
                        logger.error(f"Order rejected after {max_retries} attempts")
                        return None
                        
            except Exception as e:
                logger.error(f"Error submitting order (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(0.1)
                else:
                    return None
        
        return None
        
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation successful
        """
        success = await self.client.cancel_order(order_id)
        
        if success and order_id in self.active_orders:
            # Update order status
            order = self.active_orders[order_id]
            order.status = 'cancelled'
            
            # Remove from active orders
            del self.active_orders[order_id]
            
            logger.info(f"Order {order_id} cancelled and removed from active orders")
        
        return success
        
    async def cancel_all_orders(self, symbol: Optional[str] = None) -> int:
        """Cancel all active orders, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol to filter cancellations
            
        Returns:
            Number of orders successfully cancelled
        """
        orders_to_cancel = [
            order_id for order_id, order in self.active_orders.items()
            if symbol is None or order.symbol == symbol
        ]
        
        if not orders_to_cancel:
            logger.debug("No active orders to cancel")
            return 0
        
        logger.info(f"Cancelling {len(orders_to_cancel)} orders" +
                   (f" for {symbol}" if symbol else ""))
        
        # Cancel concurrently
        tasks = [self.cancel_order(order_id) for order_id in orders_to_cancel]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        cancelled_count = sum(1 for r in results if r is True)
        logger.info(f"Successfully cancelled {cancelled_count}/{len(orders_to_cancel)} orders")
        
        return cancelled_count
        
    async def update_order_status(self) -> None:
        """Update status of all active orders from exchange.
        
        Removes filled or cancelled orders from active tracking.
        """
        try:
            current_orders = await self.client.get_order_status()
            
            # Create lookup by order ID
            current_order_ids = {order.order_id for order in current_orders}
            
            # Check for filled/cancelled orders
            for order_id in list(self.active_orders.keys()):
                if order_id not in current_order_ids:
                    # Order no longer active (filled or cancelled)
                    order = self.active_orders[order_id]
                    order.status = 'filled'  # Assume filled if not in active list
                    del self.active_orders[order_id]
                    logger.debug(f"Order {order_id} marked as filled")
            
            # Update status for remaining active orders
            for order in current_orders:
                if order.order_id in self.active_orders:
                    self.active_orders[order.order_id].status = order.status
                    
        except Exception as e:
            logger.error(f"Error updating order status: {e}", exc_info=True)
            
    def get_active_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get list of active orders, optionally filtered by symbol.
        
        Args:
            symbol: Optional symbol to filter
            
        Returns:
            List of active Order objects
        """
        if symbol:
            return [
                order for order in self.active_orders.values()
                if order.symbol == symbol
            ]
        return list(self.active_orders.values())
        
    def get_rejection_count(self, symbol: str) -> int:
        """Get number of consecutive rejections for a symbol.
        
        Args:
            symbol: Product symbol
            
        Returns:
            Number of consecutive rejections
        """
        return self.rejection_count.get(symbol, 0)
        
    def should_pause_trading(self, symbol: str, threshold: int = 3) -> bool:
        """Check if trading should be paused due to repeated rejections.
        
        Args:
            symbol: Product symbol
            threshold: Rejection count threshold
            
        Returns:
            True if trading should be paused
        """
        count = self.get_rejection_count(symbol)
        if count >= threshold:
            logger.warning(f"Trading paused for {symbol} due to {count} consecutive rejections")
            return True
        return False
