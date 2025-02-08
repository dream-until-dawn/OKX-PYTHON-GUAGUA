from datetime import datetime, timezone
import json
import base64
import hmac
import hashlib
import requests


class RequestBase:
    def __init__(self, api_key: str, passphrase: str, secret_key: str):
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
        params: dict = None,
        body: dict = None,
        isSign: bool = False,
        endpoint: str = "",
    ) -> dict[str, any]:
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
