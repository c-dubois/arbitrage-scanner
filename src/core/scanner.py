""" Core scanner module for arbitrage opportunity detection."""

import asyncio
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from ..models.chain import Chain
from ..models.token import Token
from ..models.opportunity import ArbitrageOpportunity
from ..providers.dex_providers.base_dex_provider import BaseDexProvider
from ..providers.redemption_rate_provider import RedemptionRateProvider

class ArbitrageScanner:
    """Scanner for detecting arbitrage opportunities across DEX aggregators."""

    def __init__(
        self,
        providers: List[BaseDexProvider],
        chains: List[Chain],
        tokens: Dict[str, Token],
        trade_sizes: List[Decimal],
        redemption_rate_provider: RedemptionRateProvider
    ):
        """Initialize the ArbitrageScanner.
        
        Args:
            providers: List of DEX aggregator providers
            chains: List of blockchain networks to scan
            tokens: Dictionary of token symbols to Token objects
            trade_sizes: List of trade sizes to evaluate
            redemption_rate_provider: Provider for fetching redemption rates
        """
        self.providers = providers
        self.chains = chains
        self.tokens = tokens
        self.trade_sizes = sorted(trade_sizes)  # Ensure trade sizes are sorted
        self.redemption_rate_provider = redemption_rate_provider