from okx_base import RequestBase


class OkxAccount(RequestBase):
    def __init__(self, api_key: str, passphrase: str, secret_key: str):
        super().__init__(api_key, passphrase, secret_key)

    def __get_mark_price(self, instId: str) -> dict[str, str]:
        """
        获取当前产品标记价格

        参数:
            instId: 合约ID
        """
        endpoint = f"/api/v5/market/ticker?instId={instId}"
        url = f"{self.base_url}{endpoint}"
        response = self._request("GET", url, None, None, False, endpoint)
        if "code" in response and response["code"] == "0":
            data = response["data"][0]
            return float(data["last"])
        else:
            return 0.0

    def __convert_usdt_to_contract_size(
        self, instId: str, posSide: str, usdt: str
    ) -> dict[str, str]:
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
        response = self._request("GET", url, None, None, False, endpoint)
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
        response = self._request("GET", url, None, None, True, endpoint)
        if "code" in response and response["code"] == "0":
            data = response["data"][0]["details"][0]
            return float(data["availEq"])
        else:
            return 0.0

    def get_balance(self, ccy: str = "USDT") -> dict[str, str]:
        """
        获取账户余额信息

        参数:
            ccy: 币种,默认USDT
        """
        endpoint = f"/api/v5/account/balance?ccy={ccy}"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, None, None, True, endpoint)

    def get_account_positions(self) -> list[dict[str, str]]:
        """
        获取账户持仓信息
        """
        endpoint = "/api/v5/account/positions"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, None, None, True, endpoint)

    def get_leverage_info(self, instId: str = None, mgnMode: str = "isolated") -> dict:
        """
        获取杠杆倍率信息

        参数:
            instId: 合约ID,默认为空-获取所有合约的杠杆倍率信息
            mgnMode: 保证金模式,默认isolated-逐仓模式
        """
        endpoint = f"/api/v5/account/leverage-info?mgnMode={mgnMode}"
        if instId:
            endpoint += f"&instId={instId}"
        url = f"{self.base_url}{endpoint}"
        return self._request("GET", url, None, None, True, endpoint)

    def set_leverage(self, instId: str, lever: int, posSide: str) -> dict[str, str]:
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
        return self._request("POST", url, None, body, True, endpoint)

    # 开仓
    def open_position_at_market_price(
        self, instId: str, posSide: str, lever: int = 0, usdt: str | None = None
    ) -> int:
        """
        以市价直接开仓

        参数:
            instId: 合约ID
            posSide: 持仓方向,long或short
            lever: 杠杆倍数,默认0-使用当前杠杆
            usdt: 开仓数量,单位为USDT,默认None-使用当前可用余额
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
            leverage_info = self.get_leverage_info(instId)
            if "code" in leverage_info and leverage_info["code"] == "0":
                curget = [x for x in leverage_info["data"] if x["posSide"] == posSide]
                use_lever = int(curget[0]["lever"])
            else:
                return {"code": "500", "msg": "获取杠杆倍率失败"}
        # 计算合约张数
        sz = self.__convert_usdt_to_contract_size(
            instId, posSide, self.get_avail_usdt() if usdt is None else usdt
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
        return body
        return self._request("POST", url, None, body, True, endpoint)

    # 平仓
    def closePosition(self, instId: str, posSide: str) -> dict[str, str]:
        endpoint = f"/api/v5/trade/close-position"
        url = f"{self.base_url}{endpoint}"
        body = {
            "instId": instId,
            "mgnMode": "isolated",
            "posSide": posSide,
        }
        return self._request("POST", url, None, body, True, endpoint)


if __name__ == "__main__":
    api_key = "7ad26990-74b8-4f47-a844-163b4426d9fc"
    passphrase = "ABCabc123456!@#"
    secret_key = "40A69446A34170F14DBC54AA28ABE9D0"

    account = OkxAccount(api_key, passphrase, secret_key)
    print(account.open_position_at_market_price("ETH-USDT-SWAP", "long"))
