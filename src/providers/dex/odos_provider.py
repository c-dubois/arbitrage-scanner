"""ODOS DEX aggregator provider implementation."""

from decimal import Decimal
from typing import Optional, Dict, Any

from .base_provider import BaseProvider
from ...models.chain import Chain
from ...models.token import Token

class OdosProvider(BaseProvider):
    """ODOS DEX aggregator provider."""

    BASE_URL = "https://api.odos.xyz"
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
            print(f"Chain {chain.name} not supported by ODOS")
            return None

        from_address = from_token.get_address(chain.name)
        to_address = to_token.get_address(chain.name)

        if not from_address or not to_address:
            print(f"Missing token addresses for {chain.name}: from={from_address}, to={to_address}")
            return None

        raw_amount = from_token.convert_decimal_to_raw_amount(amount)

        payload = {
            "chainID": int(chain.id),
            "inputTokens": [
                {
                    "tokenAddress": from_address,
                    "amount": str(raw_amount)
                }
            ],
            "outputTokens": [
                {
                    "tokenAddress": to_address,
                    "proportion": 1 # Float: 1 = 100% of output
                }
            ],
            "userAddr": "0x0000000000000000000000000000000000000000", # Placeholder address
            "slippageLimitPercent": 0.3, # Float: 0.3 = 0.3% slippage
            "referralCode": 0,
            "compact": True,  # Use compact calldata
            "disableRFQs": True,  # Disable time-sensitive RFQ quotes
            "simple": False  # Set to True for simpler/faster quotes if needed
        }

        try:
            # Use v3 quote endpoint
            url = f"{self.BASE_URL}/sor/quote/v3"

            response = await self._make_request(
                "POST",
                url,
                json=payload,
                headers={"Content-Type": "application/json"}
            )

            if response and 'outAmounts' in response:
                # ODOS returns amounts in array format
                output_amount = int(response['outAmounts'][0])
                # Add normalized field for compatibility
                response['toAmount'] = output_amount

            return response
        
        except Exception as e:
            print(f"Error fetching quote from ODOS: {e}")
            return None
        
    def calculate_output_amount(
        self,
        quote_data: Dict[str, Any],
        token: Token
    ) -> Decimal:
        """
        Calculate output amount from ODOS quote data.
        
        Args:
            quote_data: The quote data returned by ODOS
            token: Output token for which to calculate the amount
            
        Returns:
            Output amount in decimal format
        """
        # ODOS v3 returns outAmounts as array
        if 'outAmounts' in quote_data:
            raw_amount = int(quote_data['outAmounts'][0])
        else:
            # Fallback to normalized field
            raw_amount = quote_data.get('toAmount', 0)
        
        # Use token's conversion method
        return token.convert_raw_to_decimal_amount(raw_amount)