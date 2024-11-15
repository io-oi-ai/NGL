from typing import Dict, Any

class TokenScorer:
    """代币评分系统"""
    
    @staticmethod
    def calculate_score(token_data: Dict[str, Any]) -> int:
        """计算代币综合评分"""
        score = 50  # 基础分
        
        try:
            # 流动性评分 (最高20分)
            liquidity = float(token_data.get('liquidity', 0))
            if liquidity > 1_000_000:  # >100万美元
                score += 20
            elif liquidity > 500_000:  # >50万美元
                score += 15
            elif liquidity > 100_000:  # >10万美元
                score += 10
            elif liquidity > 50_000:   # >5万美元
                score += 5
                
            # 交易量评分 (最高15分)
            volume = float(token_data.get('volume24h', 0))
            volume_to_liquidity = volume / liquidity if liquidity > 0 else 0
            if volume_to_liquidity > 1:  # 24h交易量超过流动性
                score += 15
            elif volume_to_liquidity > 0.5:
                score += 10
            elif volume_to_liquidity > 0.1:
                score += 5
                
            # 价格趋势评分 (最高15分)
            price_change = float(token_data.get('priceChange24h', 0))
            if price_change > 100:     # 涨幅超过100%
                score += 15
            elif price_change > 50:    # 涨幅超过50%
                score += 10
            elif price_change > 20:    # 涨幅超过20%
                score += 5
            elif price_change < -50:   # 跌幅超过50%
                score -= 15
                
            # 交易活跃度评分 (最高10分)
            txns = token_data.get('txns', {})
            buys = int(txns.get('buys', 0))
            sells = int(txns.get('sells', 0))
            total_txns = buys + sells
            
            if total_txns > 1000:
                score += 10
            elif total_txns > 500:
                score += 7
            elif total_txns > 100:
                score += 5
                
            # 买卖比评分 (最高10分)
            if buys > 0 and sells > 0:
                buy_sell_ratio = buys / sells
                if buy_sell_ratio > 2:  # 买入是卖出的2倍以上
                    score += 10
                elif buy_sell_ratio > 1.5:
                    score += 7
                elif buy_sell_ratio > 1:
                    score += 5
                
        except Exception as e:
            print(f"计算评分时出错: {e}")
            return 50  # 出错时返回基础分
            
        # 确保分数在0-100之间
        return max(0, min(100, score))

    @staticmethod
    def get_score_explanation(score: int) -> str:
        """获取评分解释"""
        if score >= 90:
            return "极佳 🌟 - 项目表现优异，各项指标都很强劲"
        elif score >= 80:
            return "优秀 ⭐ - 项目整体表现良好，具有较强的发展潜力"
        elif score >= 70:
            return "良好 👍 - 项目基本面稳健，值得关注"
        elif score >= 60:
            return "一般 👌 - 项目表现中规中矩，建议继续观察"
        elif score >= 50:
            return "待观察 👀 - 项目还需要时间验证"
        else:
            return "风险较高 ⚠️ - 建议谨慎对待" 