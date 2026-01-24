# 🤖 Multi-Platform Prediction Market MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![MCP Protocol](https://img.shields.io/badge/MCP-1.0-purple.svg)](https://modelcontextprotocol.io)
[![Status](https://img.shields.io/badge/status-Phase_3_MVP-blue.svg)](#-project-status)

**🚧 Work In Progress: Evolving to Support Multiple Prediction Markets + Cross-Platform Arbitrage 🚧**

Unified AI-powered trading platform for Polymarket and Kalshi prediction markets, with cross-platform arbitrage capabilities and foundation for autonomous AI agents.

---

## 📢 Project Status

### ✅ **Polymarket**: Fully Operational (v0.1.0)
- **45 comprehensive tools** across all categories
- Real-time WebSocket monitoring
- Enterprise-grade safety features
- Production-ready trading

### ✅ **Phase 1 & 2 COMPLETE**: Kalshi Full Integration (v0.2.0)
**52 Kalshi tools** now operational - exceeding original Phase 2 target!
- ✅ **Market Discovery** (10 tools) - Search, filter, trending markets
- ✅ **Market Analysis** (11 tools) - Liquidity, spreads, risk assessment
- ✅ **Trading** (13 tools) - Order management, execution, simulation
- ✅ **Portfolio** (10 tools) - Positions, P&L, risk analysis, exports
- ✅ **Real-time** (8 tools) - WebSocket subscriptions (ticker, orderbook, trades, fills)
- ✅ **Authentication** - RSA-PSS signing for production API
- ✅ **WebSocket Core** - Connected, authenticated, message handling
- ✅ **Code Quality** - Comprehensive cleanup (17/19 issues resolved)

**Total: 97 tools across 2 platforms** 🎉

### 🚀 **Phase 3 STARTED**: Cross-Platform Arbitrage (MVP Complete!)
**5 cross-platform tools** now operational:
- ✅ `search_all_markets` - Search both platforms simultaneously
- ✅ `compare_prices` - Price comparison across platforms
- ✅ `find_price_discrepancies` - **Arbitrage opportunity scanner!**
- ✅ `unified_portfolio` - Combined portfolio view
- ✅ `create_market_pair` - Manual market linking

**Total: 102 tools (97 platform + 5 cross-platform)** 🚀

### 📅 **Next Steps**
- **Phase 3 Remaining**: Redis market pairs, AI matching (3 tools)
- **Phase 4**: Arbitrage engine with strategy execution (15 tools)
- **Phase 5**: AI agent foundation for autonomous trading
- **Phase 6**: Production polish and deployment

See [docs/plans/](docs/plans/) for detailed roadmap.

---

## ⚡ What's Working Now

**Ready to use today with Claude Desktop or Claude Code:**

### Polymarket (45 tools)
- ✅ Search & discover markets by keywords, categories, volume
- ✅ Analyze liquidity, spreads, orderbooks
- ✅ Place limit & market orders with smart execution
- ✅ Track positions, P&L, and portfolio value
- ✅ Real-time WebSocket streams (prices, orders, fills)

### Kalshi (52 tools)
- ✅ Search markets with advanced filters (category, close time, status)
- ✅ Analyze market opportunities, risk, and liquidity
- ✅ Create, modify, and cancel orders with validation
- ✅ Monitor portfolio with position tracking and exports
- ✅ Real-time data subscriptions (WebSocket ready)
- ✅ Production API with RSA-PSS authentication

### Cross-Platform Arbitrage (5 tools) ⭐ NEW!
- ✅ Search all markets across both platforms at once
- ✅ Compare prices for equivalent markets
- ✅ **Find arbitrage opportunities** with profit analysis
- ✅ Unified portfolio view (total value across platforms)
- ✅ Manual market pairing for tracking

**102 total tools** across platforms + cross-platform - all accessible through natural language with Claude!

Example queries:
```
"Show me the top 10 trending markets on Kalshi"
"What's the current spread on KXBTC-24JAN-B95000?"
"Place a limit buy order for 50 YES tokens at $0.65"
"Show my P&L for all Kalshi positions"

# NEW Cross-Platform Queries:
"Search for Bitcoin markets on both Kalshi and Polymarket"
"Find arbitrage opportunities with at least 3% spread"
"Show me my unified portfolio across all platforms"
```

---

## 👨‍💻 Created By

**[Caio Vicentino](https://github.com/caiovicentino)** (Original Polymarket implementation)

Forked and extended by **[swizzleshizzle](https://github.com/swizzleshizzle)** for multi-platform support

Powered by **[Claude Code](https://claude.ai/code)** from Anthropic

---

## 🎯 Vision: Multi-Platform Arbitrage System

### Architecture Goals

```
┌─────────────────────────────────────────────────────────────────┐
│                    MULTI-PLATFORM MCP SERVER                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 1: PLATFORM-SPECIFIC TOOLS                               │
│  ─────────────────────────────────                              │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │    Polymarket        │  │      Kalshi          │            │
│  │    45 Tools ✅       │  │   52 Tools ✅        │            │
│  │  • Market Discovery  │  │  • Market Discovery  │            │
│  │  • Analysis          │  │  • Analysis          │            │
│  │  • Trading           │  │  • Trading           │            │
│  │  • Portfolio         │  │  • Portfolio         │            │
│  │  • Real-time         │  │  • Real-time         │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                 │
│  LAYER 2: CROSS-PLATFORM TOOLS (Phase 3) 📅                    │
│  ──────────────────────────────────────                         │
│  • search_all_markets        • compare_prices                   │
│  • find_equivalent_markets   • aggregate_liquidity              │
│  • create_market_pair        • unified_portfolio                │
│                                                                 │
│  LAYER 3: ARBITRAGE TOOLS (Phase 4) 📅                         │
│  ────────────────────────────────────                           │
│  • scan_price_discrepancies  • execute_strategy                 │
│  • scan_calendar_spreads     • monitor_positions                │
│  • create_strategy           • force_exit                       │
│                                                                 │
│  DATA LAYER: Redis Stack 🚧                                     │
│  ───────────────────────                                        │
│  • JSON documents    • Vector search (AI matching)              │
│  • Time series       • Pub/sub (real-time)                      │
│  • Full-text search  • Strategy persistence                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### What's Coming

#### Cross-Platform Arbitrage
Identify and exploit price discrepancies across platforms:
- **Price Arbitrage**: Same market, different prices
- **Calendar Spreads**: Same underlying, different dates
- **Hedging**: Lock in profit with opposing positions

#### Hybrid Market Matching
- **Automatic**: AI-powered similarity matching (>95% confidence)
- **Semi-Automatic**: AI suggests, you confirm (>80% confidence)
- **Manual**: Explicit market pairs for complex relationships

#### Strategy Engine
Full lifecycle management:
- Strategy creation from detected opportunities
- Multi-leg position sizing (Kelly criterion, fixed, etc.)
- Entry/exit condition monitoring
- Risk management and stop-loss
- Simultaneous or sequential execution modes

#### AI Agent Foundation (Phase 5)
Architecture ready for autonomous operation:
- **Observer Mode**: Monitor and log opportunities
- **Advisor Mode**: Propose strategies, human executes
- **Semi-Autonomous**: Auto-execute under thresholds
- **Autonomous**: Full execution with safety limits

All through the **same MCP interface** you use!

---

## ⭐ Current Features (Polymarket - Fully Operational)

### 🎯 45 Comprehensive Tools Across 5 Categories

<table>
<tr>
<td width="20%" align="center"><b>🔍<br/>Market Discovery</b><br/>8 tools</td>
<td width="20%" align="center"><b>📊<br/>Market Analysis</b><br/>10 tools</td>
<td width="20%" align="center"><b>💼<br/>Trading</b><br/>12 tools</td>
<td width="20%" align="center"><b>📈<br/>Portfolio</b><br/>8 tools</td>
<td width="20%" align="center"><b>⚡<br/>Real-time</b><br/>7 tools</td>
</tr>
</table>

#### 🔍 Market Discovery (8 tools)
- Search and filter markets by keywords, categories, events
- Trending markets by volume (24h, 7d, 30d)
- Category-specific markets (Politics, Sports, Crypto)
- Markets closing soon alerts
- Featured and promoted markets

#### 📊 Market Analysis (10 tools)
- Real-time prices and spreads
- Complete orderbook depth analysis
- Liquidity and volume metrics
- Historical price data
- **AI-powered opportunity analysis** with BUY/SELL/HOLD recommendations
- Multi-market comparison
- Risk assessment and scoring

#### 💼 Trading (12 tools)
- **Limit orders** (GTC, GTD, FOK, FAK)
- **Market orders** (immediate execution)
- Batch order submission
- **AI-suggested pricing** (aggressive/passive/mid strategies)
- Order status tracking and history
- Single and bulk order cancellation
- **Smart trade execution** (natural language → automated strategy)
- **Position rebalancing** with slippage protection

#### 📈 Portfolio Management (8 tools)
- Real-time position tracking
- P&L calculation (realized/unrealized)
- Portfolio value aggregation
- **Risk analysis** (concentration, liquidity, diversification)
- Trade history with filters
- Performance metrics
- **AI-powered portfolio optimization**

#### ⚡ Real-time Monitoring (7 tools)
- Live price updates via WebSocket
- Orderbook depth streaming
- Order status notifications
- Trade execution alerts
- Market resolution notifications
- Auto-reconnect with exponential backoff

### 🛡️ Enterprise-Grade Safety & Risk Management

- ✅ **Order Size Limits** - Configurable maximum per order
- ✅ **Exposure Caps** - Total portfolio exposure limits
- ✅ **Position Limits** - Per-market position caps
- ✅ **Liquidity Validation** - Minimum liquidity requirements
- ✅ **Spread Tolerance** - Maximum spread checks before execution
- ✅ **Confirmation Flow** - User confirmation for large orders
- ✅ **Pre-trade Validation** - Comprehensive safety checks

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- For trading: Polygon wallet with private key
- For Kalshi (Phase 1+): Kalshi account with API credentials

### Installation

**Try DEMO mode first** (Polymarket read-only, no wallet needed):
```bash
git clone https://github.com/swizzleshizzle/prediction-market-mcp-server.git
cd prediction-market-mcp-server
./install.sh --demo
```

**Full installation** (with Polymarket trading):
```bash
./install.sh
```

The automated installer will:
- ✓ Check Python version (3.10+)
- ✓ Create virtual environment
- ✓ Install all dependencies
- ✓ Configure environment
- ✓ Set up Claude Desktop integration
- ✓ Test the installation

### Configuration

**Option 1: DEMO Mode** (Polymarket read-only)
```bash
cp .env.example .env
# Edit .env and set:
DEMO_MODE=true
```

**Option 2: Full Trading Mode** (Polymarket)
```bash
cp .env.example .env
# Edit with your Polygon wallet credentials
nano .env
```

**Required credentials (Full Mode):**
```env
# Polymarket (currently working)
POLYGON_PRIVATE_KEY=your_private_key_without_0x_prefix
POLYGON_ADDRESS=0xYourPolygonAddress

# Kalshi (Phase 1 - coming soon)
KALSHI_ENABLED=false  # Set true when Phase 1 complete
KALSHI_API_KEY_ID=your_key_id
KALSHI_PRIVATE_KEY_PATH=/path/to/kalshi_rsa.pem

# Multi-platform features (Phase 3+)
ARBITRAGE_ENABLED=false  # Future: cross-platform arbitrage

# Redis (Phase 1+)
REDIS_URL=redis://localhost:6379
```

### Claude Desktop Integration

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%
Claude
otebook_desktop_config.json`

```json
{
  "mcpServers": {
    "prediction-markets": {
      "command": "/path/to/your/venv/bin/python",
      "args": ["-m", "prediction_mcp.server"],
      "cwd": "/path/to/prediction-market-mcp-server",
      "env": {
        "POLYGON_PRIVATE_KEY": "your_private_key",
        "POLYGON_ADDRESS": "0xYourAddress",
        "POLYMARKET_ENABLED": "true",
        "KALSHI_ENABLED": "false"
      }
    }
  }
}
```

**Restart Claude Desktop** and you're ready! 🎉

---

## 💡 Usage Examples

### Current: Polymarket Markets

Ask Claude:
```
"Show me the top 10 trending markets on Polymarket in the last 24 hours"
"Analyze the trading opportunity for the government shutdown market"
"Buy $100 of YES tokens in [market_id] at $0.65"
"Show me all my current positions"
```

### Phase 1+: Multi-Platform Discovery
```
"Search for Bitcoin price markets on both Polymarket and Kalshi"
"Compare liquidity between Polymarket and Kalshi for [topic]"
"Show me all my positions across both platforms"
```

### Phase 3+: Cross-Platform Analysis
```
"Find equivalent markets for 'Trump wins 2024' across platforms"
"Show me price discrepancies between Polymarket and Kalshi"
"Which platform has better liquidity for crypto markets?"
```

### Phase 4+: Arbitrage Trading
```
"Scan for price arbitrage opportunities with >3% spread"
"Create a strategy to capture the 5% spread on [equivalent markets]"
"What calendar spreads are available for BTC price markets?"
"Execute my confirmed arbitrage strategy for [market pair]"
```

### Phase 5+: AI Agent Collaboration
```
"What opportunities has the AI agent detected in the last hour?"
"Review and confirm the proposed strategy #123"
"Set AI agent to auto-execute strategies under $200"
```

---

## 📖 Documentation

### Getting Started
- **[Visual Installation Guide](VISUAL_INSTALL_GUIDE.md)** - Step-by-step with diagrams
- **[FAQ](FAQ.md)** - Frequently asked questions
- **[Setup Guide](SETUP_GUIDE.md)** - Detailed configuration

### Current Implementation
- **[Tools Reference](TOOLS_REFERENCE.md)** - Complete API for all 45 Polymarket tools
- **[Trading Architecture](TRADING_ARCHITECTURE.md)** - System design
- **[WebSocket Integration](WEBSOCKET_INTEGRATION.md)** - Real-time data

### Multi-Platform Roadmap
- **[Design Document](docs/plans/2025-01-20-multi-platform-arbitrage-design.md)** - Complete vision and architecture
- **[Phase 1 Plan](docs/plans/2025-01-20-phase1-foundation-plan.md)** - Multi-platform foundation (current)
- **[Implementation Phases](docs/plans/2025-01-20-multi-platform-arbitrage-design.md#12-implementation-phases)** - Detailed roadmap

### Developer Resources
- **[Agent Integration Guide](AGENT_INTEGRATION_GUIDE.md)** - Integrate with AI agents
- **[Usage Examples](USAGE_EXAMPLES.py)** - Code examples
- **[Contributing](CONTRIBUTING.md)** - How to contribute

---

## 🗓️ Roadmap

### Phase 1: Foundation ✅ **COMPLETE**
- [x] Design multi-platform architecture
- [x] Kalshi authentication (RSA-PSS)
- [x] Kalshi API client
- [x] 10 Kalshi market discovery tools
- [x] Unified configuration system
- [ ] Redis Stack integration (deferred to Phase 3)

### Phase 2: Kalshi Parity ✅ **COMPLETE**
- [x] Complete Kalshi toolset (52 tools total)
- [x] Real-time WebSocket for Kalshi (core infrastructure)
- [x] Event/series hierarchy tools
- [x] Portfolio and trading tools (13 + 10 tools)
- [x] Market analysis tools (11 tools)

### Phase 3: Cross-Platform 🚧 **In Progress - MVP Complete!**
- [x] Cross-platform search aggregation
- [x] Price comparison across platforms
- [x] Arbitrage opportunity scanner
- [x] Unified portfolio view
- [x] Market pair creation (manual)
- [ ] Redis-backed market pairs (persistent storage)
- [ ] AI-powered market matching (vector similarity)
- [ ] Auto-matching with confidence scores

### Phase 4: Arbitrage Engine (Weeks 7-8) 📅
- [ ] Strategy object model
- [ ] Opportunity scanner
- [ ] Multi-leg execution engine
- [ ] Risk management system
- [ ] 15 arbitrage tools

### Phase 5: AI Agent Foundation (Weeks 9-10) 📅
- [ ] Permission model (read-only → autonomous)
- [ ] Proposal/confirmation workflow
- [ ] Audit logging
- [ ] Basic scanner agent (advisor mode)

### Phase 6: Production Polish (Weeks 11-12) 📅
- [ ] Performance optimization
- [ ] Complete documentation
- [ ] Docker production stack
- [ ] Security audit
- [ ] Monitoring and observability

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run specific test suite
pytest tests/test_trading_tools.py -v

# Run with coverage
pytest --cov=prediction_mcp --cov-report=html

# Integration tests (requires API credentials)
pytest -m integration
```

---

## 🛡️ Safety & Security

### ⚠️ Important Security Considerations

- **Private Key Protection**: Never share or commit your private keys
- **Start Small**: Begin with small amounts ($50-100) to test
- **Understand Markets**: Only trade in markets you understand
- **Monitor Positions**: Check your positions regularly
- **Use Safety Limits**: Configure appropriate limits for your risk tolerance
- **Arbitrage Risk**: Understand settlement timing and correlation assumptions

### Default Safety Limits

```env
MAX_ORDER_SIZE_USD=1000              # Maximum $1,000 per order
MAX_TOTAL_EXPOSURE_USD=10000         # Maximum $10,000 total exposure
MAX_POSITION_PER_MARKET_USD=2000     # Maximum $2,000 per market
MIN_LIQUIDITY_REQUIRED=10000         # Minimum $10,000 market liquidity
MAX_SPREAD_TOLERANCE=0.05            # Maximum 5% spread
REQUIRE_CONFIRMATION_ABOVE_USD=500   # Confirm orders over $500

# Future: Arbitrage limits
AI_DAILY_AUTONOMOUS_LIMIT_USD=500    # AI daily limit
AI_MAX_SINGLE_TRADE_USD=100          # AI per-trade limit
```

---

## 🤝 Contributing

Contributions are welcome! Whether you're:
- Testing Phase 1 Kalshi integration
- Suggesting arbitrage strategies
- Improving documentation
- Reporting bugs

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

---

## 📊 Project Stats

- **Lines of Code**: ~15,000+ (Python, growing)
- **Current Tools**: 45 (Polymarket)
- **Target Tools**: 120+ (multi-platform + arbitrage)
- **Test Coverage**: High (real API integration)
- **Documentation**: Comprehensive with detailed roadmap

---

## 🙏 Acknowledgments

This project was made possible by:

- **Caio Vicentino** - Creator of original Polymarket MCP server
- **swizzleshizzle** - Multi-platform architecture and arbitrage system
- **Yield Hacker Community** - DeFi expertise and testing
- **Renda Cripto Community** - Trading insights and validation
- **Cultura Builder Community** - Builder culture and support
- **[Polymarket](https://polymarket.com)** - Prediction market platform
- **[Kalshi](https://kalshi.com)** - Regulated prediction exchange
- **[Anthropic](https://anthropic.com)** - Claude and MCP protocol
- **[py-clob-client](https://github.com/Polymarket/py-clob-client)** - Polymarket SDK
- **[kalshi-python](https://github.com/Kalshi/kalshi-python)** - Kalshi SDK

---

## ⚠️ Disclaimer

This software is provided for educational and research purposes. Trading prediction markets involves financial risk.

**Important Reminders:**
- Cryptocurrency and prediction market trading carry significant risk
- Only invest what you can afford to lose
- Arbitrage opportunities may be fleeting or illusory
- Past performance does not guarantee future results
- This is not financial advice
- Always do your own research (DYOR)
- Start with small amounts to learn the system
- Understand the markets and platforms you're trading
- Monitor your positions regularly
- **Phase 1+ features are under active development**

The authors and contributors are not responsible for any financial losses incurred through the use of this software.

---

## 🔗 Links

- **GitHub Repository**: [github.com/swizzleshizzle/prediction-market-mcp-server](https://github.com/swizzleshizzle/prediction-market-mcp-server)
- **Original Polymarket Server**: [github.com/caiovicentino/polymarket-mcp-server](https://github.com/caiovicentino/polymarket-mcp-server)
- **Polymarket**: [polymarket.com](https://polymarket.com)
- **Kalshi**: [kalshi.com](https://kalshi.com)
- **MCP Protocol**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Claude Code**: [claude.ai/code](https://claude.ai/code)

---

<div align="center">

**Built with ❤️ for autonomous AI trading across prediction markets**

*Ready to make Claude your personal multi-platform prediction market trader!* 🚀

[⭐ Star this repo](https://github.com/swizzleshizzle/prediction-market-mcp-server) | [🐛 Report Bug](https://github.com/swizzleshizzle/prediction-market-mcp-server/issues) | [✨ Request Feature](https://github.com/swizzleshizzle/prediction-market-mcp-server/issues/new)

**Phase 1 In Progress** - Follow development in [docs/plans/](docs/plans/)

</div>
