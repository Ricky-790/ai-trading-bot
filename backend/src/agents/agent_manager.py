from pydantic_ai import Agent
from pydantic_ai.models.openrouter import OpenRouterModel, OpenRouterModelSettings
import asyncio
from dotenv import load_dotenv
from src.services.trading_service import TradingService
from src.schemas.agent_response_schema import AgentResponse
from dotenv import load_dotenv
import os
import time
from src.logger_config import logger
from src.services.cycle_log_service import insert_cycle_log
from src.models.trade_cycle_log import CycleStatus

load_dotenv()


class AgentManager:
    def __init__(self, agent: Agent, trading_service: TradingService):
        self.agent = agent
        self.trading_service = trading_service

    async def get_market_data(self) -> str:
        logger.info("Fetching market data...")
        return await self.trading_service.get_market_summary_prompt()

    async def invoke_agent(self):
        market_data = await self.get_market_data()
        logger.info("Invoking agent...")
        response = await self.agent.run(market_data)
        logger.info("Agent invoked successfully")
        return response.output

    async def execute_decision(self, response: AgentResponse):
        if response.decision == "HOLD":
            logger.info(
                f"{self.trading_service.name} Agent: Decision is HOLD. No trade will be executed."
            )
        else:
            logger.info(
                f"{self.trading_service.name} Agent: Decision is {response.decision}. Executing trade for {response.trade.base_amount} BTC"
            )
            response = await self.trading_service.execute_trade(response)

    async def log_cycle(self, response: AgentResponse):
        # invocation_count = await get_invocation_count()
        market_ctx, account_ctx = self.trading_service.get_cached_contexts()
        await insert_cycle_log(
            agent_name=self.trading_service.name,
            status=CycleStatus.SUCCESS,
            invocation_count=self.trading_service.invocation_count,
            cycle_duration_ms=time.time() - self.start_time,
            decision=response.decision,
            reasoning=response.reasoning,
            base_amount=response.trade.base_amount if response.trade else None,
            market_ctx=market_ctx,
            account_ctx=account_ctx,
        )

    async def run(self, start_time: float):
        try:
            self.start_time = start_time
            agent_response = await self.invoke_agent()
            execute_response = await self.execute_decision(agent_response)
            logger.info(f"Creating new log")
            await self.log_cycle(agent_response)
            logger.info("Log created successfully")
        except Exception as e:
            logger.error(f"Cycle failed: {str(e)}")
            await insert_cycle_log(
                agent_name=self.trading_service.name,
                status=CycleStatus.FAILED,
                invocation_count=self.trading_service.invocation_count,
                error_message=str(e),
            )

        # return response
