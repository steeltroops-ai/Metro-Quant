"""
Structured logging for trading bot operations.

Provides JSON-formatted logging for trades, regime changes, and errors.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger


class TradingLogger:
    """
    Structured logger for trading bot operations.
    
    Logs all trades, regime changes, and errors in JSON format for easy parsing
    and analysis. Provides both file and console output.
    """
    
    def __init__(self, log_dir: str = "logs", log_level: str = "INFO"):
        """
        Initialize trading logger.
        
        Args:
            log_dir: Directory for log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Remove default logger
        logger.remove()
        
        # Add console handler with color
        logger.add(
            lambda msg: print(msg, end=""),
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
            level=log_level,
            colorize=True
        )
        
        # Add file handler for all logs
        logger.add(
            self.log_dir / "trading_bot_{time:YYYY-MM-DD}.log",
            rotation="00:00",
            retention="30 days",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}"
        )
        
        # Add JSON file handler for structured logs
        self.json_log_path = self.log_dir / "trades_{time:YYYY-MM-DD}.json"
        logger.add(
            self.json_log_path,
            rotation="00:00",
            retention="30 days",
            level="INFO",
            format="{message}",
            serialize=True
        )
        
        self.logger = logger
    
    def log_trade(
        self,
        symbol: str,
        size: float,
        price: float,
        signal: float,
        regime: str,
        reasoning: str,
        order_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a trade execution with full context.
        
        Args:
            symbol: Trading symbol
            size: Position size (positive for long, negative for short)
            price: Execution price
            signal: Signal strength that triggered the trade
            regime: Current market regime
            reasoning: Human-readable explanation of trade decision
            order_id: Exchange order ID if available
            metadata: Additional context (confidence, features, etc.)
        
        Performance: ~1ms
        """
        trade_log = {
            "event": "trade",
            "timestamp": datetime.utcnow().isoformat(),
            "symbol": symbol,
            "size": size,
            "price": price,
            "signal": signal,
            "regime": regime,
            "reasoning": reasoning,
            "order_id": order_id,
            "metadata": metadata or {}
        }
        
        # Escape curly braces in reasoning to avoid format string issues
        safe_reasoning = reasoning.replace("{", "{{").replace("}", "}}")
        
        self.logger.info(
            f"TRADE: {symbol} size={size:.2f} @ {price:.4f} | "
            f"signal={signal:.3f} regime={regime} | {safe_reasoning}",
            extra={"trade_data": trade_log}
        )
    
    def log_regime_change(
        self,
        old_regime: str,
        new_regime: str,
        new_parameters: Dict[str, Any],
        confidence: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a market regime transition.
        
        Args:
            old_regime: Previous regime classification
            new_regime: New regime classification
            new_parameters: Updated strategy parameters
            confidence: Confidence in new regime classification
            metadata: Additional context (volatility, trend metrics, etc.)
        
        Performance: ~1ms
        """
        regime_log = {
            "event": "regime_change",
            "timestamp": datetime.utcnow().isoformat(),
            "old_regime": old_regime,
            "new_regime": new_regime,
            "new_parameters": new_parameters,
            "confidence": confidence,
            "metadata": metadata or {}
        }
        
        # Convert parameters to string and escape curly braces
        params_str = str(new_parameters).replace("{", "{{").replace("}", "}}")
        
        self.logger.info(
            f"REGIME CHANGE: {old_regime} → {new_regime} "
            f"(confidence={confidence:.2f}) | params={params_str}",
            extra={"regime_data": regime_log}
        )
    
    def log_error(
        self,
        error_type: str,
        message: str,
        exception: Optional[Exception] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log an error with full context and stack trace.
        
        Args:
            error_type: Category of error (data_fetch, order_submission, etc.)
            message: Human-readable error description
            exception: Exception object if available
            context: Additional context (state, parameters, etc.)
        
        Performance: ~1ms
        """
        error_log = {
            "event": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error_type": error_type,
            "message": message,
            "exception": str(exception) if exception else None,
            "context": context or {}
        }
        
        # Escape braces in message to prevent format string issues
        safe_message = message.replace('{', '{{').replace('}', '}}')
        
        if exception:
            self.logger.error(
                f"ERROR [{error_type}]: {safe_message}",
                exc_info=exception,
                extra={"error_data": error_log}
            )
        else:
            self.logger.error(
                f"ERROR [{error_type}]: {safe_message}",
                extra={"error_data": error_log}
            )
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log informational message."""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(message, **kwargs)
