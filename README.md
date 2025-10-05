# Arbitrage Scanner

A sophisticated cryptocurrency arbitrage opportunity scanner that identifies profitable trades across multiple blockchain networks and liquid staking tokens (LSTs).

## What This Program Does

This scanner finds "risk-free" profit opportunities by comparing market prices of liquid staking tokens (like cbETH, wstETH) with their actual redemption values.

**Simple Example:**

- wstETH should be worth 1.15 ETH (based on staking rewards)
- But you can buy wstETH for only 1.12 ETH on a DEX
- **Profit**: Buy for 1.12 ETH, redeem for 1.15 ETH = 0.03 ETH profit (2.7% return)

The program scans across 9 blockchain networks and 5 different liquid staking tokens to find these opportunities automatically.

## Supported Networks & Tokens

### Blockchain Networks

- **Ethereum** (mainnet)
- **Arbitrum** (Layer 2)
- **Base** (Coinbase L2)
- **Optimism** (Layer 2)
- **Linea** (ConsenSys L2)
- **Fraxtal** (Frax L2)
- **Mantle** (Mantle Network)
- **Unichain** (Uniswap L2)
- **Polygon** (MATIC network)
- **Sonic** (Sonic Labs L1)

### Liquid Staking Tokens

- **cbETH** - Coinbase's staked ETH
- **wstETH** - Lido's wrapped staked ETH
- **stETH** - Lido's rebasing staked ETH
- **frxETH/sfrxETH** - Frax protocol staking tokens
- **METH** - Mantle's staked ETH
- **stS** - Sonic's staked S
- **oS** - Orbit staked S
- **anS** - Ankr staked S

## Prerequisites

- **Python 3.8+** (check with `python --version`)
- **Git** (for cloning the repository)
- **Internet connection** (for API calls and blockchain data)

## Setup Instructions

### 1. Install Git and Clone Repository

If you don't have Git installed:

- **Windows**: Download from [git-scm.com](https://git-scm.com/download/win)
- **Mac**: Install via Homebrew `brew install git` or from [git-scm.com](https://git-scm.com/download/mac)
- **Linux**: `sudo apt install git` (Ubuntu/Debian) or `sudo yum install git` (CentOS/RHEL)

Clone this repository to your local machine:

```bash
# Navigate to where you want the project folder
cd ~/Documents  # or wherever you keep projects

# Clone the repository (replace USERNAME with actual GitHub username)
git clone https://github.com/USERNAME/arbitrage-scanner.git

# Enter the project directory
cd arbitrage-scanner
```

### 2. Set Up Python Virtual Environment

A virtual environment keeps this project's dependencies separate from your system Python:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# You should see (venv) in your terminal prompt when activated
```

### 3. Install Dependencies

```bash
# Make sure virtual environment is activated first!
pip install -r requirements.txt
```

### 4. Create Environment Configuration

Create a `.env` file in the project root directory with your configuration:

```bash
# Create the file
touch .env  # Mac/Linux
# Or on Windows, create a new file named .env
```

Add these variables to your `.env` file:

```env
# API Keys (optional - some providers work without keys)
ONE_INCH_API_KEY=your_api_key_here
ODOS_API_KEY=your_api_key_here

# RPC Configuration (for blockchain data)
RPC_URL=https://eth.llamarpc.com

# Trade Size Configuration
# Min and Max in ETH
MIN_TRADE_SIZE_ETH=100
MAX_TRADE_SIZE_ETH=2000
# Step multiplier (e.g., 2 = 10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10000)
TRADE_SIZE_MULTIPLIER=1.5

# Scanner Configuration
SCAN_INTERVAL_SECONDS=60
REQUEST_TIMEOUT_SECONDS=30

# Caching Configuration
ON_CHAIN_CACHE_TTL=60
API_CACHE_TTL=30
```

**Note**: The program will work with the default RPC URL and without API keys for basic functionality.

## How to Run

### Single Scan (One-time Check)

```bash
# Activate virtual environment first
source venv/bin/activate  # Mac/Linux
# or
venv\Scripts\activate     # Windows

# Run single scan across all chains
python -m src.main

# Run scan on specific chains only
python -m src.main --chains ethereum arbitrum base
```

### Continuous Monitoring

```bash
# Run continuous scanning (updates every 60 seconds)
python -m src.main --continuous

# Run continuous scan on specific chains
python -m src.main --continuous --chains ethereum arbitrum
```

### Example Output

```bash

🚀 Starting Arbitrage Scanner
🔗 Monitoring chains: Ethereum, Arbitrum, Base
💰 Trade sizes (ETH): 10, 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10000
🔌 Using DEX providers: OdosProvider

✅ Best trade size for each route:

┌─────────┬───────┬──────────────────────┬─────────────────────┬────────┬──────────┬─────────────────┐
│ Chain   │ Token │ Best Trade Size (ETH)│ Principal + Profit  │ Profit │ Profit % │ Redemption Rate │
├─────────┼───────┼──────────────────────┼─────────────────────┼────────┼──────────┼─────────────────┤
│ Arbitrum│ wstETH│ 100                  │ 100.85             │ 0.85   │ 0.85%    │ 1.1500         │
│ Base    │ cbETH │ 500                  │ 501.20             │ 1.20   │ 0.24%    │ 1.0520         │
└─────────┴───────┴──────────────────────┴─────────────────────┴────────┴──────────┴─────────────────┘

🏆 BEST OVERALL OPPORTUNITY:
Chain: Arbitrum
Token: wstETH
Best Trade Size (ETH): 100
Profit: 0.85 ETH (0.85%)
```

## Understanding the Code Structure

This project uses modern Python patterns that might be unfamiliar:

### Project Organization

```bash

arbitrage-scanner/
├── src/                    # Main source code
│   ├── core/              # Business logic
│   │   └── scanner.py     # Main arbitrage detection
│   ├── models/            # Data structures
│   │   ├── chain.py       # Blockchain representation
│   │   ├── token.py       # Token representation  
│   │   └── opportunity.py # Arbitrage opportunity
│   ├── providers/         # External data sources
│   │   ├── dex_providers/ # DEX aggregator APIs
│   │   └── rate_providers/ # Token redemption rates
│   └── utils/             # Configuration and helpers
├── config/                # Configuration files
│   └── tokens.yaml       # Chain and token definitions
├── requirements.txt       # Python dependencies
└── .env                  # Your environment variables
```

### Modern Python Features Used

**1. Dataclasses (instead of traditional classes):**

```python
# Traditional way you might be used to:
class Chain:
    def __init__(self, id, name, native_token):
        self.id = id
        self.name = name
        self.native_token = native_token

# Modern dataclass way (used in this project):
@dataclass
class Chain:
    id: str
    name: str
    native_token: str
    # __init__ method is automatically generated!
```

**2. Type Hints:**

```python
# Variables have type annotations
def get_quote(self, amount: Decimal) -> Optional[Dict[str, Any]]:
    #             ^^^^^^^ input type    ^^^^^^^ return type
```

**3. Async/Await (for concurrent operations):**

```python
# All API calls are asynchronous for better performance
async def get_quote(...):
    response = await self.session.get(url)  # Non-blocking
    return await response.json()
```

**4. Abstract Base Classes:**

```python
# Ensures all DEX providers implement required methods
class BaseDexProvider(ABC):
    @abstractmethod
    async def get_quote(self):
        pass  # Must be implemented by subclasses
```

### Key Components Explained

**Scanner (`src/core/scanner.py`)**

- Main orchestrator that coordinates all scanning
- Tries different trade sizes to find most profitable
- Manages async operations across multiple chains/tokens

**Providers (`src/providers/`)**

- **DEX Providers**: Get market prices from exchanges (ODOS, 1inch, etc.)
- **Rate Providers**: Get "true" redemption values from protocols

**Models (`src/models/`)**

- **Chain**: Represents a blockchain (Ethereum, Arbitrum, etc.)
- **Token**: Represents a cryptocurrency token
- **ArbitrageOpportunity**: Represents a profitable trade opportunity

## Configuration

### Adding New Tokens

Edit `config/tokens.yaml` to add new liquid staking tokens:

```yaml
tokens:
  NEW_TOKEN:
    name: "New Staking Token"
    symbol: "newETH"
    decimals: 18
    addresses:
      ethereum: "0x1234567890123456789012345678901234567890"
      arbitrum: "0x0987654321098765432109876543210987654321"
```

### Adding New Chains

```yaml
chains:
  new_chain:
    id: "999"
    name: "New Chain"
    native_token: "ETH"
    wrapped_native: "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd"
```

## Potential Improvements & Extensions

### 1. Additional Chains to Add

- **BNB Smart Chain (BSC)** - Large DeFi ecosystem
- **Avalanche** - Popular L1 with liquid staking
- **Scroll** - zkEVM Layer 2
- **zkSync Era** - Matter Labs Layer 2
- **Blast** - Yield-bearing Layer 2
- **Mode Network** - DeFi-focused Layer 2

### 2. Additional Tokens to Support

- **rETH** - Rocket Pool liquid staking token
- **WBETH** - Binance liquid staking token
- **swETH** - Swell liquid staking token
- **ETHx** - Stader liquid staking token
- **osETH** - StakeWise liquid staking token
- **ankrETH** - Ankr liquid staking token

### 3. Additional DEX Providers

- **1inch** - Multi-DEX aggregator
- **Paraswap** - Another popular aggregator
- **0x/Matcha** - Professional trading infrastructure
- **CowSwap** - MEV-protected trading
- **LI.FI** - Cross-chain DEX aggregator

### 4. Technical Improvements

**Logging System:**

```python
# Add structured logging for better monitoring
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Found opportunity", extra={
    "chain": "arbitrum",
    "token": "wstETH", 
    "profit": 0.85
})
```

**Database Storage:**

- Store opportunities in SQLite/PostgreSQL for historical analysis
- Track opportunity frequency and success rates
- Build performance analytics

**Web Interface:**

- Flask/FastAPI web dashboard
- Real-time opportunity updates via WebSocket
- Mobile-responsive design for monitoring on phone

**Notifications:**

- Discord/Slack bot integration
- Email alerts for high-profit opportunities
- Telegram bot for instant notifications

**Trade Execution:**

- Integrate with DEX APIs for actual trade execution
- Gas price optimization
- MEV protection strategies
- Multi-chain transaction coordination

**Risk Management:**

- Slippage protection
- Maximum position sizing
- Cool-down periods between trades
- Blacklist problematic tokens/chains

**Performance Optimizations:**

- Redis caching for redemption rates
- Connection pooling for HTTP requests
- Parallel scanning across chains
- Smart rate limiting to avoid API throttling

### 5. Data & Analytics Features

**Historical Analysis:**

- Track opportunity patterns over time
- Identify most profitable time periods
- Correlation analysis between opportunities and market conditions

**Reporting:**

- Daily/weekly profit summaries
- Success rate tracking
- Performance by chain/token
- Export to CSV/Excel for analysis

**Monitoring & Alerting:**

- Health checks for providers
- Alert on scanning failures
- Performance metrics tracking
- Uptime monitoring

## Troubleshooting

### Common Issues

#### "ModuleNotFoundError"

```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

#### "No opportunities found"

- Market conditions may not have profitable arbitrage
- Try different trade sizes or chains
- Check if API endpoints are accessible

#### API Rate Limiting

- Add delays between requests in settings
- Get API keys for higher rate limits
- Use multiple RPC endpoints

#### Connection Errors

- Check internet connection
- Verify RPC URL is working
- Some networks may be temporarily unavailable

## Getting Updates

To get the latest version:

```bash

# Pull latest changes
git pull origin main

# Update dependencies if requirements.txt changed
pip install -r requirements.txt
```

## Security Notes

- **Never commit your `.env` file** to version control
- **Use environment variables** for sensitive data like API keys
- **Consider using a dedicated server** for continuous monitoring
- **Be cautious with large trade sizes** until you verify the program works correctly

## Support

If you encounter issues:

1. Check this README for common solutions
2. Verify your `.env` configuration
3. Test with smaller trade sizes first
4. Check the console output for specific error messages
