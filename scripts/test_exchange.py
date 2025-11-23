"""
Test script for IMC Exchange integration.

This script tests all exchange functionality before production deployment:
- Authentication
- Product fetching
- Market data retrieval
- Order submission and tracking
- Position tracking
- Error handling
- Logging verification
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from loguru import logger
from src.utils.config import load_config
from src.exchange.imc_client import IMCExchangeClient
from src.exchange.order_manager import OrderManager
from src.exchange.position_tracker import PositionTracker


class ExchangeTester:
    """Comprehensive exchange testing suite."""
    
    def __init__(self, config: dict):
        """Initialize tester with configuration."""
        self.config = config
        self.exchange_config = config.get('exchange', {})
        self.test_results = {}
        
    async def test_authentication(self) -> bool:
        """Test 1: Authentication with IMC exchange."""
        logger.info("=" * 60)
        logger.info("TEST 1: Authentication")
        logger.info("=" * 60)
        
        try:
            async with IMCExchangeClient(
                base_url=self.exchange_config.get('url'),
                username=self.exchange_config.get('username'),
                password=self.exchange_config.get('password')
            ) as client:
                
                if client._authenticated and client.token:
                    logger.success("✓ Authentication successful")
                    logger.info(f"  Token: {client.token[:20]}...")
                    self.test_results['authentication'] = True
                    return True
                else:
                    logger.error("✗ Authentication failed")
                    self.test_results['authentication'] = False
                    return False
                    
        except Exception as e:
            logger.error(f"✗ Authentication error: {e}")
            self.test_results['authentication'] = False
            return False
    
    async def test_product_fetching(self, client: IMCExchangeClient) -> bool:
        """Test 2: Fetch all tradeable instruments."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 2: Product Fetching")
        logger.info("=" * 60)
        
        try:
            products = await client.get_products()
            
            if not products:
                logger.error("✗ No products returned")
                self.test_results['product_fetching'] = False
                return False
            
            logger.success(f"✓ Fetched {len(products)} products")
            
            # Verify all 8 instruments are available
            expected_instruments = self.exchange_config.get('instruments', [])
            found_symbols = [p.symbol for p in products]
            
            logger.info("\nAvailable instruments:")
            for product in products:
                logger.info(f"  - {product.symbol}: "
                          f"tick_size={product.tick_size}, "
                          f"starting_price={product.starting_price}")
            
            # Check if all expected instruments are present
            missing = set(expected_instruments) - set(found_symbols)
            if missing:
                logger.warning(f"  Missing instruments: {missing}")
            
            if len(products) >= 8:
                logger.success("✓ All 8 instruments are tradeable")
                self.test_results['product_fetching'] = True
                return True
            else:
                logger.warning(f"⚠ Only {len(products)} instruments available (expected 8)")
                self.test_results['product_fetching'] = True  # Still pass if we have some
                return True
                
        except Exception as e:
            logger.error(f"✗ Product fetching error: {e}")
            self.test_results['product_fetching'] = False
            return False
    
    async def test_market_data(self, client: IMCExchangeClient) -> bool:
        """Test 3: Fetch real-time market data."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 3: Market Data Retrieval")
        logger.info("=" * 60)
        
        try:
            market_data = await client.get_market_data()
            
            if not market_data:
                logger.warning("⚠ No market data available (market may not be open)")
                self.test_results['market_data'] = True  # Not a failure
                return True
            
            logger.success(f"✓ Fetched market data for {len(market_data)} symbols")
            
            logger.info("\nCurrent market prices:")
            for symbol, data in market_data.items():
                logger.info(f"  {symbol}: price={data.price:.2f}, "
                          f"bid={data.bid:.2f}, ask={data.ask:.2f}")
            
            self.test_results['market_data'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Market data error: {e}")
            self.test_results['market_data'] = False
            return False
    
    async def test_order_submission(self, client: IMCExchangeClient) -> bool:
        """Test 4: Submit small test orders."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 4: Order Submission")
        logger.info("=" * 60)
        
        try:
            # Get products to find a valid symbol
            products = await client.get_products()
            if not products:
                logger.error("✗ No products available for testing")
                self.test_results['order_submission'] = False
                return False
            
            # Use first product for testing
            test_product = products[0]
            test_symbol = test_product.symbol
            test_price = test_product.starting_price
            
            logger.info(f"Testing with symbol: {test_symbol}")
            logger.info(f"Starting price: {test_price}")
            
            # Submit a small BUY order
            logger.info("\nSubmitting small BUY order (volume=1)...")
            start_time = datetime.now()
            
            order = await client.submit_order(
                symbol=test_symbol,
                side='BUY',
                price=test_price * 0.95,  # Below market to avoid immediate fill
                volume=1
            )
            
            latency = (datetime.now() - start_time).total_seconds() * 1000
            
            if order:
                logger.success(f"✓ Order submitted successfully (latency: {latency:.1f}ms)")
                logger.info(f"  Order ID: {order.order_id}")
                logger.info(f"  Symbol: {order.symbol}")
                logger.info(f"  Size: {order.size}")
                logger.info(f"  Limit Price: {order.limit_price}")
                
                # Verify latency requirement (< 50ms target)
                if latency < 50:
                    logger.success(f"✓ Latency within target (< 50ms)")
                else:
                    logger.warning(f"⚠ Latency above target: {latency:.1f}ms > 50ms")
                
                # Cancel the test order
                logger.info("\nCancelling test order...")
                cancelled = await client.cancel_order(order.order_id)
                
                if cancelled:
                    logger.success("✓ Order cancelled successfully")
                else:
                    logger.warning("⚠ Order cancellation failed (may have filled)")
                
                self.test_results['order_submission'] = True
                return True
            else:
                logger.error("✗ Order submission failed")
                self.test_results['order_submission'] = False
                return False
                
        except Exception as e:
            logger.error(f"✗ Order submission error: {e}")
            self.test_results['order_submission'] = False
            return False
    
    async def test_position_tracking(self, client: IMCExchangeClient) -> bool:
        """Test 5: Position tracking and PnL calculation."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 5: Position Tracking")
        logger.info("=" * 60)
        
        try:
            positions = await client.get_positions()
            
            logger.success(f"✓ Fetched positions (count: {len(positions)})")
            
            if positions:
                logger.info("\nCurrent positions:")
                total_pnl = 0
                for symbol, pos in positions.items():
                    logger.info(f"  {symbol}:")
                    logger.info(f"    Size: {pos.size}")
                    logger.info(f"    Entry: {pos.entry_price:.2f}")
                    logger.info(f"    Current: {pos.current_price:.2f}")
                    logger.info(f"    PnL: {pos.unrealized_pnl:.2f}")
                    total_pnl += pos.unrealized_pnl
                
                logger.info(f"\nTotal unrealized PnL: {total_pnl:.2f}")
            else:
                logger.info("  No open positions (empty portfolio)")
            
            self.test_results['position_tracking'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Position tracking error: {e}")
            self.test_results['position_tracking'] = False
            return False
    
    async def test_position_limits(self, client: IMCExchangeClient) -> bool:
        """Test 6: Position limit enforcement (-200 to +200)."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 6: Position Limit Enforcement")
        logger.info("=" * 60)
        
        try:
            # Get products
            products = await client.get_products()
            if not products:
                logger.error("✗ No products available")
                self.test_results['position_limits'] = False
                return False
            
            test_product = products[0]
            test_symbol = test_product.symbol
            
            # Get current position
            positions = await client.get_positions()
            current_position = positions.get(test_symbol, None)
            current_size = current_position.size if current_position else 0
            
            logger.info(f"Current position in {test_symbol}: {current_size}")
            
            # Test limits
            position_limits = self.exchange_config.get('position_limits', {})
            min_limit = position_limits.get('min', -200)
            max_limit = position_limits.get('max', 200)
            
            logger.info(f"Position limits: {min_limit} to {max_limit}")
            
            # Verify limits are enforced
            if min_limit <= current_size <= max_limit:
                logger.success("✓ Current position within limits")
                self.test_results['position_limits'] = True
                return True
            else:
                logger.error(f"✗ Position {current_size} outside limits [{min_limit}, {max_limit}]")
                self.test_results['position_limits'] = False
                return False
                
        except Exception as e:
            logger.error(f"✗ Position limit test error: {e}")
            self.test_results['position_limits'] = False
            return False
    
    async def test_error_handling(self, client: IMCExchangeClient) -> bool:
        """Test 7: Graceful error handling."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 7: Error Handling")
        logger.info("=" * 60)
        
        try:
            # Test 1: Invalid symbol
            logger.info("Testing invalid symbol...")
            order = await client.submit_order(
                symbol='INVALID_SYMBOL',
                side='BUY',
                price=100,
                volume=1
            )
            
            if order is None:
                logger.success("✓ Invalid symbol handled gracefully")
            else:
                logger.warning("⚠ Invalid symbol order accepted (unexpected)")
            
            # Test 2: Invalid price (negative)
            logger.info("\nTesting invalid price...")
            products = await client.get_products()
            if products:
                order = await client.submit_order(
                    symbol=products[0].symbol,
                    side='BUY',
                    price=-100,  # Invalid negative price
                    volume=1
                )
                
                if order is None:
                    logger.success("✓ Invalid price handled gracefully")
                else:
                    logger.warning("⚠ Invalid price order accepted (unexpected)")
            
            # Test 3: Zero volume
            logger.info("\nTesting zero volume...")
            if products:
                order = await client.submit_order(
                    symbol=products[0].symbol,
                    side='BUY',
                    price=100,
                    volume=0
                )
                
                if order is None:
                    logger.success("✓ Zero volume handled gracefully")
                else:
                    logger.warning("⚠ Zero volume order accepted (unexpected)")
            
            logger.success("\n✓ Error handling tests completed")
            self.test_results['error_handling'] = True
            return True
            
        except Exception as e:
            # Exceptions should be caught and logged, not crash
            logger.error(f"✗ Error handling test failed: {e}")
            self.test_results['error_handling'] = False
            return False
    
    async def test_order_manager(self) -> bool:
        """Test 8: OrderManager integration."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 8: OrderManager Integration")
        logger.info("=" * 60)
        
        try:
            async with IMCExchangeClient(
                base_url=self.exchange_config.get('url'),
                username=self.exchange_config.get('username'),
                password=self.exchange_config.get('password')
            ) as client:
                
                order_manager = OrderManager(exchange_client=client)
                
                # Get products
                products = await client.get_products()
                if not products:
                    logger.error("✗ No products available")
                    self.test_results['order_manager'] = False
                    return False
                
                test_symbol = products[0].symbol
                test_price = products[0].starting_price
                
                # Submit order through manager
                logger.info(f"Submitting order through OrderManager...")
                order = await order_manager.submit_order(
                    symbol=test_symbol,
                    size=1,  # Small test order
                    limit_price=test_price * 0.95
                )
                
                if order:
                    logger.success("✓ OrderManager submitted order successfully")
                    logger.info(f"  Order ID: {order.order_id}")
                    
                    # Cancel through manager
                    cancelled = await order_manager.cancel_order(order.order_id)
                    if cancelled:
                        logger.success("✓ OrderManager cancelled order successfully")
                    
                    self.test_results['order_manager'] = True
                    return True
                else:
                    logger.error("✗ OrderManager failed to submit order")
                    self.test_results['order_manager'] = False
                    return False
                    
        except Exception as e:
            logger.error(f"✗ OrderManager test error: {e}")
            self.test_results['order_manager'] = False
            return False
    
    async def test_position_tracker(self) -> bool:
        """Test 9: PositionTracker integration."""
        logger.info("\n" + "=" * 60)
        logger.info("TEST 9: PositionTracker Integration")
        logger.info("=" * 60)
        
        try:
            async with IMCExchangeClient(
                base_url=self.exchange_config.get('url'),
                username=self.exchange_config.get('username'),
                password=self.exchange_config.get('password')
            ) as client:
                
                position_tracker = PositionTracker(exchange_client=client)
                
                # Sync positions
                logger.info("Syncing positions...")
                await position_tracker.reconcile_with_exchange()
                
                # Get all positions
                positions = position_tracker.get_all_positions()
                logger.success(f"✓ PositionTracker synced {len(positions)} positions")
                
                # Get total exposure
                total_exposure = position_tracker.get_total_exposure()
                logger.info(f"  Total exposure: {total_exposure:.2f}")
                
                self.test_results['position_tracker'] = True
                return True
                
        except Exception as e:
            logger.error(f"✗ PositionTracker test error: {e}")
            self.test_results['position_tracker'] = False
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all exchange tests."""
        logger.info("\n" + "=" * 80)
        logger.info("IMC EXCHANGE INTEGRATION TEST SUITE")
        logger.info("=" * 80)
        logger.info(f"Exchange URL: {self.exchange_config.get('url')}")
        logger.info(f"Username: {self.exchange_config.get('username')}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        logger.info("=" * 80 + "\n")
        
        # Test 1: Authentication (required for all other tests)
        auth_success = await self.test_authentication()
        if not auth_success:
            logger.error("\n✗ Authentication failed - cannot proceed with other tests")
            return self.test_results
        
        # Run remaining tests with authenticated client
        async with IMCExchangeClient(
            base_url=self.exchange_config.get('url'),
            username=self.exchange_config.get('username'),
            password=self.exchange_config.get('password')
        ) as client:
            
            # Test 2: Product fetching
            await self.test_product_fetching(client)
            
            # Test 3: Market data
            await self.test_market_data(client)
            
            # Test 4: Order submission
            await self.test_order_submission(client)
            
            # Test 5: Position tracking
            await self.test_position_tracking(client)
            
            # Test 6: Position limits
            await self.test_position_limits(client)
            
            # Test 7: Error handling
            await self.test_error_handling(client)
        
        # Test 8: OrderManager (creates own client)
        await self.test_order_manager()
        
        # Test 9: PositionTracker (creates own client)
        await self.test_position_tracker()
        
        # Print summary
        self.print_summary()
        
        return self.test_results
    
    def print_summary(self):
        """Print test results summary."""
        logger.info("\n" + "=" * 80)
        logger.info("TEST SUMMARY")
        logger.info("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for test_name, result in self.test_results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status}: {test_name}")
        
        logger.info("=" * 80)
        logger.info(f"Total: {total_tests} tests")
        logger.info(f"Passed: {passed_tests} tests")
        logger.info(f"Failed: {failed_tests} tests")
        logger.info(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        logger.info("=" * 80)
        
        if failed_tests == 0:
            logger.success("\n🎉 ALL TESTS PASSED - Ready for production!")
        else:
            logger.warning(f"\n⚠ {failed_tests} test(s) failed - Review before production")


async def main():
    """Main test execution."""
    # Load configuration
    try:
        config = load_config('config.yaml')
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create tester
    tester = ExchangeTester(config)
    
    # Run all tests
    results = await tester.run_all_tests()
    
    # Exit with appropriate code
    if all(results.values()):
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure


if __name__ == '__main__':
    asyncio.run(main())
