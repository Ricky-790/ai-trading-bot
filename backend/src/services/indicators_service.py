import asyncio
import os
import time
from pprint import pprint
from typing import List, Tuple

import lighter
from dotenv import load_dotenv
from lighter.models.candle import Candle
from lighter.models.candles import Candles
from lighter.models.account_position import AccountPosition
from lighter.models.account_asset import AccountAsset
from lighter.rest import ApiException
from src.schemas.indicator_schema import ResolutionEnum, MarketContext
from src.logger_config import logger

load_dotenv()
BASE_URL: str = os.getenv("LIGHTER_BASE_URL", "https://testnet.zklighter.elliot.ai")
L1_ADDRESS: str = os.getenv("WALLET_PUB_KEY", "")


class IndicatorsService:
    def __init__(self):
        self.configuration = lighter.Configuration(host=BASE_URL)
        self.market_id = int(os.getenv("BITCOIN_MARKET_ID", 1))

    async def get_candles(
        self,
        num_candles: int = 50,
        resolution: ResolutionEnum = ResolutionEnum.FOUR_HOUR,
    ) -> List[Candle]:
        """
        Fetch candles data
        Args:
            num_candles (int): Number of candles to fetch
            resolution (ResolutionEnum): Resolution of candles
        Returns:
            List[Candle]: List of candles
        """
        async with lighter.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = lighter.CandlestickApi(api_client)
            market_id = self.market_id  # int |
            resolution = resolution  # str |
            start_timestamp = (
                int(time.time() - 60 * 60 * 24) * 1000
            )  # 24 hours ago in ms
            end_timestamp = int(time.time()) * 1000  # now in ms
            count_back = num_candles  # int |
            set_timestamp_to_end = False  # bool |  (optional) (default to False)

            try:
                # candles
                logger.info("Fetching candles data...")
                api_response = await api_instance.candles(
                    market_id,
                    resolution.value,
                    start_timestamp,
                    end_timestamp,
                    count_back,
                    set_timestamp_to_end=set_timestamp_to_end,
                )
                if api_response.code == 200:
                    logger.info(f"{len(api_response.c)} Candles fetched")
                    # print("The response of CandlestickApi->candles:\n")
                    return api_response.c
            except Exception as e:
                logger.error("Exception when calling CandlestickApi->candles: %s\n" % e)
                raise e

    def get_mid_prices(self, candles: List[Candle]) -> list[float]:
        """
        Get mid prices from candles data
        Args:
            candles (List[Candle]): List of candles
        Returns:
            List[float]: List of mid prices
        """
        mid_prices: List[float] = []
        for candle in candles:
            mid_prices.append(round(((candle.h + candle.l) / 2), 2))
        logger.info("Mid prices calculated")
        # logger.info(mid_prices)
        return mid_prices

    def get_ema(self, prices: List[float], period: int) -> List[float]:
        """
        Calculate the Exponential Moving Average (EMA)
        Args:
            prices (List[float]): List of mid prices
            period (int): The period for which the EMA is being calculated
        Returns:
            List[float]: List of EMA values
        """
        if len(prices) < period:
            raise ValueError("Not enough prices provided")

        multiplier: float = 2 / (period + 1)

        # Calculate initial SMA
        sma: float = sum(prices[:period]) / period
        emas: List[float] = [sma]

        # Calculate EMA for remaining prices
        for i in range(period, len(prices)):
            ema: float = emas[-1] * (1 - multiplier) + prices[i] * multiplier
            emas.append(ema)

        logger.info(f"ema{period} calculated")
        return emas

    def get_macd(self, prices: List[float], a: int = 26, b: int = 12) -> list[float]:
        """
        Calculate the Moving Average Convergence Divergence (MACD)
        Args:
            prices (List[float]): List of mid prices
            a (int): The period for the first EMA
            b (int): The period for the second EMA
        Returns:
            List[float]: List of MACD values
        """
        emaA: List[float] = self.get_ema(prices, a)
        emaB: List[float] = self.get_ema(prices, b)

        emaB = emaB[-len(emaA) :]
        macd: List[float] = [emaB[i] - emaA[i] for i in range(len(emaA))]
        logger.info("MACD calculated")
        return macd

    def get_current_price(self, candles: List[Candle]) -> float:
        """
        Get the current price from the latest candle's close price
        Args:
            candles (List[Candle]): List of candles
        Returns:
            float: The current price
        """
        logger.info("Current price fetched")
        return candles[-1].c

    def get_rsi(self, prices: List[float], period: int = 14) -> float:
        """
        Calculate the Relative Strength Index (RSI)
        Args:
            prices (List[float]): List of mid prices
            period (int): The period for which the RSI is being calculated
        Returns:
            float: The RSI value
        """
        if len(prices) < period + 1:
            logger.error(
                f"Not enough prices provided. Expected at least {period + 1}, got {len(prices)}"
            )
            raise ValueError("Not enough prices provided")

        # Calculate gains and losses
        gains = []
        losses = []
        for i in range(1, len(prices)):
            change = prices[i] - prices[i - 1]
            gains.append(max(change, 0))
            losses.append(abs(min(change, 0)))

        # Step 3: Average gain/loss over the period
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period

        # Avoid division by zero
        if avg_loss == 0:
            return 100.0

        # Step 4 & 5: RS and RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        logger.info("RSI calculated")
        return rsi

    async def get_funding_rate(self) -> float:
        """
        Get the funding rate from the latest candle's close price
        Returns:
            float: The funding rate for the market
        """
        async with lighter.ApiClient(self.configuration) as api_client:
            api_instance = lighter.FundingApi(api_client)
            result = await api_instance.funding_rates()
            funding_rates = result.funding_rates
            for funding_rate in funding_rates:
                if funding_rate.market_id == self.market_id:
                    return funding_rate.rate

    async def fetch_market_context(
        self,
        market_id: int = 1,
        num_candles: int = 50,
        resolution: ResolutionEnum = ResolutionEnum.FOUR_HOUR,
    ):
        """
        Main function to call
        Get the market context for llm
        Args:
            market_id (int): Market ID
        Returns:
            MarketContext: Market context
        """
        candles: List[Candle] = await self.get_candles(num_candles, resolution)
        mid_prices: List[float] = self.get_mid_prices(candles)
        ema26: float = self.get_ema(mid_prices, 26)[-1]
        ema12: float = self.get_ema(mid_prices, 12)[-1]
        macd: float = self.get_macd(mid_prices)[-1]
        rsi: float = self.get_rsi(mid_prices)
        current_price: float = self.get_current_price(candles)
        funding_rate: float = await self.get_funding_rate()
        logger.info("MarketContext generated")

        self.market_context = MarketContext(
            mid_prices=mid_prices,
            ema26=ema26,
            ema12=ema12,
            macd=macd,
            rsi=rsi,
            current_price=current_price,
            funding_rate=funding_rate,  # Return 4h & 10m candles
        )
        return {"success": True}

    def get_market_context(self) -> MarketContext:
        return self.market_context


indicators_service = IndicatorsService()
