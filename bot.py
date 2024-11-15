import logging
import re
import time
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime
import requests
from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from utils import format_price, format_number
from commands import CommandHandler, client
from openai import OpenAI
import os
from dotenv import load_dotenv
import sys
import asyncio
import aiohttp
from difflib import SequenceMatcher

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入所需的服务类
from src.services.message_handler import MessageHandler
from src.services.alert_service import AlertService
from src.api.dex_screener import DexScreenerAPI

# 加载环境变量
load_dotenv()

# 获取 Telegram Bot Token
TELEGRAM_BOT_TOKEN = "7520032539:AAHdT_kU9Vo7SHeIiw0enDKz3p4ZSEM8fIw"

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.timestamps = []

    async def acquire(self):
        now = time.time()
        self.timestamps = [t for t in self.timestamps if now - t < self.period]
        
        if len(self.timestamps) >= self.calls:
            sleep_time = self.period - (now - self.timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                
        self.timestamps.append(now)

class MarketDataService:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5分钟缓存
        
    async def get_comprehensive_market_data(self) -> Dict[str, Any]:
        """获取综合市场数据"""
        try:
            data = {
                'basic_metrics': await self._get_coingecko_data(),
                'defi_metrics': await self._get_defillama_data(),
                'social_metrics': await self._get_social_data(),
                'onchain_metrics': await self._get_onchain_data(),
                'news_sentiment': await self._get_news_sentiment()
            }
            return data
        except Exception as e:
            logger.error(f"获取��合市场数据失败: {e}")
            return {}

    async def _get_coingecko_data(self) -> Dict[str, Any]:
        """CoinGecko API - 基础市场数据"""
        endpoints = {
            'global': 'https://api.coingecko.com/api/v3/global',
            'trending': 'https://api.coingecko.com/api/v3/search/trending',
            'btc_price': 'https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd'
        }
        # ... API 实现逻辑

    async def _get_defillama_data(self) -> Dict[str, Any]:
        """DefiLlama API - DeFi数据"""
        endpoints = {
            'tvl': 'https://api.llama.fi/protocols',
            'chains': 'https://api.llama.fi/chains',
            'yields': 'https://yields.llama.fi/pools'
        }
        # ... API 实现逻辑

    async def _get_social_data(self) -> Dict[str, Any]:
        """社交媒体数据"""
        endpoints = {
            'lunarcrush': 'https://lunarcrush.com/api3/public',  # 需要API密钥
            'cryptopanic': 'https://cryptopanic.com/api/v1/posts/?auth_token=',  # 需要API密钥
        }
        # ... API 实现逻辑

    async def _get_onchain_data(self) -> Dict[str, Any]:
        """链上数据"""
        endpoints = {
            'etherscan': 'https://api.etherscan.io/api',  # 基础版免费
            'bscscan': 'https://api.bscscan.com/api',     # 基版免费
        }
        # ... API 实现逻辑

    async def _get_news_sentiment(self) -> Dict[str, Any]:
        """新闻情绪分析"""
        endpoints = {
            'cryptopanic': 'https://cryptopanic.com/api/v1/posts/?auth_token=',  # 新闻聚合
            'cryptocompare': 'https://min-api.cryptocompare.com/data/v2/news/?lang=EN'  # 新闻源
        }
        # ... API 实现逻辑

    def _cache_data(self, key: str, data: Any, duration: int = 300):
        """缓存数据"""
        self.cache[key] = {
            'data': data,
            'timestamp': time.time(),
            'duration': duration
        }

    def _get_cached_data(self, key: str) -> Optional[Any]:
        """获取缓存数据"""
        if key in self.cache:
            cache_item = self.cache[key]
            if time.time() - cache_item['timestamp'] < cache_item['duration']:
                return cache_item['data']
        return None

    async def _fetch_with_retry(self, url: str, retries: int = 3) -> Optional[Dict]:
        """带重试的数据获取"""
        for i in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.json()
            except Exception as e:
                if i == retries - 1:
                    logger.error(f"获取数据失败: {url}, 错误: {e}")
                    return None
                await asyncio.sleep(1)
        return None

class CryptoAnalysisBot:
    def __init__(self):
        logger.info("初始化机器人...")
        self.bot = TeleBot(TELEGRAM_BOT_TOKEN)
        self.message_handler = MessageHandler()
        self.alert_service = AlertService()
        self.command_handler = CommandHandler()
        self.chat_contexts = {}
        self.openai_client = client
        self.dex_screener = DexScreenerAPI()
        self.market_data_service = MarketDataService()
        self.token_address_cache = {}
        self.cache_duration = 3600  # 1小时缓存
        self.max_retries = 3  # 最大重试次数
        self._setup_handlers()
        logger.info("机器人初始化完成")

    def _setup_handlers(self):
        """设置消息处理器"""
        @self.bot.message_handler(func=lambda message: True)
        def handle_message(message):
            try:
                logger.info(f"收到消息: {message.text} from chat {message.chat.id}")
                text = message.text if message.text else ""
                
                # 检查是否是群组消息
                if message.chat.type in ['group', 'supergroup']:
                    # 检查消息类型
                    if text.startswith('/N') or text.startswith('/n'):
                        self._handle_chat(message)
                    elif self._is_token_address(text):  # 使用新方法检查是否是代币地址
                        self._handle_token_analysis(message)
                    elif text.startswith('/'):
                        self._handle_command(message)
                else:
                    # 私聊消息处理
                    if text.startswith('/'):
                        if text.startswith(('/N', '/n')):
                            self._handle_chat(message)
                        else:
                            self._handle_command(message)
                    elif self._is_token_address(text):
                        self._handle_token_analysis(message)
                    else:
                        # 处理普通对话
                        self._handle_chat(message)
                    
            except Exception as e:
                logger.error(f"处理消息错误: {e}", exc_info=True)
                self.bot.reply_to(message, "处理请求时出错，请重试")

    def _is_token_address(self, text: str) -> bool:
        """检查文本是否是代币地址"""
        # 检查是否是 EVM 地址
        if re.match(r'^0x[a-fA-F0-9]{40}$', text):
            return True
        # 检查是否是 Solana 地址
        if len(text) in [32, 44] and text.isalnum():
            return True
        return False

    def _safe_reply(self, message: Message, text: str, **kwargs):
        """安全的消息回复方法，带重试机制"""
        for attempt in range(self.max_retries):
            try:
                # 如果消息太长，分段发送
                if len(text) > 4000:
                    chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
                    for chunk in chunks:
                        self.bot.reply_to(message, chunk, **kwargs)
                else:
                    self.bot.reply_to(message, text, **kwargs)
                return True
            except Exception as e:
                logger.error(f"发送消息失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(1)  # 等待1秒后重试
                continue
        return False

    def _handle_chat(self, message: Message):
        """处理聊天消息"""
        try:
            chat_id = message.chat.id
            text = message.text.strip()
            
            if text.startswith(('/N', '/n')):
                text = text[2:].strip()
            
            if not text:
                self.bot.reply_to(message, "请在 /N 后输入您想说的话，例如：/N 最近市场如何？")
                return

            # 获取最新市场数据
            market_data = self._get_latest_market_data()
            
            # 构建 AI 回复
            try:
                system_prompt = """你是一个专业的加密货币分析师和市场专家。
请基于提供的实时市场数据，给出具体、详细、有价值的分析和建议。
回答要：
1. 使用提供的实时数据进行分析
2. 给出具体的市场趋势判断
3. 结合数据提供见解
4. 使用表情符号增可读性
5. 如果用户用英文提问，请用英文回答

重要提示：
- 对于具体代币询问：
  * 分析当前价格位置和交易量
  * 评估市场情绪和热度
  * 提供短期和中期的可能走
  * 强调投资风险
  * 建议合理的仓位管理

- 对于市场预测：
  * 分��当前市场周期位置
  * 结合宏观经济因素
  * 考虑历史数据和季节性规律
  * 提供多个可能的场景预测
  * 说明影响因素和风险点

- 必须包含免责声明：
  * 提醒这只是分析和建议，不构成投资建议
  * 强调加密货币市场的高风险性
  * 建议用户做好风险管理

请确保回答专业、客观、谨慎，避免过度乐观或悲观的预测。"""

                user_prompt = f"""用户问题：{text}

实时市场数据：
{self._format_market_data(market_data)}

请根据这些最新数据，给出专业的分析和见解。
回答要简洁但要有深度，突出关键信息。"""

                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                reply = response.choices[0].message.content
                if not self._safe_reply(message, reply):
                    # 如果所有重试都失败，发送简短的错误消息
                    self._safe_reply(message, "抱歉，发送回复时出错，请稍后重试。")
                
            except Exception as e:
                logger.error(f"生成回复时出错: {e}")
                self._safe_reply(message, "抱歉，我现在无法回答，请稍后再试。")
                
        except Exception as e:
            logger.error(f"处理聊天消息时出错: {e}")
            self._safe_reply(message, "处理消息时出错，请重试")

    def _get_latest_market_data(self) -> Dict[str, Any]:
        """获取最新市场数据"""
        try:
            market_data = {
                'trending': [],
                'stats': {}
            }
            
            # 获取各链的热门代币
            chains = ['ethereum', 'bsc', 'polygon', 'arbitrum']
            for chain in chains:
                hot_tokens = self.dex_screener.get_hot_tokens(chain, 5)
                if hot_tokens:
                    # 计算链上数据
                    total_volume = sum(t['volume24h'] for t in hot_tokens)
                    avg_price_change = sum(t['priceChange24h'] for t in hot_tokens) / len(hot_tokens)
                    
                    market_data['stats'][chain] = {
                        'total_volume': total_volume,
                        'avg_price_change': avg_price_change,
                        'hot_tokens': hot_tokens[:3]  # 只取前3
                    }
                    
                    # 添加到趋势列表
                    market_data['trending'].extend(hot_tokens)
            
            # 按24h成交量排序趋势代币
            market_data['trending'].sort(key=lambda x: x['volume24h'], reverse=True)
            market_data['trending'] = market_data['trending'][:5]  # 只保留前5个
            
            return market_data
            
        except Exception as e:
            logger.error(f"获取最新市场数据时出错: {e}")
            return {}

    def _format_market_data(self, market_data: Dict[str, Any]) -> str:
        """格式化市场数据"""
        if not market_data:
            return "暂无市场数据"
            
        result = "🔥 热门趋势：\n"
        for token in market_data.get('trending', []):
            result += (
                f"• {token['baseToken']['symbol']} ({token['chain']}): "
                f"${token['price']:.12f} "
                f"({token['priceChange24h']:+.2f}%) "
                f"成交量: ${token['volume24h']:,.2f}\n"
            )
        
        result += "\n📊 各链数据：\n"
        for chain, stats in market_data.get('stats', {}).items():
            result += (
                f"{chain.upper()}:\n"
                f"• 总成交量: ${stats['total_volume']:,.2f}\n"
                f"• 平均涨跌: {stats['avg_price_change']:+.2f}%\n"
            )
        
        return result

    def _extract_token_info(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取代币信息"""
        try:
            # 如果文本包含合约地址，直接回
            if re.match(r'^0x[a-fA-F0-9]{40}$', text) or len(text) in [32, 44]:
                return self.message_handler.token_analyzer.dex_screener.get_token_info(text)

            # 尝试从热门代币中匹配
            hot_tokens = self._get_hot_tokens()
            if hot_tokens:
                text_lower = text.lower()
                for token in hot_tokens:
                    symbol = token['baseToken']['symbol'].lower()
                    name = token['baseToken']['name'].lower()
                    if symbol in text_lower or name in text_lower:
                        return token

            return None
        except Exception as e:
            logger.error(f"提取代币信息时出错: {e}")
            return None

    def _get_hot_tokens(self) -> List[Dict[str, Any]]:
        """获取热门代币列表"""
        try:
            # 使用 DexScreener API 获取热门代币
            hot_tokens = self.message_handler.token_analyzer.dex_screener.get_hot_tokens()
            return hot_tokens if hot_tokens else []
        except Exception as e:
            logger.error(f"获取热门代币时出错: {e}")
            return []

    def _format_hot_tokens(self, tokens: List[Dict[str, Any]]) -> str:
        """格式化热门代币信息"""
        if not tokens:
            return "暂无热门代币数据"
            
        result = "当前热门代币：\n"
        for token in tokens[:5]:  # 只显示前5个
            result += (
                f"• {token['baseToken']['symbol']}: "
                f"${token['price']:.12f} "
                f"({token['priceChange24h']:+.2f}%) "
                f"24h成交量: ${token['volume24h']:,.2f}\n"
            )
        return result

    def _handle_token_analysis_with_info(self, message: Message, token_info: Dict[str, Any]):
        """使用已有的代币信息进行分析"""
        try:
            response, kwargs = self.command_handler.format_token_info(token_info)
            self.bot.reply_to(message, response, **kwargs)
        except Exception as e:
            logger.error(f"代币分错误: {e}")
            self.bot.reply_to(message, "分析代币时出错，请重试")

    def _handle_private_message(self, message: Message):
        """处理私聊消息"""
        try:
            text = message.text if message.text else ""
            
            # 处理合约地址
            if re.match(r'^0x[a-fA-F0-9]{40}$', text) or len(text) in [32, 44]:
                self._handle_token_analysis(message)
                return
                
            # 处理命令
            if text.startswith('/'):
                if text.startswith(('/N', '/n')):
                    self._handle_chat(message)
                else:
                    self._handle_command(message)
                return
                
            # 处理普通对话
            self._handle_chat(message)
            
        except Exception as e:
            logger.error(f"处理私聊消息错误: {e}")
            self.bot.reply_to(message, "处理消息时出错，请重试")

    def _handle_token_analysis(self, message: Message):
        """处理代币分析"""
        try:
            token_data = self.message_handler.token_analyzer.dex_screener.get_token_info(message.text)
            if token_data:
                # 构建分析回复
                token_name = f"{token_data['baseToken'].get('name', 'Unknown')} ({token_data['baseToken'].get('symbol', 'Unknown')})"
                
                response = f"""您提供的内容是 {token_name} 的代币合约地址，这是一个在{token_data['chain']}区块链上{'流行的 meme 币' if self._is_meme_token(token_name) else '的代币项目'}。

{token_name} 概述
类别: {'Meme币' if self._is_meme_token(token_name) else '实用代币'}
当前价格: ${token_data['price']:.12f}
24小时交易量: ${token_data['volume24h']:,.2f}
24小时涨跌: {token_data['priceChange24h']:+.2f}%
流动性: ${token_data['liquidity']:,.2f}

最近动态
• 交易量{'显著' if token_data['volume24h'] > token_data['liquidity'] * 2 else '正常'}
• 买入/卖出比: {token_data['txns'].get('buys', 0)}/{token_data['txns'].get('sells', 0)}
• {'买盘压力较大' if token_data['txns'].get('buys', 0) > token_data['txns'].get('sells', 0) else '卖盘压力较大'}
• 在 {token_data['dex']} 上交易活跃

社区情绪
• 交易活跃度: {'非常高' if token_data['volume24h'] > token_data['liquidity'] * 2 else '正常'}
• 市场情绪: {'看涨' if token_data['priceChange24h'] > 0 else '看跌'}
• 流动性状况: {'充足' if token_data['liquidity'] > 500000 else '一般'}

如果您需要更多具体信息或见解，请随时告诉我！"""

                self._safe_reply(message, response)
            else:
                self._safe_reply(message, "未找到该代币信息，请确认地址是否正确")
        except Exception as e:
            logger.error(f"代币分析错误: {e}")
            self._safe_reply(message, "分析代币时出错，请重试")

    def _is_meme_token(self, token_name: str) -> bool:
        """判断是否为 meme 代币"""
        name_lower = token_name.lower()
        meme_keywords = [
            'pepe', 'doge', 'shib', 'inu', 'elon', 'moon', 'safe', 'baby',
            'rocket', 'chad', 'wojak', 'cat', 'dog', 'meme', 'ai', 'coin',
            'token', 'gpt', 'chat', 'based', 'rick', 'morty', 'punk', 'ape',
            'monkey', 'bird', 'frog', 'bear', 'bull', 'diamond', 'hands'
        ]
        return any(keyword in name_lower for keyword in meme_keywords)

    def _check_alerts(self):
        """检查价格提醒"""
        while True:
            try:
                triggered_alerts = self.alert_service.get_triggered_alerts()
                if triggered_alerts:
                    for user_id, message in triggered_alerts.items():
                        try:
                            self.bot.send_message(user_id, message)
                        except Exception as e:
                            logger.error(f"发送提醒消息失败: {e}")
            except Exception as e:
                logger.error(f"检查价格提醒时出错: {e}")
            time.sleep(60)

    def run(self):
        """运行机器人"""
        logger.info("Bot始运行...")
        try:
            # 使用线程来运行价格提醒检查
            import threading
            alert_thread = threading.Thread(target=self._check_alerts)
            alert_thread.daemon = True
            alert_thread.start()
            
            # 启动bot
            logger.info("开始轮询消息...")
            self.bot.infinity_polling(timeout=20, long_polling_timeout=10)
            
        except Exception as e:
            logger.error(f"Bot运行错误: {e}", exc_info=True)
        finally:
            logger.info("Bot停止运行")

    async def _analyze_token(self, token_symbol: str) -> Dict[str, Any]:
        """获取并分析特定代币的详细数据"""
        try:
            # 获取基础价格数据
            token_data = await self.dex_screener.get_token_info(token_symbol)
            
            # 获取社交媒体数据
            social_data = await self._get_social_metrics(token_symbol)
            
            # 获取链上数据
            onchain_data = await self._get_onchain_metrics(token_symbol)
            
            # 获取市场情绪数据
            sentiment_data = await self._get_market_sentiment(token_symbol)
            
            return {
                'token_metrics': {
                    'current_price': token_data.get('price'),
                    'price_change_24h': token_data.get('priceChange24h'),
                    'volume_24h': token_data.get('volume24h'),
                    'market_cap': token_data.get('marketCap'),
                    'liquidity': token_data.get('liquidity'),
                    'holders': token_data.get('holders')
                },
                'social_metrics': {
                    'twitter_mentions': social_data.get('twitter_mentions'),
                    'telegram_members': social_data.get('telegram_members'),
                    'github_activity': social_data.get('github_activity')
                },
                'onchain_metrics': {
                    'unique_holders': onchain_data.get('unique_holders'),
                    'transactions_24h': onchain_data.get('transactions_24h'),
                    'buy_vs_sell_ratio': onchain_data.get('buy_sell_ratio')
                },
                'market_sentiment': {
                    'fear_greed_index': sentiment_data.get('fear_greed_index'),
                    'social_sentiment': sentiment_data.get('social_sentiment'),
                    'trending_rank': sentiment_data.get('trending_rank')
                }
            }
        except Exception as e:
            logger.error(f"获取代币分析数据失败: {e}")
            return {}

    def _format_token_analysis(self, token_data: Dict[str, Any]) -> str:
        """格式化代币分析数据为易读格式"""
        if not token_data:
            return "暂无数据"
        
        analysis = f"""📊 市场数据分析：

💰 基础指标：
• 当前价格: ${token_data['token_metrics']['current_price']:.12f}
• 24h涨跌: {token_data['token_metrics']['price_change_24h']:+.2f}%
• 24h成交量: ${token_data['token_metrics']['volume_24h']:,.2f}
• 市值: ${token_data['token_metrics']['market_cap']:,.2f}
• 流动性: ${token_data['token_metrics']['liquidity']:,.2f}

👥 社交指标：
• Twitter提及量: {token_data['social_metrics']['twitter_mentions']:,}
• Telegram成员: {token_data['social_metrics']['telegram_members']:,}
• Github活跃度: {token_data['social_metrics']['github_activity']}

⛓ 链上数据：
• 持有人数: {token_data['onchain_metrics']['unique_holders']:,}
• 24h交易次数: {token_data['onchain_metrics']['transactions_24h']:,}
• 买卖比例: {token_data['onchain_metrics']['buy_vs_sell_ratio']:.2f}

🌡 市场情绪：
• 恐慌贪婪指数: {token_data['market_sentiment']['fear_greed_index']}/100
• 社交情绪: {token_data['market_sentiment']['social_sentiment']}
• 热度排名: #{token_data['market_sentiment']['trending_rank']}
"""
        return analysis

    async def _handle_token_query(self, message: Message, token_name: str):
        """处理代币查询"""
        try:
            # 发送等待消息
            wait_msg = self.bot.reply_to(message, "🔍 正在收集数据，请稍候...")
            
            # 获取代币地址
            token_address = await self._find_token_address(token_name)
            if not token_address:
                self.bot.edit_message_text(
                    "❌ 未找到该代币信息，请检查名称是否正确。",
                    message.chat.id,
                    wait_msg.message_id
                )
                return

            # 获取综合数据
            token_data = await self.dex_screener.get_comprehensive_token_info(token_address)
            
            if not token_data:
                self.bot.edit_message_text(
                    "❌ 获取代币数据失败，请稍后重试。",
                    message.chat.id,
                    wait_msg.message_id
                )
                return

            # 构建分析提示
            system_prompt = """你是一个专业的加密货币分析师。请基于提供的综合数据分析代币。
分析要点：
1. 价格走势和交易量分析
2. 市场情绪和社区活跃度
3. 相对于整体市场的表现
4. 潜在的机会和风险

要求：
- 使用具体数据支持分析
- 保持客观专业
- 突出关键信息
- 包含风险提示"""

            user_prompt = f"""请分析 {token_name} 的最新市场表现。

综合数据：
{self._format_comprehensive_data(token_data)}

请提供详细分析和见解。"""

            # 获取AI分析
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # 构建完整回复
            full_response = (
                f"📊 {token_name} 分析报告\n\n"
                f"{response.choices[0].message.content}\n\n"
                f"⚠️ 免责声明：以上分析仅供参考，不构成投资建议。"
            )
            
            # 更新消息
            self.bot.edit_message_text(
                full_response,
                message.chat.id,
                wait_msg.message_id
            )
            
        except Exception as e:
            logger.error(f"处理代币查询失败: {e}")
            self.bot.reply_to(message, "处理查询时出错，请重试")

    def _format_comprehensive_data(self, data: Dict[str, Any]) -> str:
        """格式化综合数据"""
        result = ""
        
        # DEX数据
        if 'dex_data' in data:
            dex = data['dex_data']
            result += (
                "🔸 交易数据:\n"
                f"价格: ${dex.get('price', 0):.12f}\n"
                f"24h成交量: ${dex.get('volume24h', 0):,.2f}\n"
                f"流动性: ${dex.get('liquidity', 0):,.2f}\n"
            )
        
        # CoinGecko数据
        if 'coingecko_data' in data:
            cg = data['coingecko_data']
            result += (
                "\n🔸 市场数据:\n"
                f"市值: ${cg.get('market_cap', 0):,.2f}\n"
                f"总成交量: ${cg.get('total_volume', 0):,.2f}\n"
            )
        
        # 社交数据
        if 'social_data' in data:
            social = data['social_data']
            result += (
                "\n🔸 社区数据:\n"
                f"Twitter关注: {social.get('twitter', {}).get('followers', 0):,}\n"
                f"Telegram成员: {social.get('telegram', {}).get('members', 0):,}\n"
            )
        
        # 市场情绪
        if 'sentiment' in data:
            sentiment = data['sentiment']
            result += (
                "\n🔸 市场情绪:\n"
                f"整体情绪: {sentiment.get('overall', 'neutral')}\n"
                f"社交情绪: {sentiment.get('social_sentiment', 'neutral')}\n"
            )
        
        return result

    async def _find_token_address(self, token_name: str) -> Optional[str]:
        """根据代币名称查找合约地址"""
        try:
            # 检查缓存
            if token_name in self.token_address_cache:
                cache_data = self.token_address_cache[token_name]
                if time.time() - cache_data['timestamp'] < self.cache_duration:
                    return cache_data['address']

            # 1. 先从 DexScreener 搜索
            search_result = await self.dex_screener.search_token(token_name)
            if search_result:
                return search_result['address']

            # 2. 尝试从 CoinGecko 搜索
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/search?query={token_name}"
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get('coins'):
                            # 返回第一个匹配结果的合约地址
                            return data['coins'][0].get('platforms', {}).get('ethereum')

            # 3. 尝试从 1inch API 搜索
            async with aiohttp.ClientSession() as session:
                url = f"https://api.1inch.io/v5.0/1/tokens"  # 以太坊链为例
                async with session.get(url) as response:
                    if response.status == 200:
                        data = await response.json()
                        for address, token_data in data['tokens'].items():
                            if token_name.lower() in token_data['symbol'].lower():
                                return address

            return None
        except Exception as e:
            logger.error(f"查找代币地址失败: {e}")
            return None

    def _handle_message(self, message: Message):
        """处理消息的主函数"""
        try:
            text = message.text.strip()
            
            # 检查是否是代币地址
            if self._is_token_address(text):
                asyncio.run(self._handle_token_analysis(message))
                return
                
            # 检查是否是代币名称
            if self._looks_like_token_name(text):
                asyncio.run(self._handle_token_name_query(message))
                return
                
            # 其他消息处理...
            self._handle_chat(message)
            
        except Exception as e:
            logger.error(f"处理消息错误: {e}")
            self.bot.reply_to(message, "处理请求时出错，请重试")

    def _looks_like_token_name(self, text: str) -> bool:
        """判断文本是否像代币名称"""
        # 1. 检查是否全是大写字母
        if text.isupper() and len(text) <= 10:
            return True
            
        # 2. 检查是否包含常见代币关键词
        token_keywords = ['token', 'coin', 'swap', 'dao', 'finance', 'protocol']
        if any(keyword in text.lower() for keyword in token_keywords):
            return True
            
        # 3. 检查是否符合代币命名模式
        if re.match(r'^[A-Za-z0-9]+$', text) and len(text) <= 10:
            return True
            
        # 添加编辑距离检查
        known_tokens = ['BTC', 'ETH', 'BNB', ...]  # 已知代币列表
        
        for known_token in known_tokens:
            similarity = SequenceMatcher(None, text.upper(), known_token).ratio()
            if similarity > 0.8:  # 80% 相似度
                return True
            
        return False

    async def _handle_token_name_query(self, message: Message):
        """处理代币名称查询"""
        try:
            token_name = message.text.strip()
            
            # 发送等待消息
            wait_msg = self.bot.reply_to(message, "🔍 正在搜索代币信息，请稍候...")
            
            # 查找代币地址
            token_address = await self._find_token_address(token_name)
            
            if not token_address:
                self.bot.edit_message_text(
                    "❌ 未找到该代币信息，请检查名称是否正确，或直接输入代币合约地址。",
                    message.chat.id,
                    wait_msg.message_id
                )
                return
                
            # 获取代币数据
            token_data = await self._analyze_token(token_address)
            
            if not token_data:
                self.bot.edit_message_text(
                    "❌ 获取代币数据失败，请稍后重试。",
                    message.chat.id,
                    wait_msg.message_id
                )
                return
                
            # 格式化数据
            analysis = self._format_token_analysis(token_data)
            
            # 构建AI分析提示
            system_prompt = """你是加密货币分析师。基于市场数据分析代币投资时机。
遵循以下规则：
1. 简明扼要，每点分析不超过2句话
2. 使用表情符号增加可读性
3. 必须包含风险提示
4. 给出明确的建议"""

            user_prompt = f"""分析{token_name}当前是否值得买入。

市场数据：
{analysis}

请从以下4个方面简要分析：
1. 价格位置评估
2. 市场热度分析
3. 具体建议
4. 风险提示"""

            # 获取AI分析
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            # 发送完整分析
            full_response = (
                f"📊 {token_name} ({token_address[:6]}...{token_address[-4:]}) 分析：\n\n"
                f"{analysis}\n\n"
                f"💡 分析建议：\n"
                f"{response.choices[0].message.content}\n\n"
                f"⚠️ 免责声明：以上分析仅供参考，不构成投资建议。"
            )
            
            # 编辑等待消息为完整分析
            self.bot.edit_message_text(
                full_response,
                message.chat.id,
                wait_msg.message_id
            )
            
        except Exception as e:
            logger.error(f"处理代币名称查询失败: {e}")
            self.bot.reply_to(message, "处理查询时出错，请重试")

def main():
    try:
        logger.info("程序启动")
        bot = CryptoAnalysisBot()
        bot.run()
    except KeyboardInterrupt:
        logger.info("程序被用户中")
    except Exception as e:
        logger.critical(f"程序发生严重错误: {e}", exc_info=True)
    finally:
        logger.info("程序结束")

if __name__ == "__main__":
    main()
