"""Market regime detection using volatility, trend, and mean-reversion metrics.

This module classifies market state to enable adaptive strategy.
"""

from typing import List, Tuple
import numpy as np
import pandas as pd
from loguru import logger
from datetime import datetime, timedelta


class RegimeDetector:
    """
    Detects market regime using multiple metrics.
    
    Classifies markets as:
    - trending: Strong directional movement
    - mean-reverting: Price oscillates around mean
    - high-volatility: Large price swings
    - low-volatility: Stable prices
    """
    
    def __init__(
        self,
        volatility_window: int = 20,
        trend_fast_window: int = 10,
        trend_slow_window: int = 30,
        autocorr_lag: int = 5,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize regime detector.
        
        Args:
            volatility_window: Window for volatility calculation
            trend_fast_window: Fast moving average window
            trend_slow_window: Slow moving average window
            autocorr_lag: Lag for autocorrelation calculation
            confidence_threshold: Minimum confidence for regime classification
        """
        self.volatility_window = volatility_window
        self.trend_fast_window = trend_fast_window
        self.trend_slow_window = trend_slow_window
        self.autocorr_lag = autocorr_lag
        self.confidence_threshold = confidence_threshold
        
        self.current_regime = 'uncertain'
        self.regime_confidence = 0.0
        self.last_detection_time = None
        
        logger.info(
            f"RegimeDetector initialized: vol_window={volatility_window}, "
            f"trend_windows=({trend_fast_window},{trend_slow_window})"
        )
    
    def detect(self, returns: List[float]) -> str:
        """
        Classify current market regime based on returns.
        
        Args:
            returns: List of historical returns (most recent last)
            
        Returns:
            Regime classification: 'trending', 'mean-reverting', 
                                  'high-volatility', 'low-volatility', or 'uncertain'
        """
        if len(returns) < self.trend_slow_window:
            logger.warning(
                f"Insufficient data for regime detection: {len(returns)} < {self.trend_slow_window}"
            )
            self.current_regime = 'uncertain'
            self.regime_confidence = 0.0
            self.last_detection_time = datetime.now()
            return self.current_regime
        
        # Convert to numpy array for calculations
        returns_array = np.array(returns)
        
        # Calculate regime metrics
        volatility = self._calculate_volatility(returns_array)
        trend_strength = self._calculate_trend_strength(returns_array)
        mean_reversion = self._calculate_mean_reversion(returns_array)
        
        # Classify regime based on metrics
        regime, confidence = self._classify_regime(
            volatility, trend_strength, mean_reversion
        )
        
        # Update state
        old_regime = self.current_regime
        self.current_regime = regime
        self.regime_confidence = confidence
        self.last_detection_time = datetime.now()
        
        if old_regime != regime:
            logger.info(
                f"Regime change detected: {old_regime} -> {regime} "
                f"(confidence={confidence:.3f})"
            )
        else:
            logger.debug(
                f"Regime unchanged: {regime} (confidence={confidence:.3f})"
            )
        
        return self.current_regime
    
    def _calculate_volatility(self, returns: np.ndarray) -> float:
        """
        Calculate rolling volatility (standard deviation of returns).
        
        Args:
            returns: Array of returns
            
        Returns:
            Volatility measure (annualized)
        """
        # Use recent window for volatility
        recent_returns = returns[-self.volatility_window:]
        
        # Calculate standard deviation
        volatility = np.std(recent_returns)
        
        # Annualize (assuming daily returns)
        annualized_vol = volatility * np.sqrt(252)
        
        return float(annualized_vol)
    
    def _calculate_trend_strength(self, returns: np.ndarray) -> float:
        """
        Calculate trend strength using moving average crossover.
        
        Positive = uptrend, Negative = downtrend, Near zero = no trend
        
        Args:
            returns: Array of returns
            
        Returns:
            Trend strength [-1.0, 1.0]
        """
        # Convert returns to prices (cumulative)
        prices = np.cumprod(1 + returns)
        
        # Calculate moving averages
        fast_ma = np.mean(prices[-self.trend_fast_window:])
        slow_ma = np.mean(prices[-self.trend_slow_window:])
        
        # Calculate crossover strength
        # Normalize by slow MA to get percentage difference
        if slow_ma > 0:
            trend_strength = (fast_ma - slow_ma) / slow_ma
        else:
            trend_strength = 0.0
        
        # Clip to [-1, 1] range
        trend_strength = np.clip(trend_strength, -1.0, 1.0)
        
        return float(trend_strength)
    
    def _calculate_mean_reversion(self, returns: np.ndarray) -> float:
        """
        Calculate mean reversion tendency using autocorrelation.
        
        Negative autocorrelation = mean-reverting
        Positive autocorrelation = trending
        
        Args:
            returns: Array of returns
            
        Returns:
            Mean reversion score [-1.0, 1.0]
        """
        # Use recent window
        recent_returns = returns[-self.volatility_window:]
        
        if len(recent_returns) < self.autocorr_lag + 1:
            return 0.0
        
        # Calculate autocorrelation at specified lag
        # Negative autocorr = mean reversion, positive = momentum
        autocorr = self._autocorrelation(recent_returns, self.autocorr_lag)
        
        # Invert sign: negative autocorr -> positive mean reversion score
        mean_reversion_score = -autocorr
        
        # Clip to [-1, 1] range
        mean_reversion_score = np.clip(mean_reversion_score, -1.0, 1.0)
        
        return float(mean_reversion_score)
    
    def _autocorrelation(self, data: np.ndarray, lag: int) -> float:
        """
        Calculate autocorrelation at specified lag.
        
        Args:
            data: Time series data
            lag: Lag for autocorrelation
            
        Returns:
            Autocorrelation coefficient [-1.0, 1.0]
        """
        if len(data) < lag + 1:
            return 0.0
        
        # Demean the data
        mean = np.mean(data)
        demeaned = data - mean
        
        # Calculate autocorrelation
        c0 = np.dot(demeaned, demeaned) / len(demeaned)
        
        if c0 == 0:
            return 0.0
        
        c_lag = np.dot(demeaned[:-lag], demeaned[lag:]) / len(demeaned)
        
        autocorr = c_lag / c0
        
        return float(autocorr)
    
    def _classify_regime(
        self,
        volatility: float,
        trend_strength: float,
        mean_reversion: float
    ) -> Tuple[str, float]:
        """
        Classify regime based on calculated metrics.
        
        Args:
            volatility: Volatility measure
            trend_strength: Trend strength [-1, 1]
            mean_reversion: Mean reversion score [-1, 1]
            
        Returns:
            Tuple of (regime_name, confidence)
        """
        # Define thresholds
        HIGH_VOL_THRESHOLD = 0.3  # 30% annualized
        LOW_VOL_THRESHOLD = 0.1   # 10% annualized
        STRONG_TREND_THRESHOLD = 0.3
        STRONG_MEAN_REV_THRESHOLD = 0.3
        
        # Score each regime
        regime_scores = {}
        
        # High volatility regime
        if volatility > HIGH_VOL_THRESHOLD:
            vol_score = min((volatility - HIGH_VOL_THRESHOLD) / HIGH_VOL_THRESHOLD, 1.0)
            regime_scores['high-volatility'] = vol_score
        
        # Low volatility regime
        if volatility < LOW_VOL_THRESHOLD:
            vol_score = 1.0 - (volatility / LOW_VOL_THRESHOLD)
            regime_scores['low-volatility'] = vol_score
        
        # Trending regime
        if abs(trend_strength) > STRONG_TREND_THRESHOLD:
            trend_score = abs(trend_strength)
            regime_scores['trending'] = trend_score
        
        # Mean-reverting regime
        if mean_reversion > STRONG_MEAN_REV_THRESHOLD:
            mr_score = mean_reversion
            regime_scores['mean-reverting'] = mr_score
        
        # Select regime with highest score
        if regime_scores:
            best_regime = max(regime_scores.items(), key=lambda x: x[1])
            regime_name, confidence = best_regime
            
            # Check if confidence meets threshold
            if confidence >= self.confidence_threshold:
                return regime_name, confidence
        
        # If no clear regime or low confidence, return uncertain
        return 'uncertain', max(regime_scores.values()) if regime_scores else 0.0
    
    def get_confidence(self) -> float:
        """
        Get confidence in current regime classification.
        
        Returns:
            Confidence score [0.0, 1.0]
        """
        return self.regime_confidence
    
    def get_current_regime(self) -> str:
        """
        Get current regime without recalculating.
        
        Returns:
            Current regime name
        """
        return self.current_regime
    
    def time_since_last_detection(self) -> float:
        """
        Get time elapsed since last regime detection.
        
        Returns:
            Seconds since last detection, or infinity if never detected
        """
        if self.last_detection_time is None:
            return float('inf')
        
        elapsed = datetime.now() - self.last_detection_time
        return elapsed.total_seconds()
