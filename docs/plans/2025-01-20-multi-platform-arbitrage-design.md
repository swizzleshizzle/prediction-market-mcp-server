# Multi-Platform Prediction Market MCP Server

## Design Document

**Date:** 2025-01-20
**Status:** Draft
**Author:** Collaborative Design Session

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Vision & Goals](#2-vision--goals)
3. [System Architecture](#3-system-architecture)
4. [Platform Integration](#4-platform-integration)
5. [Tool Design](#5-tool-design)
6. [Arbitrage System](#6-arbitrage-system)
7. [Strategy Object Model](#7-strategy-object-model)
8. [Data Storage Architecture](#8-data-storage-architecture)
9. [AI Agent Integration](#9-ai-agent-integration)
10. [Permission Model](#10-permission-model)
11. [Configuration](#11-configuration)
12. [Implementation Phases](#12-implementation-phases)

---

## 1. Executive Summary

### What We're Building

A multi-platform MCP (Model Context Protocol) server that provides unified access to prediction markets across Polymarket and Kalshi, with dedicated arbitrage capabilities and a foundation for AI-driven autonomous opportunity detection.

### Key Capabilities

- **Platform-Specific Tools**: Full native API access for each platform (45 Polymarket tools, 52 Kalshi tools)
- **Cross-Platform Research**: Aggregated market search and comparison across platforms
- **Arbitrage Engine**: Detection and execution of price discrepancies, calendar spreads, and hedging strategies
- **Strategy Management**: Full lifecycle management of multi-leg trading strategies
- **AI-Ready Architecture**: Foundation for autonomous opportunity scanning with human-in-the-loop confirmation

### Architectural Principles

1. **Native Interfaces**: Each platform exposes its full API capabilities without abstraction loss
2. **Configuration-Driven**: Platforms can be enabled/disabled independently
3. **Redis-Centric**: All state stored in Redis Stack for performance and AI vector support
4. **MCP as Control Plane**: Single interface for both human operators and AI agents
5. **Safety First**: All operations subject to configurable safety limits

---

## 2. Vision & Goals

### Near-Term Goals

1. Extend existing Polymarket MCP server to support Kalshi API
2. Implement cross-platform market matching and comparison
3. Build arbitrage detection and strategy execution engine
4. Establish Redis-based persistence layer

### Long-Term Vision

```
┌─────────────────────────────────────────────────────────────────┐
│                    LONG-TERM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   YOU (via Claude Desktop/CLI)                                  │
│   ─────────────────────────────                                 │
│   • Review AI-generated opportunities                           │
│   • Confirm/reject strategy proposals                           │
│   • Manual research and trading                                 │
│   • Override AI decisions                                       │
│   • Set risk parameters and matching rules                      │
│                         │                                       │
│                         ▼                                       │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │                 MCP SERVER                               │  │
│   │        (Your Command & Control Interface)                │  │
│   │                                                          │  │
│   │   Polymarket │ Kalshi │ Arbitrage │ Strategy Engine      │  │
│   └─────────────────────────────────────────────────────────┘  │
│                         ▲                                       │
│                         │                                       │
│   AI AGENT (Autonomous Scanner)                                 │
│   ─────────────────────────────                                 │
│   • Monitors markets 24/7                                       │
│   • Detects arbitrage opportunities                             │
│   • Proposes strategies for your approval                       │
│   • Learns from outcomes                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Success Criteria

- [ ] Can trade independently on Polymarket OR Kalshi with full tool access
- [ ] Can identify equivalent markets across platforms automatically
- [ ] Can detect and alert on price discrepancy opportunities
- [ ] Can execute multi-leg arbitrage strategies with safety controls
- [ ] Architecture supports future AI agent integration without changes

---

## 3. System Architecture

### Docker Compose Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                     DOCKER COMPOSE STACK                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    HUMAN LAYER                            │  │
│  │                                                           │  │
│  │   Claude Desktop / Claude CLI / Web Dashboard             │  │
│  │                                                           │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │ MCP Protocol                      │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               MCP SERVER (Container 1)                    │  │
│  │               prediction-mcp-server                       │  │
│  │                                                           │  │
│  │   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │  │
│  │   │ Polymarket  │ │   Kalshi    │ │  Arbitrage  │        │  │
│  │   │  45 tools   │ │  52 tools   │ │   tools     │        │  │
│  │   └─────────────┘ └─────────────┘ └─────────────┘        │  │
│  │                                                           │  │
│  │   Platform Adapters │ Strategy Engine │ Safety Limits     │  │
│  │                                                           │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │               REDIS STACK (Container 2)                   │  │
│  │               redis/redis-stack                           │  │
│  │                                                           │  │
│  │   RedisJSON │ RediSearch │ RedisTimeSeries │ Streams     │  │
│  │                                                           │  │
│  └──────────────────────────┬───────────────────────────────┘  │
│                             │                                   │
│                             ▲                                   │
│  ┌──────────────────────────┴───────────────────────────────┐  │
│  │               AI AGENT (Container 3 - Optional)           │  │
│  │               prediction-ai-agent                         │  │
│  │                                                           │  │
│  │   MCP Client │ Opportunity Scanner │ Strategy Generator   │  │
│  │                                                           │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **MCP Server** | Tool execution, platform API integration, safety enforcement |
| **Redis Stack** | State persistence, real-time data, vector search, pub/sub |
| **AI Agent** | Autonomous scanning, opportunity detection, strategy proposals |
| **Human (Claude)** | Oversight, confirmation, manual operations, configuration |

### Communication Patterns

```
Human ←──MCP Protocol──→ MCP Server ←──Redis Protocol──→ Redis
                              ↑
AI Agent ←──MCP Protocol──────┘
         ←──Redis Protocol─────────────────────────────→ Redis
```

---

## 4. Platform Integration

### Platform Adapter Architecture

Each platform implements a common adapter interface while exposing its full native API:

```python
class PlatformAdapter(Protocol):
    """Base interface all platform adapters must implement"""

    platform_id: str  # "polymarket" | "kalshi"

    # === Connection ===
    async def connect(self) -> bool
    async def disconnect(self) -> None
    async def health_check(self) -> HealthStatus

    # === Market Data (normalized for cross-platform use) ===
    async def get_market_normalized(self, market_id: str) -> NormalizedMarket
    async def search_markets_normalized(self, query: str, **filters) -> List[NormalizedMarket]
    async def get_orderbook_normalized(self, market_id: str) -> NormalizedOrderbook
    async def get_price(self, market_id: str, outcome: str) -> PriceQuote

    # === Trading (normalized) ===
    async def create_order_normalized(self, order: NormalizedOrderRequest) -> NormalizedOrder
    async def cancel_order(self, order_id: str) -> bool
    async def get_order_normalized(self, order_id: str) -> NormalizedOrder

    # === Portfolio (normalized) ===
    async def get_positions_normalized(self) -> List[NormalizedPosition]
    async def get_balance(self) -> Balance

    # === Real-time ===
    async def subscribe_price(self, market_id: str, callback: PriceCallback) -> Subscription
    async def subscribe_fills(self, callback: FillCallback) -> Subscription

    # === Native passthrough ===
    def get_native_client(self) -> Any  # Access full native API
```

### Normalized Data Models

```python
@dataclass
class NormalizedMarket:
    id: str                          # Platform-prefixed: "poly_xxx" / "kalshi_xxx"
    platform: str                    # "polymarket" | "kalshi"
    native_id: str                   # Original platform ID
    title: str
    description: str
    category: str                    # Normalized category
    outcomes: List[NormalizedOutcome]
    expiration: datetime
    resolution_source: str
    volume_24h_usd: float
    liquidity_usd: float
    status: str                      # "open" | "closed" | "resolved"

    # Platform-specific data preserved
    polymarket_data: Optional[Dict]  # condition_id, token_ids, etc.
    kalshi_data: Optional[Dict]      # event_id, series_id, ticker, etc.

@dataclass
class NormalizedOutcome:
    id: str
    name: str                        # YES/NO or named outcome
    price_bid: float
    price_ask: float
    price_last: float
    native_token_id: str

@dataclass
class NormalizedOrder:
    id: str                          # Platform-prefixed
    platform: str
    native_id: str
    market_id: str
    side: str                        # "BUY" | "SELL"
    outcome: str                     # YES/NO/named
    price: float                     # 0-1
    size: int                        # Contracts
    size_usd: float
    order_type: str                  # "limit" | "market"
    time_in_force: str               # GTC | GTD | IOC | FOK
    status: str                      # pending | open | partial | filled | cancelled
    filled_size: int
    avg_fill_price: float
    created_at: datetime
    strategy_id: Optional[str]       # Links to parent strategy

@dataclass
class NormalizedPosition:
    id: str
    platform: str
    market_id: str
    outcome: str
    size: int                        # Signed: + long, - short
    avg_entry_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    strategy_id: Optional[str]
```

### Polymarket Integration

**Authentication:**
- L1: Private key signing via EIP-712 (OrderSigner)
- L2: API key/secret/passphrase (derived from L1 signature)

**APIs:**
- CLOB API: `https://clob.polymarket.com` (trading)
- Gamma API: `https://gamma-api.polymarket.com` (market data)
- WebSocket: Real-time price feeds

**Existing Implementation:** 45 tools already implemented in current codebase.

### Kalshi Integration

**Authentication:**
- RSA-PSS signatures (private key signing of requests)
- API key ID + private key pair

**APIs:**
- Trading API: `https://trading-api.kalshi.com/trade-api/v2`
- Demo API: `https://demo-api.kalshi.co/trade-api/v2`
- WebSocket: Real-time orderbook, tickers, fills

**Market Structure:**
- Kalshi organizes markets hierarchically: **Events → Markets**
- Example: "2024 Presidential Election" (event) contains multiple markets
- This hierarchy will be fully exposed in the Kalshi toolset

---

## 5. Tool Design

### Tool Organization

```
┌─────────────────────────────────────────────────────────────────┐
│                        TOOL LAYERS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 1: PLATFORM-SPECIFIC TOOLS                               │
│  ─────────────────────────────────                              │
│  Enabled/disabled based on platform configuration               │
│                                                                 │
│  polymarket_*  (45 tools)    │    kalshi_*  (52 tools)          │
│  ─────────────────────────   │    ────────────────────          │
│  Full native Polymarket API  │    Full native Kalshi API        │
│                              │    + Event/Series hierarchy      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 2: CROSS-PLATFORM TOOLS                                  │
│  ─────────────────────────────                                  │
│  Enabled when 2+ platforms configured                           │
│                                                                 │
│  • search_all_markets        • compare_prices                   │
│  • find_equivalent_markets   • aggregate_liquidity              │
│  • create_market_pair        • unified_portfolio                │
│  • list_market_pairs         • suggest_correlations             │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LAYER 3: ARBITRAGE TOOLS                                       │
│  ─────────────────────────                                      │
│  Enabled when 2+ platforms + arbitrage enabled                  │
│                                                                 │
│  Detection:                  Strategy Management:               │
│  • scan_price_discrepancies  • create_strategy                  │
│  • scan_calendar_spreads     • list_strategies                  │
│  • analyze_opportunity       • get_strategy                     │
│                              • modify_strategy                  │
│  Execution:                  • confirm_strategy                 │
│  • execute_strategy          • reject_strategy                  │
│  • check_execution_status    • cancel_strategy                  │
│  • force_exit                                                   │
│                                                                 │
│  Monitoring:                                                    │
│  • subscribe_to_pair         • get_active_positions             │
│  • set_opportunity_alert     • calculate_net_exposure           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Polymarket Tools (45 - Existing)

#### Market Discovery (8 tools)
| Tool | Description |
|------|-------------|
| `polymarket_search_markets` | Search markets by keyword |
| `polymarket_get_trending_markets` | Get trending markets by volume |
| `polymarket_get_markets_by_category` | Filter by category |
| `polymarket_get_markets_closing_soon` | Markets near expiration |
| `polymarket_get_featured_markets` | Featured/promoted markets |
| `polymarket_get_sports_markets` | Sports category markets |
| `polymarket_get_crypto_markets` | Crypto category markets |
| `polymarket_get_market_details` | Full market details |

#### Market Analysis (10 tools)
| Tool | Description |
|------|-------------|
| `polymarket_get_market_prices` | Current bid/ask/last prices |
| `polymarket_get_orderbook` | Full orderbook |
| `polymarket_get_orderbook_depth` | Orderbook depth analysis |
| `polymarket_analyze_liquidity` | Liquidity metrics |
| `polymarket_get_price_history` | Historical prices |
| `polymarket_analyze_market_opportunity` | AI opportunity analysis |
| `polymarket_compare_markets` | Multi-market comparison |
| `polymarket_get_market_trades` | Recent trades |
| `polymarket_get_spread` | Current spread |
| `polymarket_assess_market_risk` | Risk scoring |

#### Trading (12 tools)
| Tool | Description |
|------|-------------|
| `polymarket_create_limit_order` | Place limit order |
| `polymarket_create_market_order` | Place market order |
| `polymarket_create_batch_orders` | Batch order submission |
| `polymarket_get_ai_suggested_price` | AI pricing strategy |
| `polymarket_get_order_status` | Check order status |
| `polymarket_get_order_history` | Order history |
| `polymarket_get_open_orders` | List open orders |
| `polymarket_cancel_order` | Cancel single order |
| `polymarket_cancel_all_orders` | Cancel all orders |
| `polymarket_execute_smart_trade` | Smart execution algorithm |
| `polymarket_amend_order` | Modify existing order |
| `polymarket_rebalance_position` | Position rebalancing |

#### Portfolio (8 tools)
| Tool | Description |
|------|-------------|
| `polymarket_get_positions` | Current positions |
| `polymarket_get_position_pnl` | P&L calculation |
| `polymarket_get_portfolio_value` | Total portfolio value |
| `polymarket_analyze_portfolio_risk` | Risk analysis |
| `polymarket_get_trade_history` | Trade history |
| `polymarket_get_activity_log` | On-chain activity |
| `polymarket_get_performance_metrics` | Performance stats |
| `polymarket_optimize_portfolio` | AI portfolio optimization |

#### Real-time (7 tools)
| Tool | Description |
|------|-------------|
| `polymarket_subscribe_price_updates` | Price WebSocket |
| `polymarket_subscribe_orderbook` | Orderbook WebSocket |
| `polymarket_subscribe_order_status` | Order status updates |
| `polymarket_subscribe_trades` | Trade feed |
| `polymarket_subscribe_resolution` | Resolution notifications |
| `polymarket_manage_subscriptions` | Subscription management |
| `polymarket_get_system_health` | System status |

### Kalshi Tools (52 - New)

#### Market Discovery (10 tools)
| Tool | Description | Mapping |
|------|-------------|---------|
| `kalshi_search_markets` | Search markets | Direct |
| `kalshi_get_markets_by_volume` | Trending by volume | Adapt |
| `kalshi_get_events_by_category` | Events by category | Adapt |
| `kalshi_get_markets_by_close_date` | Markets closing soon | Direct |
| `kalshi_get_featured_markets` | Featured markets | Direct |
| `kalshi_get_sports_markets` | Sports markets | Direct |
| `kalshi_get_crypto_markets` | Crypto markets | Direct |
| `kalshi_get_market` | Market details | Direct |
| `kalshi_get_event` | Event details | Kalshi-specific |
| `kalshi_get_event_markets` | All markets in event | Kalshi-specific |

#### Market Analysis (11 tools)
| Tool | Description | Mapping |
|------|-------------|---------|
| `kalshi_get_market_ticker` | Current prices | Direct |
| `kalshi_get_orderbook` | Full orderbook | Direct |
| `kalshi_analyze_liquidity` | Liquidity metrics | Build |
| `kalshi_get_candlesticks` | OHLC price history | Direct |
| `kalshi_analyze_market_opportunity` | AI analysis | Build |
| `kalshi_compare_markets` | Multi-market comparison | Build |
| `kalshi_get_trades` | Recent trades | Direct |
| `kalshi_get_spread` | Current spread | Build |
| `kalshi_assess_market_risk` | Risk scoring | Build |
| `kalshi_get_series` | Market series data | Kalshi-specific |
| `kalshi_get_exchange_schedule` | Trading schedule | Kalshi-specific |

#### Trading (13 tools)
| Tool | Description | Mapping |
|------|-------------|---------|
| `kalshi_create_order` | Place order (limit) | Direct |
| `kalshi_create_market_order` | Market order | Adapt |
| `kalshi_batch_create_orders` | Batch submission | Direct |
| `kalshi_get_ai_suggested_price` | AI pricing | Build |
| `kalshi_get_order` | Order status | Direct |
| `kalshi_get_orders` | Order history | Direct |
| `kalshi_get_open_orders` | Open orders | Direct |
| `kalshi_cancel_order` | Cancel order | Direct |
| `kalshi_batch_cancel_orders` | Batch cancel | Direct |
| `kalshi_execute_smart_trade` | Smart execution | Build |
| `kalshi_amend_order` | Modify order | Direct |
| `kalshi_decrease_order` | Reduce order size | Kalshi-specific |
| `kalshi_rebalance_position` | Rebalancing | Build |

#### Portfolio (10 tools)
| Tool | Description | Mapping |
|------|-------------|---------|
| `kalshi_get_positions` | Current positions | Direct |
| `kalshi_get_portfolio_settlements` | P&L from settlements | Adapt |
| `kalshi_get_balance` | Account balance | Direct |
| `kalshi_analyze_portfolio_risk` | Risk analysis | Build |
| `kalshi_get_fills` | Fill history | Direct |
| `kalshi_get_portfolio_history` | Activity log | Direct |
| `kalshi_get_performance_metrics` | Performance stats | Build |
| `kalshi_optimize_portfolio` | AI optimization | Build |
| `kalshi_get_portfolio_rsss` | Risk settlement summary | Kalshi-specific |
| `kalshi_get_announcements` | Platform announcements | Kalshi-specific |

#### Real-time (8 tools)
| Tool | Description | Mapping |
|------|-------------|---------|
| `kalshi_subscribe_ticker` | Price WebSocket | Direct |
| `kalshi_subscribe_orderbook` | Orderbook WebSocket | Direct |
| `kalshi_subscribe_fills` | Fill notifications | Direct |
| `kalshi_subscribe_trades` | Trade feed | Direct |
| `kalshi_subscribe_settlements` | Settlement events | Adapt |
| `kalshi_manage_subscriptions` | Subscription management | Build |
| `kalshi_get_exchange_status` | System health | Direct |
| `kalshi_subscribe_positions` | Position updates | Kalshi-specific |

### Cross-Platform Tools (8 - New)

| Tool | Description |
|------|-------------|
| `search_all_markets` | Search across all enabled platforms |
| `find_equivalent_markets` | Auto-detect matching markets |
| `create_market_pair` | Manually pair markets |
| `list_market_pairs` | View all tracked pairs |
| `suggest_correlations` | AI-suggested related markets |
| `compare_prices` | Side-by-side price comparison |
| `aggregate_liquidity` | Combined depth analysis |
| `unified_portfolio` | Positions across all platforms |

### Arbitrage Tools (15 - New)

#### Opportunity Detection (3 tools)
| Tool | Description |
|------|-------------|
| `scan_price_discrepancies` | Find mispriced equivalent markets |
| `scan_calendar_spreads` | Find term structure opportunities |
| `analyze_opportunity` | Deep analysis of specific opportunity |

#### Strategy Management (7 tools)
| Tool | Description |
|------|-------------|
| `create_strategy` | Build strategy from opportunity |
| `list_strategies` | View all strategies |
| `get_strategy` | Detailed strategy view |
| `modify_strategy` | Adjust strategy parameters |
| `confirm_strategy` | Approve for execution |
| `reject_strategy` | Decline proposed strategy |
| `cancel_strategy` | Abort active strategy |

#### Execution (3 tools)
| Tool | Description |
|------|-------------|
| `execute_strategy` | Run confirmed strategy |
| `check_execution_status` | Monitor fill progress |
| `force_exit` | Emergency close all legs |

#### Monitoring (4 tools)
| Tool | Description |
|------|-------------|
| `subscribe_to_pair` | Real-time pair price alerts |
| `set_opportunity_alert` | Alert when threshold hit |
| `get_active_positions` | Cross-platform exposure |
| `calculate_net_exposure` | Hedged vs unhedged risk |

---

## 6. Arbitrage System

### Supported Arbitrage Types

| Type | Description | Example |
|------|-------------|---------|
| **Price Discrepancy** | Same event priced differently across platforms | "BTC > $100k Jan 31" at 60¢ (Kalshi) vs 65¢ (Polymarket) |
| **Calendar Spread** | Same underlying, different expiration dates | "BTC > $100k Jan 31" vs "BTC > $100k Feb 28" |
| **Cross-Platform Hedge** | Opposing positions to lock in profit | Long YES on one platform, Long NO on other |
| **Correlated Markets** | Related but not identical events | "Trump wins" vs "Republican wins" |

### Market Pair Model

```python
@dataclass
class MarketPair:
    id: str                              # "pair_xxx"
    name: str                            # Human-readable name
    pair_type: str                       # "equivalent" | "calendar" | "correlated"

    leg_a: MarketLeg
    leg_b: MarketLeg

    relationship: PairRelationship
    matching: MatchingInfo
    monitoring: MonitoringConfig

@dataclass
class MarketLeg:
    platform: str                        # "polymarket" | "kalshi"
    market_id: str                       # Normalized ID
    native_id: str                       # Platform's original ID
    outcome: str                         # "YES" | "NO" | named outcome
    expiration: datetime

@dataclass
class PairRelationship:
    correlation: float                   # 1.0 = equivalent, <1.0 = correlated
    price_offset: float                  # Expected price difference (usually 0)
    notes: str                           # Explanation of relationship

@dataclass
class MatchingInfo:
    method: str                          # "manual" | "auto_suggested" | "auto_confirmed"
    confidence: float                    # 0-1 confidence score
    verified_by: str                     # "user" | "ai"
    created_at: datetime

@dataclass
class MonitoringConfig:
    active: bool                         # Currently monitoring
    alert_threshold: float               # Alert if spread exceeds this
    last_spread: float                   # Most recent spread
    last_check: datetime
```

### Calendar Pair Extension

```python
@dataclass
class CalendarPair(MarketPair):
    """Extended model for calendar spread pairs"""
    underlying: str                      # "BTC price", "ETH price", etc.
    strike: float                        # Strike price if applicable
    near_leg: str                        # Reference to shorter-dated leg
    far_leg: str                         # Reference to longer-dated leg
    days_between: int                    # Days between expirations
    implied_vol_spread: Optional[float]  # Derived volatility spread
```

### Hybrid Market Matching

The system supports three matching modes:

1. **Manual Pairing**: User explicitly defines market pairs
2. **Semi-Automatic**: AI suggests matches, user confirms
3. **Automatic**: AI matches with high-confidence, user can override

```
┌─────────────────────────────────────────────────────────────────┐
│                   MATCHING FLOW                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AUTO DISCOVERY                                                 │
│  ──────────────                                                 │
│  1. Embed market descriptions (title + details)                 │
│  2. Vector similarity search across platforms                   │
│  3. Filter by category, expiration proximity                    │
│  4. Score confidence based on:                                  │
│     - Text similarity (0.4 weight)                              │
│     - Category match (0.2 weight)                               │
│     - Expiration proximity (0.2 weight)                         │
│     - Historical price correlation (0.2 weight)                 │
│                                                                 │
│  CONFIDENCE THRESHOLDS                                          │
│  ─────────────────────                                          │
│  > 0.95: Auto-confirm as equivalent                             │
│  > 0.80: Suggest to user for confirmation                       │
│  > 0.60: Flag as potentially correlated                         │
│  < 0.60: Ignore                                                 │
│                                                                 │
│  USER OVERRIDE                                                  │
│  ─────────────                                                  │
│  • Can reject any auto-match                                    │
│  • Can create manual pairs AI missed                            │
│  • Can adjust correlation assumptions                           │
│  • Can define custom relationship types                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Strategy Object Model

### Strategy Definition

The Strategy object is the core primitive for arbitrage execution:

```python
@dataclass
class Strategy:
    # Identity
    id: str                              # "strat_xxx"
    name: str                            # Human-readable name
    strategy_type: str                   # "calendar_spread" | "price_discrepancy" | "hedge"
    status: StrategyStatus               # Lifecycle state

    # Market Legs
    legs: List[StrategyLeg]              # 2+ legs for multi-leg strategies
    pair_id: Optional[str]               # Reference to MarketPair if applicable

    # Position Sizing
    sizing: PositionSizing

    # Entry Conditions
    entry: EntryConditions

    # Exit Conditions
    exit: ExitConditions

    # Risk Parameters
    risk: RiskParameters

    # Execution State
    execution: ExecutionState

    # Metadata
    metadata: StrategyMetadata

class StrategyStatus(Enum):
    PROPOSED = "proposed"                # AI/user created, awaiting confirmation
    CONFIRMED = "confirmed"              # Approved, ready to execute
    EXECUTING = "executing"              # Orders being placed
    ACTIVE = "active"                    # Fully entered, monitoring
    CLOSING = "closing"                  # Exit in progress
    CLOSED = "closed"                    # Fully exited
    CANCELLED = "cancelled"              # Aborted before completion
    REJECTED = "rejected"                # User declined proposal

@dataclass
class StrategyLeg:
    leg_id: str                          # "leg_a", "leg_b", etc.
    platform: str
    market_id: str
    native_market_id: str
    outcome: str                         # YES/NO
    direction: str                       # "BUY" | "SELL"
    target_price: float
    current_price: float
    size_contracts: int
    size_usd: float

@dataclass
class PositionSizing:
    size_mode: str                       # "fixed_usd" | "fixed_contracts" | "kelly" | "custom"
    base_size_usd: float
    max_size_usd: float
    scale_in: bool                       # Enter in multiple tranches
    num_tranches: int

@dataclass
class EntryConditions:
    spread_threshold: float              # Minimum spread to enter
    min_liquidity_usd: float             # Per leg
    max_slippage_pct: float
    entry_mode: str                      # "simultaneous" | "leg_into"

@dataclass
class ExitConditions:
    profit_target_spread: float          # Exit when spread narrows to this
    stop_loss_spread: float              # Exit if spread widens to this
    time_exit_hours: Optional[int]       # Exit N hours before first expiration
    exit_mode: str                       # "simultaneous" | "leg_out"

@dataclass
class RiskParameters:
    max_loss_usd: float
    correlation_assumption: float        # Expected correlation (1.0 for equivalent)
    settlement_risk_buffer: float        # Buffer for settlement timing differences

@dataclass
class ExecutionState:
    orders: List[str]                    # Order IDs
    fills: List[Fill]                    # Fill records
    avg_entry_spread: Optional[float]
    current_spread: Optional[float]
    current_pnl_usd: float
    entry_time: Optional[datetime]

@dataclass
class StrategyMetadata:
    created_by: str                      # "ai_scanner" | "manual"
    created_at: datetime
    hypothesis: str                      # Why this trade makes sense
    confidence_score: float              # AI confidence
    tags: List[str]
    outcome: Optional[str]               # Filled after close: "profit" | "loss" | "breakeven"
    outcome_pnl: Optional[float]
```

### Execution Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                   EXECUTION MODES                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  STRICT (Default)                                               │
│  ────────────────                                               │
│  • Both legs must fill within 5 seconds                         │
│  • Auto-cancel unfilled leg if timeout exceeded                 │
│  • No partial position risk                                     │
│  • Best for: High-liquidity equivalent markets                  │
│                                                                 │
│  TOLERANT                                                       │
│  ────────                                                       │
│  • Allow up to 30 seconds for second leg                        │
│  • Alert if price moves > 2% while waiting                      │
│  • User decides to proceed or abort                             │
│  • Best for: Medium-liquidity markets                           │
│                                                                 │
│  LEGGED                                                         │
│  ──────                                                         │
│  • Explicitly allow sequential entry                            │
│  • Manual confirmation between legs                             │
│  • Best for: Illiquid markets, complex strategies               │
│                                                                 │
│  MANUAL                                                         │
│  ──────                                                         │
│  • System proposes, you execute each leg                        │
│  • Full control over timing and prices                          │
│  • Best for: Learning, unusual situations                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Strategy Lifecycle

```
                              ┌──────────┐
          User/AI creates     │ PROPOSED │
                              └────┬─────┘
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
        ┌──────────┐        ┌───────────┐        ┌──────────┐
        │ REJECTED │        │ CONFIRMED │        │ (modify) │
        └──────────┘        └─────┬─────┘        └──────────┘
                                  │
                                  ▼
                           ┌───────────┐
              execute()    │ EXECUTING │
                           └─────┬─────┘
                                 │
                    ┌────────────┼────────────┐
                    │            │            │
                    ▼            ▼            ▼
             ┌───────────┐ ┌──────────┐ ┌───────────┐
             │  ACTIVE   │ │ timeout/ │ │ CANCELLED │
             │           │ │ partial  │ └───────────┘
             └─────┬─────┘ └──────────┘
                   │
      exit conditions triggered
                   │
                   ▼
             ┌───────────┐
             │  CLOSING  │
             └─────┬─────┘
                   │
                   ▼
             ┌───────────┐
             │  CLOSED   │
             └───────────┘
```

---

## 8. Data Storage Architecture

### Redis Stack Components

```
┌─────────────────────────────────────────────────────────────────┐
│                      REDIS STACK                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RedisJSON                         RedisTimeSeries              │
│  ─────────                         ───────────────              │
│  • Strategies                      • Price ticks                │
│  • Market pairs                    • Spread history             │
│  • Orders/Positions                • Volume data                │
│  • Platform configs                • P&L snapshots              │
│  • Opportunity queue               • Latency metrics            │
│                                                                 │
│  RediSearch                        Redis Streams                │
│  ───────────                       ─────────────                │
│  • Market full-text search         • Order events               │
│  • Vector similarity (AI)          • Fill notifications         │
│  • Fuzzy market matching           • Price alerts               │
│  • Strategy lookup                 • Audit log                  │
│                                                                 │
│  Redis Pub/Sub                     Core Redis                   │
│  ─────────────                     ──────────                   │
│  • Real-time price feeds           • Session state              │
│  • Opportunity alerts              • Rate limit counters        │
│  • Execution status                • Locks (order dedup)        │
│  • WebSocket fan-out               • Cache (API responses)      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Schema

```
STRATEGIES
──────────
strategy:{id}              → JSON document (full strategy)
strategy:index             → RediSearch index
strategies:active          → SET of active strategy IDs
strategies:proposed        → SET of pending approval
strategies:by_pair:{pair}  → SET of strategies for a pair

MARKET PAIRS
────────────
pair:{id}                  → JSON document (pair definition)
pair:index                 → RediSearch index (for matching)
pairs:active               → SET of monitored pair IDs
pairs:by_type:{type}       → SET (equivalent/calendar/correlated)

MARKETS (Cached/Normalized)
────────────────────────────
market:{platform}:{id}     → JSON (normalized market data)
market:index               → RediSearch index (full-text)
market:embeddings          → Vector index (AI similarity)

PRICES (Time Series)
─────────────────────
price:{platform}:{market}:{outcome}
                           → TimeSeries (bid, ask, last)
spread:{pair_id}           → TimeSeries (spread over time)

ORDERS & POSITIONS
──────────────────
order:{platform}:{id}      → JSON (order state)
orders:open:{platform}     → SET of open order IDs
position:{platform}:{market}
                           → JSON (current position)

OPPORTUNITIES
─────────────
opportunity:{id}           → JSON (detected opportunity)
opportunities:queue        → SORTED SET (by score/edge)
opportunities:stream       → STREAM (real-time detections)

REAL-TIME
─────────
sub:{platform}:{market}    → Pub/Sub channel
alert:{pair_id}            → Pub/Sub channel
ws:connections             → SET of active WS clients

AI / VECTORS
────────────
embedding:market:{id}      → Vector (market description)
embedding:strategy:{id}    → Vector (strategy hypothesis)
ai:index                   → RediSearch vector index

SYSTEM
──────
ratelimit:{platform}:{endpoint}
                           → Token bucket state
lock:order:{id}            → Distributed lock
config:platforms           → JSON (enabled platforms)
health:{platform}          → Last health check result
```

### Vector Store for AI

```python
# Create vector index for market matching
FT.CREATE market:vectors
  ON JSON
  PREFIX 1 market:
  SCHEMA
    $.title AS title TEXT
    $.platform AS platform TAG
    $.category AS category TAG
    $.embedding AS embedding VECTOR FLAT 6
      TYPE FLOAT32
      DIM 1536          # OpenAI embedding size
      DISTANCE_METRIC COSINE

# Search for similar markets
FT.SEARCH market:vectors
  "(@platform:{kalshi})=>[KNN 5 @embedding $query_vec AS score]"
  PARAMS 2 query_vec <binary_vector>
  SORTBY score
  RETURN 4 title platform category score
```

### AI Vector Use Cases

1. **Market Matching**: Embed descriptions → find similar markets across platforms
2. **Opportunity Similarity**: Find setups similar to past successful trades
3. **Hypothesis Search**: Search strategies by reasoning/hypothesis
4. **Correlation Discovery**: Find markets that move together but aren't paired

---

## 9. AI Agent Integration

### Architecture

The AI Agent runs as a separate container, connecting to the MCP server as a client:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI AGENT CONTAINER                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   MCP CLIENT                             │   │
│  │  • Connects to MCP Server                                │   │
│  │  • Calls same tools as human operator                    │   │
│  │  • Subject to same safety limits                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                OPPORTUNITY SCANNER                       │   │
│  │  • Monitors all active market pairs                      │   │
│  │  • Subscribes to price feeds via MCP                     │   │
│  │  • Detects when spread exceeds threshold                 │   │
│  │  • Checks liquidity and execution feasibility            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               STRATEGY GENERATOR                         │   │
│  │  • Creates strategy proposals from opportunities         │   │
│  │  • Calculates optimal sizing (Kelly, etc.)               │   │
│  │  • Generates hypothesis/reasoning                        │   │
│  │  • Writes to Redis for human review                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   LLM BRAIN                              │   │
│  │  • Claude API for reasoning                              │   │
│  │  • Evaluates opportunity quality                         │   │
│  │  • Generates hypotheses                                  │   │
│  │  • Learns from trade outcomes                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why This Architecture

| Benefit | Explanation |
|---------|-------------|
| **Single Interface** | AI uses same MCP tools as human - no special APIs |
| **Safety Enforcement** | MCP server enforces limits - AI cannot bypass |
| **Independent Scaling** | Restart/upgrade AI without affecting MCP server |
| **Human Override** | You can always intervene via same interface |
| **Audit Trail** | All AI actions logged through MCP |
| **Gradual Autonomy** | Start read-only, increase permissions over time |

### AI Agent Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                   AI AGENT OPERATING MODES                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OBSERVER MODE                                                  │
│  ─────────────                                                  │
│  • Monitors markets and pairs                                   │
│  • Logs detected opportunities                                  │
│  • No proposals, no actions                                     │
│  • Use for: Initial testing, learning market patterns           │
│                                                                 │
│  ADVISOR MODE                                                   │
│  ────────────                                                   │
│  • Creates opportunity proposals                                │
│  • Writes to Redis queue for review                             │
│  • Sends alerts via configured channels                         │
│  • No execution capability                                      │
│  • Use for: Human-in-the-loop operation                         │
│                                                                 │
│  SEMI-AUTONOMOUS MODE                                           │
│  ─────────────────────                                          │
│  • Auto-executes under configured thresholds                    │
│  • Large opportunities require human confirmation               │
│  • Daily/weekly autonomous limits                               │
│  • Use for: Trusted setups, small position sizes                │
│                                                                 │
│  AUTONOMOUS MODE                                                │
│  ───────────────                                                │
│  • Full execution capability                                    │
│  • Still subject to safety limits                               │
│  • All actions logged                                           │
│  • Use for: Proven strategies, mature system                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 10. Permission Model

### Operator Types

| Operator | Description |
|----------|-------------|
| `human` | Full access to all tools and confirmations |
| `ai_agent` | Restricted based on permission level configuration |

### AI Permission Levels

```
┌─────────────────────────────────────────────────────────────────┐
│                AI AGENT PERMISSION LEVELS                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Level 0: READ_ONLY                                             │
│  ─────────────────                                              │
│  ✓ Market discovery & analysis tools                            │
│  ✓ Price monitoring                                             │
│  ✓ Read strategies and pairs                                    │
│  ✗ Cannot create opportunities/strategies                       │
│  ✗ Cannot place any orders                                      │
│                                                                 │
│  Level 1: PROPOSE_ONLY                                          │
│  ──────────────────────                                         │
│  ✓ Everything in Level 0                                        │
│  ✓ Create market pairs (suggested)                              │
│  ✓ Create strategy proposals (status: proposed)                 │
│  ✓ Create opportunity alerts                                    │
│  ✗ Cannot confirm strategies                                    │
│  ✗ Cannot execute trades                                        │
│                                                                 │
│  Level 2: LIMITED_AUTONOMOUS                                    │
│  ───────────────────────────                                    │
│  ✓ Everything in Level 1                                        │
│  ✓ Auto-confirm strategies under $X threshold                   │
│  ✓ Execute confirmed strategies                                 │
│  ✓ Cancel own strategies                                        │
│  ✗ Strategies over threshold require human confirmation         │
│  ✗ Subject to daily autonomous limit                            │
│                                                                 │
│  Level 3: FULL_AUTONOMOUS                                       │
│  ─────────────────────────                                      │
│  ✓ Full trading capability                                      │
│  ✓ Can confirm any strategy within safety limits                │
│  ✓ All platform tools available                                 │
│  ✗ Still subject to global safety limits                        │
│  ✗ All actions logged for audit                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Safety Limits (Enforced at MCP Layer)

```yaml
safety_limits:
  # Per-order limits
  max_order_size_usd: 1000
  max_order_size_contracts: 10000

  # Portfolio limits
  max_total_exposure_usd: 10000
  max_position_per_market_usd: 2000
  max_open_orders: 50

  # Execution limits
  max_slippage_pct: 2.0
  min_liquidity_usd: 5000
  max_spread_pct: 5.0

  # Strategy limits
  max_strategy_legs: 4
  max_active_strategies: 20

  # AI-specific limits
  ai_daily_autonomous_limit_usd: 500
  ai_max_single_trade_usd: 100
  ai_require_human_for:
    - new_market_pairs
    - strategies_over_500_usd
    - correlated_pair_trades
    - first_trade_on_new_pair
```

---

## 11. Configuration

### Environment Variables

```bash
# ═══════════════════════════════════════════════════
# REDIS
# ═══════════════════════════════════════════════════
REDIS_URL=redis://localhost:6379

# ═══════════════════════════════════════════════════
# POLYMARKET
# ═══════════════════════════════════════════════════
POLYMARKET_ENABLED=true
POLYMARKET_MODE=full                    # full | read_only | disabled

# Wallet (L1 Auth)
POLYGON_PRIVATE_KEY=<your_private_key>
POLYGON_ADDRESS=0x<your_address>
POLYMARKET_CHAIN_ID=137                 # Polygon mainnet

# API Credentials (L2 Auth - optional, auto-generated if not provided)
POLYMARKET_API_KEY=<optional>
POLYMARKET_API_SECRET=<optional>
POLYMARKET_PASSPHRASE=<optional>

# Endpoints
POLYMARKET_CLOB_URL=https://clob.polymarket.com
POLYMARKET_GAMMA_URL=https://gamma-api.polymarket.com

# ═══════════════════════════════════════════════════
# KALSHI
# ═══════════════════════════════════════════════════
KALSHI_ENABLED=true
KALSHI_MODE=full                        # full | read_only | disabled

# Authentication
KALSHI_EMAIL=<your_email>
KALSHI_API_KEY_ID=<your_api_key_id>
KALSHI_PRIVATE_KEY_PATH=/secrets/kalshi_rsa.pem

# Endpoints
KALSHI_API_URL=https://trading-api.kalshi.com/trade-api/v2
KALSHI_WS_URL=wss://trading-api.kalshi.com/trade-api/ws/v2

# Demo mode (for testing)
KALSHI_USE_DEMO=false
KALSHI_DEMO_URL=https://demo-api.kalshi.co/trade-api/v2

# ═══════════════════════════════════════════════════
# ARBITRAGE
# ═══════════════════════════════════════════════════
ARBITRAGE_ENABLED=true
DEFAULT_EXECUTION_MODE=strict           # strict | tolerant | legged | manual
STRATEGY_TIMEOUT_SECONDS=5              # For strict mode

# ═══════════════════════════════════════════════════
# SAFETY LIMITS
# ═══════════════════════════════════════════════════
MAX_ORDER_SIZE_USD=1000
MAX_TOTAL_EXPOSURE_USD=10000
MAX_POSITION_PER_MARKET_USD=2000
MIN_LIQUIDITY_USD=5000
MAX_SPREAD_PCT=5.0
MAX_SLIPPAGE_PCT=2.0

# ═══════════════════════════════════════════════════
# AI AGENT (if enabled)
# ═══════════════════════════════════════════════════
AI_AGENT_ENABLED=false
AI_PERMISSION_LEVEL=PROPOSE_ONLY        # READ_ONLY | PROPOSE_ONLY | LIMITED_AUTONOMOUS | FULL_AUTONOMOUS
AI_AUTO_CONFIRM_BELOW_USD=0
AI_DAILY_AUTONOMOUS_LIMIT_USD=500
AI_MODEL=claude-sonnet-4-20250514
ANTHROPIC_API_KEY=<your_api_key>

# ═══════════════════════════════════════════════════
# EMBEDDING MODEL (for market matching)
# ═══════════════════════════════════════════════════
EMBEDDING_MODEL=openai                  # openai | local
OPENAI_API_KEY=<your_api_key>           # If using OpenAI
EMBEDDING_DIMENSION=1536

# ═══════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════
LOG_LEVEL=INFO
LOG_FORMAT=json                         # json | text
```

### Docker Compose

```yaml
version: '3.8'

services:
  # ═══════════════════════════════════════════════════
  # DATA LAYER
  # ═══════════════════════════════════════════════════
  redis:
    image: redis/redis-stack:latest
    container_name: prediction-redis
    ports:
      - "6379:6379"
      - "8001:8001"     # RedisInsight UI
    volumes:
      - redis_data:/data
    environment:
      - REDIS_ARGS=--appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ═══════════════════════════════════════════════════
  # MCP SERVER
  # ═══════════════════════════════════════════════════
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.mcp
    container_name: prediction-mcp
    depends_on:
      redis:
        condition: service_healthy
    ports:
      - "3000:3000"     # MCP protocol (stdio or HTTP)
      - "8080:8080"     # Web dashboard
    env_file:
      - .env
    environment:
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./secrets:/secrets:ro
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # ═══════════════════════════════════════════════════
  # AI AGENT (Optional)
  # ═══════════════════════════════════════════════════
  ai-agent:
    build:
      context: .
      dockerfile: Dockerfile.agent
    container_name: prediction-ai
    depends_on:
      mcp-server:
        condition: service_healthy
      redis:
        condition: service_healthy
    env_file:
      - .env
    environment:
      - MCP_SERVER_URL=http://mcp-server:3000
      - REDIS_URL=redis://redis:6379
    profiles:
      - with-ai    # docker compose --profile with-ai up

volumes:
  redis_data:
```

### Claude Desktop Configuration

```json
{
  "mcpServers": {
    "prediction-markets": {
      "command": "docker",
      "args": [
        "exec", "-i", "prediction-mcp",
        "python", "-m", "prediction_mcp.server"
      ],
      "env": {}
    }
  }
}
```

Or for direct execution (non-Docker):

```json
{
  "mcpServers": {
    "prediction-markets": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "prediction_mcp.server"],
      "cwd": "/path/to/prediction-mcp-server",
      "env": {
        "REDIS_URL": "redis://localhost:6379",
        "POLYMARKET_ENABLED": "true",
        "KALSHI_ENABLED": "true",
        "POLYGON_PRIVATE_KEY": "your_key",
        "POLYGON_ADDRESS": "0xYourAddress",
        "KALSHI_EMAIL": "your_email",
        "KALSHI_API_KEY_ID": "your_key_id",
        "KALSHI_PRIVATE_KEY_PATH": "/path/to/kalshi_rsa.pem"
      }
    }
  }
}
```

---

## 12. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal:** Establish multi-platform architecture and Kalshi integration

- [ ] Refactor project structure for multi-platform support
- [ ] Create platform adapter interface
- [ ] Implement Kalshi authentication (RSA-PSS signing)
- [ ] Implement Kalshi REST client
- [ ] Port core Kalshi tools (market discovery, basic trading)
- [ ] Set up Redis Stack integration
- [ ] Update configuration system for multi-platform

**Deliverables:**
- Working Kalshi authentication
- 15-20 Kalshi tools operational
- Redis persistence for basic state

### Phase 2: Kalshi Parity (Weeks 3-4)

**Goal:** Complete Kalshi toolset to match Polymarket capabilities

- [ ] Complete all 52 Kalshi tools
- [ ] Implement Kalshi WebSocket client
- [ ] Add real-time subscription tools
- [ ] Implement AI analysis tools for Kalshi
- [ ] Add event/series hierarchy tools
- [ ] Write comprehensive tests

**Deliverables:**
- Full Kalshi tool parity
- Real-time price feeds working
- Event hierarchy fully exposed

### Phase 3: Cross-Platform (Weeks 5-6)

**Goal:** Enable cross-platform research and market matching

- [ ] Implement normalized data models
- [ ] Build market embedding pipeline
- [ ] Implement vector similarity search
- [ ] Create cross-platform search tools
- [ ] Build market pair management
- [ ] Implement auto-matching with confidence scores

**Deliverables:**
- 8 cross-platform tools working
- Market pairing system operational
- Vector search for market matching

### Phase 4: Arbitrage Engine (Weeks 7-8)

**Goal:** Full arbitrage detection and strategy execution

- [ ] Implement Strategy object model
- [ ] Build opportunity scanner
- [ ] Create strategy management tools
- [ ] Implement multi-leg execution engine
- [ ] Add execution modes (strict, tolerant, etc.)
- [ ] Build monitoring and alerting

**Deliverables:**
- 15 arbitrage tools working
- Strategy lifecycle complete
- Multi-leg execution operational

### Phase 5: AI Agent Foundation (Weeks 9-10)

**Goal:** Prepare architecture for autonomous AI agent

- [ ] Define AI agent interface
- [ ] Implement permission model
- [ ] Build proposal/confirmation workflow
- [ ] Create audit logging
- [ ] Document AI integration points
- [ ] Build basic scanner agent (advisor mode)

**Deliverables:**
- Permission system enforced
- AI agent container template
- Basic scanner operational in advisor mode

### Phase 6: Polish & Production (Weeks 11-12)

**Goal:** Production-ready release

- [ ] Performance optimization
- [ ] Error handling improvements
- [ ] Documentation completion
- [ ] Docker production configuration
- [ ] Monitoring and observability
- [ ] Security audit

**Deliverables:**
- Production-ready Docker stack
- Complete documentation
- Deployment guide

---

## Appendix A: API Reference Links

- **Polymarket CLOB API:** https://docs.polymarket.com
- **Kalshi Trading API:** https://trading-api.kalshi.com/docs
- **Redis Stack:** https://redis.io/docs/stack/
- **MCP Protocol:** https://modelcontextprotocol.io

## Appendix B: Related Documents

- `TOOLS_REFERENCE.md` - Detailed tool documentation
- `TRADING_ARCHITECTURE.md` - Existing Polymarket architecture
- `WEBSOCKET_INTEGRATION.md` - Real-time data setup

---

*Document Version: 1.0*
*Last Updated: 2025-01-20*
