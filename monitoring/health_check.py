#!/usr/bin/env python3
"""
Health check script for Telegram Auto Post Bot
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.config import get_pricing_config
from app.core.perplexity import PerplexityProcessor
from app.bot.database import Database


class HealthChecker:
    """Класс для проверки здоровья приложения."""
    
    def __init__(self):
        self.results: Dict[str, Any] = {}
    
    async def check_config(self) -> bool:
        """Проверка конфигурации."""
        try:
            markup = get_pricing_config()
            self.results['config'] = {
                'status': 'healthy',
                'markup_percentage': markup
            }
            return True
        except Exception as e:
            self.results['config'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    async def check_database(self) -> bool:
        """Проверка базы данных."""
        try:
            db = Database()
            # Проверяем подключение к БД
            db.get_applications()
            self.results['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
            return True
        except Exception as e:
            self.results['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    async def check_perplexity(self) -> bool:
        """Проверка Perplexity API."""
        try:
            # Проверяем только инициализацию, без реального API вызова
            processor = PerplexityProcessor("test_key")
            self.results['perplexity'] = {
                'status': 'healthy',
                'message': 'Perplexity processor initialized'
            }
            return True
        except Exception as e:
            self.results['perplexity'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    async def check_filesystem(self) -> bool:
        """Проверка файловой системы."""
        try:
            required_dirs = ['downloads', 'temp', 'logs']
            for dir_name in required_dirs:
                dir_path = project_root / dir_name
                if not dir_path.exists():
                    dir_path.mkdir(parents=True, exist_ok=True)
            
            self.results['filesystem'] = {
                'status': 'healthy',
                'message': 'Required directories exist'
            }
            return True
        except Exception as e:
            self.results['filesystem'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            return False
    
    async def run_all_checks(self) -> Dict[str, Any]:
        """Запуск всех проверок."""
        checks = [
            self.check_config,
            self.check_database,
            self.check_perplexity,
            self.check_filesystem
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        overall_status = 'healthy' if all(results) else 'unhealthy'
        
        return {
            'status': overall_status,
            'timestamp': asyncio.get_event_loop().time(),
            'checks': self.results
        }


async def main():
    """Основная функция."""
    checker = HealthChecker()
    result = await checker.run_all_checks()
    
    # Выводим результат в JSON формате
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Возвращаем код выхода
    sys.exit(0 if result['status'] == 'healthy' else 1)


if __name__ == '__main__':
    asyncio.run(main()) 