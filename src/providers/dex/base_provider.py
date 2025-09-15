from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, Dict, Any
from aiohttp import ClientSession, ClientTimeout
from tenacity import retry, stop_after_attempt, wait_exponential

from ...models.chain import Chain
from ...models.token import Token

class BaseProvider(ABC):
    """Abstract base class for DEX aggregator providers."""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 30):
        self.api_key = api_key
        self.timeout = ClientTimeout(total=timeout)
        self.session: Optional[ClientSession] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.session = ClientSession(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()

    @abstractmethod
    async def get_quote(
        self,
        chain: Chain,
        from_token: Token,
        to_token: Token,
        amount: Decimal
    ) -> Optional[Dict[str, Any]]:
        """
        Get a quote for token swap.
        
        Args:
            chain: The blockchain network
            from_token: Source token
            to_token: Destination token
            amount: Amount to swap (in decimal format)
            
        Returns:
            Quote data or None if unavailable
        """
        pass

    @abstractmethod
    def is_chain_supported(self, chain: Chain) -> bool:
        """Check if the provider supports the given chain."""
        pass

    # potentially can use AsyncRetrying??
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _make_request(
        self, 
        method: str,
        url: str,
        headers: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Make HTTP request with retry logic.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            **kwargs: Additional request parameters
            
        Returns:
            Response data
        """
        if not self.session:
            raise RuntimeError("Provider not initialized. Use async context manager.")
        
        headers = headers or {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        async with self.session.request(method, url, headers=headers, **kwargs) as response:
            response.raise_for_status()
            return await response.json()

    def calculate_output_amount(
        self,
        quote_data: Dict[str, Any],
        token: Token
    ) -> Decimal:
        """
        Calculate output amount from quote data.
        
        Args:
            quote_data: The quote data returned by the provider
            token: The token for which to calculate the amount
            
        Returns:
            Output amount in decimal format
        """
        raw_amount = int(quote_data.get('toAmount', 0))
        return token.convert_raw_amount_to_decimal(raw_amount)