""" Core scanner module for arbitrage opportunity detection."""

import asyncio
from decimal import Decimal
from typing import List, Dict, Optional, Tuple
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
        trade_sizes_eth: List[Decimal],
        redemption_rate_provider: RedemptionRateProvider,
        trade_sizes_sonic: Optional[List[Decimal]] = None
    ):
        """Initialize the ArbitrageScanner.
        
        Args:
            providers: List of DEX aggregator providers
            chains: List of blockchain networks to scan
            tokens: Dictionary of token symbols to Token objects
            trade_sizes: List of trade sizes to evaluate
            redemption_rate_provider: Provider for fetching redemption rates
            trade_sizes_sonic: Optional list of trade sizes for Sonic chain (in S)
        """
        self.providers = providers
        self.chains = chains
        self.tokens = tokens
        self.trade_sizes_eth = sorted(trade_sizes_eth)  # sorted ETH trade sizes
        self.trade_sizes_sonic = sorted(trade_sizes_sonic) if trade_sizes_sonic else []
        self.redemption_rate_provider = redemption_rate_provider

    def _get_base_token_for_chain(self, chain: Chain) -> Optional[Token]:
        """Get the appropriate base token for a given chain.
        
        Args:
            chain: The blockchain network
            
        Returns:
            The base token (WS for Sonic, WETH for others) or None if not found
        """
        if chain.name.lower() == "sonic":
            base_token = self.tokens.get("WS")
            if not base_token:
                # Fallback: try to find wrapped S by address
                for token in self.tokens.values():
                    if token.get_address("sonic") == chain.wrapped_native:
                        return token
                raise ValueError("WS (Wrapped S) token not found in configuration")
        else:
            base_token = self.tokens.get("WETH")
            if not base_token:
                raise ValueError("WETH token not found in configuration")
        
        return base_token
    
    def _get_trade_sizes_for_chain(self, chain: Chain) -> List[Decimal]:
        """Get the appropriate trade sizes for a given chain.
        
        Args:
            chain: The blockchain network
            
        Returns:
            List of trade sizes in the appropriate currency
        """
        if chain.name.lower() == "sonic":
            return self.trade_sizes_sonic
        return self.trade_sizes_eth

    async def scan_all_sizes(self) -> Dict[str, List[ArbitrageOpportunity]]:
        """Scan for arbitrage opportunities across all trade sizes.
        
        Returns:
            Dictionary mapping "chain-token-provider" to list of ArbitrageOpportunity objects at different sizes.
        """
        all_opportunities: Dict[str, List[ArbitrageOpportunity]] = {}
        tasks = []

        for chain in self.chains:
            # Get the appropriate base token for this chain
            try:
                base_token = self._get_base_token_for_chain(chain)
            except ValueError as e:
                print(f"Skipping {chain.name}: {e}")
                continue
            
            for token_symbol, token in self.tokens.items():
                # Skip if token not available on this chain
                if not token.is_available_on_chain(chain.name):
                    continue
                
                # Skip if trying to trade base token to itself
                if token.symbol == base_token.symbol:
                    continue   
                
                # For Sonic, only process Sonic-specific tokens
                if chain.name.lower() == "sonic":
                    if token.symbol not in ["stS", "OS", "anS"]:
                        continue
                
                # For other chains, skip Sonic-specific tokens
                else:
                    if token.symbol in ["stS", "OS", "anS", "WS"]:
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

        # Get appropriate trade sizes for chain
        trade_sizes = self._get_trade_sizes_for_chain(chain)

        for trade_size in trade_sizes:
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
        # Get appropriate token for chain
        try:
            base_token = self._get_base_token_for_chain(chain)
        except ValueError as e:
            print(f"Error getting base token for {chain.name}: {e}")
            return None
        
        # Skip if trying to trade same token (ex: WETH -> WETH)
        if token.symbol == base_token.symbol:
            return None
    
        # Verify base token is available on this chain
        if not base_token.is_available_on_chain(chain.name):
            print(f"{base_token.symbol} not available on {chain.name}")
            return None
        
        # Verify target token is available on this chain
        if not token.is_available_on_chain(chain.name):
            return None

        # Get a quote for base_token (WETH) -> token (LST)
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

        # Show trade sizes for each chain type
        has_sonic = any(chain.name.lower() == "sonic" for chain in self.chains)
        has_other = any(chain.name.lower() != "sonic" for chain in self.chains)

        if has_other:
            print(f"ETH Trade sizes: {self.trade_sizes}")
        if has_sonic:
            print(f"S Trade sizes: {self.trade_sizes_sonic}")

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
                        base_symbol = opp.base_token.symbol
                        display_symbol = "S" if base_symbol == "WS" else "ETH" if base_symbol == "WETH" else base_symbol
                        print(f"  {opp.chain.name:12} | {opp.base_token.symbol:5} -> {opp.target_token.symbol:5} | "
                                f"Size: {float(opp.trade_size):8.0f} {display_symbol:3} | "
                                f"Profit: {float(opp.profit):8.4f} {display_symbol:3} ({opp.profit_percentage:.2f}%) | "
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
