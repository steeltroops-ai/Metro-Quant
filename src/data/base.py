"""Base data client interface for async data fetching.

This module defines the abstract base class for all data clients.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime

import aiohttp
from loguru import logger


class DataClient(ABC):
    """Abstract base class for data clients.
    
    All data clients must implement fetch() and validate() methods.
    Provides common functionality for HTTP requests and error handling.
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        Initialize data client.
        
        Args:
            api_key: Optional API key for authentication
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._session = aiohttp.ClientSession(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._session:
            await self._session.close()
    
    @abstractmethod
    async def fetch(self) -> Dict[str, Any]:
        """
        Fetch data from external source.
        
        Returns:
            Dictionary containing fetched data
            
        Raises:
            aiohttp.ClientError: If request fails
            ValueError: If data validation fails
        """
        pass
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate data format and content.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    async def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Make async GET request.
        
        Args:
            url: Request URL
            params: Optional query parameters
            
        Returns:
            Response JSON as dictionary
            
        Raises:
            aiohttp.ClientError: If request fails
        """
        if not self._session:
            raise RuntimeError("Client must be used as async context manager")
        
        try:
            async with self._session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            logger.error(f"HTTP request failed: {url} - {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during request: {url} - {e}")
            raise
    
    def _add_timestamp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add timestamp to data dictionary.
        
        Args:
            data: Data dictionary
            
        Returns:
            Data dictionary with timestamp added
        """
        data['timestamp'] = datetime.now()
        return data
