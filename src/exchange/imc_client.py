"""IMC Exchange REST API client.

This module provides async communication with the IMC trading exchange.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from loguru import logger
import aiohttp
from pydantic import BaseModel, Field

from src.utils.types import Order, Position, MarketData


class Product(BaseModel):
    """Exchange product information."""
    
    symbol: str = Field(..., description="Product symbol")
    tick_size: float = Field(..., alias="tickSize", description="Minimum price increment")
    starting_price: float = Field(..., alias="startingPrice", description="Starting price")
    contract_size: int = Field(..., alias="contractSize", description="Contract size")


class IMCExchangeClient:
    """Async REST API client for IMC exchange.
    
    Handles authentication, market data fetching, and order management
    with automatic reconnection and exponential backoff.
    """
    
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        timeout: int = 5000,
        max_retries: int = 3
    ):
        """Initialize IMC exchange client.
        
        Args:
            base_url: Exchange base URL (e.g., http://exchange.com)
            username: Team username
            password: Team password
            timeout: Request timeout in milliseconds
            max_retries: Maximum retry attempts for failed requests
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = aiohttp.ClientTimeout(total=timeout / 1000)
        self.max_retries = max_retries
        
        self.token: Optional[str] = None
        self.session: Optional[aiohttp.ClientSession] = None
        self._authenticated = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(timeout=self.timeout)
        await self.authenticate()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
            
    async def authenticate(self) -> bool:
        """Authenticate with the exchange and obtain bearer token.
        
        Returns:
            True if authentication successful, False otherwise
            
        Performance: ~50-100ms typical
        """
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=self.timeout)
            
        url = f"{self.base_url}/api/user/authenticate"
        payload = {
            "username": self.username,
            "password": self.password
        }
        
        try:
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    # Token is in the Authorization header, not the body
                    auth_header = response.headers.get('Authorization', '')
                    if auth_header.startswith('Bearer '):
                        self.token = auth_header.replace('Bearer ', '')
                        self._authenticated = True
                        logger.info(f"Successfully authenticated as {self.username}")
                        return True
                    else:
                        logger.error("Authentication response missing Bearer token")
                        return False
                else:
                    logger.error(f"Authentication failed with status {response.status}")
                    return False
                    
        except aiohttp.ClientError as e:
            logger.error(f"Authentication request failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {e}", exc_info=True)
            return False
            
    async def _ensure_authenticated(self) -> None:
        """Ensure client is authenticated, re-authenticate if needed."""
        if not self._authenticated or not self.token:
            await self.authenticate()
            
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication token."""
        if not self.token:
            return {}
        return {"Authorization": f"Bearer {self.token}"}
        
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        **kwargs
    ) -> Dict:
        """Make HTTP request with exponential backoff retry.
        
        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            **kwargs: Additional arguments for aiohttp request
            
        Returns:
            Response data as dictionary
            
        Raises:
            aiohttp.ClientError: If all retries fail
        """
        await self._ensure_authenticated()
        
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers()
        headers.update(kwargs.pop('headers', {}))
        
        for attempt in range(self.max_retries):
            try:
                async with self.session.request(
                    method,
                    url,
                    headers=headers,
                    **kwargs
                ) as response:
                    # If unauthorized, try to re-authenticate once
                    if response.status == 401 and attempt == 0:
                        logger.warning("Token expired, re-authenticating...")
                        await self.authenticate()
                        headers = self._get_headers()
                        continue
                    
                    # Read response data before returning
                    if response.status in (200, 201, 204):
                        if response.status == 204:
                            return {'status': 'success'}
                        try:
                            data = await response.json()
                            return {'status': response.status, 'data': data}
                        except:
                            text = await response.text()
                            return {'status': response.status, 'text': text}
                    else:
                        text = await response.text()
                        return {'status': response.status, 'error': text}
                    
            except aiohttp.ClientError as e:
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Request failed (attempt {attempt + 1}/{self.max_retries}), "
                                 f"retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"Request failed after {self.max_retries} attempts: {e}")
                    raise
                    
    async def get_products(self) -> List[Product]:
        """Fetch all tradeable instruments from the exchange.
        
        Returns:
            List of Product objects with symbol, tick size, etc.
            
        Performance: ~20-50ms typical
        """
        try:
            result = await self._request_with_retry('GET', '/api/product')
            if result.get('status') == 200 and 'data' in result:
                data = result['data']
                products = [Product(**item) for item in data]
                logger.debug(f"Fetched {len(products)} products")
                return products
            else:
                logger.error(f"Failed to fetch products: {result.get('status')}")
                return []
                    
        except Exception as e:
            logger.error(f"Error fetching products: {e}", exc_info=True)
            return []
            
    async def get_market_data(self, symbol: Optional[str] = None) -> Dict[str, MarketData]:
        """Fetch real-time market data and order book.
        
        Args:
            symbol: Optional symbol to filter (if None, returns all)
            
        Returns:
            Dictionary mapping symbol to MarketData
            
        Performance: ~20-50ms typical
        """
        try:
            result = await self._request_with_retry('GET', '/api/trade')
            if result.get('status') == 200 and 'data' in result:
                data = result['data']
                
                # Transform exchange data to MarketData format
                market_data = {}
                for item in data:
                    sym = item.get('symbol')
                    if symbol and sym != symbol:
                        continue
                        
                    # Extract price data
                    price = item.get('price', 0)
                    bid = item.get('bid', price)
                    ask = item.get('ask', price)
                    volume = item.get('volume', 0)
                    
                    if price > 0:  # Only include valid data
                        market_data[sym] = MarketData(
                            timestamp=datetime.now(),
                            symbol=sym,
                            price=price,
                            volume=volume,
                            bid=bid,
                            ask=ask,
                            returns=[]
                        )
                
                logger.debug(f"Fetched market data for {len(market_data)} symbols")
                return market_data
            else:
                logger.error(f"Failed to fetch market data: {result.get('status')}")
                return {}
                    
        except Exception as e:
            logger.error(f"Error fetching market data: {e}", exc_info=True)
            return {}
            
    async def submit_order(
        self,
        symbol: str,
        side: str,
        price: float,
        volume: int
    ) -> Optional[Order]:
        """Submit a limit order to the exchange.
        
        Args:
            symbol: Product symbol (e.g., '7_ETF')
            side: 'BUY' or 'SELL'
            price: Limit price
            volume: Order volume (positive integer)
            
        Returns:
            Order object if successful, None otherwise
            
        Performance: Target < 50ms
        """
        payload = {
            "symbol": symbol,
            "side": side.upper(),
            "price": price,
            "volume": abs(volume)  # Ensure positive
        }
        
        try:
            start_time = datetime.now()
            
            result = await self._request_with_retry(
                'POST',
                '/api/order',
                json=payload
            )
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            if result.get('status') in (200, 201) and 'data' in result:
                data = result['data']
                order_id = data.get('orderId', data.get('id', 'unknown'))
                
                # Convert to internal Order format
                order = Order(
                    order_id=str(order_id),
                    symbol=symbol,
                    size=volume if side.upper() == 'BUY' else -volume,
                    limit_price=price,
                    status='pending',
                    timestamp=datetime.now()
                )
                
                logger.info(f"Order submitted: {symbol} {side} {volume}@{price} "
                          f"(ID: {order_id}, latency: {latency:.1f}ms)")
                return order
                
            else:
                error_text = result.get('error', 'Unknown error')
                logger.error(f"Order submission failed ({result.get('status')}): {error_text}")
                return None
                    
        except Exception as e:
            logger.error(f"Error submitting order: {e}", exc_info=True)
            return None
            
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            result = await self._request_with_retry(
                'DELETE',
                f'/api/order/{order_id}'
            )
            
            if result.get('status') in (200, 204):
                logger.info(f"Order {order_id} cancelled successfully")
                return True
            else:
                logger.error(f"Failed to cancel order {order_id}: {result.get('status')}")
                return False
                    
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}", exc_info=True)
            return False
            
    async def get_order_status(self) -> List[Order]:
        """Get all active orders for current user.
        
        Returns:
            List of active Order objects
        """
        try:
            result = await self._request_with_retry(
                'GET',
                '/api/order/current-user'
            )
            
            if result.get('status') == 200 and 'data' in result:
                data = result['data']
                
                orders = []
                for item in data:
                    order = Order(
                        order_id=str(item.get('orderId', item.get('id', 'unknown'))),
                        symbol=item.get('symbol', ''),
                        size=item.get('volume', 0) if item.get('side') == 'BUY' else -item.get('volume', 0),
                        limit_price=item.get('price', 0),
                        status=item.get('status', 'unknown').lower(),
                        timestamp=datetime.fromisoformat(item.get('timestamp', datetime.now().isoformat()))
                    )
                    orders.append(order)
                
                logger.debug(f"Fetched {len(orders)} active orders")
                return orders
            else:
                logger.error(f"Failed to fetch orders: {result.get('status')}")
                return []
                    
        except Exception as e:
            logger.error(f"Error fetching orders: {e}", exc_info=True)
            return []
            
    async def get_positions(self) -> Dict[str, Position]:
        """Get current positions for all instruments.
        
        Returns:
            Dictionary mapping symbol to Position
            
        Note: May return 500 error if portfolio is empty (exchange bug)
        """
        try:
            result = await self._request_with_retry(
                'GET',
                '/api/position/current-user'
            )
            
            if result.get('status') == 200 and 'data' in result:
                data = result['data']
                
                positions = {}
                for item in data:
                    symbol = item.get('symbol', '')
                    size = item.get('volume', 0)
                    entry_price = item.get('averagePrice', 0)
                    current_price = item.get('currentPrice', entry_price)
                    
                    if size != 0:  # Only include non-zero positions
                        positions[symbol] = Position(
                            symbol=symbol,
                            size=size,
                            entry_price=entry_price,
                            current_price=current_price,
                            unrealized_pnl=size * (current_price - entry_price)
                        )
                
                logger.debug(f"Fetched {len(positions)} positions")
                return positions
                
            elif result.get('status') == 500:
                # Known issue: exchange returns 500 for empty portfolio
                logger.debug("No positions (empty portfolio)")
                return {}
            else:
                logger.error(f"Failed to fetch positions: {result.get('status')}")
                return {}
                    
        except Exception as e:
            logger.error(f"Error fetching positions: {e}", exc_info=True)
            return {}
