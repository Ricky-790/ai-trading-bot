from src.agents.agent_manager import AgentManager
from src.agents.gpt_agent import GPT_agent
from src.agents.nemotron_agent import NEMOTRON_agent
from src.services.trading_service import TradingService
from src.services.indicators_service import indicators_service
from src.models.trade_cycle_log import CycleStatus
from src.services.cycle_log_service import insert_cycle_log
from src.logger_config import logger
import asyncio
import os
import time
import traceback
from dotenv import load_dotenv

load_dotenv()

# Create the trading agents
private_key_index: int = os.getenv("PRIV_KEY_INDEX")

# GPT agent

gpt_account_index: int = os.getenv("GPT_LIGHTER_ACCOUNT_INDEX")
gpt_private_key: dict = {private_key_index: os.getenv("GPT_PRIVATE_KEY")}
gpt_trader = AgentManager(
    GPT_agent,
    TradingService(
        name="GPT-OSS-120b",
        account_index=gpt_account_index,
        private_key=gpt_private_key,
    ),
)

# Nemotron agent
nemotron_account_index: int = os.getenv("NEMOTRON_LIGHTER_ACCOUNT_INDEX")
nemotron_private_key: dict = {private_key_index: os.getenv("NEMOTRON_PRIVATE_KEY")}
nemo_trader = AgentManager(
    NEMOTRON_agent,
    TradingService(
        name="Nemotron-OSS-24B",
        account_index=nemotron_account_index,
        private_key=nemotron_private_key,
    ),
)

# EXECUTION CYCLE
count = 0
CYCLE_INTERVAL_SECONDS = 300
RETRY_INTERVAL_SECONDS = 5


async def main():
    global RETRY_COUNT
    RETRY_COUNT = 0
    while True:
        try:
            logger.info(f"Starting Cycle {count + 1}")
            # set start time
            start_time = time.time()
            res = await indicators_service.fetch_market_context()
            if res["success"]:
                logger.info("Starting Agents")
            await asyncio.gather(
                gpt_trader.run(start_time=start_time),
                nemo_trader.run(start_time=start_time),
            )
            logger.info(f"Cycle complete. Sleeping {CYCLE_INTERVAL_SECONDS}s...")
            RETRY_COUNT = 0
            await asyncio.sleep(CYCLE_INTERVAL_SECONDS)

        except Exception as e:
            RETRY_COUNT += 1
            if RETRY_COUNT > 3:
                logger.error("Max retries reached. Exiting...")
                break
            traceback_str = traceback.format_exc()
            logger.error(f"Cycle failed: {traceback_str}")
            logger.error(f"Retrying in {RETRY_INTERVAL_SECONDS}s...")
            await asyncio.sleep(RETRY_INTERVAL_SECONDS)


if __name__ == "__main__":
    asyncio.run(main())
