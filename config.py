import os

# API Keys
OPENAI_API_KEY = "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"
TELEGRAM_BOT_TOKEN = '7520032539:AAHdT_kU9Vo7SHeIiw0enDKz3p4ZSEM8fIw'
ETHERSCAN_API_KEY = 'YOUR_ETHERSCAN_API_KEY'

# 代理设置
PROXY = None  # 先禁用代理，直接连接

# 如果需要代理，可以设置为：
# PROXY = {
#     'http': 'http://127.0.0.1:7890',
#     'https': 'http://127.0.0.1:7890'
# }

# AI 模型配置
MODEL_CONFIG = {
    'name': "gpt-4o-mini",
    'max_tokens': 2048,
    'temperature': 0.7
}

# 日志配置
LOG_CONFIG = {
    'level': 'DEBUG',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'filename': 'logs/bot.log',
    'max_bytes': 10*1024*1024,  # 10MB
    'backup_count': 5
}

# OpenAI API 配置
OPENAI_API_KEY = "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"

# 添加重试和速率限制配置
API_CONFIG = {
    'max_retries': 3,
    'retry_delay': 1,
    'rate_limit_per_minute': 50
}

API_KEYS = {
    'COINGECKO_API_KEY': 'your_key',
    'TWITTER_API_KEY': 'your_key',
    'REDDIT_API_KEY': 'your_key',
    'NEWS_API_KEY': 'your_key'
}