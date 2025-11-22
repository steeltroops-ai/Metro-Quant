"""Unit tests for configuration loader."""

import os
import tempfile
from pathlib import Path

import pytest

from src.utils.config import load_config, get_config_value, _substitute_env_vars


def test_substitute_env_vars():
    """Test environment variable substitution."""
    os.environ['TEST_VAR'] = 'test_value'
    
    content = "key: ${TEST_VAR}"
    result = _substitute_env_vars(content)
    
    assert result == "key: test_value"
    
    # Cleanup
    del os.environ['TEST_VAR']


def test_substitute_env_vars_missing():
    """Test handling of missing environment variables."""
    content = "key: ${MISSING_VAR}"
    result = _substitute_env_vars(content)
    
    # Should return empty string for missing vars
    assert result == "key: "


def test_get_config_value():
    """Test nested configuration value retrieval."""
    config = {
        "strategy": {
            "signal_threshold": 0.3,
            "nested": {
                "value": 42
            }
        }
    }
    
    # Test simple nested access
    assert get_config_value(config, "strategy.signal_threshold") == 0.3
    
    # Test deeper nesting
    assert get_config_value(config, "strategy.nested.value") == 42
    
    # Test missing key with default
    assert get_config_value(config, "missing.key", default=100) == 100
    
    # Test missing key without default
    assert get_config_value(config, "missing.key") is None


def test_load_config():
    """Test loading configuration from YAML file."""
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("""
strategy:
  signal_threshold: 0.3
  confidence_threshold: 0.5

risk:
  max_position_size: 0.20
""")
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        
        assert config['strategy']['signal_threshold'] == 0.3
        assert config['strategy']['confidence_threshold'] == 0.5
        assert config['risk']['max_position_size'] == 0.20
    finally:
        # Cleanup
        Path(temp_path).unlink()


def test_load_config_missing_file():
    """Test error handling for missing config file."""
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_config.yaml")
