from binance.client import Client
from binance.exceptions import BinanceAPIException
import time

# 你的Testnet API密钥（替换为你的实际密钥）
api_key = '7f4k13YO0JqshqWkx39z0VZZ7mnb4jOi8XYTxxNkfgLWhAoo3mWJWkgT5eWhTKt7'
api_secret = '4BjbkA4DImJPZ7gSIG9oEu2I1kcCjlaVRxfsP5sGDVEcZJ3O5fxawWs4Y4D0CdWn'

# 初始化Testnet客户端
client = Client(api_key, api_secret, testnet=True)


def safe_api_call(func, max_retries=3, **kwargs):
    """安全调用，处理常见错误"""
    for attempt in range(max_retries):
        try:
            return func(**kwargs)
        except BinanceAPIException as e:
            if e.code == -1021:  # 时间戳问题
                print(f"时间戳错误，重试 {attempt + 1}/{max_retries}...")
                time.sleep(1)
                continue
            elif e.code == -2015:  # 权限/IP问题
                print(f"权限错误 (-2015): {e}. 可能原因: IP限制（中国大陆常见）或密钥未启用'Trade'权限。")
                print("解决: 1. 检查IP: whatismyipaddress.com; 2. 登录testnet.binance.vision启用权限; 3. 生成新密钥。")
                raise e
            else:
                raise e
    raise Exception("重试失败")

try:
    account = client.get_account(recvWindow=10000)
    print("账户余额:", account['balances'])
except Exception as e:
    print(f"余额查询失败: {e}")
# 查询API权限
try:
    permissions = safe_api_call(client.get_account_api_permissions, recvWindow=10000)
    print("API密钥权限详情:")
    for key, value in permissions.items():
        print(f"  {key}: {value}")

    # 判断关键权限
    if permissions.get('enableReading', False):
        print("\n✓ 读取权限: 已启用（可查询价格/K线）")
    else:
        print("\n✗ 读取权限: 未启用")

    if permissions.get('enableSpotAndMarginTrading', False):
        print("✓ 现货/杠杆交易权限: 已启用（可下单、查询余额）")
    else:
        print("✗ 现货/杠杆交易权限: 未启用（当前你的问题可能在此）")

    if permissions.get('enableWithdrawals', False):
        print("⚠ 提现权限: 已启用（不推荐，安全风险高）")
    else:
        print("✓ 提现权限: 已禁用（推荐）")

except Exception as e:
    print(f"查询权限失败: {e}")
    print("提示: 这本身可能因权限不足而失败。手动登录testnet.binance.vision检查。")

# 测试简单读取权限（无需签名）
try:
    ticker = client.get_symbol_ticker(symbol="BTCUSDT")
    print(f"\n测试读取权限: BTC/USDT 当前价格: {ticker['price']} USDT (成功)")
except Exception as e:
    print(f"测试读取权限失败: {e}")

# 测试交易权限（模拟下单，需签名）
try:
    order = client.create_test_order(
        symbol='BTCUSDT',
        side=Client.SIDE_BUY,
        type=Client.ORDER_TYPE_MARKET,
        quantity=0.001
    )
    print("测试交易权限: 模拟下单成功:", order['orderId'])
except Exception as e:
    print(f"测试交易权限失败: {e} (确认未启用交易权限或IP限制)")

# 关闭连接
client.close_connection()