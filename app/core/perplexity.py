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
    
    def create_prompt(self, announcement_text: str, ocr_data: str, custom_id: str, markup_percentage: float) -> str:
        """
        Создает промпт для Perplexity на основе текста объявления, OCR данных и наценки.
        """
        prompt = f"""
Ты — эксперт по автомобилям. Проанализируй объявление и создай привлекательное описание для продажи автомобиля.

Исходный текст объявления:
{announcement_text}

Дополнительная информация из фото (OCR):
{ocr_data if ocr_data else "Информация из фото не найдена"}

Требования к результату:
1. Создай КРАТКОЕ структурированное описание автомобиля (максимум 800 символов)
2. Добавь наценку {markup_percentage}% к цене (если цена указана)
3. Используй формат: [Марка] [Модель] [Год] - Цена: [цена с наценкой]
4. Добавь только основные характеристики (год, двигатель, пробег, коробка)
5. Сделай текст привлекательным для покупателей

Пример структуры ответа (КРАТКО):
[Марка] [Модель] [Год] - Цена: [цена с наценкой]

Краткое описание автомобиля (2-3 предложения).

Основные характеристики:
• Год: [год] | Двигатель: [объем] л | Пробег: [пробег] км
• Коробка: [тип] | Привод: [тип] | Кузов: [тип]

[Марка] [Модель] — [короткий слоган]

#хэштеги
        """
        return prompt.strip()
    
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