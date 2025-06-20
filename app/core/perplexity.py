import aiohttp
import json
from typing import Dict, Optional

class PerplexityProcessor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = 'https://api.perplexity.ai'
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    async def process_text(self, prompt: str) -> str:
        """Отправляет готовый промпт в Perplexity и возвращает текстовый ответ."""
        payload = {
            'model': 'sonar-pro', # Исправленная модель с доступом в интернет
            'messages': [
                {'role': 'system', 'content': 'Ты — помощник, который точно следует инструкциям по форматированию текста.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.2,
            'max_tokens': 1000
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{self.base_url}/chat/completions',
                headers=self.headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    # Просто возвращаем текстовое содержимое ответа
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    raise Exception(f'Perplexity API error: {response.status} {error_text}') 