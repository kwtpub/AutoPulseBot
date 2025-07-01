#!/usr/bin/env node

/**
 * Безопасный запуск улучшенного сервера
 * Проверяет модули перед запуском и выводит подробную информацию об ошибках
 */

const fs = require('fs');
const path = require('path');

console.log('🚀 Безопасный запуск улучшенного сервера...');

// Проверяем наличие необходимых файлов
const requiredFiles = [
  'app/db/database_pool.js',
  'app/db/car_improved.js', 
  'app/db/server_improved.js'
];

console.log('📋 Проверка необходимых файлов...');
for (const file of requiredFiles) {
  const fullPath = path.resolve(__dirname, file);
  if (fs.existsSync(fullPath)) {
    console.log(`✅ ${file} найден`);
  } else {
    console.error(`❌ ${file} НЕ НАЙДЕН`);
    process.exit(1);
  }
}

// Проверяем .env файл
const envPath = path.resolve(__dirname, '.env');
if (fs.existsSync(envPath)) {
  console.log('✅ .env файл найден');
} else {
  console.warn('⚠️ .env файл НЕ НАЙДЕН - создайте его из example.env');
  console.warn('   Сервер может не запуститься без настроек базы данных');
}

// Проверяем синтаксис модулей
console.log('\n🔍 Проверка модулей на синтаксические ошибки...');

try {
  console.log('📦 Загрузка database_pool...');
  require('./app/db/database_pool');
  console.log('✅ database_pool загружен без ошибок');
} catch (error) {
  console.error('❌ Ошибка в database_pool.js:');
  console.error('   ', error.message);
  if (error.message.includes('already been declared')) {
    console.error('💡 Совет: возможно есть дублированные импорты в database_pool.js');
  }
  process.exit(1);
}

try {
  console.log('📦 Загрузка car_improved...');
  require('./app/db/car_improved'); 
  console.log('✅ car_improved загружен без ошибок');
} catch (error) {
  console.error('❌ Ошибка в car_improved.js:');
  console.error('   ', error.message);
  process.exit(1);
}

try {
  console.log('📦 Загрузка server_improved...');
  require('./app/db/server_improved');
  console.log('✅ server_improved загружен без ошибок');
} catch (error) {
  console.error('❌ Ошибка в server_improved.js:');
  console.error('   ', error.message);
  process.exit(1);
}

console.log('\n🎉 Все модули загружены успешно!');
console.log('💡 Если сервер не запускается, проверьте:');
console.log('   - Настройки DATABASE_URL в .env файле');
console.log('   - Доступность PostgreSQL базы данных');
console.log('   - Права доступа к порту 3001');
console.log('\n📊 Для проверки состояния сервера: curl http://localhost:3001/api/health');
console.log('🔄 Для автоматического перезапуска используйте: node app/db/start_improved_server.js'); 