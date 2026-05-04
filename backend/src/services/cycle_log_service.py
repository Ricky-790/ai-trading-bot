from src.models.session import get_session
from src.models.trade_cycle_log import TradeCycleLog, CycleStatus
from src.schemas.indicator_schema import MarketContext
from src.schemas.account_context_schema import AccountContext
from datetime import datetime, timezone
from sqlalchemy import select, func


async def insert_cycle_log(
    agent_name: str,
    status: str,
    invocation_count: int,
    cycle_duration_ms: int | None = None,
    error_message: str | None = None,
    decision: str | None = None,
    reasoning: str | None = None,
    base_amount: float | None = None,
    market_ctx: MarketContext | None = None,
    account_ctx: AccountContext | None = None,
):
    open_position = (
        account_ctx.open_positions[0]
        if account_ctx and account_ctx.open_positions
        else None
    )

    log = TradeCycleLog(
        agent_name=agent_name,
        invoked_at=datetime.now(timezone.utc),
        cycle_duration_ms=cycle_duration_ms,
        status=status,
        error_message=error_message,
        decision=decision,
        reasoning=reasoning,
        base_amount=base_amount,
        invocation_count=invocation_count,
        # Market context
        current_price=market_ctx.current_price if market_ctx else None,
        ema12=market_ctx.ema12 if market_ctx else None,
        ema26=market_ctx.ema26 if market_ctx else None,
        macd=market_ctx.macd if market_ctx else None,
        rsi=market_ctx.rsi if market_ctx else None,
        funding_rate=market_ctx.funding_rate if market_ctx else None,
        # Account context
        available_balance=account_ctx.available_balance if account_ctx else None,
        collateral=account_ctx.collateral if account_ctx else None,
        # Position
        had_open_position=open_position is not None,
        position_side=open_position.sign.value if open_position else None,
        position_entry_price=(
            float(open_position.avg_entry_price) if open_position else None
        ),
        position_value=float(open_position.position_value) if open_position else None,
        unrealized_pnl=float(open_position.unrealized_pnl) if open_position else None,
    )

    async with get_session() as session:
        session.add(log)


async def get_invocation_count(agent_name: str) -> int:
    async with get_session() as session:
        result = await session.execute(
            select(func.count()).where(TradeCycleLog.agent_name == agent_name)
        )
        return result.scalar() or 0
