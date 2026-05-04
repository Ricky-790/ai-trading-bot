from pydantic import BaseModel, Field
from enum import Enum
from typing import List


class PositionSign(Enum):
    LONG = "long"
    SHORT = "short"

    @classmethod
    def from_sign(cls, sign: int) -> "PositionSign":
        return cls.LONG if sign == 1 else cls.SHORT


class PositionContext(BaseModel):
    initial_margin_fraction: float = Field(
        default=0.0, description="The initial margin fraction"
    )
    avg_entry_price: float = Field(default=0.0, description="The average entry price")
    position_value: float = Field(default=0.0, description="The position value")
    unrealized_pnl: float = Field(default=0.0, description="The unrealized PnL")
    realized_pnl: float = Field(default=0.0, description="The realized PnL")
    total_funding_paid_out: float = Field(
        default=0.0, description="The total funding paid out"
    )
    liquidation_price: float = Field(default=0.0, description="The liquidation price")
    sign: PositionSign = Field(
        default=PositionSign.LONG, description="Long or Short position"
    )


class AccountContext(BaseModel):
    available_balance: float = Field(
        default=0.0,
        description="The available balance: What can be used for new trades",
    )
    collateral: float = Field(
        default=0.0, description="The amount of collateral locked up for this position"
    )
    open_positions: List[PositionContext] = Field(
        default_factory=list, description="The open positions"
    )
