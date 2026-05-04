from lighter.models import Candle
from typing import List, Tuple
from src.services.accounts_service import accounts_service
from src.services.indicators_service import indicators_service
from src.schemas.indicator_schema import ResolutionEnum, MarketContext
from src.schemas.account_context_schema import (
    AccountContext,
    PositionContext,
    PositionSign,
)
from src.services.cycle_log_service import get_invocation_count
from src.schemas.agent_response_schema import AgentResponse
from src.constants.llm_prompts import PROMPT
from src.logger_config import logger


class TradingService:
    def __init__(self, name: str, account_index: int, private_key: dict):
        self.account_service = accounts_service
        self.indicators_service = indicators_service
        self.name = name
        self.account_index = account_index
        self.private_key = private_key
        self.decision_map = {
            "OPEN_LONG": {"is_ask": False, "reduce_only": False},
            "OPEN_SHORT": {"is_ask": True, "reduce_only": False},
            "CLOSE_LONG": {"is_ask": True, "reduce_only": True},
            "CLOSE_SHORT": {"is_ask": False, "reduce_only": True},
        }
        self.side_map = {
            "OPEN_LONG": "LONG",
            "OPEN_SHORT": "SHORT",
            "CLOSE_LONG": "LONG",
            "CLOSE_SHORT": "SHORT",
        }

    async def execute_trade(self, agent_response: AgentResponse):
        res = await self.account_service.create_position(
            account_index=self.account_index,
            private_key=self.private_key,
            side=self.side_map.get(agent_response.decision),
            base_amount=agent_response.trade.base_amount,
            is_ask=self.decision_map.get(agent_response.decision).get("is_ask"),
            reduce_only=self.decision_map.get(agent_response.decision).get(
                "reduce_only"
            ),
        )
        if res.get("success") == False:
            raise Exception(res.get("error"))
        logger.info(f"Trade executed successfully: {res}")

    def get_cached_contexts(self) -> Tuple[MarketContext, AccountContext]:
        market_ctx = self.indicators_service.get_market_context()
        account_ctx = self.account_context
        return (market_ctx, account_ctx)

    async def get_market_context(
        self,
    ) -> tuple[MarketContext, AccountContext, List[Candle], List[Candle]]:
        market_ctx: MarketContext = self.indicators_service.get_market_context()
        account_ctx: AccountContext = await self.account_service.get_account_context(
            self.account_index
        )
        # cache account_ctx to self for supplying to log later
        self.account_context = account_ctx

        four_hour_candles = await self.indicators_service.get_candles(
            resolution=ResolutionEnum.FOUR_HOUR
        )
        five_min_candles = await self.indicators_service.get_candles(
            resolution=ResolutionEnum.FIVE_MIN
        )
        return (
            market_ctx,
            account_ctx,
            four_hour_candles,
            five_min_candles,
        )

    async def set_invocation_count(self):
        self.invocation_count = await get_invocation_count(self.name)

    def build_prompt(
        self,
        market_ctx: MarketContext,
        account_ctx: AccountContext,
        four_hour_candles: List[Candle],
        five_min_candles: List[Candle],
        invocation_count: int,
    ) -> str:

        four_hour_summary = "\n".join(
            [
                f"  [{i+1}] O:{c.o:.2f} H:{c.h:.2f} L:{c.l:.2f} C:{c.c:.2f} Vol:{c.v}"
                for i, c in enumerate(four_hour_candles[-10:])
            ]
        )

        five_min_summary = "\n".join(
            [
                f"  [{i+1}] O:{c.o:.2f} H:{c.h:.2f} L:{c.l:.2f} C:{c.c:.2f} Vol:{c.v}"
                for i, c in enumerate(five_min_candles[-10:])
            ]
        )

        position_summary = (
            "No open position."
            if not account_ctx.open_positions
            else "\n".join(
                [
                    f"  Side: {p.sign.value.upper()} | Entry: ${p.avg_entry_price:.2f} | Value: ${p.position_value:.2f} | PnL: ${p.unrealized_pnl:.2f} | Liq: ${p.liquidation_price:.2f}"
                    for p in account_ctx.open_positions
                ]
            )
        )

        return PROMPT.format(
            invocation_count=invocation_count,
            current_price=f"{market_ctx.current_price:.2f}",
            ema12=f"{market_ctx.ema12:.2f}",
            ema26=f"{market_ctx.ema26:.2f}",
            ema_trend=(
                "EMA12 > EMA26 (Uptrend)"
                if market_ctx.ema12 > market_ctx.ema26
                else "EMA12 < EMA26 (Downtrend)"
            ),
            macd=f"{market_ctx.macd:.4f}",
            macd_trend=(
                "Bullish momentum" if market_ctx.macd > 0 else "Bearish momentum"
            ),
            rsi=f"{market_ctx.rsi:.2f}",
            rsi_trend=(
                "Overbought"
                if market_ctx.rsi > 70
                else "Oversold" if market_ctx.rsi < 30 else "Neutral"
            ),
            funding_rate=f"{market_ctx.funding_rate:.6f}",
            funding_rate_trend=(
                "Favors longs (shorts pay longs)"
                if market_ctx.funding_rate < 0
                else "Favors shorts (longs pay shorts)"
            ),
            four_hour_candles=four_hour_summary,
            five_min_candles=five_min_summary,
            available_balance=f"{account_ctx.available_balance:.2f}",
            collateral=f"{account_ctx.collateral:.2f}",
            max_position_size=f"{account_ctx.available_balance * 0.2:.2f}",
            position_summary=position_summary,
            btc_to_usd=f"{market_ctx.current_price * 0.001:.2f}",
        )

    async def get_market_summary_prompt(self):
        """
        Wrapper function to get total market summary as a prompt
        Args:
            None
        Returns:
            str: Market summary as a prompt
        """
        logger.info("Building market summary prompt...")
        market_ctx, acc_ctx, four_hour_candles, five_min_candles = (
            await self.get_market_context()
        )
        await self.set_invocation_count()
        market_summary = self.build_prompt(
            market_ctx,
            acc_ctx,
            four_hour_candles,
            five_min_candles,
            self.invocation_count,
        )
        logger.info("Market summary prompt built successfully")
        return market_summary
