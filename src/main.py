"""
IMC Trading Bot - Main entry point.

This is the main entry point for the trading bot. It initializes all components,
starts the event loop, and coordinates trading operations.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.logger import setup_logging, get_logger


async def main_loop(config: dict) -> None:
    """
    Main trading loop.
    
    Args:
        config: Configuration dictionary
    """
    logger = get_logger()
    logger.info("Starting IMC Trading Bot main loop")
    
    # TODO: Initialize components in subsequent tasks
    # - Data clients
    # - Signal processors
    # - Strategy components
    # - Risk management
    # - Exchange client
    
    logger.info("Trading bot initialized successfully")
    
    # Placeholder for main event loop
    # Will be implemented in task 10
    logger.info("Main event loop not yet implemented")


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
