"""Main redemption rate provider that coordinates API and on-chain sources with caching."""

from decimal import Decimal
from time import time
from typing import Optional, Dict, List, Tuple

from .rate_providers.base_rate_provider import BaseRateProvider
from .rate_providers.api_rate_provider import APIRateProvider
from .rate_providers.onchain_rate_provider import OnchainRateProvider
from ..models.token import Token

#want to change this so api rate is not cached? since just cbeth?

class RedemptionRateProvider:
    """
    Coordinates redemption rate providers (API and on-chain) with TTL-based caching.
    
    This is the main interface for getting LST redemption rates (e.g., cbETH→ETH, wstETH→ETH).
    It manages multiple sub-providers and caches results to minimize API/RPC calls.
    """

    def __init__(self, rpc_url: str = "https://eth.llamarpc.com", cache_ttl: int = 60):
        """
        Initialize the redemption rate provider.
        
        Args:
            rpc_url: Ethereum RPC endpoint for on-chain calls
            cache_ttl: Cache time-to-live in seconds (default: 60)
        """
        # Initialize sub-providers
        self.api_provider = APIRateProvider()
        self.onchain_provider = OnchainRateProvider(rpc_url)

        # List of providers in priority order
        self.providers: List[BaseRateProvider] = [
            self.api_provider,      # Try API first (faster)
            self.onchain_provider   # Fallback to on-chain if API fails
        ]

        # Cache with TTL: {token_symbol: (rate, timestamp)}
        self._rate_cache: Dict[str, Tuple[Decimal, float]] = {}
        self.cache_ttl = cache_ttl

        print(f"Redemption rate cache TTL set to {self.cache_ttl} seconds")

    async def __aenter__(self):
        """Async context manager entry: initialize sub-providers / async resources."""
        await self.api_provider.__aenter__()
        await self.onchain_provider.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit: close sub-providers / cleanup async resources."""
        await self.api_provider.__aexit__(exc_type, exc_val, exc_tb)
        await self.onchain_provider.__aexit__(exc_type, exc_val, exc_tb)

    def _is_cache_valid(self, token_symbol: str) -> bool:
        """Check if the cached rate for the token is still valid based on TTL."""
        if token_symbol in self._rate_cache:
            _, timestamp = self._rate_cache[token_symbol]
            if (time() - timestamp) < self.cache_ttl:
                return True
        return False
    
    async def get_redemption_rate(self, token: Token) -> Optional[Decimal]:
        """
        Get the redemption rate for a liquid staking token (LST).

        Checks cache first, then tries each provider until a rate is found.
        Returns None if no rate available (no fallback rates).
        
        Args:
            token: The liquid staking token (e.g., cbETH, wstETH)
            
        Returns:
            The redemption rate (LST/ETH) as a Decimal, or None if unavailable
        """
        # Check cache first
        if self._is_cache_valid(token.symbol):
            rate, timestamp = self._rate_cache[token.symbol]
            age = int(time() - timestamp)
            print(f"Cache hit for {token.symbol}: {rate} (age: {age}s)")
            return rate

        # Try each provider in order until one returns a valid rate
        for provider in self.providers:
            if provider.supports_token(token):
                try:
                    rate = await provider.get_exchange_rate(token)

                    if rate is not None:
                        # Cache the rate with current timestamp
                        self._rate_cache[token.symbol] = (rate, time())
                        provider_name = provider.__class__.__name__
                        print(f"Got {token.symbol} rate from {provider_name}: {rate}")
                        return rate
                    
                except Exception as e:
                    provider_name = provider.__class__.__name__
                    print(f"{provider_name} failed for {token.symbol}: {e}")
                    continue

        # All providers failed - return None (no fallback)
        print(f"WARNING: Could not get redemption rate for {token.symbol} - skipping")
        return None
    
    def clear_cache(self):
        """Clear the entire rate cache."""
        self._rate_cache.clear()
        print("Redemption rate cache cleared")

    def clear_token_cache(self, token_symbol: str):
        """Clear the cache entry for a specific token."""
        if token_symbol in self._rate_cache:
            del self._rate_cache[token_symbol]
            print(f"Cleared cache for {token_symbol}")

    def get_cache_status(self) -> Dict[str, Dict[str, Optional[int]]]:
        """Get the current cache status with token symbols and age in seconds for monitoring."""
        status = {}
        current_time = time()

        for symbol, (rate, timestamp) in self._rate_cache.items():
            age = int(current_time - timestamp)
            status[symbol] = {
                'rate': float(rate),
                'age_seconds': age,
                'is_valid': age < self.cache_ttl,
                'expires_in_seconds': max(0, self.cache_ttl - age)
            }

        return status