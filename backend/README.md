# AI Trading Arena
(Inspired from nof1.ai)

A multi-agent AI trading bot. Each agent trades BTC/USDC perpetual futures on [Lighter](https://lighter.xyz) using real market data, technical indicators, and its own reasoning to make trading decisions every few minutes.

> Using the Lighter testnet for this project is recommended rather than actual money.

## How It Works

- Multiple LLM agents (e.g. GPT, Claude, Gemini) each operate on their own Lighter sub-account
- Every cycle, market data is fetched once and shared across all agents
- Each agent receives technical indicators (EMA, MACD, RSI, funding rate) and its own account state
- The LLM returns a structured decision: `OPEN_LONG`, `OPEN_SHORT`, `CLOSE_LONG`, `CLOSE_SHORT`, or `HOLD`
- Trades are executed via the Lighter SDK, and every cycle is logged to a PostgreSQL database
- Currently supports **BTC/USDC perpetual futures only**, and only free open router models(`nvidia nemotron` and `gpt oss 120b`)

---

## Setup

### 1. Install dependencies

This project uses [uv](https://github.com/astral-sh/uv) for package management.

```bash
# Install uv if you don't have it
curl -Lsf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/Ricky-790/ai-trading-bot
cd ai-trading-bot/backend

# Install dependencies
uv sync
```

### 2. Configure environment variables

Create a `.env` file in the `backend/` directory according to the `.env.example` file and put your api keys.


### 3. Run database migrations

```bash
# Apply migrations
alembic upgrade head
```

### 4. Run the bot

```bash
uv run src/agents_runner.py
```

---

## Todos

- [ ] **Multi-market support** — enable agents to trade across multiple markets (ETH, SOL, etc.), not just BTC/USDC
- [ ] **Native tool calling** — let the LLM call trade functions directly via tool calling instead of returning structured arguments for the backend to execute
- [ ] **Indicator accuracy tests** — add unit tests to verify correctness of MACD, EMA, RSI and other indicator calculations
- [ ] **Frontend leaderboard** — build a React dashboard to visualize each agent's PnL, decisions, and performance over time
- [ ] **Stop loss / take profit** — allow agents to set automatic exit conditions when opening a position
- [ ] **Multi-market per agent** — allow a single agent to manage positions across multiple markets simultaneously