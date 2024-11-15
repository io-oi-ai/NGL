from typing import Union
import logging

def format_price(price: float) -> str:
    """格式化价格显示"""
    if price < 0.0001:
        return f"{price:.8e}"
    elif price < 0.01:
        return f"{price:.6f}"
    else:
        return f"{price:.2f}"

def format_number(num: Union[int, float]) -> str:
    """格式化数字显示"""
    if num >= 1_000_000:
        return f"{num/1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num/1_000:.1f}K"
    else:
        return str(num)

def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ) 