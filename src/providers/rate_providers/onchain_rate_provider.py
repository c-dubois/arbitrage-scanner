"""On-chain exchange rate provider for LSTs."""

from decimal import Decimal
from typing import Optional, Set, Dict, Any
from web3 import AsyncWeb3, AsyncHTTPProvider

from .base_rate_provider import BaseRateProvider
from ...models.token import Token

class OnchainRateProvider(BaseRateProvider):
    """Handles on-chain exchange rate fetching for LSTs like stETH, METH, wstETH, sfrxETH."""

    SUPPORTED_TOKENS = {'wstETH', 'stETH', 'METH', 'sfrxETH', 'frxETH'}

    def __init__(self, rpc_url: str = "https://eth.llamarpc.com"):
        """Initialize the provider with RPC URL.

        Args:
            rpc_url: The RPC URL of the Ethereum node.
        """
        self.rpc_url = rpc_url
        self.web3: Optional[AsyncWeb3] = None
        self.contracts = self._init_contracts()

    async def __aenter__(self):
        """Async context manager entry: initialize async Web3 connection"""
        self.web3 = AsyncWeb3(AsyncHTTPProvider(self.rpc_url))
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit: close async Web3 connection"""
        if self.web3 and hasattr(self.web3, 'provider'):
            try:
                if hasattr(self.web3.provider, 'session'):
                    await self.web3.provider.session.close()
            except Exception as e:
                print(f"Error closing Web3 session: {e}")
        self.web3 = None

    def _init_contracts(self) -> Dict[str, Dict[str, Any]]:
        """Initialize contract configurations with ABIs and addresses for supported tokens.
        
        Returns:
            A dictionary mapping token symbols to their contract configurations.
        """
        return {
            'wstETH': {
                'address': '0x7f39C581F595B53c5cb19bD0b3f8dA6c935E2Ca0',
                'abi': [{
                    "inputs": [{"name": "_wstETHAmount", "type": "uint256"}],
                    "name": "getStETHByWstETH",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }],
                'method': 'getStETHByWstETH',
                'args': [10**18]  # 1 wstETH -> returns stETH amount
            },
            'stETH': {
                # stETH is rebasing, always 1:1 with ETH
                'static_rate': Decimal('1.0')
            },
            'METH': {
                'address': '0xe3cBd06D7dadB3F4e6557bAb7EdD924CD1489E8f', # METH Oracle contract
                'abi': [{
                    "inputs": [{"name": "mETHAmount", "type": "uint256"}],
                    "name": "mETHToETH",
                    "outputs": [{"type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }],
                'method': 'mETHToETH',
                'args': [10**18] # 1 METH -> returns ETH amount
            },
            'sfrxETH': {
                'address': '0xac3E018457B222d9311445847689839724446d9f',
                'abi': [{
                    "inputs": [{"name": "shares", "type": "uint256"}],
                    "name": "convertToAssets",
                    "outputs": [{"name": "assets", "type": "uint256"}],
                    "stateMutability": "view",
                    "type": "function"
                }],
                'method': 'convertToAssets',
                'args': [10**18] # 1 sfrxETH -> returns frxETH amount
            },
            'frxETH': {
                # frxETH is rebasing, always 1:1 with ETH
                'static_rate': Decimal('1.0')
            },
        }
    
    @property
    def get_supported_tokens(self) -> Set[str]:
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
        Fetch the exchange rate for a given token from on-chain data.
        
        Args:
            token: The token for which to fetch the exchange rate.
            
        Returns:
            The exchange rate as a Decimal, or None if unavailable.
        """
        if not self.supports_token(token):
            return None

        config = self.contracts.get(token.symbol)
        if not config:
            return None

        # Check for static rate (e.g. stETH, frxETH)
        if 'static_rate' in config:
            return config['static_rate']
        
        try:
            return await self._call_contract(token.symbol, config)
        except Exception as e:
            print(f"Error fetching {token.symbol} on-chain rate: {e}")
            return None
        
    async def _call_contract(self, symbol: str, config: Dict[str, Any]) -> Optional[Decimal]:
        """Call the contract method to get the exchange rate.
        
        Args:
            symbol: The token symbol.
            config: The contract configuration dictionary.
            
        Returns:
            The exchange rate as a Decimal, or None if unavailable.
        """
        if not self.web3:
            raise RuntimeError("Web3 not initialized. Use async context manager.")

        try:
            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(config['address']),
                abi=config['abi']
            )

            method = getattr(contract.functions, config['method'])
            raw_result = await method(*config['args']).call()
            
            # Convert raw result (in wei) to Decimal ETH amount (divide by 10^18)
            rate = Decimal(str(raw_result)) / Decimal(10**18)
            print(f"On-chain rate for {symbol}: {rate}")
            
            return rate
        
        except Exception as e:
            print(f"Contract call failed for {symbol}: {e}")
            return None