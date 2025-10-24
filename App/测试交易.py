from binance.client import Client
from binance.exceptions import BinanceAPIException
import pandas as pd
import matplotlib.pyplot as plt
import time
import warnings

# 忽略析构警告
warnings.filterwarnings('ignore', category=RuntimeWarning)

# 你的Testnet API密钥（如果无效，请替换为新密钥）
api_key = '7f4k13YO0JqshqWkx39z0VZZ7mnb4jOi8XYTxxNkfgLWhAoo3mWJWkgT5eWhTKt7'
api_secret = '4BjbkA4DImJPZ7gSIG9oEu2I1kcCjlaVRxfsP5sGDVEcZJ3O5fxawWs4Y4D0CdWn'

# 初始化Testnet客户端
try:
    client = Client(api_key, api_secret, testnet=True)
    print("API客户端初始化成功")
    print(client.get_account_api_permissions())
except Exception as e:
    print(f"初始化失败: {e}. 请检查API密钥或网络（中国大陆IP可能受限）。")
    exit()

# 检查时间同步
try:
    server_time = client.get_server_time()['serverTime']
    local_time = int(time.time() * 1000)
    time_diff = local_time - server_time
    print(f"服务器时间: {pd.to_datetime(server_time, unit='ms')} (UTC)")
    print(f"时间差: {time_diff}ms (理想<1000ms)")
    if abs(time_diff) > 1000:
        print("警告：时间差过大！请同步Windows时间（任务栏 > 日期/时间 > 自动同步）。")
except Exception as e:
    print(f"时间同步检查失败: {e}")

# 安全API调用函数（区分签名/非签名API）
def safe_api_call(func, *args, max_retries=3, signed=False, **kwargs):
    if signed:
        kwargs['recvWindow'] = 10000  # 仅签名API使用recvWindow
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except BinanceAPIException as e:
            if e.code == -1021 and attempt < max_retries - 1:
                print(f"时间戳错误，重试 {attempt + 1}/{max_retries}...")
                time.sleep(1)
                continue
            elif e.code == -2015:
                print(f"错误: 无效API密钥、IP受限或权限不足。请检查：")
                print("1. 登录 testnet.binance.vision，确认密钥启用'Trade'权限。")
                print("2. 如果使用中国大陆IP，可能被限制，尝试香港/新加坡IP。")
                print("3. 生成新密钥或联系支持: support.binance.com")
                raise e
            elif e.code == -1104:
                print(f"参数错误: {e}. 尝试移除无效参数。")
                raise e
            else:
                raise e
    raise Exception("重试失败")

# 示例1: 获取账户余额
try:
    account_info = safe_api_call(client.get_account, signed=True)
    balances = [bal for bal in account_info['balances'] if float(bal['free']) > 0 or float(bal['locked']) > 0]
    print("模拟账户余额:", balances)
    if not balances:
        print("提示：余额为空，请登录 testnet.binance.vision 点击'Faucet'领取虚拟资金。")
except Exception as e:
    print(f"获取余额失败: {e}")

# 示例2: 获取API密钥权限
try:
    permissions = safe_api_call(client.get_account_api_permissions, signed=True)
    print("API密钥权限:", permissions)
except Exception as e:
    print(f"获取API权限失败: {e}. 请登录 testnet.binance.vision 手动检查密钥权限（'Trade'应启用）。")

# 示例3: 获取最近交易历史
try:
    trades = safe_api_call(client.get_my_trades, symbol="BTCUSDT", limit=5, signed=True)
    print("最近5笔交易历史:", trades)
    if not trades:
        print("提示：无交易历史，请先尝试模拟下单。")
except Exception as e:
    print(f"获取交易历史失败: {e}")

# 示例4: 获取BTC/USDT实时价格（非签名API）
try:
    ticker = safe_api_call(client.get_symbol_ticker, symbol="BTCUSDT", signed=False)
    print(f"BTC/USDT 当前价格: {ticker['price']} USDT")
except Exception as e:
    print(f"获取价格失败: {e}")

# 示例5: 模拟下单（市价买入0.001 BTC）
try:
    order = safe_api_call(client.create_test_order,
                          symbol='BTCUSDT',
                          side=Client.SIDE_BUY,
                          type=Client.ORDER_TYPE_MARKET,
                          quantity=0.001,
                          signed=True)
    print("模拟订单:", order)
except Exception as e:
    print(f"模拟下单失败: {e}")

# 示例6: 获取历史K线并绘图（非签名API）
try:
    klines = safe_api_call(client.get_historical_klines, "BTCUSDT", Client.KLINE_INTERVAL_1HOUR, "1 day ago UTC", signed=False)
    print("最近1小时K线（前3条）:", klines[:10])

    # 转换为DataFrame
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'trades', 'taker_buy_base', 'taker_buy_quote', 'ignored'])
    df['close'] = df['close'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # 绘制价格曲线
    plt.figure(figsize=(10, 5))
    plt.plot(df['timestamp'], df['close'], label='BTC/USDT Close Price', color='blue')
    plt.title('BTC/USDT 1-Hour Price (Last 24 Hours)')
    plt.xlabel('Time (UTC)')
    plt.ylabel('Price (USDT)')
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('btc_price_chart.png')
    print("图表已保存为 btc_price_chart.png")
    plt.show()
except Exception as e:
    print(f"获取K线或绘图失败: {e}")

# 显式关闭连接
try:
    client.close_connection()
    print("API连接已关闭")
except Exception as e:
    print(f"关闭连接失败: {e}")