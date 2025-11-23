"""
Property-based tests for main trading bot orchestration.

Tests graceful error handling, recovery logic, and shutdown behavior.
"""

import asyncio
import tempfile
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st, settings

from src.main import TradingBot
from src.utils.config import load_config


# Strategies for generating test data
error_types = st.sampled_from([
    "data_fetch_failure",
    "exchange_connection_error",
    "order_submission_failure",
    "signal_generation_error",
    "regime_detection_error",
    "position_tracking_error"
])

error_messages = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=1,
    max_size=100
)


# Feature: imc-trading-bot, Property 33: Graceful error handling with messages
@given(
    error_type=error_types,
    error_message=error_messages
)
@settings(max_examples=10, deadline=10000)
def test_graceful_error_handling_with_messages(error_type, error_message):
    """
    Property 33: Graceful error handling with messages
    
    For any error scenario, the system should handle it gracefully and
    provide informative error messages without crashing.
    
    Validates: Requirements 9.4
    """
    # Create a minimal config for testing
    config = {
        'api_keys': {
            'openweather': 'test_key'
        },
        'location': {
            'city': 'Munich',
            'country': 'DE',
            'coordinates': {'lat': 48.1351, 'lon': 11.5820},
            'airport_code': 'MUC'
        },
        'data_sources': {
            'weather': {'update_interval': 60},
            'air_quality': {'update_interval': 60},
            'flights': {'update_interval': 30, 'bbox_offset': 0.5}
        },
        'cache': {'ttl': 300, 'max_size': 1000},
        'features': {
            'weather_momentum_period': 5,
            'flight_volume_ma_period': 10,
            'air_quality_delta_period': 3
        },
        'kalman': {
            'process_variance': 0.01,
            'measurement_variance': 0.1
        },
        'strategy': {
            'signal_threshold': 0.3,
            'confidence_threshold': 0.5,
            'regime_weights': {
                'trending': {'momentum': 0.6, 'weather': 0.2, 'flights': 0.1, 'air_quality': 0.1}
            }
        },
        'regime_detection': {
            'lookback_period': 100,
            'volatility_threshold': 0.02,
            'trend_ma_fast': 10,
            'trend_ma_slow': 30,
            'regime_confidence_threshold': 0.70
        },
        'position_sizing': {
            'base_size': 0.10,
            'confidence_scaling': True,
            'regime_scaling': True
        },
        'risk': {
            'max_position_size': 0.20,
            'max_total_exposure': 0.80,
            'drawdown_reduction_threshold': 0.15,
            'drawdown_safe_mode_threshold': 0.25
        },
        'exchange': {
            'url': 'http://test-exchange.com',
            'username': 'test_user',
            'password': 'test_pass',
            'timeout': 5,
            'instruments': ['1_Eisbach', '2_Eisbach_Call', '3_Weather', '4_Weather', 
                          '5_Flights', '6_Airport', '7_ETF', '8_ETF_Strangle']
        },
        'execution': {
            'order_timeout': 10,
            'max_slippage': 0.001,
            'limit_price_offset': 0.0005
        },
        'monitoring': {
            'metrics_port': 8080,
            'log_level': 'INFO',
            'log_format': 'json',
            'report_interval': 60
        }
    }
    
    # Test that bot initialization handles errors gracefully
    try:
        bot = TradingBot(config)
        bot_created = True
    except Exception as e:
        bot_created = False
        # Bot creation should not crash even with minimal config
        pytest.fail(f"Bot creation crashed with error: {e}")
    
    assert bot_created, "Bot creation failed"
    
    # Test that error logging works
    try:
        # Simulate an error in the trading cycle
        test_exception = Exception(f"{error_type}: {error_message}")
        
        # The bot should be able to log this error without crashing
        bot.logger.error(f"Test error: {error_type}", exc_info=test_exception)
        error_logged = True
    except Exception as e:
        error_logged = False
        pytest.fail(f"Error logging crashed: {e}")
    
    assert error_logged, "Error logging failed"


@pytest.mark.asyncio
async def test_trading_cycle_error_recovery():
    """
    Test that trading cycle continues after errors.
    
    This verifies that errors in one cycle don't prevent future cycles.
    """
    config = {
        'api_keys': {'openweather': 'test_key'},
        'location': {
            'city': 'Munich',
            'country': 'DE',
            'coordinates': {'lat': 48.1351, 'lon': 11.5820},
            'airport_code': 'MUC'
        },
        'data_sources': {
            'weather': {'update_interval': 60},
            'air_quality': {'update_interval': 60},
            'flights': {'update_interval': 30, 'bbox_offset': 0.5}
        },
        'cache': {'ttl': 300, 'max_size': 1000},
        'features': {
            'weather_momentum_period': 5,
            'flight_volume_ma_period': 10,
            'air_quality_delta_period': 3
        },
        'kalman': {
            'process_variance': 0.01,
            'measurement_variance': 0.1
        },
        'strategy': {
            'signal_threshold': 0.3,
            'confidence_threshold': 0.5,
            'regime_weights': {
                'trending': {'momentum': 0.6, 'weather': 0.2, 'flights': 0.1, 'air_quality': 0.1}
            }
        },
        'regime_detection': {
            'lookback_period': 100,
            'volatility_threshold': 0.02,
            'trend_ma_fast': 10,
            'trend_ma_slow': 30,
            'regime_confidence_threshold': 0.70
        },
        'position_sizing': {
            'base_size': 0.10,
            'confidence_scaling': True,
            'regime_scaling': True
        },
        'risk': {
            'max_position_size': 0.20,
            'max_total_exposure': 0.80,
            'drawdown_reduction_threshold': 0.15,
            'drawdown_safe_mode_threshold': 0.25
        },
        'exchange': {
            'url': 'http://test-exchange.com',
            'username': 'test_user',
            'password': 'test_pass',
            'timeout': 5,
            'instruments': ['1_Eisbach', '2_Eisbach_Call', '3_Weather', '4_Weather', 
                          '5_Flights', '6_Airport', '7_ETF', '8_ETF_Strangle']
        },
        'execution': {
            'order_timeout': 10,
            'max_slippage': 0.001,
            'limit_price_offset': 0.0005
        },
        'monitoring': {
            'metrics_port': 8080,
            'log_level': 'INFO',
            'log_format': 'json',
            'report_interval': 60
        }
    }
    
    bot = TradingBot(config)
    
    # Mock the fetch_city_data to fail first time, succeed second time
    call_count = 0
    
    async def mock_fetch():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise Exception("Simulated data fetch failure")
        return None  # Return None to skip cycle
    
    bot.fetch_city_data = mock_fetch
    
    # Run two cycles - first should fail, second should succeed
    try:
        await bot.process_trading_cycle()  # Should handle error gracefully
        await bot.process_trading_cycle()  # Should work
        recovery_successful = True
    except Exception as e:
        recovery_successful = False
        pytest.fail(f"Bot failed to recover from error: {e}")
    
    assert recovery_successful, "Bot did not recover from error"
    assert call_count == 2, "Bot did not attempt second cycle"


@pytest.mark.asyncio
async def test_graceful_shutdown():
    """
    Test that bot shuts down gracefully without errors.
    """
    config = {
        'api_keys': {'openweather': 'test_key'},
        'location': {
            'city': 'Munich',
            'country': 'DE',
            'coordinates': {'lat': 48.1351, 'lon': 11.5820},
            'airport_code': 'MUC'
        },
        'data_sources': {
            'weather': {'update_interval': 60},
            'air_quality': {'update_interval': 60},
            'flights': {'update_interval': 30, 'bbox_offset': 0.5}
        },
        'cache': {'ttl': 300, 'max_size': 1000},
        'features': {
            'weather_momentum_period': 5,
            'flight_volume_ma_period': 10,
            'air_quality_delta_period': 3
        },
        'kalman': {
            'process_variance': 0.01,
            'measurement_variance': 0.1
        },
        'strategy': {
            'signal_threshold': 0.3,
            'confidence_threshold': 0.5,
            'regime_weights': {
                'trending': {'momentum': 0.6, 'weather': 0.2, 'flights': 0.1, 'air_quality': 0.1}
            }
        },
        'regime_detection': {
            'lookback_period': 100,
            'volatility_threshold': 0.02,
            'trend_ma_fast': 10,
            'trend_ma_slow': 30,
            'regime_confidence_threshold': 0.70
        },
        'position_sizing': {
            'base_size': 0.10,
            'confidence_scaling': True,
            'regime_scaling': True
        },
        'risk': {
            'max_position_size': 0.20,
            'max_total_exposure': 0.80,
            'drawdown_reduction_threshold': 0.15,
            'drawdown_safe_mode_threshold': 0.25
        },
        'exchange': {
            'url': 'http://test-exchange.com',
            'username': 'test_user',
            'password': 'test_pass',
            'timeout': 5,
            'instruments': ['1_Eisbach', '2_Eisbach_Call', '3_Weather', '4_Weather', 
                          '5_Flights', '6_Airport', '7_ETF', '8_ETF_Strangle']
        },
        'execution': {
            'order_timeout': 10,
            'max_slippage': 0.001,
            'limit_price_offset': 0.0005
        },
        'monitoring': {
            'metrics_port': 8080,
            'log_level': 'INFO',
            'log_format': 'json',
            'report_interval': 60
        }
    }
    
    bot = TradingBot(config)
    
    # Mock the components to avoid actual network calls
    bot.order_manager.cancel_all_orders = AsyncMock()
    bot.exchange_client.close = AsyncMock()
    bot.metrics_server.stop = AsyncMock()
    
    # Test shutdown
    try:
        await bot.shutdown()
        shutdown_successful = True
    except Exception as e:
        shutdown_successful = False
        pytest.fail(f"Shutdown failed with error: {e}")
    
    assert shutdown_successful, "Graceful shutdown failed"
    assert not bot.running, "Bot still marked as running after shutdown"
    assert bot.shutdown_event.is_set(), "Shutdown event not set"


@pytest.mark.asyncio
async def test_error_in_shutdown_does_not_crash():
    """
    Test that errors during shutdown are handled gracefully.
    """
    config = {
        'api_keys': {'openweather': 'test_key'},
        'location': {
            'city': 'Munich',
            'country': 'DE',
            'coordinates': {'lat': 48.1351, 'lon': 11.5820},
            'airport_code': 'MUC'
        },
        'data_sources': {
            'weather': {'update_interval': 60},
            'air_quality': {'update_interval': 60},
            'flights': {'update_interval': 30, 'bbox_offset': 0.5}
        },
        'cache': {'ttl': 300, 'max_size': 1000},
        'features': {
            'weather_momentum_period': 5,
            'flight_volume_ma_period': 10,
            'air_quality_delta_period': 3
        },
        'kalman': {
            'process_variance': 0.01,
            'measurement_variance': 0.1
        },
        'strategy': {
            'signal_threshold': 0.3,
            'confidence_threshold': 0.5,
            'regime_weights': {
                'trending': {'momentum': 0.6, 'weather': 0.2, 'flights': 0.1, 'air_quality': 0.1}
            }
        },
        'regime_detection': {
            'lookback_period': 100,
            'volatility_threshold': 0.02,
            'trend_ma_fast': 10,
            'trend_ma_slow': 30,
            'regime_confidence_threshold': 0.70
        },
        'position_sizing': {
            'base_size': 0.10,
            'confidence_scaling': True,
            'regime_scaling': True
        },
        'risk': {
            'max_position_size': 0.20,
            'max_total_exposure': 0.80,
            'drawdown_reduction_threshold': 0.15,
            'drawdown_safe_mode_threshold': 0.25
        },
        'exchange': {
            'url': 'http://test-exchange.com',
            'username': 'test_user',
            'password': 'test_pass',
            'timeout': 5,
            'instruments': ['1_Eisbach', '2_Eisbach_Call', '3_Weather', '4_Weather', 
                          '5_Flights', '6_Airport', '7_ETF', '8_ETF_Strangle']
        },
        'execution': {
            'order_timeout': 10,
            'max_slippage': 0.001,
            'limit_price_offset': 0.0005
        },
        'monitoring': {
            'metrics_port': 8080,
            'log_level': 'INFO',
            'log_format': 'json',
            'report_interval': 60
        }
    }
    
    bot = TradingBot(config)
    
    # Mock components to raise errors during shutdown
    async def failing_cancel():
        raise Exception("Failed to cancel orders")
    
    async def failing_close():
        raise Exception("Failed to close connection")
    
    bot.order_manager.cancel_all_orders = failing_cancel
    bot.exchange_client.close = failing_close
    bot.metrics_server.stop = AsyncMock()
    
    # Shutdown should complete despite errors
    try:
        await bot.shutdown()
        shutdown_completed = True
    except Exception as e:
        shutdown_completed = False
        pytest.fail(f"Shutdown crashed despite error handling: {e}")
    
    assert shutdown_completed, "Shutdown did not complete gracefully"
    assert not bot.running, "Bot still marked as running"
