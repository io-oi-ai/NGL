import re
import logging
from telebot import TeleBot
from telebot.types import Message, ReplyKeyboardMarkup, KeyboardButton
from .token_analyzer import TokenAnalyzer
from .chain_service import ChainService
from .alert_service import AlertService, PriceAlert
from .trend_analyzer import TrendAnalyzer

class MessageHandler:
    def __init__(self):
        self.token_analyzer = TokenAnalyzer()
        self.chain_service = ChainService()
        self.alert_service = AlertService()
        self.trend_analyzer = TrendAnalyzer()
        
    def handle(self, message: Message, bot: TeleBot) -> None:
        """处理所有incoming消息"""
        try:
            if message.text.startswith('/'):
                self._handle_command(message, bot)
            elif re.match(r'^0x[a-fA-F0-9]{40}$', message.text) or \
                 self.chain_service.is_solana_address(message.text):
                self._handle_token_analysis(message, bot)
            else:
                bot.reply_to(message, "请发送正确的代币合约地址(支持EVM链和Solana)或使用命令。")
                
        except Exception as e:
            logging.error(f"处理消息时出错: {e}")
            bot.reply_to(message, "处理消息时出错，请重试。")
            
    def _handle_command(self, message: Message, bot: TeleBot) -> None:
        """处理命令"""
        command = message.text.split()[0].lower()
        
        if command == '/hot':
            self._handle_hot_command(message, bot)
        elif command == '/alert':
            self._handle_alert_command(message, bot)
        elif command == '/trend':
            self._handle_trend_command(message, bot)
        elif command == '/start':
            self._handle_start_command(message, bot)
        elif command == '/help':
            self._handle_help_command(message, bot)
            
    def _handle_hot_command(self, message: Message, bot: TeleBot) -> None:
        """处理/hot命令"""
        try:
            # 创建链选择键盘
            markup = ReplyKeyboardMarkup(resize_keyboard=True)
            chains = self.chain_service.get_all_chains()
            
            for chain in chains:
                markup.add(KeyboardButton(f"🔍 {chain['name']}"))
                
            bot.reply_to(
                message,
                "请选择要查看的链:",
                reply_markup=markup
            )
            
        except Exception as e:
            logging.error(f"处理hot命令时出错: {e}")
            bot.reply_to(message, "获取热门代币失败，请重试。")
            
    def _handle_alert_command(self, message: Message, bot: TeleBot) -> None:
        """处理/alert命令"""
        try:
            parts = message.text.split()
            if len(parts) != 4:
                bot.reply_to(
                    message,
                    "格式错误。正确格式：/alert <合约地址> <价格> <条件>\n"
                    "例如：/alert 0x123... 0.01 >"
                )
                return
                
            _, address, price, condition = parts
            
            if condition not in ['>', '<']:
                bot.reply_to(message, "条件只能是 > 或 <")
                return
                
            alert = PriceAlert(
                token_address=address,
                target_price=float(price),
                condition=condition,
                user_id=message.from_user.id
            )
            
            if self.alert_service.add_alert(alert):
                bot.reply_to(message, "✅ 价格提醒设置成功！")
            else:
                bot.reply_to(message, "❌ 设置价格提醒失败，请重试。")
                
        except ValueError:
            bot.reply_to(message, "价格格式错误，请输入有效的数字。")
        except Exception as e:
            logging.error(f"设置价格提醒时出错: {e}")
            bot.reply_to(message, "设置价格提醒时出错，请重试。")
            
    def _handle_trend_command(self, message: Message, bot: TeleBot) -> None:
        """处理/trend命令"""
        try:
            # 获取市场趋势分析
            trend_data = self.trend_analyzer.analyze_market_trend('bsc')  # 默认分析BSC
            
            if not trend_data:
                bot.reply_to(message, "获取市场趋势数据失败，请重试。")
                return
                
            # 构建回复消息
            reply = (
                "📊 市场趋势分析\n\n"
                f"市场情绪: {trend_data['market_sentiment']}\n"
                f"24h总成交量: ${trend_data['total_volume']:,.2f}\n"
                f"平均价格变化: {trend_data['avg_price_change']:+.2f}%\n\n"
                f"买入压力: {trend_data['buy_pressure']}\n"
                f"卖出压力: {trend_data['sell_pressure']}\n\n"
                "🔥 热门代币:\n"
            )
            
            for token in trend_data['hot_tokens']:
                reply += (
                    f"• {token['baseToken']['symbol']}: "
                    f"${token['price']:.12f} "
                    f"({token['priceChange24h']:+.2f}%)\n"
                )
                
            bot.reply_to(message, reply)
            
        except Exception as e:
            logging.error(f"处理trend命令时出错: {e}")
            bot.reply_to(message, "获取市场趋势失败，请重试。")

    def _handle_start_command(self, message: Message, bot: TeleBot) -> None:
        """处理 /start 命令"""
        try:
            welcome_text = """
👋 欢迎使用代币分析机器人！

🔍 支持的链:
• Ethereum (ETH)
• BNB Chain (BSC)
• Polygon
• Arbitrum
• Base
• Solana (SOL)

📝 可用命令：
/help - 显示帮助信息
/hot - 显示热门代币
/trend - 市场趋势分析
/alert - 设置价格提醒

💡 使用方法：
直接发送代币合约地址即可获取详细分析
支持 EVM 链地址(0x...)和 Solana 地址
            """
            bot.reply_to(message, welcome_text)
        except Exception as e:
            logging.error(f"处理 start 命令时出错: {e}")
            bot.reply_to(message, "命令处理出错，请重试")

    def _handle_help_command(self, message: Message, bot: TeleBot) -> None:
        """处理 /help 命令"""
        try:
            help_text = """
🤖 代币分析机器人使用指南：

1️⃣ 基本功能：
• 直接发送代币合约地址，获取详细分析
• 支持 EVM 链和 Solana 代币
• AI 驱动的市场分析
• 实时价格监控

2️⃣ 命令列表：
/hot - 显示当前热门代币
• 可选择不同链查看
• 显示价格、交易量等信息

/trend - 市场趋势分析
• 显示市场情绪
• 交易量分析
• 买卖压力分析

/alert <合约地址> <价格> <条件>
• 设置价格提醒
• 条件支持 > 和 <
• 例如：/alert 0x123... 0.01 >

3️⃣ 分析内容包括：
• 基本市场数据
• 流动性分析
• 价格走势
• 交易量分析
• 综合评分
• AI 市场分析

4️⃣ 支持的链：
• ETH - Ethereum
• BSC - BNB Chain
• POLYGON - Polygon
• ARBITRUM - Arbitrum
• BASE - Base
• SOL - Solana

❓ 如有问题，请联系管理员
            """
            bot.reply_to(message, help_text)
        except Exception as e:
            logging.error(f"处理 help 命令时出错: {e}")
            bot.reply_to(message, "命令处理出错，请重试")
            