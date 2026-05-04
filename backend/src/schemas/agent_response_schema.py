from pydantic import BaseModel, Field
from typing import Literal, Optional


class TradeSchema(BaseModel):
    base_amount: float = Field(..., description="Amount of BTC to trade", gt=0.0)


class AgentResponse(BaseModel):
    decision: Literal[
        "OPEN_LONG", "OPEN_SHORT", "CLOSE_LONG", "CLOSE_SHORT", "HOLD"
    ] = Field(..., description="The trading decision")
    reasoning: str = Field(..., description="Reasoning behind the decision")
    trade: Optional[TradeSchema] = Field(
        default=None,
        description="Required when decision is not HOLD. Null when decision is HOLD.",
    )
