"""
Утилита для миграции custom_id в базе данных на новый формат XXX-XXX
"""

import asyncio
import aiohttp
import json
from typing import List, Dict, Tuple
from app.utils.id_generator import (
    convert_old_id_to_new_format, 
    is_valid_custom_id,
    mark_id_as_used,
    get_id_statistics
)

class CustomIDMigrator:
    """Класс для миграции custom_id в базе данных"""
    
    def __init__(self, node_api_url: str = "http://localhost:3001"):
        self.node_api_url = node_api_url
        self.migration_log = []
        self.conflicts = []
        
    async def get_all_cars(self) -> List[Dict]:
        """Получает все автомобили из базы данных"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.node_api_url}/api/cars") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('cars', [])
                    else:
                        print(f"❌ Ошибка получения автомобилей: {response.status}")
                        return []
        except Exception as e:
            print(f"❌ Исключение при получении автомобилей: {e}")
            return []
    
    async def update_car_id(self, old_id: str, new_id: str, car_data: Dict) -> bool:
        """Обновляет custom_id автомобиля в базе данных"""
        try:
            # Обновляем car_data с новым ID
            updated_data = car_data.copy()
            updated_data['custom_id'] = new_id
            
            async with aiohttp.ClientSession() as session:
                # Обновляем запись
                async with session.put(
                    f"{self.node_api_url}/api/cars/{old_id}",
                    json=updated_data,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        print(f"❌ Ошибка обновления {old_id} → {new_id}: {response.status}")
                        error_text = await response.text()
                        print(f"   Детали: {error_text}")
                        return False
        except Exception as e:
            print(f"❌ Исключение при обновлении {old_id} → {new_id}: {e}")
            return False
    
    def analyze_existing_ids(self, cars: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Анализирует существующие ID и классифицирует их
        
        Returns:
            Tuple[valid_cars, needs_migration, conflicts]
        """
        valid_cars = []
        needs_migration = []
        conflicts = []
        
        existing_new_ids = set()
        
        for car in cars:
            custom_id = car.get('custom_id', '')
            
            if is_valid_custom_id(custom_id):
                valid_cars.append(car)
                existing_new_ids.add(custom_id)
            else:
                needs_migration.append(car)
        
        # Проверяем конфликты - когда конвертация приводит к уже существующему ID
        for car in needs_migration:
            old_id = car.get('custom_id', '')
            new_id = convert_old_id_to_new_format(old_id)
            
            if new_id in existing_new_ids:
                conflicts.append({
                    'car': car,
                    'old_id': old_id,
                    'proposed_new_id': new_id,
                    'conflict_reason': 'Конвертированный ID уже существует'
                })
        
        return valid_cars, needs_migration, conflicts
    
    async def migrate_ids(self, dry_run: bool = True) -> Dict:
        """
        Выполняет миграцию ID в базе данных
        
        Args:
            dry_run: Если True, только показывает что будет сделано без изменений
            
        Returns:
            Словарь с результатами миграции
        """
        print("🔄 Начинаем анализ custom_id в базе данных...")
        
        # Получаем все автомобили
        cars = await self.get_all_cars()
        if not cars:
            return {'error': 'Не удалось получить данные из базы'}
        
        print(f"📊 Найдено автомобилей в базе: {len(cars)}")
        
        # Анализируем ID
        valid_cars, needs_migration, conflicts = self.analyze_existing_ids(cars)
        
        print(f"✅ Уже в правильном формате: {len(valid_cars)}")
        print(f"🔄 Требуют миграции: {len(needs_migration)}")
        print(f"⚠️  Конфликтов: {len(conflicts)}")
        
        # Отмечаем все валидные ID как использованные
        for car in valid_cars:
            mark_id_as_used(car['custom_id'])
        
        migration_plan = []
        successful_migrations = 0
        failed_migrations = 0
        
        # Планируем миграцию для автомобилей без конфликтов
        for car in needs_migration:
            old_id = car.get('custom_id', '')
            new_id = convert_old_id_to_new_format(old_id)
            
            # Проверяем, нет ли этого ID в конфликтах
            is_conflict = any(c['old_id'] == old_id for c in conflicts)
            
            if not is_conflict:
                migration_plan.append({
                    'car': car,
                    'old_id': old_id,
                    'new_id': new_id
                })
        
        print(f"\n📋 План миграции: {len(migration_plan)} автомобилей")
        
        # Показываем несколько примеров
        if migration_plan:
            print("🔍 Примеры миграции:")
            for i, item in enumerate(migration_plan[:5]):
                print(f"  {i+1}. {item['old_id']} → {item['new_id']}")
            if len(migration_plan) > 5:
                print(f"  ... и еще {len(migration_plan) - 5}")
        
        # Показываем конфликты
        if conflicts:
            print(f"\n⚠️  Найдены конфликты ({len(conflicts)}):")
            for conflict in conflicts[:3]:
                print(f"  {conflict['old_id']} → {conflict['proposed_new_id']} (уже существует)")
            if len(conflicts) > 3:
                print(f"  ... и еще {len(conflicts) - 3}")
        
        if dry_run:
            print(f"\n🔍 Это пробный запуск - изменения НЕ вносились")
            return {
                'dry_run': True,
                'total_cars': len(cars),
                'valid_cars': len(valid_cars),
                'needs_migration': len(needs_migration),
                'conflicts': len(conflicts),
                'migration_plan': len(migration_plan)
            }
        
        # Выполняем реальную миграцию
        print(f"\n🚀 Выполняем миграцию...")
        
        for i, item in enumerate(migration_plan):
            car = item['car']
            old_id = item['old_id']
            new_id = item['new_id']
            
            print(f"  [{i+1}/{len(migration_plan)}] {old_id} → {new_id}...", end="")
            
            success = await self.update_car_id(old_id, new_id, car)
            if success:
                successful_migrations += 1
                mark_id_as_used(new_id)
                print(" ✅")
                self.migration_log.append(f"SUCCESS: {old_id} → {new_id}")
            else:
                failed_migrations += 1
                print(" ❌")
                self.migration_log.append(f"FAILED: {old_id} → {new_id}")
            
            # Небольшая пауза между обновлениями
            await asyncio.sleep(0.1)
        
        # Статистика
        stats = get_id_statistics()
        
        print(f"\n📊 Результаты миграции:")
        print(f"   ✅ Успешно: {successful_migrations}")
        print(f"   ❌ Ошибок: {failed_migrations}")
        print(f"   ⚠️  Конфликтов: {len(conflicts)}")
        print(f"   📈 Всего ID в системе: {stats['used_count']}")
        
        return {
            'dry_run': False,
            'total_cars': len(cars),
            'valid_cars': len(valid_cars),
            'successful_migrations': successful_migrations,
            'failed_migrations': failed_migrations,
            'conflicts': len(conflicts),
            'migration_log': self.migration_log,
            'id_statistics': stats
        }
    
    async def handle_conflicts(self) -> Dict:
        """Обрабатывает конфликтные ID путем генерации новых уникальных ID"""
        cars = await self.get_all_cars()
        if not cars:
            return {'error': 'Не удалось получить данные из базы'}
        
        valid_cars, needs_migration, conflicts = self.analyze_existing_ids(cars)
        
        if not conflicts:
            print("✅ Конфликтов не найдено")
            return {'conflicts_resolved': 0}
        
        print(f"🔧 Разрешение {len(conflicts)} конфликтов...")
        
        # Отмечаем все валидные ID как использованные
        for car in valid_cars:
            mark_id_as_used(car['custom_id'])
        
        resolved_conflicts = 0
        failed_conflicts = 0
        
        for i, conflict in enumerate(conflicts):
            car = conflict['car']
            old_id = conflict['old_id']
            
            print(f"  [{i+1}/{len(conflicts)}] Разрешаем конфликт для {old_id}...", end="")
            
            # Генерируем новый уникальный ID вместо конфликтного
            from app.utils.id_generator import generate_custom_id
            new_id = generate_custom_id()
            
            success = await self.update_car_id(old_id, new_id, car)
            if success:
                resolved_conflicts += 1
                print(f" ✅ → {new_id}")
                self.migration_log.append(f"CONFLICT_RESOLVED: {old_id} → {new_id}")
            else:
                failed_conflicts += 1
                print(" ❌")
                self.migration_log.append(f"CONFLICT_FAILED: {old_id}")
            
            await asyncio.sleep(0.1)
        
        print(f"\n📊 Результаты разрешения конфликтов:")
        print(f"   ✅ Разрешено: {resolved_conflicts}")
        print(f"   ❌ Ошибок: {failed_conflicts}")
        
        return {
            'conflicts_resolved': resolved_conflicts,
            'conflicts_failed': failed_conflicts,
            'migration_log': self.migration_log
        }
    
    def save_migration_log(self, filename: str = "migration_log.json"):
        """Сохраняет лог миграции в файл"""
        log_data = {
            'migration_log': self.migration_log,
            'conflicts': self.conflicts,
            'timestamp': asyncio.get_event_loop().time()
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 Лог миграции сохранен в {filename}")

async def main():
    """Основная функция для запуска миграции"""
    print("🔄 Утилита миграции Custom ID")
    print("=" * 50)
    
    migrator = CustomIDMigrator()
    
    # Сначала пробный запуск
    print("🔍 Шаг 1: Анализ текущего состояния")
    dry_run_result = await migrator.migrate_ids(dry_run=True)
    
    if 'error' in dry_run_result:
        print(f"❌ {dry_run_result['error']}")
        return
    
    if dry_run_result['needs_migration'] == 0:
        print("✅ Все ID уже в правильном формате, миграция не требуется")
        return
    
    # Запрашиваем подтверждение
    print(f"\n❓ Выполнить миграцию {dry_run_result['migration_plan']} автомобилей? (y/N): ", end="")
    
    try:
        import sys
        response = input().strip().lower()
        if response == 'y':
            print("\n🚀 Шаг 2: Выполнение миграции")
            result = await migrator.migrate_ids(dry_run=False)
            
            # Обрабатываем конфликты если есть
            if result.get('conflicts', 0) > 0:
                print(f"\n🔧 Шаг 3: Разрешение конфликтов")
                conflict_result = await migrator.handle_conflicts()
            
            # Сохраняем лог
            migrator.save_migration_log()
            
            print("\n✅ Миграция завершена!")
        else:
            print("❌ Миграция отменена пользователем")
    except (EOFError, KeyboardInterrupt):
        print("\n❌ Миграция прервана пользователем")

if __name__ == "__main__":
    asyncio.run(main()) 