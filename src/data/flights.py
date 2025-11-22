"""Flight data client for OpenSky Network API.

This module fetches flight data from OpenSky Network API.
"""

from typing import Any, Dict, List, Optional

from loguru import logger

from src.data.base import DataClient
from src.utils.types import FlightData


class FlightClient(DataClient):
    """
    Client for fetching flight data from OpenSky Network API.
    
    API Documentation: https://openskynetwork.github.io/opensky-api/
    """
    
    BASE_URL = "https://opensky-network.org/api/states/all"
    
    def __init__(
        self,
        bbox: List[float],
        airport_code: str = "MUC",
        api_key: Optional[str] = None,
        timeout: int = 10
    ):
        """
        Initialize flight client.
        
        Args:
            bbox: Bounding box [lon_min, lat_min, lon_max, lat_max]
            airport_code: Airport ICAO code (default: MUC for Munich)
            api_key: Optional OpenSky API key for higher rate limits
            timeout: Request timeout in seconds
        """
        super().__init__(api_key=api_key, timeout=timeout)
        self.bbox = bbox
        self.airport_code = airport_code
        logger.info(f"FlightClient initialized for bbox: {bbox}, airport: {airport_code}")
    
    async def fetch(self) -> Dict[str, Any]:
        """
        Fetch flight data from OpenSky Network API.
        
        Returns:
            Dictionary containing flight data with timestamp
            
        Raises:
            aiohttp.ClientError: If API request fails
            ValueError: If data validation fails
        """
        params = {
            'lamin': self.bbox[1],  # lat_min
            'lomin': self.bbox[0],  # lon_min
            'lamax': self.bbox[3],  # lat_max
            'lomax': self.bbox[2],  # lon_max
        }
        
        # Add authentication if API key provided
        if self.api_key:
            params['auth'] = self.api_key
        
        try:
            logger.debug(f"Fetching flight data for bbox: {self.bbox}")
            raw_data = await self._get(self.BASE_URL, params=params)
            
            # Validate raw data
            if not self.validate(raw_data):
                raise ValueError("Flight data validation failed")
            
            # Transform to our format
            data = self._transform(raw_data)
            
            # Add timestamp
            data = self._add_timestamp(data)
            
            logger.info(f"Flight data fetched successfully: {data.get('active_flights', 0)} active flights")
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch flight data: {e}")
            raise
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate flight data format.
        
        Args:
            data: Raw API response data
            
        Returns:
            True if data is valid, False otherwise
        """
        try:
            # Check states field exists
            if 'states' not in data:
                logger.warning("Flight data missing 'states' field")
                return False
            
            # states can be None if no flights in area
            if data['states'] is None:
                logger.debug("No flights in specified area")
                return True
            
            # Check if states is a list
            if not isinstance(data['states'], list):
                logger.warning("Flight data 'states' is not a list")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Flight data validation error: {e}")
            return False
    
    def _transform(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw API response to our data format.
        
        Args:
            raw_data: Raw API response
            
        Returns:
            Transformed data dictionary
        """
        states = raw_data.get('states', [])
        
        # Handle None case (no flights)
        if states is None:
            states = []
        
        # Count active flights
        active_flights = len(states)
        
        # Analyze flight data
        departures = 0
        arrivals = 0
        delays = []
        
        for state in states:
            # OpenSky state vector format:
            # [0] icao24, [1] callsign, [2] origin_country, [3] time_position,
            # [4] last_contact, [5] longitude, [6] latitude, [7] baro_altitude,
            # [8] on_ground, [9] velocity, [10] true_track, [11] vertical_rate,
            # [12] sensors, [13] geo_altitude, [14] squawk, [15] spi, [16] position_source
            
            if len(state) < 9:
                continue
            
            # Check if on ground (index 8)
            on_ground = state[8] if state[8] is not None else False
            
            # Estimate departures/arrivals based on altitude and velocity
            altitude = state[7] if state[7] is not None else 0
            velocity = state[9] if state[9] is not None else 0
            
            # Simple heuristic: low altitude + high velocity = departure/arrival
            if altitude < 1000 and velocity > 50:
                if on_ground:
                    departures += 1
                else:
                    arrivals += 1
        
        # Calculate average delay (placeholder - OpenSky doesn't provide delay data)
        # In production, would need additional API or data source
        avg_delay = 0.0
        
        return {
            'active_flights': active_flights,
            'departures': departures,
            'arrivals': arrivals,
            'avg_delay': avg_delay,
        }
    
    def parse_to_model(self, data: Dict[str, Any]) -> FlightData:
        """
        Parse data dictionary to FlightData model.
        
        Args:
            data: Data dictionary (without timestamp)
            
        Returns:
            FlightData model instance
        """
        # Remove timestamp if present
        data_copy = {k: v for k, v in data.items() if k != 'timestamp'}
        return FlightData(**data_copy)
