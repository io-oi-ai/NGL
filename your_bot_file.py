import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 从环境变量中获取bot token
BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("未设置TELEGRAM_BOT_TOKEN环境变量")
    raise ValueError("请设置TELEGRAM_BOT_TOKEN环境变量")

# 创建一个会话对象
session = requests.Session()

# 配置重试策略
retries = Retry(total=5,  # 总共重试5次
                backoff_factor=1,  # 重试之间的等待时间会以指数形式增加
                status_forcelist=[429, 500, 502, 503, 504])  # 这些HTTP状态码会触发重试

# 将重试策略应用到会话对象
session.mount('https://', HTTPAdapter(max_retries=retries))

# 假设这是您原来的函数
def send_telegram_request(method, params):
    try:
        # 使用会话对象发送请求，并增加超时时间到60秒
        response = session.get(f'https://api.telegram.org/bot{BOT_TOKEN}/{method}',
                               params=params,
                               timeout=60)
        response.raise_for_status()  # 如果状态码不是200，会抛出异常
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {e}")
        return None

# 定义要特别关注的 meme 币列表
WATCHED_MEME_COINS = ['DOGE', 'SHIB', 'PEPE', 'FLOKI', 'BONK', 'WOJAK']

# 获取所有币种信息的函数
def get_all_crypto_prices():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 250,  # 获取前250种加密货币
        'page': 1,
        'sparkline': False
    }
    response = requests.get(url, params=params)
    return response.json()

# 监控所有币种，特别关注 meme 币的函数
def monitor_cryptocurrencies():
    all_cryptos = get_all_crypto_prices()
    for crypto in all_cryptos:
        symbol = crypto['symbol'].upper()
        current_price = crypto['current_price']
        price_change_24h = crypto['price_change_percentage_24h']
        
        # 对所有币种进行基本监控
        if abs(price_change_24h) > 5:  # 如果24小时价格变化超过5%
            print(f"警报：{symbol} 价格在24小时内变化了 {price_change_24h:.2f}%")
        
        # 对 meme 币进行特别关注
        if symbol in WATCHED_MEME_COINS:
            print(f"Meme币 {symbol} 当前价格: ${current_price:.4f}, 24小时变化: {price_change_24h:.2f}%")

# 定义要关注的虚拟货币列表
WATCHED_CRYPTOCURRENCIES = ['BTC', 'ETH', 'USDT', 'BNB', 'XRP']

# ... 其他代码 ...

def get_crypto_prices():
    for crypto in WATCHED_CRYPTOCURRENCIES:
        # 获取每种加密货币的价格
        # 这里需要调用相应的API或使用适当的库
        pass

# ... 其他代码 ...

def main():
    try:
        # 您的主程序逻辑
        pass
    except Exception as e:
        logger.error(f"Bot运行时发生错误: {e}")
    finally:
        logger.info("Bot停止运行")

if __name__ == "__main__":
    monitor_cryptocurrencies()