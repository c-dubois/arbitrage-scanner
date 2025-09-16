import asyncio
import argparse
from tabulate import tabulate

from utils.settings import Settings
from core.scanner import ArbitrageScanner

async def main(args):
    """Main execution function for the arbitrage scanner."""
    # Load settings
    settings = Settings()