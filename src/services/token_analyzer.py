import logging
from typing import Dict, Any, Optional
import sys
import os

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from src.api.dex_screener import DexScreenerAPI
from src.services.token_scorer import TokenScorer

class TokenAnalyzer:
    """代币分析类"""
    
    def __init__(self):
        self.dex_screener = DexScreenerAPI()
        self.token_scorer = TokenScorer()
        
    async def analyze_token(self, token_address: str) -> Optional[str]:
        """分析代币并返回格式化的结果"""
        try:
            # 获取代币数据
            token_data = self.dex_screener.get_token_info(token_address)
            if not token_data:
                return None
                
            # 计算评分
            score = self.token_scorer.calculate_score(token_data)
            
            # 格式化结果
            return self._format_token_info(token_data, score)
            
        except Exception as e:
            logging.error(f"代币分析错误: {e}")
            return None

    def _format_token_info(self, token_data: Dict[str, Any], score: int) -> str:
        """格式化代币信息"""
        try:
            token_name = token_data['baseToken'].get('name', 'Unknown')
            token_symbol = token_data['baseToken'].get('symbol', 'Unknown')
            
            return f"""
📊 代币信息：

名称: {token_name} ({token_symbol})

💰 市场数据:
• 价格: ${token_data['price']:.12f}
• 流动性: ${token_data['liquidity']:,.2f}
• 24h成交量: ${token_data['volume24h']:,.2f}
• 24h涨跌: {token_data['priceChange24h']:+.2f}% {'🚀' if token_data['priceChange24h'] > 0 else '📉'}

📈 综合评分: {score}/100
{self.token_scorer.get_score_explanation(score)}

🔄 交易数据:
• 买入/卖出: {token_data['txns'].get('buys', 0)}/{token_data['txns'].get('sells', 0)}
• DEX: {token_data['dex']}
• 链: {token_data['chain']}
"""
        except Exception as e:
            logging.error(f"格式化代币信息时出错: {e}")
            return "格式化数据时出错"