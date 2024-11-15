import requests
import json

class ClaudeAIModel:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "x-api-key": api_key
        }
        
    def generate_response(self, prompt, max_length=2048):
        try:
            payload = {
                "model": "claude-3-sonnet-20240229",
                "max_tokens": max_length,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
            
            response = requests.post(
                self.api_url, 
                headers=self.headers,
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"API Response: {response_data}")
                return response_data['content'][0]['text']
            else:
                error_message = f"API调用失败: {response.status_code}\n响应内容: {response.text}"
                print(error_message)
                return error_message
                
        except Exception as e:
            error_message = f"生成回复时出错: {str(e)}"
            print(error_message)
            return error_message