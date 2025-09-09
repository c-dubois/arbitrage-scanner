"""ODOS DEX aggregator provider implementation."""

from decimal import Decimal
from typing import Optional, Dict, Any

from .base_provider import BaseProvider
from ..models.chain import Chain
from ..models.token import Token

class OdosProvider(BaseProvider):
    """ODOS DEX aggregator provider."""

    BASE_URL = "https://api.odos.xyz/v1/quote"
    SUPPORTED_CHAINS = {
        "ethereum": "1",
        "polygon": "137",
        "optimism": "10",
        "arbitrum": "42161",
        "base": "8453",
        "mantle": "5000",
        "linea": "59144",
        "fraxtal": "252",
        "unichain": "130",
    }

    def is_chain_supported(self, chain: Chain) -> bool:
        """Check if ODOS supports the given chain."""
        return chain.name.lower() in self.SUPPORTED_CHAINS

    async def get_quote(
        self,
        chain: Chain,
        from_token: Token,
        to_token: Token,
        amount: Decimal
    ) -> Optional[Dict[str, Any]]:
        """
        Get a quote from ODOS.
        
        Args:
            chain: The blockchain network
            from_token: Source token
            to_token: Destination token
            amount: Amount to swap (in decimal format)
            
        Returns:
            Quote data or None if unavailable
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context.")

        if not self.is_chain_supported(chain):
            return None

        from_address = from_token.get_address(chain.name)
        to_address = to_token.get_address(chain.name)

        if not from_address or not to_address:
            return None

        raw_amount = from_token.convert_decimal_to_raw_amount(amount)

        payload = {
            "chainID": int(chain.id),
            
        }