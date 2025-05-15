from okx_account import OkxAccount
from okx_market import OkxMarket


class OkxGuagua:
    def __init__(self, api_key: str, passphrase: str, secret_key: str) -> None:
        self.account = OkxAccount(api_key, passphrase, secret_key)
        self.market = OkxMarket(api_key, passphrase, secret_key)


if __name__ == "__main__":
    # Example usage
    api_key = "7ad26990-74b8-4f47-a844-163b4426d9fc"
    passphrase = "ABCabc123456!@#"
    secret_key = "40A69446A34170F14DBC54AA28ABE9D0"

    okx_guagua = OkxGuagua(api_key, passphrase, secret_key)
    # print(okx_guagua.account.open_position_at_market_price("ETH-USDT-SWAP", "long"))
    print(okx_guagua.account.get_balance())
    # from time import time
    # latest_ts = f"{(time()+30*60) * 1000:.0f}"
    # print(okx_guagua.market.get_candlesticks("ETH-USDT-SWAP", latest_ts, "1D"))
