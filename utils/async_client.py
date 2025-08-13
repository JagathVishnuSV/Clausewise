import aiohttp
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AsyncHTTPClient:
    """Async HTTP client with connection pooling and retry logic."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_retries = max_retries
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=100,  # Connection pool size
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=self.timeout,
            headers={"User-Agent": "LegalDocAnalyzer/1.0"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
    
    async def post(self, url: str, **kwargs):
        """POST request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                async with self._session.post(url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    async def get(self, url: str, **kwargs):
        """GET request with retry logic."""
        for attempt in range(self.max_retries):
            try:
                async with self._session.get(url, **kwargs) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)

# Global client instance
http_client = AsyncHTTPClient()
