from sqlalchemy import Integer, String, Float, Boolean, DateTime, Enum
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base import Base
from datetime import datetime, timezone


class CycleStatus(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class TradeCycleLog(Base):
    __tablename__ = "trade_cycle_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    agent_name: Mapped[str] = mapped_column(String, nullable=False)
    invoked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    cycle_duration_ms: Mapped[int] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False)  # "SUCCESS" or "FAILED"
    error_message: Mapped[str] = mapped_column(String, nullable=True)  # null if SUCCESS

    # Decision
    decision: Mapped[str] = mapped_column(String, nullable=True)  # null if FAILED
    reasoning: Mapped[str] = mapped_column(String, nullable=True)  # null if FAILED
    base_amount: Mapped[float] = mapped_column(Float, nullable=True)

    # Market Context — null if cycle failed before fetching
    current_price: Mapped[float] = mapped_column(Float, nullable=True)
    ema12: Mapped[float] = mapped_column(Float, nullable=True)
    ema26: Mapped[float] = mapped_column(Float, nullable=True)
    macd: Mapped[float] = mapped_column(Float, nullable=True)
    rsi: Mapped[float] = mapped_column(Float, nullable=True)
    funding_rate: Mapped[float] = mapped_column(Float, nullable=True)

    # Account Context — null if cycle failed before fetching
    available_balance: Mapped[float] = mapped_column(Float, nullable=True)
    collateral: Mapped[float] = mapped_column(Float, nullable=True)

    # Position at time of decision
    had_open_position: Mapped[bool] = mapped_column(Boolean, nullable=True)
    position_side: Mapped[str] = mapped_column(String, nullable=True)
    position_entry_price: Mapped[float] = mapped_column(Float, nullable=True)
    position_value: Mapped[float] = mapped_column(Float, nullable=True)
    unrealized_pnl: Mapped[float] = mapped_column(Float, nullable=True)
    invocation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
