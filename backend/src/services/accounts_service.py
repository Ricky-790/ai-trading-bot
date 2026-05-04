from lighter.models.account_position import AccountPosition
from lighter.models.account_asset import AccountAsset
from src.logger_config import logger
from src.schemas.account_context_schema import (
    AccountContext,
    PositionContext,
    PositionSign,
)
from typing import Tuple, List, Dict, Literal
import asyncio
import lighter
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL: str = os.getenv("LIGHTER_BASE_URL", "https://testnet.zklighter.elliot.ai")
SIGN_LITERAL = Literal["LONG", "SHORT"]


class AccountsService:
    def __init__(self):
        self.configuration = lighter.Configuration(host=BASE_URL)

    async def get_account_context(self, account_index: int) -> AccountContext:
        """
        Fetch the current holdings (positions & assets) under the account
        Args:
            account_index (str): The index of the account
        Returns:
            AccountContext object
        """
        async with lighter.ApiClient(self.configuration) as api_client:
            # Create an instance of the API class
            api_instance = lighter.AccountApi(api_client)
            by = "index"  # [account_index, l1_address]
            value = account_index  # self.account_index  # [account_index_number, l1_address_pub_key]
            active_only = False  # bool |  (optional) (default to False)

            try:
                logger.info("Fetching account data...")
                api_response = await api_instance.account(
                    by, value, active_only=active_only
                )
                logger.info("Account fetched")

                account = api_response.accounts[0]
                # print(account.model_dump_json(indent=4))

                positions: List[AccountPosition] = account.positions

                position_contexts: List[PositionContext] = [
                    PositionContext(
                        initial_margin_fraction=position.initial_margin_fraction,
                        avg_entry_price=position.avg_entry_price,
                        position_value=position.position_value,
                        unrealized_pnl=position.unrealized_pnl,
                        realized_pnl=position.realized_pnl,
                        total_funding_paid_out=position.total_funding_paid_out,
                        liquidation_price=position.liquidation_price,
                        sign=PositionSign.from_sign(position.sign),
                    )
                    for position in positions
                ]

                account_context: AccountContext = AccountContext(
                    available_balance=account.available_balance,
                    collateral=account.collateral,
                    open_positions=position_contexts,
                )

                return account_context

            except Exception as e:
                logger.error("Exception when calling AccountApi->account: %s\n" % e)
                raise e

    async def create_position(
        self,
        account_index: int,
        private_key: Dict[int, str],
        side: Literal["LONG", "SHORT"],
        base_amount: float,
        is_ask: bool,
        reduce_only: bool,
        max_slippage: float = 0.05,
    ):
        # api_client = lighter.ApiClient(configuration=self.configuration)
        try:
            client = lighter.SignerClient(
                url=BASE_URL,
                account_index=account_index,
                api_private_keys=private_key,
            )
            # print(f"CHECKING: {client.check_client()}")
            # Note: change this to 2048 to trade spot ETH. Make sure you have at least 0.1 ETH to trade spot.
            market_index = int(os.getenv("BITCOIN_MARKET_ID", 1))
            # best_price = await client.get_best_price(
            #     market_index=market_index, is_ask=False
            # )
            # print(f"Best Price: {best_price}")
            tx, tx_hash, err = await client.create_market_order_if_slippage(
                market_index=market_index,
                client_order_index=0,
                base_amount=int(base_amount * 10**5),  # Amount of bitcoin
                max_slippage=max_slippage,
                is_ask=is_ask,
                reduce_only=reduce_only,
            )
            logger.info(f"Create Order {tx=} {tx_hash=} {err=}")
            if err is not None:
                raise Exception(err)
            return {"success": True, "tx": tx, "tx_hash": tx_hash}
        except Exception as e:
            logger.error("Exception when calling AccountApi->create_position: %s\n" % e)
            return {"success": False, "error": str(e)}
        finally:
            await client.close()

    async def close_position():
        return "Close Position called"


accounts_service = AccountsService()


async def main():
    acc_serv = AccountsService()
    # account_context = await acc_serv.get_account_context("281474976710642")
    # print(account_context.model_dump_json(indent=4))
    await acc_serv.create_position(
        account_index="281474976710641",
        private_key={
            4: "4fa3582af50ce7f3c5fea115feb8e47c0d629f58d8e2d6c2847d3885ee00de33554f11b3d144d110"
        },
        side="LONG",
        base_amount=0.0014,
        is_ask=False,
        reduce_only=False,
    )


# if __name__ == "__main__":
#     asyncio.run(main())
