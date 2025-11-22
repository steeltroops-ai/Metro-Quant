"""Configuration loader with environment variable substitution."""

import os
import re
from pathlib import Path
from typing import Any, Dict

import yaml

from src.utils.constants import get_active_location


def load_config(config_path: str = "config.yaml", override_location: bool = True) -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment variable substitution.
    
    Environment variables are specified as ${VAR_NAME} in the YAML file.
    
    Args:
        config_path: Path to configuration file
        override_location: If True, override location from constants.py (default: True)
        
    Returns:
        Configuration dictionary with environment variables expanded
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If required environment variable is not set
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    # Read raw YAML content
    with open(config_file, 'r') as f:
        content = f.read()
    
    # Substitute environment variables
    content = _substitute_env_vars(content)
    
    # Parse YAML
    config = yaml.safe_load(content)
    
    # Override location from constants.py if requested
    if override_location:
        config['location'] = get_active_location()
    
    return config


def _substitute_env_vars(content: str) -> str:
    """
    Substitute environment variables in format ${VAR_NAME}.
    
    Args:
        content: String content with environment variable placeholders
        
    Returns:
        Content with environment variables expanded
        
    Raises:
        ValueError: If required environment variable is not set
    """
    pattern = re.compile(r'\$\{([^}]+)\}')
    
    def replace_var(match):
        var_name = match.group(1)
        value = os.environ.get(var_name)
        
        if value is None:
            # For optional variables, return empty string
            # For required variables, this will be caught during validation
            return ""
        
        return value
    
    return pattern.sub(replace_var, content)


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """
    Get nested configuration value using dot notation.
    
    Args:
        config: Configuration dictionary
        key_path: Dot-separated path to value (e.g., "strategy.signal_threshold")
        default: Default value if key not found
        
    Returns:
        Configuration value or default
        
    Example:
        >>> config = {"strategy": {"signal_threshold": 0.3}}
        >>> get_config_value(config, "strategy.signal_threshold")
        0.3
    """
    keys = key_path.split('.')
    value = config
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return default
    
    return value


def get_location_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get location configuration with computed values.
    
    Args:
        config: Configuration dictionary
        
    Returns:
        Location configuration with computed bounding box for flights
        
    Example:
        >>> location = get_location_config(config)
        >>> print(location['city'])  # 'Munich'
        >>> print(location['bbox'])  # [10.8351, 47.6351, 12.0351, 48.6351]
    """
    location = config.get('location', {})
    
    # Compute bounding box for flight data
    lat = location.get('coordinates', {}).get('lat', 0)
    lon = location.get('coordinates', {}).get('lon', 0)
    bbox_offset = config.get('data_sources', {}).get('flights', {}).get('bbox_offset', 0.5)
    
    location['bbox'] = [
        lon - bbox_offset,  # lon_min
        lat - bbox_offset,  # lat_min
        lon + bbox_offset,  # lon_max
        lat + bbox_offset,  # lat_max
    ]
    
    # Create location string for API calls
    location['location_string'] = f"{location.get('city', 'Unknown')},{location.get('country', 'XX')}"
    
    return location
