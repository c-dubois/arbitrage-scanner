from dataclasses import dataclass, field
from typing import Dict, Optional
from decimal import Decimal

@dataclass
class Token:
    """Represents a cryptocurrency token."""

    name: str
    symbol: str
    decimals: int
    exchange_rate_api: Optional[str] = None
    addresses: Dict[str, str] = field(default_factory=dict)

    def get_address(self, chain_name: str) -> Optional[str]:
        """Get token address for a specific chain."""
        return self.addresses.get(chain_name.lower())

    def is_available_on_chain(self, chain_name: str) -> bool:
        """Check if token is available on a specific chain."""
        return chain_name.lower() in self.addresses

    def convert_raw_amount_to_decimal(self, amount: int) -> Decimal:
        """Convert raw amount to decimal format."""
        return Decimal(amount) / (10 ** self.decimals)

    def convert_decimal_to_raw_amount(self, amount: Decimal) -> int:
        """Convert decimal amount to raw format."""
        return int(amount * (10 ** self.decimals))

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return f"Token(name={self.name}, symbol={self.symbol})"