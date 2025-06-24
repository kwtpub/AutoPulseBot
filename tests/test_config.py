import pytest
import os
from unittest.mock import patch
from app.utils.config import get_pricing_config, set_pricing_config


class TestConfig:
    """Тесты для модуля конфигурации."""
    
    def test_get_pricing_config_default(self):
        """Тест получения наценки по умолчанию."""
        with patch('os.path.exists', return_value=False):
            config = get_pricing_config()
            assert isinstance(config, float)
            assert config >= 0
    
    def test_set_pricing_config(self):
        """Тест установки наценки."""
        test_markup = 15.5
        with patch('configparser.ConfigParser') as mock_config:
            mock_instance = mock_config.return_value
            mock_instance.read.return_value = []
            
            set_pricing_config(test_markup)
            
            mock_instance.set.assert_called_with('pricing', 'markup_percentage', str(test_markup))
            mock_instance.write.assert_called_once()
    
    def test_get_pricing_config_from_file(self):
        """Тест получения наценки из файла."""
        test_markup = 12.0
        with patch('configparser.ConfigParser') as mock_config:
            mock_instance = mock_config.return_value
            mock_instance.read.return_value = ['config.ini']
            mock_instance.getfloat.return_value = test_markup
            
            config = get_pricing_config()
            assert config == test_markup 