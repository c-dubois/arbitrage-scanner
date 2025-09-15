"""API-based exchange rate provider for tokens like cbETH."""

from decimal import Decimal
from typing import Optional, Set
from aiohttp import ClientSession

from .base_rate_provider import BaseRateProvider
from ...models.token import Token

class APIRateProvider(BaseRateProvider):
    """Handles API-based exchange rate fetching for tokens like cbETH."""

    SUPPORTED_TOKENS = {'cbETH'}

    def __init__(self):
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    @property
    def supported_tokens(self) -> Set[str]:
        """Return a set of supported token symbols."""
        return self.SUPPORTED_TOKENS

    def supports_token(self, token: Token) -> bool:
        """Check if the provider supports the given token.
        
        Args:
            token: The token to check.
            
        Returns:
            True if supported, False otherwise.
        """
        return token.symbol in self.SUPPORTED_TOKENS
    
    async def get_exchange_rate(self, token: Token) -> Optional[Decimal]:
        """
        Fetch the exchange rate for a given token from API.
        
        Args:
            token: The token for which to fetch the exchange rate.
            
        Returns:
            The exchange rate as a Decimal, or None if unavailable.
        """
        if not self.supports_token(token):
            return None
        
        if token.symbol == 'cbETH':
            return await self._fetch_cbeth_rate(token)
        
        return None
    
    async def _fetch_cbeth_rate(self, token: Token) -> Optional[Decimal]:
        """Fetch cbETH exchange rate from Coinbase API.
        Args:
            token: cbETH token with API endpoint

        Returns:
            cbETH/ETH exchange rate as a Decimal, or None if unavailable.
        """
        if not token.exchange_rate_api:
            return None
        
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")

        try:
            async with self.session.get(token.exchange_rate_api) as response:
                if response.status == 200:
                    data = await response.json()
                    # Coinbase API returns rate in 'amount' field
                    rate = Decimal(str(data.get('amount', '1')))
                    return rate
                else:
                    print(f"Failed to fetch cbETH rate: API returned status {response.status}")
                    return None

        except Exception as e:
            print(f"Error fetching cbETH rate from API: {e}")
            return None