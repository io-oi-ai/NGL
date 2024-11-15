import logging
from telebot import TeleBot
import asyncio
from services.message_handler import MessageHandler
from services.alert_service import AlertService
from config import TELEGRAM_BOT_TOKEN

class CryptoAnalysisBot:
    def __init__(self):
        self.bot = TeleBot(TELEGRAM_BOT_TOKEN)
        self.message_handler = MessageHandler()
        self.alert_service = AlertService()
        self._setup_handlers()
        
    def _setup_handlers(self):
        """设置消息处理器"""
        @self.bot.message_handler(func=lambda message: True)
        async def handle_message(message):
            await self.message_handler.handle(message, self.bot)
            
    async def _check_alerts(self):
        """定期检查价格提醒"""
        while True:
            try:
                triggered_alerts = await self.alert_service.check_alerts()
                for user_id, message in triggered_alerts.items():
                    self.bot.send_message(user_id, message)
            except Exception as e:
                logging.error(f"检查价格提醒时出错: {e}")
            await asyncio.sleep(60)  # 每分钟检查一次
            
    def run(self):
        """运行机器人"""
        logging.info("Bot开始运行...")
        try:
            # 启动价格提醒检查
            asyncio.create_task(self._check_alerts())
            # 启动bot
            self.bot.infinity_polling(timeout=10, long_polling_timeout=5)
        except Exception as e:
            logging.error(f"Bot运行错误: {e}")
        finally:
            logging.info("Bot停止运行") 