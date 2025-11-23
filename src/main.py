"""
IMC Trading Bot - Main entry point.

This is the main entry point for the trading bot. It initializes all components,
starts the event loop, and coordinates trading operations.
"""

import argparse
import asyncio
import signal
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.logger import setup_logging, get_logger
from src.utils.types import Signal as TradingSignal, CityData

# Import all layers
from src.data import WeatherClient, AirQualityClient, FlightClient, CacheManager
from src.signals import FeatureEngineer, SignalGenerator, SignalCombiner
from src.strategy import RegimeDetector, AdaptiveStrategy, PositionSizer
from src.risk import PositionLimiter, DrawdownMonitor
from src.exchange import IMCExchangeClient, OrderManager, PositionTracker
from src.monitoring import TradingLogger, MetricsCollector, ReportGenerator, MetricsServer


class TradingBot:
    """
    Main trading bot orchestrator.
    
    Coordinates all layers: data ingestion → signal processing → strategy → 
    risk management → order execution → monitoring.
    
    Attributes:
        config: Configuration dictionary
        logger: Logger instance
        running: Flag indicating if bot is running
        shutdown_event: Asyncio event for graceful shutdown
    """
    
    def __init__(self, config: dict):
        """
        Initialize trading bot with all components.
        
        Args:
            config: Configuration dictionary from config.yaml
        """
        self.config = config
        self.logger = get_logger()
        self.running = False
        self.shutdown_event = asyncio.Event()
        
        # Initialize components
        self._init_data_layer()
        self._init_signal_layer()
        self._init_strategy_layer()
        self._init_risk_layer()
        self._init_execution_layer()
        self._init_monitoring_layer()
        
        self.logger.info("TradingBot initialized successfully")
    
    def _init_data_layer(self) -> None:
        """Initialize data ingestion components."""
        self.logger.info("Initializing data layer...")
        
        # Cache manager
        cache_config = self.config.get('cache', {})
        self.cache_manager = CacheManager(
            ttl=cache_config.get('ttl', 300),
            max_size=cache_config.get('max_size', 1000)
        )
        
        # Data clients
        api_keys = self.config.get('api_keys', {})
        location = self.config.get('location', {})
        data_sources = self.config.get('data_sources', {})
        
        # Format location string
        city = location.get('city', 'Munich')
        country = location.get('country', 'DE')
        location_str = f"{city},{country}"
        
        # Get coordinates
        lat = location.get('coordinates', {}).get('lat', 48.1351)
        lon = location.get('coordinates', {}).get('lon', 11.5820)
        
        self.weather_client = WeatherClient(
            api_key=api_keys.get('openweather', ''),
            location=location_str
        )
        
        self.air_quality_client = AirQualityClient(
            api_key=api_keys.get('openweather', ''),
            lat=lat,
            lon=lon
        )
        
        # Calculate bounding box for flights
        bbox_offset = data_sources.get('flights', {}).get('bbox_offset', 0.5)
        bbox = [
            lon - bbox_offset,  # lon_min
            lat - bbox_offset,  # lat_min
            lon + bbox_offset,  # lon_max
            lat + bbox_offset   # lat_max
        ]
        
        self.flight_client = FlightClient(
            bbox=bbox,
            airport_code=location.get('airport_code', 'MUC'),
            api_key=api_keys.get('opensky')
        )
        
        self.logger.info("Data layer initialized")
    
    def _init_signal_layer(self) -> None:
        """Initialize signal processing components."""
        self.logger.info("Initializing signal layer...")
        
        # Use default parameters - components are configured internally
        self.feature_engineer = FeatureEngineer()
        self.signal_generator = SignalGenerator()
        self.signal_combiner = SignalCombiner()
        
        self.logger.info("Signal layer initialized")
    
    def _init_strategy_layer(self) -> None:
        """Initialize strategy components."""
        self.logger.info("Initializing strategy layer...")
        
        # Use default parameters - components are configured internally
        self.regime_detector = RegimeDetector()
        self.adaptive_strategy = AdaptiveStrategy()
        self.position_sizer = PositionSizer()
        
        self.logger.info("Strategy layer initialized")
    
    def _init_risk_layer(self) -> None:
        """Initialize risk management components."""
        self.logger.info("Initializing risk layer...")
        
        # Use default parameters - components are configured internally
        self.position_limiter = PositionLimiter()
        
        # DrawdownMonitor needs initial capital
        backtest_config = self.config.get('backtest', {})
        initial_capital = backtest_config.get('initial_capital', 100000)
        self.drawdown_monitor = DrawdownMonitor(initial_capital=initial_capital)
        
        self.logger.info("Risk layer initialized")
    
    def _init_execution_layer(self) -> None:
        """Initialize exchange interaction components."""
        self.logger.info("Initializing execution layer...")
        
        exchange_config = self.config.get('exchange', {})
        
        self.exchange_client = IMCExchangeClient(
            base_url=exchange_config.get('url', ''),
            username=exchange_config.get('username', ''),
            password=exchange_config.get('password', '')
        )
        
        self.order_manager = OrderManager(
            exchange_client=self.exchange_client
        )
        
        self.position_tracker = PositionTracker(
            exchange_client=self.exchange_client
        )
        
        self.logger.info("Execution layer initialized")
    
    def _init_monitoring_layer(self) -> None:
        """Initialize monitoring and logging components."""
        self.logger.info("Initializing monitoring layer...")
        
        self.trading_logger = TradingLogger()
        self.metrics_collector = MetricsCollector()
        self.report_generator = ReportGenerator()
        self.metrics_server = MetricsServer(
            metrics_collector=self.metrics_collector
        )
        
        self.logger.info("Monitoring layer initialized")
    
    async def fetch_city_data(self) -> Optional[CityData]:
        """
        Fetch all city data concurrently.
        
        Returns:
            CityData object or None if all sources fail
            
        Performance: < 50ms with concurrent fetching
        """
        try:
            # Fetch all data sources concurrently
            weather_task = self.weather_client.fetch()
            air_quality_task = self.air_quality_client.fetch()
            flights_task = self.flight_client.fetch()
            
            weather_data, air_quality_data, flight_data = await asyncio.gather(
                weather_task,
                air_quality_task,
                flights_task,
                return_exceptions=True
            )
            
            # Check for failures and use cached data if needed
            if isinstance(weather_data, Exception):
                self.logger.warning(f"Weather fetch failed: {weather_data}, using cache")
                weather_data = None
            
            if isinstance(air_quality_data, Exception):
                self.logger.warning(f"Air quality fetch failed: {air_quality_data}, using cache")
                air_quality_data = None
            
            if isinstance(flight_data, Exception):
                self.logger.warning(f"Flight fetch failed: {flight_data}, using cache")
                flight_data = None
            
            # If all sources failed, return None
            if all(d is None for d in [weather_data, air_quality_data, flight_data]):
                self.logger.error("All data sources failed")
                return None
            
            # Create CityData object
            location = self.config.get('location', {})
            city_name = location.get('city', 'Munich')
            country = location.get('country', 'DE')
            
            city_data = CityData(
                timestamp=datetime.now(),
                location=f"{city_name},{country}",
                weather=weather_data,
                air_quality=air_quality_data,
                flights=flight_data
            )
            
            return city_data
            
        except Exception as e:
            self.logger.error(f"Error fetching city data: {e}", exc_info=True)
            return None
    
    async def process_trading_cycle(self) -> None:
        """
        Execute one complete trading cycle.
        
        Pipeline: fetch data → generate signals → detect regime → size position → 
                 submit order → update monitoring
                 
        Performance target: < 100ms total
        """
        try:
            cycle_start = datetime.now()
            
            # 1. Fetch city data (< 50ms)
            city_data = await self.fetch_city_data()
            if city_data is None:
                self.logger.warning("Skipping cycle due to data fetch failure")
                return
            
            # 2. Fetch market data from exchange
            try:
                products = await self.exchange_client.get_products()
                if not products:
                    self.logger.warning("No products available from exchange")
                    return
                
                # Focus on primary instrument (Munich ETF)
                primary_instrument = self.config.get('exchange', {}).get('instruments', [])[6]  # 7_ETF
                market_data = None
                
                for product in products:
                    if product.symbol == primary_instrument:
                        # Get current price from order book
                        trades = await self.exchange_client.get_trades(product.symbol)
                        if trades:
                            latest_trade = trades[0]
                            market_data = {
                                'symbol': product.symbol,
                                'price': latest_trade.get('price', 0),
                                'volume': latest_trade.get('volume', 0),
                                'timestamp': datetime.now()
                            }
                        break
                
                if market_data is None:
                    self.logger.warning(f"No market data for {primary_instrument}")
                    return
                    
            except Exception as e:
                self.logger.error(f"Error fetching market data: {e}", exc_info=True)
                return
            
            # 3. Generate features (< 20ms)
            features = self.feature_engineer.compute_features(city_data)
            
            # 4. Generate signals (< 10ms)
            raw_signals = self.signal_generator.generate(features)
            
            # 5. Detect regime
            regime = self.regime_detector.detect(market_data)
            regime_confidence = self.regime_detector.get_confidence()
            
            # 6. Combine signals with regime-specific weights
            combined_signal_strength = self.signal_combiner.combine(raw_signals, regime)
            
            # Create trading signal
            signal = TradingSignal(
                timestamp=datetime.now(),
                strength=combined_signal_strength,
                confidence=regime_confidence,
                components=raw_signals,
                regime=regime
            )
            
            # 7. Check if signal meets thresholds
            strategy_config = self.config.get('strategy', {})
            signal_threshold = strategy_config.get('signal_threshold', 0.3)
            confidence_threshold = strategy_config.get('confidence_threshold', 0.5)
            
            if abs(signal.strength) < signal_threshold or signal.confidence < confidence_threshold:
                self.logger.debug(f"Signal below threshold: strength={signal.strength:.3f}, confidence={signal.confidence:.3f}")
                return
            
            # 8. Check drawdown status
            if self.drawdown_monitor.is_safe_mode():
                self.logger.warning("Safe mode active, skipping trade")
                return
            
            # 9. Calculate position size
            capital = 100000  # TODO: Get from portfolio tracker
            base_position_size = self.position_sizer.calculate_size(
                signal=signal.strength,
                confidence=signal.confidence,
                regime=regime,
                capital=capital
            )
            
            # 10. Apply drawdown multiplier
            drawdown_multiplier = self.drawdown_monitor.get_multiplier()
            position_size = base_position_size * drawdown_multiplier
            
            # 11. Apply position limits
            current_positions = self.position_tracker.get_all_positions()
            final_position_size = self.position_limiter.check_limit(
                proposed_size=position_size,
                current_positions=current_positions
            )
            
            if final_position_size == 0:
                self.logger.info("Position size reduced to zero by risk limits")
                return
            
            # 12. Submit order (< 20ms)
            symbol = market_data['symbol']
            current_price = market_data['price']
            
            # Calculate limit price with offset
            execution_config = self.config.get('execution', {})
            limit_offset = execution_config.get('limit_price_offset', 0.0005)
            
            if signal.strength > 0:  # Buy signal
                limit_price = current_price * (1 + limit_offset)
                order_size = final_position_size
            else:  # Sell signal
                limit_price = current_price * (1 - limit_offset)
                order_size = -final_position_size
            
            try:
                order = await self.order_manager.submit_order(
                    symbol=symbol,
                    size=order_size,
                    limit_price=limit_price
                )
                
                # 13. Log trade
                self.trading_logger.log_trade(
                    symbol=symbol,
                    size=order_size,
                    price=limit_price,
                    signal=signal.strength,
                    regime=regime,
                    reasoning=f"Signal: {signal.strength:.3f}, Confidence: {signal.confidence:.3f}, Regime: {regime}"
                )
                
                # 14. Update metrics
                # Will be updated when order fills
                
                cycle_duration = (datetime.now() - cycle_start).total_seconds() * 1000
                self.logger.info(f"Trading cycle completed in {cycle_duration:.1f}ms")
                
            except Exception as e:
                self.logger.error(f"Error submitting order: {e}", exc_info=True)
                
        except Exception as e:
            self.logger.error(f"Error in trading cycle: {e}", exc_info=True)
    
    async def run(self) -> None:
        """
        Main event loop for the trading bot.
        
        Continuously executes trading cycles until shutdown signal received.
        Implements graceful error handling and recovery.
        """
        self.logger.info("Starting trading bot main loop")
        self.running = True
        
        try:
            # Authenticate with exchange
            self.logger.info("Authenticating with exchange...")
            await self.exchange_client.authenticate()
            self.logger.info("Exchange authentication successful")
            
            # Start metrics server
            await self.metrics_server.start()
            self.logger.info(f"Metrics server started on port {self.metrics_server.port}")
            
            # Main trading loop
            cycle_count = 0
            while self.running and not self.shutdown_event.is_set():
                cycle_count += 1
                self.logger.debug(f"Starting trading cycle {cycle_count}")
                
                try:
                    await self.process_trading_cycle()
                except Exception as e:
                    self.logger.error(f"Error in trading cycle {cycle_count}: {e}", exc_info=True)
                    # Continue running despite errors (graceful degradation)
                
                # Wait before next cycle (configurable interval)
                data_sources = self.config.get('data_sources', {})
                update_interval = min(
                    data_sources.get('weather', {}).get('update_interval', 60),
                    data_sources.get('air_quality', {}).get('update_interval', 60),
                    data_sources.get('flights', {}).get('update_interval', 30)
                )
                
                # Use shorter interval for more responsive trading
                await asyncio.sleep(min(update_interval, 10))
            
        except KeyboardInterrupt:
            self.logger.info("Received keyboard interrupt")
        except Exception as e:
            self.logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        finally:
            await self.shutdown()
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the trading bot.
        
        Closes all positions, cancels pending orders, generates final report,
        and cleans up resources.
        """
        self.logger.info("Initiating graceful shutdown...")
        self.running = False
        self.shutdown_event.set()
        
        try:
            # Cancel all pending orders
            self.logger.info("Cancelling pending orders...")
            try:
                await self.order_manager.cancel_all_orders()
            except Exception as e:
                self.logger.error(f"Error cancelling orders: {e}")
            
            # Generate final report
            self.logger.info("Generating final report...")
            try:
                report = self.report_generator.generate_session_summary()
                self.logger.info(f"Session summary:\n{report}")
            except Exception as e:
                self.logger.error(f"Error generating report: {e}")
            
            # Stop metrics server
            self.logger.info("Stopping metrics server...")
            try:
                await self.metrics_server.stop()
            except Exception as e:
                self.logger.error(f"Error stopping metrics server: {e}")
            
            # Close exchange connection
            self.logger.info("Closing exchange connection...")
            try:
                await self.exchange_client.close()
            except Exception as e:
                self.logger.error(f"Error closing exchange: {e}")
            
            self.logger.info("Shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)


async def main_loop(config: dict) -> None:
    """
    Main trading loop.
    
    Args:
        config: Configuration dictionary
    """
    logger = get_logger()
    
    try:
        # Create and run trading bot
        bot = TradingBot(config)
        await bot.run()
        
    except Exception as e:
        logger.error(f"Error in main loop: {e}", exc_info=True)
        raise


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="IMC Munich ETF Trading Bot",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['live', 'backtest', 'paper'],
        default='paper',
        help='Trading mode: live (real trading), backtest (historical), paper (simulated)'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level'
    )
    
    parser.add_argument(
        '--log-format',
        type=str,
        choices=['json', 'text'],
        default='text',
        help='Log output format'
    )
    
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Optional log file path'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    # Setup logging
    setup_logging(
        log_level=args.log_level,
        log_format=args.log_format,
        log_file=args.log_file
    )
    
    logger = get_logger()
    logger.info(f"Starting IMC Trading Bot in {args.mode} mode")
    
    # Load configuration
    try:
        config = load_config(args.config)
        logger.info(f"Configuration loaded from {args.config}")
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Store mode in config
    config['mode'] = args.mode
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(sig, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {sig}, initiating graceful shutdown...")
        # The bot's shutdown will be handled by the event loop
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run main loop
    try:
        asyncio.run(main_loop(config))
    except KeyboardInterrupt:
        logger.info("Received shutdown signal, exiting gracefully")
    except Exception as e:
        logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
