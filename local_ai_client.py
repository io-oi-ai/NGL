from ai_models import ClaudeAIModel
import logging

class AIClient:
    def __init__(self, api_key=None):
        self.model = ClaudeAIModel(api_key)
        self.conversation_history = []
        
    def get_ai_response(self, prompt):
        try:
            logging.info(f"正在处理用户输入: {prompt}")
            
            # 添加到对话历史
            self.conversation_history.append({
                "role": "user", 
                "content": prompt
            })
            
            # 获取响应
            logging.info("正在调用 Claude API...")
            response = self.model.generate_response(prompt)
            logging.info(f"收到 API 响应: {response}")
            
            # 添加响应到对话历史
            if response:
                self.conversation_history.append({
                    "role": "assistant", 
                    "content": response
                })
            
            return response
        except Exception as e:
            error_message = f"Error generating response: {e}"
            logging.error(error_message)
            return "抱歉，生成回复时出现错误。"