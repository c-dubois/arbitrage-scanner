import os
import yaml
from pathlib import Path
from decimal import Decimal
from typing import Dict, List
from dotenv import load_dotenv

from ..models.chain import Chain
from ..models.token import Token

class Settings:
    """Application settings manager."""

    def __init__(self):
        """Initialize settings for loading environment variables and config files."""
        load_dotenv()

        # Load YAML config
        config_path = Path(__file__).parent.parent.parent / "config" / "tokens.yaml"
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)

        # API Keys
        self.odos_api_key = os.getenv("ODOS_API_KEY")
        self.one_inch_api_key = os.getenv("ONE_INCH_API_KEY")

        # RPC URL for on-chain data
        self.rpc_url = os.getenv("RPC_URL", "https://eth.llamarpc.com")

        # Trade size configuration
        self.min_trade_size_eth = Decimal(os.getenv("MIN_TRADE_SIZE_ETH", "10"))
        self.max_trade_size_eth = Decimal(os.getenv("MAX_TRADE_SIZE_ETH", "10000"))
        self.trade_size_multiplier = Decimal(os.getenv("TRADE_SIZE_MULTIPLIER", "2")) # or float?

        # Scanner settings
        self.scan_interval = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))
        self.request_timeout = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))

        # On-chain and API cache TTLs
        self.on_chain_cache_ttl = int(os.getenv("ON_CHAIN_CACHE_TTL", "60"))
        self.api_cache_ttl = int(os.getenv("API_CACHE_TTL", "30"))

    def get_trade_sizes(self) -> List[Decimal]:
        """
        Generate a list of trade sizes from min to max using exponential stepping multiplier.
        
        Returns list like: [10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10000]
        """
        sizes = []
        current_size = self.min_trade_size_eth

        while current_size <= self.max_trade_size_eth:
            sizes.append(current_size)
            current_size *= Decimal(str(self.trade_size_multiplier))

        # Ensure max size is included if not already
        if self.max_trade_size_eth not in sizes:
            sizes.append(self.max_trade_size_eth)

        return sizes
    
    def get_chains(self) -> List[Chain]:
        """Load and return list of configured Chain objects."""
        chains = []
        for chain_name, chain_data in self.config.get('chains', {}).items():
            chain = Chain(
                id=chain_data['id'],
                name=chain_data['name'],
                native_token=chain_data['native_token'],
                wrapped_native=chain_data['wrapped_native'],
                weth_address=chain_data.get('weth_address')
            )
            chains.append(chain)
        return chains
    
    def get_tokens(self) -> Dict[str, Token]:
        """Load and return dictionary of configured Token objects keyed by symbol."""
        tokens = {}
        for token_symbol, token_data in self.config.get('tokens', {}).items():
            token = Token(
                name=token_data['name'],
                symbol=token_data['symbol'],
                decimals=token_data['decimals'],
                exchange_rate_api=token_data.get("exchange_rate_api"),
                addresses=token_data.get("addresses", {})
            )
            tokens[token_symbol] = token
        return tokens
