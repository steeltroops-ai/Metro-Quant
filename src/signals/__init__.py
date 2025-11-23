"""Signal processing layer for trading bot.

This module contains feature engineering, signal generation, and signal combination.
"""

from src.signals.features import FeatureEngineer
from src.signals.generator import SignalGenerator
from src.signals.combiner import SignalCombiner

__all__ = ['FeatureEngineer', 'SignalGenerator', 'SignalCombiner']
