import requests
import time
import hmac
import hashlib
import json
from urllib.parse import urljoin


class OKXApi:
    """欧易（OKX）API工具类，支持模拟仓、历史数据等常用操作"""

    def __init__(self, api_key, secret_key, passphrase="", is_testnet=True):
        """
        初始化API客户端
        :param api_key: 欧易APIKey
        :param secret_key: 欧易SecretKey
        :param passphrase: 账户API密码（若无则留空）
        :param is_testnet: 是否使用测试网（模拟仓）
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.is_testnet = is_testnet

        # 基础URL（测试网/正式网）
        self.base_url = "https://www.okx.com" if not is_testnet else "https://www.okx.com"
        # 模拟仓（测试网）部分接口需使用特定前缀
        self.testnet_prefix = "/api/v5" if not is_testnet else "/api/v5"

    def _sign(self, timestamp, method, request_path, body=""):
        """
        生成API请求签名（欧易API要求的签名算法）
        :param timestamp: 时间戳（毫秒级）
        :param method: HTTP方法（GET/POST等）
        :param request_path: API路径（如/account/balance）
        :param body: POST请求的请求体（JSON字符串）
        :return: 签名字符串
        """
        # 拼接签名源字符串
        message = f"{timestamp}{method}{request_path}{body}"
        # HMAC-SHA256签名
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return signature.hex()

    def _request(self, method, path, params=None, data=None):
        """
        发送API请求（内部通用方法）
        :param method: HTTP方法（GET/POST）
        :param path: API路径（如/market/index-components）
        :param params: GET请求参数（字典）
        :param data: POST请求参数（字典）
        :return: 接口返回的JSON数据（dict）
        """
        # 生成时间戳（毫秒级）
        timestamp = str(int(time.time() * 1000))
        # 拼接完整URL
        request_path = f"{self.testnet_prefix}{path}"
        url = urljoin(self.base_url, request_path)

        # 处理请求体
        body = json.dumps(data) if data else ""

        # 生成签名
        signature = self._sign(timestamp, method, request_path, body)

        # 请求头
        headers = {
            "Content-Type": "application/json",
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
        }

        # 发送请求
        try:
            if method == "GET":
                response = requests.get(url, params=params, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, data=body, headers=headers, timeout=10)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")

            # 解析响应
            result = response.json()
            if result.get("code") != "0":
                # 错误处理（如API返回错误码）
                raise Exception(f"API错误: {result.get('msg')} (code: {result.get('code')})")
            return result.get("data", [])

        except Exception as e:
            print(f"请求失败: {str(e)}")
            return None

    # ------------------------------ 模拟仓相关接口 ------------------------------
    def get_testnet_balance(self):
        """获取模拟仓账户余额"""
        return self._request("GET", "/account/balance")

    # ------------------------------ 市场数据接口 ------------------------------
    def get_ticker(self, inst_id="BTC-USDT"):
        """
        获取指定交易对的最新行情
        :param inst_id: 交易对（如BTC-USDT、ETH-USDT）
        :return: 行情数据
        """
        return self._request("GET", "/market/ticker", params={"instId": inst_id})

    def get_history_klines(self, inst_id="BTC-USDT", bar="1H", limit=100):
        """
        获取历史K线数据
        :param inst_id: 交易对
        :param bar: K线周期（1m, 5m, 1H, 1D等）
        :param limit: 返回数据条数（最大100）
        :return: K线数据列表（时间戳、开盘价、最高价、最低价、收盘价、成交量等）
        """
        return self._request(
            "GET",
            "/market/history-candles",
            params={"instId": inst_id, "bar": bar, "limit": limit}
        )

    def get_instruments(self, inst_type="SPOT", inst_id=None):
        """
        获取交易对列表（可指定单个交易对）
        :param inst_type: 产品类型（SPOT：现货，FUTURES：期货等）
        :param inst_id: 具体交易对（如BTC-USDT，不填则返回所有）
        :return: 交易对信息列表
        """
        params = {"instType": inst_type}
        if inst_id:
            params["instId"] = inst_id
        return self._request("GET", "/public/instruments", params=params)

    # ------------------------------ 交易相关接口（模拟仓） ------------------------------
    def place_test_order(self, inst_id="BTC-USDT", side="buy", ord_type="market", sz="0.001"):
        """
        模拟仓下单（测试网）
        :param inst_id: 交易对
        :param side: 买卖方向（buy/sell）
        :param ord_type: 订单类型（market：市价单，limit：限价单）
        :param sz: 下单数量
        :return: 订单信息
        """
        data = {
            "instId": inst_id,
            "side": side,
            "ordType": ord_type,
            "sz": sz
        }
        return self._request("POST", "/trade/order", data=data)


# ------------------------------ 测试程序 ------------------------------
if __name__ == "__main__":
    # 初始化API客户端（使用你的API密钥）
    api_key = "1a3a47fb-f4e7-456b-a4ed-3bef1fd1aa72"
    secret_key = "4C41B637F57EF84F0CC126B9530FEEF7"
    okx = OKXApi(api_key=api_key, secret_key=secret_key, is_testnet=True)  # 模拟仓模式

    print("=" * 50)
    print("1. 测试获取模拟仓账户余额")
    balance = okx.get_testnet_balance()
    if balance:
        print(f"账户余额: {json.dumps(balance, indent=2, ensure_ascii=False)}")

    print("\n" + "=" * 50)
    print("2. 测试获取BTC-USDT最新行情")
    ticker = okx.get_ticker(inst_id="BTC-USDT")
    if ticker:
        print(f"最新行情: {json.dumps(ticker, indent=2, ensure_ascii=False)}")

    print("\n" + "=" * 50)
    print("3. 测试获取ETH-USDT 1小时K线（最近10条）")
    klines = okx.get_history_klines(inst_id="ETH-USDT", bar="1H", limit=10)
    if klines:
        print("K线数据（时间戳, 开盘价, 最高价, 最低价, 收盘价, 成交量）:")
        for k in klines:
            print(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(k[0]) / 1000))}, "
                  f"开: {k[1]}, 高: {k[2]}, 低: {k[3]}, 收: {k[4]}, 量: {k[5]}")

    print("\n" + "=" * 50)
    print("4. 测试获取现货交易对列表（前5条）")
    instruments = okx.get_instruments(inst_type="SPOT")
    if instruments:
        print(f"现货交易对（前5条）: {json.dumps(instruments[:5], indent=2, ensure_ascii=False)}")

    print("\n" + "=" * 50)
    print("5. 测试模拟仓下单（BTC-USDT 市价买入0.001个）")
    order = okx.place_test_order(inst_id="BTC-USDT", side="buy", ord_type="market", sz="0.001")
    if order:
        print(f"订单结果: {json.dumps(order, indent=2, ensure_ascii=False)}")