from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .chain import Chain
from .token import Token

@dataclass
class ArbitrageOpportunity:
    """Represents an arbitrage opportunity between two tokens on a specific chain."""

    chain: Chain
    base_token: Token
    target_token: Token
    trade_size: Decimal
    expected_return: Decimal
    profit: Decimal
    profit_percentage: Decimal
    exchange_rate: Decimal
    provider: str
    timestamp: datetime = field(default_factory=datetime.now)
    gas_estimate: Optional[Decimal] = None

    @property
    def net_profit(self) -> Decimal:
        """Calculate net profit after gas costs."""
        if self.gas_estimate:
            return self.profit - self.gas_estimate
        return self.profit

    @property
    def is_profitable(self) -> bool:
        """Check if the opportunity is profitable after gas costs."""
        return self.net_profit > 0
    
    def to_dict(self) -> dict:
        """Convert the opportunity to a dictionary for easy serialization."""
        return {
            'chain': str(self.chain),
            'base_token': str(self.base_token),
            'target_token': str(self.target_token),
            'trade_size': float(self.trade_size),
            'expected_return': float(self.expected_return),
            'profit': float(self.profit),
            'profit_percentage': float(self.profit_percentage),
            'exchange_rate': float(self.exchange_rate),
            'provider': self.provider,
            'timestamp': self.timestamp.isoformat(),
            'gas_estimate': float(self.gas_estimate) if self.gas_estimate else None,
            'net_profit': float(self.net_profit),
            'is_profitable': self.is_profitable,
        }

    def __str__(self):
        return (f"{self.chain.name}: {self.trade_size} {self.base_token.symbol} -> "
                f"{self.expected_return:.4f} {self.target_token.symbol} "
                f"(Profit: {self.profit:.4f} {self.base_token.symbol}, "
                f"Profit Percentage: {self.profit_percentage:.2f}%)"
        )