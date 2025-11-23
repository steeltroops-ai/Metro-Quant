"""Generate signal discovery notebook programmatically."""

import json

# Define notebook structure
notebook = {
    "cells": [],
    "metadata": {
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3"
        },
        "language_info": {
            "name": "python",
            "version": "3.11.0"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Cell 1: Title and Introduction
notebook["cells"].append({
    "cell_type": "markdown",
    "metadata": {},
    "source": [
        "# Munich ETF Signal Discovery\\n",
        "\\n",
        "This notebook explores correlations between Munich city data (weather, air quality, flights) and synthetic market data to discover novel trading signals.\\n",
        "\\n",
        "## Objectives\\n",
        "1. Fetch live Munich data from all sources\\n",
        "2. Generate synthetic market data for analysis\\n",
        "3. Compute correlation matrices\\n",
        "4. Identify 3-5 strong correlations for presentation\\n",
        "5. Visualize signal discovery process"
    ]
})

# Cell 2: Imports
notebook["cells"].append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Import required libraries\\n",
        "import asyncio\\n",
        "import sys\\n",
        "import os\\n",
        "from pathlib import Path\\n",
        "\\n",
        "# Add src to path\\n",
        "sys.path.insert(0, str(Path.cwd().parent / 'src'))\\n",
        "\\n",
        "import numpy as np\\n",
        "import pandas as pd\\n",
        "import matplotlib.pyplot as plt\\n",
        "import seaborn as sns\\n",
        "from datetime import datetime, timedelta\\n",
        "from typing import Dict, List, Any\\n",
        "import yaml\\n",
        "\\n",
        "# Configure plotting\\n",
        "plt.style.use('seaborn-v0_8-darkgrid')\\n",
        "sns.set_palette('husl')\\n",
        "%matplotlib inline\\n",
        "\\n",
        "print('Libraries imported successfully')"
    ]
})

# Cell 3: Load Configuration
notebook["cells"].append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Load configuration\\n",
        "config_path = Path.cwd().parent / 'config.yaml'\\n",
        "with open(config_path, 'r') as f:\\n",
        "    config = yaml.safe_load(f)\\n",
        "\\n",
        "# Extract location info\\n",
        "location = config['location']\\n",
        "print(f\\\"Location: {location['city']}, {location['country']}\\\")\\n",
        "print(f\\\"Coordinates: ({location['coordinates']['lat']}, {location['coordinates']['lon']})\\\")\\n",
        "print(f\\\"Airport: {location['airport_code']}\\\")"
    ]
})

# Cell 4: Data Fetching Functions
notebook["cells"].append({
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [
        "# Import data clients\\n",
        "from src.data.weather import WeatherClient\\n",
        "from src.data.air_quality import AirQualityClient\\n",
        "from src.data.flights import FlightClient\\n",
        "\\n",
        "async def fetch_munich_data():\\n",
        "    \\\"\\\"\\\"Fetch current Munich data from all sources.\\\"\\\"\\\"\\n",
        "    \\n",
        "    # Get API keys from environment\\n",
        "    api_key = os.getenv('OPENWEATHER_API_KEY', 'demo_key')\\n",
        "    \\n",
        "    # Initialize clients\\n",
        "    location_str = f\\\"{location['city']},{location['country']}\\\"\\n",
        "    lat = location['coordinates']['lat']\\n",
        "    lon = location['coordinates']['lon']\\n",
        "    \\n",
        "    # Calculate bounding box for flights\\n",
        "    bbox_offset = config['data_sources']['flights']['bbox_offset']\\n",
        "    bbox = [\\n",
        "        lon - bbox_offset,  # lon_min\\n",
        "        lat - bbox_offset,  # lat_min\\n",
        "        lon + bbox_offset,  # lon_max\\n",
        "        lat + bbox_offset   # lat_max\\n",
        "    ]\\n",
        "    \\n",
        "    # Fetch data concurrently\\n",
        "    async with WeatherClient(api_key, location_str) as weather_client, \\\\\\n",
        "               AirQualityClient(api_key, lat, lon) as aq_client, \\\\\\n",
        "               FlightClient(bbox, location['airport_code']) as flight_client:\\n",
        "        \\n",
        "        weather_data, aq_data, flight_data = await asyncio.gather(\\n",
        "            weather_client.fetch(),\\n",
        "            aq_client.fetch(),\\n",
        "            flight_client.fetch(),\\n",
        "            return_exceptions=True\\n",
        "        )\\n",
        "    \\n",
        "    return {\\n",
        "        'weather': weather_data if not isinstance(weather_data, Exception) else None,\\n",
        "        'air_quality': aq_data if not isinstance(aq_data, Exception) else None,\\n",
        "        'flights': flight_data if not isinstance(flight_data, Exception) else None\\n",
        "    }\\n",
        "\\n",
        "print('Data fetching functions defined')"
    ]
})

# Save notebook
with open('notebooks/signal_discovery.ipynb', 'w') as f:
    json.dump(notebook, f, indent=1)

print("Notebook structure created successfully!")
