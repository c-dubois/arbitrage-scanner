"""Base class for exchange rate providers."""

from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional, Set

from ...models.token import Token

class BaseRateProvider(ABC):
    """Abstract base class for exchange rate providers."""

    @property
    @abstractmethod
    def get_supported_tokens(self) -> Set[str]:
        """Return a set of supported token symbols."""
        pass

    @abstractmethod
    def supports_token(self, token: Token) -> bool:
        """Check if the provider supports the given token.
        Args:
            token: The token to check.
        Returns:
            True if supported, False otherwise."""
        pass

    @abstractmethod
    async def get_exchange_rate(self, token: Token) -> Optional[Decimal]:
        """
        Fetch the exchange rate for a given token.
        
        Args:
            token: The token for which to fetch the exchange rate.
            
        Returns:
            The exchange rate as a Decimal, or None if unavailable.
        """
        pass