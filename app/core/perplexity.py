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
    
    async def process_text(self, text: str, source_link: str = '') -> Dict:
        prompt = f'''Analyze the following text and structure it according to this template:
        - Title (if identifiable)
        - Brief description/annotation
        - Main text/key data
        - Source link: {source_link}
        - Publication date
        
        Text to analyze: {text}
        
        Return structured JSON with fields: title, description, main_text, source, date'''
        
        payload = {
            'model': 'sonar-pro',
            'messages': [
                {'role': 'system', 'content': 'Будь точным и кратким.'},
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
                    return self._parse_response(result)
                else:
                    error_text = await response.text()
                    raise Exception(f'Perplexity API error: {response.status} {error_text}')
    
    def _parse_response(self, response: Dict) -> Dict:
        try:
            content = response['choices'][0]['message']['content']
            # Parse JSON from response
            structured_data = json.loads(content)
            return structured_data
        except:
            # Fallback parsing if JSON fails
            content = response['choices'][0]['message']['content']
            return {
                'title': 'Untitled',
                'description': content[:200],
                'main_text': content,
                'source': '',
                'date': ''
            } 