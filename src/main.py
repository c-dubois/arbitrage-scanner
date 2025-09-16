import asyncio
import argparse
from tabulate import tabulate

from utils.settings import Settings
from core.scanner import ArbitrageScanner
from providers.dex_providers.odos_provider import OdosProvider
from providers.redemption_rate_provider import RedemptionRateProvider

async def main(args):
    """Main execution function for the arbitrage scanner."""
    # Load settings
    settings = Settings()

    print("🚀 Starting Arbitrage Scanner")

    # Get chains and tokens from settings
    all_chains = settings.get_chains()
    all_tokens = settings.get_tokens()