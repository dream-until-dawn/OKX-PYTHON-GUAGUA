from datetime import datetime, timezone
import json
import base64
import hmac
import hashlib
from typing import Any
import requests


class RequestBase:
    def __init__(self, api_key: str, passphrase: str, secret_key: str) -> None:
        """
        初始化OKX请求类

        参数:
            api_key: API密钥
            passphrase: API密钥对应的密码
            secret_key: API密钥对应的密钥
        """
        self.api_key = api_key
        self.passphrase = passphrase
        self.secret_key = secret_key
        self.base_url = "https://www.okx.com"

    def __generate_signature(
        self, timestamp: str, method: str, request_path: str, body: str
    ):
        """
        生成OKX签名

        参数:
            timestamp: 时间戳
            method: 请求方法
            request_path: 请求路径
            body: 请求体
        """
        sign_str = timestamp + method.upper() + request_path + body
        hmac_key = self.secret_key.encode("utf-8")
        signature = hmac.new(
            hmac_key, sign_str.encode("utf-8"), hashlib.sha256
        ).digest()
        signature_b64 = base64.b64encode(signature).decode("utf-8")
        return signature_b64

    def __generate_okx_headers(self, method: str, request_path: str, body: str):
        """
        生成OKX请求头

        参数:
            method: 请求方法
            request_path: 请求路径
            body: 请求体
        """
        # 取得当前时间戳，使用带有时区的 UTC 时间
        timestamp = (
            datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z")
        )
        signature = self.__generate_signature(timestamp, method, request_path, body)
        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
        }
        return headers

    def _request(
        self,
        method: str,
        url: str,
        params: dict = {},
        body: dict = {},
        isSign: bool = False,
        endpoint: str = "",
    ) -> Any:
        """
        发起一个okx网络请求

        参数:
            method: 请求方法
            url: 请求地址
            params: 请求参数
            body: 请求体
            isSign: 是否需要签名
            endpoint: 请求路径
        """
        headers = {}
        if isSign:
            headers = self.__generate_okx_headers(
                method, endpoint, json.dumps(body) if body is not None else ""
            )
        try:
            response = requests.request(
                method, url, headers=headers, params=params, json=body, timeout=3
            )
            return response.json()
        except:
            return {"code": 500}


class OkxAccount(RequestBase):
    def __init__(self, api_key: str, passphrase: str, secret_key: str):
        super().__init__(api_key, passphrase, secret_key)

    def __get_mark_price(self, instId: str) -> float:
        """
        获取当前产品标记价格

        参数:
            instId: 合约ID
        """
        endpoint = f"/api/v5/market/ticker?instId={instId}"
        url = f"{self.base_url}{endpoint}"
        response = self._request("GET", url, {}, {}, False, endpoint)
        if "code" in response and response["code"] == "0":
            data = response["data"][0]
            return float(data["last"])
        else:
            return 0.0

    def __convert_usdt_to_contract_size(
        self, instId: str, posSide: str, usdt: str
    ) -> float:
        """
        将USDT转换为合约张数-算出是1倍杠杆时的张数

        参数:
            instId: 合约ID
            posSide: 持仓方向,long或short
            usdt: 转换数量,单位为USDT
        """
        px = self.__get_mark_price(instId)
        endpoint = f"/api/v5/public/convert-contract-coin?instId={instId}&sz={usdt}&px={px}&unit=usds&opType={'open' if posSide == 'long' else 'close'}"
        url = f"{self.base_url}{endpoint}"
        response = self._request("GET", url, {}, {}, False, endpoint)
        if "code" in response and response["code"] == "0":
            data = response["data"][0]
            return round(float(data["sz"]), 1)
        else:
            return 0.0

    def get_avail_usdt(self) -> float:
        """
        获取账户可用余额
        """
        endpoint = "/api/v5/account/balance?ccy=USDT"
        url = "https://www.okx.com" + endpoint
        response = self._request("GET", url, {}, {}, True, endpoint)
        if "code" in response and response["code"] == "0":
            data = response["data"][0]["details"][0]
            return float(data["availEq"])
        else:
            return 0.0

    def get_balance(self, ccy: str = "USDT") -> dict[str, Any]:
        """
        获取账户余额信息

        参数:
            ccy: 币种,默认USDT
        """
        endpoint = f"/api/v5/account/balance?ccy={ccy}"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, {}, {}, True, endpoint)

    def get_account_positions(self) -> dict[str, Any]:
        """
        获取账户持仓信息
        """
        endpoint = "/api/v5/account/positions"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, {}, {}, True, endpoint)

    def get_leverage_info(
        self, instId: str = "", mgnMode: str = "isolated"
    ) -> dict[str, Any]:
        """
        获取杠杆倍率信息

        参数:
            instId: 合约ID,默认为空-获取所有合约的杠杆倍率信息
            mgnMode: 保证金模式,默认isolated-逐仓模式
        """
        endpoint = f"/api/v5/account/leverage-info?mgnMode={mgnMode}"
        if instId != "":
            endpoint += f"&instId={instId}"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, {}, {}, True, endpoint)

    def set_leverage(self, instId: str, lever: int, posSide: str) -> dict[str, Any]:
        """
        设置杠杆倍率

        参数:
            instId: 合约ID
            lever: 杠杆倍数
            posSide: 持仓方向,long或short
        """
        if lever < 1 or lever > 100:
            return {"code": "500", "msg": "杠杆倍率错误"}
        if posSide not in ["long", "short"]:
            return {"code": "500", "msg": "持仓方向错误"}
        endpoint = f"/api/v5/account/set-leverage"
        url = f"{self.base_url}{endpoint}"
        body = {
            "instId": instId,
            "lever": lever,
            "mgnMode": "isolated",
            "posSide": posSide,
        }
        return self._request("POST", url, {}, body, True, endpoint)

    def open_position_at_market_price(
        self, instId: str, posSide: str, lever: int = 0, usdt: str = "0"
    ) -> dict[str, Any]:
        """
        以市价直接开仓

        参数:
            instId: 合约ID
            posSide: 持仓方向,long或short
            lever: 杠杆倍数,默认0-使用当前杠杆
            usdt: 开仓数量,单位为USDT,默认{}-使用当前可用余额
        """
        if posSide not in ["long", "short"]:
            return {"code": "500", "msg": "持仓方向错误"}
        if lever < 0 or lever > 100:
            return {"code": "500", "msg": "杠杆倍率错误"}
        use_lever = lever
        # 设置杠杆倍率
        if lever != 0:
            self.set_leverage(instId, lever, posSide)
        else:
            leverage_info: Any = self.get_leverage_info(instId)
            if "code" in leverage_info and leverage_info["code"] == "0":
                curget = [x for x in leverage_info["data"] if x["posSide"] == posSide]
                use_lever = int(curget[0]["lever"])
            else:
                print(leverage_info)
                return {"code": "500", "msg": "获取杠杆倍率失败"}
        # 计算合约张数
        sz = self.__convert_usdt_to_contract_size(
            instId, posSide, str(self.get_avail_usdt()) if usdt == "0" else usdt
        )
        endpoint = f"/api/v5/trade/order"
        url = f"{self.base_url}{endpoint}"
        body = {
            "instId": instId,
            "tdMode": "isolated",
            "side": "buy",
            "posSide": posSide,
            "ordType": "market",
            "sz": str(round(sz * use_lever, 1)),
        }
        return self._request("POST", url, {}, body, True, endpoint)

    def close_position(self, instId: str, posSide: str) -> dict[str, Any]:
        endpoint = f"/api/v5/trade/close-position"
        url = f"{self.base_url}{endpoint}"
        body = {
            "instId": instId,
            "mgnMode": "isolated",
            "posSide": posSide,
        }
        return self._request("POST", url, {}, body, True, endpoint)


class OkxMarket(RequestBase):
    def __init__(self, api_key: str, passphrase: str, secret_key: str):
        super().__init__(api_key, passphrase, secret_key)

    def get_candlesticks(
        self,
        instId: str,
        after: str,
        bar: str,
        limit: int = 10,
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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


class OkxGuagua:
    def __init__(self, api_key: str, passphrase: str, secret_key: str) -> None:
        self.account = OkxAccount(api_key, passphrase, secret_key)
        self.market = OkxMarket(api_key, passphrase, secret_key)

    def test_url(self) -> bool:
        try:
            # 发送请求，设置超时时间为10秒
            requests.get(self.market.base_url, timeout=10)
            # 检查响应状态码
            return True
        except Exception as e:
            # 捕获其他异常
            print(f"URL {self.market.base_url} 测试出错，错误信息: {str(e)}")
            return False


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
