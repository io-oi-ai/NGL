from typing import Dict, List, Any
import logging
from ..api.dex_screener import DexScreenerAPI

class TrendAnalyzer:
    def __init__(self):
        self.dex_screener = DexScreenerAPI()
        
    async def analyze_market_trend(self, chain_id: str) -> Dict[str, Any]:
        """分析市场整体趋势"""
        try:
            # 获取热门代币数据
            hot_tokens = await self.get_hot_tokens(chain_id)
            
            # 计算市场指标
            total_volume = sum(token['volume24h'] for token in hot_tokens)
            avg_price_change = sum(token['priceChange24h'] for token in hot_tokens) / len(hot_tokens)
            
            # 分析买卖压力
            buy_pressure = sum(
                token['txns'].get('buys', 0) for token in hot_tokens
            )
            sell_pressure = sum(
                token['txns'].get('sells', 0) for token in hot_tokens
            )
            
            return {
                'market_sentiment': self._calculate_sentiment(avg_price_change),
                'total_volume': total_volume,
                'avg_price_change': avg_price_change,
                'buy_pressure': buy_pressure,
                'sell_pressure': sell_pressure,
                'hot_tokens': hot_tokens[:5]
            }
            
        except Exception as e:
            logging.error(f"分析市场趋势时出错: {e}")
            return {}
            
    def _calculate_sentiment(self, price_change: float) -> str:
        """计算市场情绪"""
        if price_change > 10:
            return "极度乐观 🚀"
        elif price_change > 5:
            return "乐观 📈"
        elif price_change > -5:
            return "稳定 ↔️"
        elif price_change > -10:
            return "悲观 📉"
        else:
            return "极度悲观 🔻" 