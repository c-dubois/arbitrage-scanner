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

    async def scan_all_sizes(self) -> Dict[str, List[ArbitrageOpportunity]]:
        """Scan for arbitrage opportunities across all trade sizes.
        
        Returns:
            Dictionary mapping "chain-token-provider" to list of ArbitrageOpportunity objects at different sizes.
        """
        all_opportunities: Dict[str, List[ArbitrageOpportunity]] = {}
        tasks = []

        for chain in self.chains:
            for token_symbol, token in self.tokens.items():
                if not token.is_available_on_chain(chain.name):
                    continue

                for provider in self.providers:
                    if provider.is_chain_supported(chain):
                        task = self._scan_size_range(chain, token, provider)
                        tasks.append(task)

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in results:
                if isinstance(result, tuple):
                    key, opportunities = result
                    all_opportunities[key] = opportunities
                elif isinstance(result, Exception):
                    print(f"Error during scanning: {result}")

        return all_opportunities
        
    async def _scan_size_range(
            self,
            chain: Chain,
            token: Token,
            provider: BaseDexProvider
        ) -> Tuple[str, List[ArbitrageOpportunity]]:
        """
        Scan all trade sizes for a specific token pair.

        Args:
            chain: The blockchain network to scan
            token: The token to evaluate
            provider: The DEX provider to use

        Returns:
            Tuple mapping "chain-token-provider" to list of ArbitrageOpportunity objects.
        """
        key = f"{chain.name}-{token.symbol}-{provider.__class__.__name__}"
        opportunities = []

        for trade_size in self.trade_sizes:
            try:
                opp = await self._scan_single_size(chain, token, trade_size, provider)
                if opp:
                    opportunities.append(opp)
            except Exception as e:
                print(f"Error scanning {key} at size {trade_size}: {e}")
                continue

        return key, opportunities

    async def _scan_single_size(
            self,
            chain: Chain,
            token: Token,
            trade_size: Decimal,
            dex_provider: BaseDexProvider
        ) -> Optional[ArbitrageOpportunity]:
        """
        Scan for arbitrage opportunity for a specific token pair at a single trade size.

        Args:
            chain: The blockchain network to scan
            token: The token to evaluate
            trade_size: The trade size to evaluate
            dex_provider: The DEX provider to use

        Returns:
            An ArbitrageOpportunity object if found, else None.
        """
        base_token = self.tokens.get(chain.native_token)

        # Get a quote for base_token -> token
        quote = await dex_provider.get_quote(
            chain, base_token, token, trade_size
        )

        if not quote:
            return None
        
        # Calculate output amount
        output_amount = dex_provider.calculate_output_amount(quote, token)

        # Fetch redemption rate for LST
        redemption_rate = await self.redemption_rate_provider.get_redemption_rate(token)

        if not redemption_rate:
            print(f"No redemption rate for {token.symbol} on {chain.name}")
            return None
        
        # Calculate expected return in base token
        expected_return = output_amount * redemption_rate

        # Calculate profit and profit percentage
        profit = expected_return - trade_size
        profit_percentage = (profit / trade_size) * Decimal('100')

        # Create and return the arbitrage opportunity
        return ArbitrageOpportunity(
            chain=chain,
            base_token=base_token,
            target_token=token,
            trade_size=trade_size,
            expected_return=expected_return,
            profit=profit,
            profit_percentage=profit_percentage,
            exchange_rate=redemption_rate,
            provider=dex_provider.__class__.__name__,
            timestamp=datetime.now()
        )
    
    def find_best_opportunities(
        self,
        all_opportunities: Dict[str, List[ArbitrageOpportunity]]
    ) -> List[ArbitrageOpportunity]:
        """
        Find the best arbitrage opportunity (trade size) for each chain-token-provider combination.

        Args:
            all_opportunities: Dictionary mapping "chain-token-provider" to list of ArbitrageOpportunity objects.

        Returns:
            List of the best ArbitrageOpportunity objects.
        """
        best_opportunities = []

        for key, opportunities in all_opportunities.items():
            if not opportunities:
                continue

            # Filter profitable opportunities
            profitable_opps = [opp for opp in opportunities if opp.is_profitable]

            if profitable_opps:
                # Select the opportunity with the highest profit
                best_opp = max(profitable_opps, key=lambda opp: opp.profit)
                best_opportunities.append(best_opp)

        return best_opportunities
    
    async def continuous_scan(self, interval_seconds: int = 60):
        """Continuously scan for arbitrage opportunities at specified intervals.
        
        Args:
            interval_seconds: Time in seconds between scans.
        """
        print(f"Starting continuous scan every {interval_seconds} seconds...")
        print(f"Trade sizes: {self.trade_sizes}")

        while True:
            try:
                print(f"{'='*60}")
                print(f"\n--- Scan started at {datetime.now().isoformat()} ---")
                print(f"{'='*60}")

                # Scan all sizes
                all_opportunities = await self.scan_all_sizes()

                # Find best opportunities
                best_opportunities = self.find_best_opportunities(all_opportunities)

                if best_opportunities:
                    # Sort by profit descending
                    best_opportunities.sort(key=lambda opp: opp.profit, reverse=True)

                    print(f"\nFound {len(best_opportunities)} profitable opportunities:")

                    for opp in best_opportunities[:10]: # Show top 10 opportunities
                        print(f"  {opp.chain.name:12} | {opp.base_token.symbol:5} -> {opp.target_token.symbol:5} | "
                              f"Size: {float(opp.trade_size):8.0f} ETH | "
                              f"Profit: {float(opp.profit):8.4f} ETH ({opp.profit_percentage:.2f}%) | "
                              f"{opp.provider}")
                    
                    best_opportunity = best_opportunities[0]
                    print("\n🏆 BEST OPPORTUNITY:")
                    print(f"   {best_opportunity}")
                else:
                    print("\n❌ No profitable opportunities found")

            except Exception as e:
                print(f"Error occurred during scanning: {e}")

            print(f"\nNext scan in {interval_seconds} seconds...")
            await asyncio.sleep(interval_seconds)
