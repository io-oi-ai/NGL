from openai import OpenAI
import logging
import time
from config import OPENAI_API_KEY, MODEL_CONFIG, API_CONFIG

class AIClient:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.last_request_time = 0
        
    def get_ai_response(self, prompt):
        try:
            # 速率限制
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < (60 / API_CONFIG['rate_limit_per_minute']):
                time.sleep((60 / API_CONFIG['rate_limit_per_minute']) - time_since_last_request)
            
            # 重试机制
            for attempt in range(API_CONFIG['max_retries']):
                try:
                    response = self.client.chat.completions.create(
                        model=MODEL_CONFIG['name'],
                        messages=[
                            {"role": "system", "content": "你是一个专业的加密货币分析师，擅长分析代币项目的优势、风险和市场机会。"},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=MODEL_CONFIG['temperature'],
                        max_tokens=MODEL_CONFIG['max_tokens']
                    )
                    
                    self.last_request_time = time.time()
                    return response.choices[0].message.content if response.choices else None
                    
                except Exception as e:
                    if attempt == API_CONFIG['max_retries'] - 1:
                        raise e
                    time.sleep(API_CONFIG['retry_delay'] * (attempt + 1))
                    
        except Exception as e:
            logging.error(f"生成 AI 响应时出错: {e}")
            return None