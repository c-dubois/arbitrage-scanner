import asyncio
import argparse
from tabulate import tabulate

from .utils.settings import Settings
from .core.scanner import ArbitrageScanner
from .providers.dex_providers.odos_provider import OdosProvider
from .providers.redemption_rate_provider import RedemptionRateProvider

async def main(args):
    """Main execution function for the arbitrage scanner."""
    # Load settings
    settings = Settings()

    print("🚀 Starting Arbitrage Scanner")

    # Get chains and tokens from settings
    all_chains = settings.get_chains()
    all_tokens = settings.get_tokens()

    # Filter chains based on user input
    if args.chains:
        selected_chain_names = {name.lower() for name in args.chains}
        chains = [chain for chain in all_chains if chain.name.lower() in selected_chain_names]
    else:
        chains = all_chains

    print(f"🔗 Monitoring chains: {', '.join([chain.name for chain in chains])}")

    # Get trade sizes
    trade_sizes = settings.get_trade_sizes()
    print(f"💰 Trade sizes (ETH): {', '.join(map(str, trade_sizes))}")

    # Initialize DEX providers
    dex_providers = []

    # Add ODOS provider (API key not required)
    odos = OdosProvider(timeout=settings.request_timeout)
    dex_providers.append(odos)

    print(f"🔌 Using DEX providers: {', '.join([p.__class__.__name__ for p in dex_providers])}")

    # Initialize Redemption Rate Provider
    redemption_rate_provider = RedemptionRateProvider(
        rpc_url=settings.rpc_url,
        cache_ttl=settings.redemption_rate_cache_ttl
        )

    # Initialize Arbitrage Scanner
    scanner = ArbitrageScanner(
        providers=dex_providers,
        chains=chains,
        tokens=all_tokens,
        trade_sizes=trade_sizes,
        redemption_rate_provider=redemption_rate_provider
    )

    # Open provider connections
    for provider in dex_providers:
        await provider.__aenter__()

    # Open redemption rate provider connections
    await redemption_rate_provider.__aenter__()

    try:
        if args.continuous:
            # Continuous scanning mode
            print("🔄 Running in continuous scan mode. Press Ctrl+C to stop.")
            await scanner.continuous_scan(interval=settings.scan_interval)
        else:
            # Single scan mode
            print("🔍 Running single scan for all trade sizes...")
            all_opportunities = await scanner.scan_all_sizes()

            # Find best opportunities
            best_opportunities = scanner.find_best_opportunities(all_opportunities)
            
            if best_opportunities:
                # Sort by profit descending
                best_opportunities.sort(key=lambda opp: opp.profit, reverse=True)

                # Prepare table data
                table_data = []
                for opp in best_opportunities:
                    table_data.append([
                        opp.chain.name,
                        f"{opp.target_token.symbol}",
                        f"{float(opp.trade_size):.0f}",
                        f"{float(opp.expected_return):.4f}",
                        f"{float(opp.profit):.4f}",
                        f"{opp.profit_percentage:.2f}%",
                        f"{float(opp.exchange_rate):.4f}"
                    ])

                # Print results in a table
                print("\n✅ Best trade size for each route:\n")
                headers = ["Chain", "Token", "Best Trade Size (ETH)", "Principal + Profit", "Profit", "Profit %", "Redemption Rate"]
                print(tabulate(table_data, headers=headers, tablefmt="grid"))

                # Show best overall opportunity
                best_opportunity = best_opportunities[0]
                print("\n🏆 BEST OVERALL OPPORTUNITY:")
                print(f"Chain: {best_opportunity.chain.name}")
                print(f"Token: {best_opportunity.target_token.symbol}")
                print(f"Best Trade Size (ETH): {float(best_opportunity.trade_size):.0f}")
                print(f"Expected Return: {float(best_opportunity.expected_return):.4f}")
                print(f"Profit: {float(best_opportunity.profit):.4f}")
                print(f"Profit %: {best_opportunity.profit_percentage:.2f}%")
                print(f"Redemption Rate: {float(best_opportunity.exchange_rate):.4f}")

            else:
                print("\n❌ No profitable opportunities found")
        
    finally:
        # Close provider connections
        for provider in dex_providers:
            await provider.__aexit__(None, None, None)

        # Close redemption rate provider connections
        await redemption_rate_provider.__aexit__(None, None, None)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Arbitrage Opportunity Scanner")

    parser.add_argument(
        '--chains', 
        nargs='*', 
        help="List of chain names to monitor (e.g., ethereum, arbitrum). If omitted, all chains are monitored."
    )

    parser.add_argument(
        '--continuous', 
        action='store_true', 
        help="Run the scanner in continuous mode, scanning at regular intervals."
    )
    return parser.parse_args()

#double check this syntax 

if __name__ == "__main__":
    args = parse_arguments()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        print("\n🛑 Scanner stopped by user")
    except Exception as e:
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()