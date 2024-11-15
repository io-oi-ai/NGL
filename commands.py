from typing import Dict, Any
from telebot import TeleBot
from telebot.types import Message
from openai import OpenAI
import logging
import os
from dotenv import load_dotenv
import re
import sys

# 添加项目根目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入所需的类
from src.api.dex_screener import DexScreenerAPI

# 加载环境变量
load_dotenv()

# 初始化 OpenAI 客户端
client = OpenAI(
    api_key="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",
    base_url="https://api.openai.com/v1"
)

class CommandHandler:
    """命令处理类，包含所有命令的具体实现"""
    
    def __init__(self):
        self.conversation_history = {}  # 用于存储每个用户的对话历史
        self.dex_screener = DexScreenerAPI()  # 现在可以正确初始化了
        
    def handle_message(self, message: Message) -> tuple[str, dict]:
        """处理用户消息，支持自然语言对话"""
        user_id = message.from_user.id
        text = message.text.strip()

        # 初始化用户的对话历史
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []

        try:
            # 分析用户意图
            intent = self._analyze_intent(text, self.conversation_history[user_id])
            
            # 根据意图处理消息
            if intent['type'] == 'token_analysis':
                return self._handle_token_analysis(intent['token_address'])
            elif intent['type'] == 'market_question':
                return self._handle_market_question(intent['question'], self.conversation_history[user_id])
            elif intent['type'] == 'general_chat':
                return self._handle_general_chat(text, self.conversation_history[user_id])
            else:
                return "我不太理解您的问题，您可以：\n1. 直接发送代币合约地址\n2. 询问市场情况\n3. 使用 /help 查看帮助", {}

        except Exception as e:
            logging.error(f"处理消息出错: {e}")
            return "抱歉，处理您的消息时出现错误，请重试。", {}

    def _analyze_intent(self, text: str, history: list) -> dict:
        """分析用户意图"""
        try:
            # 调用 OpenAI API 分析用户意图
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个加密货币分析机器人的助手，负责理解用户意图。
                        可能的意图类型包括：
                        1. token_analysis - 用户想分析特定代币
                        2. market_question - 用户询问市场相关问题
                        3. general_chat - 普通聊天或其他问题"""
                    },
                    *[{"role": msg["role"], "content": msg["content"]} for msg in history[-5:]],  # 包含最近5条对话历史
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=100
            )

            # 解析意图
            if re.match(r'^0x[a-fA-F0-9]{40}$', text) or len(text) in [32, 44]:
                return {"type": "token_analysis", "token_address": text}
            
            content = response.choices[0].message.content.lower()
            
            if any(keyword in content for keyword in ['price', 'token', 'coin', 'contract', '代币', '价格']):
                return {"type": "market_question", "question": text}
            else:
                return {"type": "general_chat"}

        except Exception as e:
            logging.error(f"分析意图时出错: {e}")
            return {"type": "unknown"}

    def _handle_market_question(self, question: str, history: list) -> tuple[str, dict]:
        """处理市场相关问题"""
        try:
            # 获取最新市场数据
            market_data = self._get_market_overview()
            
            # 构建包含实时数据的提示词
            system_prompt = """你是一个专业的加密货币分析师。
基于最新的市场数据进行分析，给出具体的见解。

分析要求：
1. 基于实时数据分析当前市场趋势
2. 指出最活跃的代币和链
3. 分析市场热点和机会
4. 使用表情符号增加可读性
5. 保持专业性和客观性"""

            user_prompt = f"""用户问题：{question}

最新市场数据：
{self._format_market_data(market_data)}

请基于这些实时数据回答用户问题。"""

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *[{"role": msg["role"], "content": msg["content"]} for msg in history[-5:]],
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )

            answer = response.choices[0].message.content
            
            # 更新对话历史
            history.append({"role": "user", "content": question})
            history.append({"role": "assistant", "content": answer})
            
            return answer, {}

        except Exception as e:
            logging.error(f"处理市场问题时出错: {e}")
            return "抱歉，我现在无法回答这个问题，请稍后再试。", {}

    def _get_market_overview(self) -> Dict[str, Any]:
        """获取市场概览数据"""
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
                        'hot_tokens': hot_tokens[:3]  # 只取前3个
                    }
                    
                    # 添加到趋势列表
                    market_data['trending'].extend(hot_tokens)
            
            # 按24h成交量排序趋势代币
            market_data['trending'].sort(key=lambda x: x['volume24h'], reverse=True)
            market_data['trending'] = market_data['trending'][:5]  # 只保留前5个
            
            return market_data
            
        except Exception as e:
            logging.error(f"获取市场概览数据时出错: {e}")
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

    def _handle_general_chat(self, text: str, history: list) -> tuple[str, dict]:
        """处理普通聊天"""
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": """你是一个友好的加密货币机器人，可以进行日常对话。
                        请用轻松愉快的语气回答，适当使用表情符号。
                        如果话题涉及加密货币，可以分享一些见解。"""
                    },
                    *[{"role": msg["role"], "content": msg["content"]} for msg in history[-5:]],
                    {"role": "user", "content": text}
                ],
                temperature=0.8,
                max_tokens=200
            )

            answer = response.choices[0].message.content
            
            # 更新对话历史
            history.append({"role": "user", "content": text})
            history.append({"role": "assistant", "content": answer})
            
            return answer, {}

        except Exception as e:
            logging.error(f"处理普通聊天时出错: {e}")
            return "抱歉，我现在无法回答，请稍后再试。", {}

    def _handle_token_analysis(self, token_address: str) -> tuple[str, dict]:
        """处理代币分析请求"""
        # 使用现有的代币分析逻辑
        return self.format_token_info(token_data) # type: ignore

    @staticmethod
    def handle_start(message: Message) -> str:
        """处理 /start 命令"""
        return """
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

    @staticmethod
    def handle_help(message: Message) -> str:
        """处理 /help 命令"""
        return """
🤖 代币分析机器人使用指南：
...  # 完整的帮助文本
        """

    @staticmethod
    def format_token_info(token_data: Dict[str, Any]) -> tuple[str, dict]:
        """格式化代币信息"""
        # 计算综合评分
        score = CommandHandler._calculate_token_score(token_data)
        
        # 生成市场叙事
        narrative = CommandHandler._generate_market_narrative(token_data)
        
        # 简化格式，去除 HTML 标签
        contract_address = token_data['baseToken'].get('address', 'Unknown')
        token_name = token_data['baseToken'].get('name', 'Unknown')
        token_symbol = token_data['baseToken'].get('symbol', 'Unknown')
        
        message = f"""
📊 代币信息：

📝 合约: {contract_address}

名称: {token_name} ({token_symbol})

💰 市场数据:
价格: ${token_data['price']:.12f}
流动性: ${token_data['liquidity']:,.2f}
24h成交量: ${token_data['volume24h']:,.2f}
24h涨跌: {token_data['priceChange24h']:+.2f}% {'🚀' if token_data['priceChange24h'] > 0 else '📉'}

📈 综合评分: {score}/100

📖 市场分析:
{narrative}
"""
        # 返回消息文本，不使用特殊格式
        return message, {}

    @staticmethod
    def _calculate_token_score(token_data: Dict[str, Any]) -> int:
        """计算代币综合评分"""
        score = 50  # 基础分
        
        # 流动性评分 (最高20分)
        liquidity = token_data['liquidity']
        if liquidity > 1_000_000:  # >100万美元
            score += 20
        elif liquidity > 500_000:  # >50万美元
            score += 15
        elif liquidity > 100_000:  # >10万美元
            score += 10
        elif liquidity > 50_000:   # >5万美元
            score += 5
            
        # 交易量评分 (最高15分)
        volume = token_data['volume24h']
        if volume > 1_000_000:     # >100万美元
            score += 15
        elif volume > 500_000:     # >50万美元
            score += 10
        elif volume > 100_000:     # >10万美元
            score += 5
            
        # 价格趋势评分 (最高15分)
        price_change = token_data['priceChange24h']
        if price_change > 100:     # 涨幅超过100%
            score += 15
        elif price_change > 50:    # 涨幅超过50%
            score += 10
        elif price_change > 20:    # 涨幅超过20%
            score += 5
        elif price_change < -50:   # 跌幅超过50%
            score -= 15
            
        return min(max(score, 0), 100)  # 确保分数在0-100之间

    @staticmethod
    def _generate_market_narrative(token_data: Dict[str, Any]) -> str:
        """使用AI生成市场叙事分析"""
        try:
            token_name = f"{token_data['baseToken'].get('name', 'Unknown')} ({token_data['baseToken'].get('symbol', 'Unknown')})"
            
            # 判断是否为 meme 代币
            is_meme = CommandHandler._is_meme_token(token_name, token_data)
            
            try:
                # 构建提示词
                system_prompt = """你是一个专业的加密货币分析师，同时也是互联网文化和meme专家。
请用简短生动的语言分析项目，重点突出项目特色和市场表现。
如果是meme代币，要突出其文化梗点和社区特色。
分析要简洁有趣，使用表情符号增加可读性。"""

                user_prompt = f"""请简要分析这个{'meme' if is_meme else ''}代币项目：

项目名称：{token_name}
链：{token_data['chain']}
DEX：{token_data['dex']}
当前价格：${token_data['price']:.12f}
24h涨跌：{token_data['priceChange24h']:+.2f}%
成交量：${token_data['volume24h']:,.2f}
买入/卖出：{token_data['txns'].get('buys', 0)}/{token_data['txns'].get('sells', 0)}

{'请分析：\n1. 项目梗点和社区特色\n2. 市场表现和活跃度' if is_meme else '请分析：\n1. 项目特点\n2. 市场表现'}

要求：
- 分析要简短精炼（100字左右）
- 突出关键信息
- 使用表情符号
- 语言要生动活泼"""

                # 调用 OpenAI API
                completion = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200  # 减少token数量以获得更简短的回复
                )
                
                return completion.choices[0].message.content

            except Exception as api_error:
                logging.error(f"OpenAI API 调用错误: {api_error}")
                if is_meme:
                    return CommandHandler._generate_fallback_meme_analysis(token_data)
                else:
                    return CommandHandler._generate_fallback_analysis(token_data)

        except Exception as e:
            logging.error(f"AI生成失败: {e}")
            return CommandHandler._generate_fallback_analysis(token_data)

    @staticmethod
    def _generate_fallback_meme_analysis(token_data: Dict[str, Any]) -> str:
        """生成备用的meme代币分析"""
        token_name = f"{token_data['baseToken'].get('name', 'Unknown')} ({token_data['baseToken'].get('symbol', 'Unknown')})"
        token_icon = CommandHandler._get_token_icon(token_name)
        meme_type = CommandHandler._analyze_meme_reference(token_name)
        
        return (
            f"{token_icon} 项目特色：\n"
            f"• {token_name} 基于{meme_type}文化，当前超级火热 🔥\n"
            f"• 社区氛围：{'超级活跃' if token_data['volume24h'] > token_data['liquidity'] * 2 else '稳定发展'} ✨\n\n"
            f"📊 市场表现：\n"
            f"• 24h交：{token_data['txns'].get('buys', 0)}买/{token_data['txns'].get('sells', 0)}卖\n"
            f"• {'买盘强势 🚀' if token_data['txns'].get('buys', 0) > token_data['txns'].get('sells', 0) else '市场平稳 ⚖️'}"
        )

    @staticmethod
    def _get_token_icon(token_name: str) -> str:
        """获取代币图标"""
        name_lower = token_name.lower()
        if 'doge' in name_lower or 'shib' in name_lower or 'inu' in name_lower:
            return '🐕'
        elif 'pepe' in name_lower or 'frog' in name_lower:
            return '🐸'
        elif 'moon' in name_lower:
            return '🌙'
        elif 'ai' in name_lower or 'gpt' in name_lower:
            return '🤖'
        elif 'cat' in name_lower:
            return '🐱'
        elif 'elon' in name_lower:
            return '🚀'
        else:
            return '💎'

    @staticmethod
    def _analyze_meme_reference(token_name: str) -> str:
        """分析代币名称中的meme梗"""
        name_lower = token_name.lower()
        
        if 'elon' in name_lower or 'musk' in name_lower:
            return "马斯克"
        elif 'pepe' in name_lower:
            return "青蛙佩佩"
        elif 'doge' in name_lower or 'shib' in name_lower:
            return "狗狗币"
        elif 'inu' in name_lower:
            return "柴犬"
        elif 'moon' in name_lower:
            return "登月"
        elif 'chad' in name_lower:
            return "硬汉"
        elif 'wojak' in name_lower:
            return "哭泣男孩"
        elif 'cat' in name_lower:
            return "猫咪"
        elif 'ai' in name_lower or 'gpt' in name_lower:
            return "人工智能"
        else:
            return "创新"

    @staticmethod
    def _is_meme_token(token_name: str, token_data: Dict[str, Any]) -> bool:
        """判断是否为meme代币"""
        # 检查名称中是否包含常见的meme关键词
        meme_keywords = [
            'pepe', 'doge', 'shib', 'inu', 'elon', 'moon', 'safe', 'baby',
            'rocket', 'chad', 'wojak', 'cat', 'dog', 'meme', 'ai', 'coin',
            'token', 'gpt', 'chat', 'based', 'rick', 'morty', 'punk', 'ape',
            'monkey', 'bird', 'frog', 'bear', 'bull', 'diamond', 'hands'
        ]
        
        name_lower = token_name.lower()
        
        # 检查名称中是否包含meme关键词
        if any(keyword in name_lower for keyword in meme_keywords):
            return True
            
        # 检查价格和交易特征
        is_low_price = token_data['price'] < 0.0001
        is_high_volatility = abs(token_data['priceChange24h']) > 50
        is_high_volume = token_data['volume24h'] > token_data['liquidity'] * 2
        
        # 如果同时满足低价、高波动、高成交量，也认为是meme代币
        if is_low_price and (is_high_volatility or is_high_volume):
            return True
            
        return False

    @staticmethod
    def _generate_fallback_analysis(token_data: Dict[str, Any]) -> str:
        """生成备用的普通代币分析"""
        token_name = f"{token_data['baseToken'].get('name', 'Unknown')} ({token_data['baseToken'].get('symbol', 'Unknown')})"
        
        return (
            f"💎 项目概况：\n"
            f"• {token_name} ({token_data['chain']})\n"
            f"• {'发展初期' if token_data['liquidity'] < 100000 else '成长阶段'}\n\n"
            f"📊 市场表现：\n"
            f"• 流动性：{'充足' if token_data['liquidity'] > 500000 else '稳定'}\n"
            f"• 趋势：{'上升' if token_data['priceChange24h'] > 0 else '调整'} "
            f"{'🚀' if token_data['priceChange24h'] > 0 else '📉'}"
        )