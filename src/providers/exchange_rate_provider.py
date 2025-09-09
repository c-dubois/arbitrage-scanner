"""Provider for fetching exchange rates of liquid staking tokens."""

from decimal import Decimal
from typing import Optional, Dict
from aiohttp import ClientSession

from ..models.token import Token

class ExchangeRateProvider:
    """Provider for fetching LST exchange rates."""

    def __init__(self):
        self.session: Optional[ClientSession] = None
        self._rate_cache: Dict[str, Decimal] = {}
        # Right now _rate_cache is permanent for the session, might wanna implement timestamp-based cache

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    async def get_exchange_rate(self, token: Token) -> Optional[Decimal]:
        """
        Fetch the exchange rate for a liquid staking token (LST).

        Args:
            token: The liquid staking token

        Returns:
            The exchange rate (LST/ETH) as a Decimal, or None if unavailable
        """
        # Check cache first
        if token.symbol in self._rate_cache:
            return self._rate_cache[token.symbol]

        rate = await self._fetch_exchange_rate(token)

        if rate is not None:
            self._rate_cache[token.symbol] = rate # Cache the rate

        return rate

    async def _fetch_exchange_rate(self, token: Token) -> Optional[Decimal]:
        """Fetch exchange rate based on token type."""
        if not self.session:
            raise RuntimeError("Session not initialized")
        if not token.exchange_rate_api or not token.exchange_rate_field:
            return None

        try:
            async with self.session.get(token.exchange_rate_api) as response:
                if response.status == 200:
                    data = await response.json()
                    field = token.exchange_rate_field
                    if field in data:
                        rate = Decimal(str(data.get(field)))
                        return rate
                    return None
        except Exception as e:
            print(f"Error fetching rate for {token.symbol}: {e}")
            return None

    def clear_cache(self):
        """Clear the rate cache."""
        self._rate_cache.clear()