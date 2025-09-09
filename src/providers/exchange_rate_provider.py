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

        rate = None

        if token.symbol == "cbETH":
            rate = await self._get_cbeth_rate(token)
        elif token.symbol in ["stETH", "wstETH"]:
            rate = await self._get_lido_rate(token)
        elif token.symbol in ["frxETH", "sfrxETH"]:
            rate = await self._get_frax_rate(token)
        elif token.symbol == "METH":
            rate = await self._get_meth_rate(token)

        if rate:
            self._rate_cache[token.symbol] = rate

        return rate

    async def _get_cbeth_rate(self, token: Token) -> Optional[Decimal]:
        """Fetch cbETH exchange rate from Coinbase API."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        if not token.exchange_rate_api:
            return None

        try:
            async with self.session.get(token.exchange_rate_api) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = Decimal(str(data.get('amount', 1)))
                    return rate
        except Exception:
            pass

        return None

    async def _get_lido_rate(self, token: Token) -> Optional[Decimal]:
        """Fetch stETH/wstETH exchange rate from Lido API."""
        if not self.session:
            raise RuntimeError("Session not initialized")

        if not token.exchange_rate_api:
            return None

        try:
            async with self.session.get(token.exchange_rate_api) as response:
                if response.status == 200:
                    data = await response.json()
                    rate = Decimal(str(data.get('stEthExchangeRate', 1)))
                    return rate
        except Exception:
            pass

        return None
