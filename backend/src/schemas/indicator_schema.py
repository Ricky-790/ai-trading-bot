from pydantic import BaseModel, Field
from enum import Enum
from typing import List
from lighter.models.account_position import AccountPosition
from lighter.models.account_asset import AccountAsset


class ResolutionEnum(Enum):
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    ONE_HOUR = "1h"
    FOUR_HOUR = "4h"


class MarketContext(BaseModel):
    current_price: float = Field(default=0.0, description="The current price")
    mid_prices: List[float] = Field(default=[], description="The list of mid prices")
    ema12: float = Field(default=0.0, description="The 12-period EMA")
    ema26: float = Field(default=0.0, description="The 26-period EMA")
    macd: float = Field(default=0.0, description="The MACD value")
    rsi: float = Field(default=0.0, description="The RSI value")
    funding_rate: float = Field(default=0.0, description="The funding rate")


# class IndicatorContext(MarketContext):
#     account_balance: float = Field(default=0.0, description="The account balance")
#     collateral: float = Field(default=0.0, description="The collateral amount")
#     account_positions: List[AccountPosition] = Field(
#         default_factory=list, description="Current active positions"
#     )
