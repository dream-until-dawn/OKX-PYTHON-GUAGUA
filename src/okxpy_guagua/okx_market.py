from typing import Any
from okx_base import RequestBase


class OkxMarket(RequestBase):
    def __init__(self, api_key: str, passphrase: str, secret_key: str):
        super().__init__(api_key, passphrase, secret_key)

    def get_candlesticks(
        self,
        instId: str,
        after: str,
        bar: str,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        """

        参数:
            instId: 交易对名称, 例如: BTC-USDT-SWAP, ETH-USDT-SWAP
            after: 开始时间, 格式: yyyy-MM-dd HH:mm:ss
            bar: 周期示例: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 12H, 1D
            limit: 最大返回条数, 默认值: 100

        返回值:
            历史数据
        """
        endpoint = f"/api/v5/market/candles?instId={instId}&after={after}&bar={bar}&limit={limit}"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, {}, {}, False, endpoint)

    def get_candlesticks_history(
        self,
        instId: str,
        after: str,
        bar: str,
        limit: int = 100,
    ) -> list[dict[str, str]]:
        """

        参数:
            instId: 交易对名称, 例如: BTC-USDT-SWAP, ETH-USDT-SWAP
            after: 开始时间, 格式: yyyy-MM-dd HH:mm:ss
            bar: 周期示例: 1m, 5m, 15m, 30m, 1H, 2H, 4H, 6H, 12H, 1D
            limit: 最大返回条数, 默认值: 100

        返回值:
            历史数据
        """
        endpoint = f"/api/v5/market/history-candles?instId={instId}&after={after}&bar={bar}&limit={limit}"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, {}, {}, False, endpoint)
