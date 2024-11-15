import logging
from typing import Dict, Optional
from datetime import datetime
import asyncio
from ..api.dex_screener import DexScreenerAPI

class PriceAlert:
    def __init__(self, token_address: str, target_price: float, condition: str, user_id: int):
        self.token_address = token_address
        self.target_price = target_price
        self.condition = condition  # '>' or '<'
        self.user_id = user_id
        self.created_at = datetime.now()
        
class AlertService:
    def __init__(self):
        self.alerts = {}
        self.dex_screener = DexScreenerAPI()
        
    def add_alert(self, alert: PriceAlert) -> bool:
        """添加新的价格提醒"""
        try:
            key = f"{alert.user_id}_{alert.token_address}_{alert.target_price}"
            self.alerts[key] = alert
            return True
        except Exception as e:
            logging.error(f"添加价格提醒失败: {e}")
            return False
            
    def get_triggered_alerts(self) -> Dict[int, str]:
        """获取已触发的提醒"""
        triggered = {}
        for key, alert in list(self.alerts.items()):
            try:
                token_data = self.dex_screener.get_token_info(alert.token_address)
                if token_data:
                    current_price = token_data['price']
                    if ((alert.condition == '>' and current_price > alert.target_price) or
                        (alert.condition == '<' and current_price < alert.target_price)):
                        triggered[alert.user_id] = (
                            f"🔔 价格提醒！\n"
                            f"代币: {token_data['baseToken']['symbol']}\n"
                            f"当前价格: ${current_price}\n"
                            f"目标价格: ${alert.target_price}"
                        )
                        del self.alerts[key]
            except Exception as e:
                logging.error(f"检查提醒时出错: {e}")
        return triggered