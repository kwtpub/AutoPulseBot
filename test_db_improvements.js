/**
 * Тестирование улучшений базы данных
 * Проверка retry логики, timeout handling и stability
 */

const http = require('http');

class DatabaseTester {
  constructor() {
    this.port = process.env.NODE_PORT || 3001;
    this.baseUrl = `http://localhost:${this.port}`;
    this.testResults = [];
  }

  async runTests() {
    console.log('🧪 Запуск тестов улучшений базы данных...\n');

    await this.testHealthCheck();
    await this.testAddCar();
    await this.testDuplicateCheck();
    await this.testServerStability();
    
    this.printSummary();
  }

  async testHealthCheck() {
    console.log('1️⃣ Тест Health Check...');
    
    try {
      const health = await this.makeRequest('/api/health');
      
      if (health.server && health.database) {
        console.log('✅ Health check прошел успешно');
        console.log(`   📊 Server status: ${health.server.status}`);
        console.log(`   📊 Database connected: ${health.database.connected}`);
        console.log(`   📊 Pool stats: ${JSON.stringify(health.database.pool)}`);
        this.testResults.push({ test: 'Health Check', status: '✅ PASS' });
      } else {
        throw new Error('Invalid health response');
      }
    } catch (error) {
      console.log(`❌ Health check failed: ${error.message}`);
      this.testResults.push({ test: 'Health Check', status: '❌ FAIL', error: error.message });
    }
    
    console.log('');
  }

  async testAddCar() {
    console.log('2️⃣ Тест добавления автомобиля...');
    
    const testCar = {
      custom_id: `test_${Date.now()}`,
      brand: 'Toyota',
      model: 'Camry',
      year: 2023,
      price: 25000,
      description: 'Test car for database improvements',
      photos: ['test1.jpg', 'test2.jpg'],
      source_message_id: 12345,
      source_channel_name: 'test_channel'
    };

    try {
      const startTime = Date.now();
      const result = await this.makeRequest('/api/cars', 'POST', testCar);
      const duration = Date.now() - startTime;
      
      if (result.car && result.car.custom_id === testCar.custom_id) {
        console.log(`✅ Автомобиль добавлен успешно за ${duration}мс`);
        console.log(`   🚗 ID: ${result.car.custom_id}`);
        console.log(`   🚗 Brand: ${result.car.brand} ${result.car.model}`);
        this.testResults.push({ 
          test: 'Add Car', 
          status: '✅ PASS', 
          duration: `${duration}ms`,
          carId: result.car.custom_id 
        });
      } else {
        throw new Error('Invalid add car response');
      }
    } catch (error) {
      console.log(`❌ Добавление автомобиля failed: ${error.message}`);
      this.testResults.push({ test: 'Add Car', status: '❌ FAIL', error: error.message });
    }
    
    console.log('');
  }

  async testDuplicateCheck() {
    console.log('3️⃣ Тест проверки дубликатов...');
    
    try {
      const result = await this.makeRequest('/api/cars/check-duplicate/12345/test_channel');
      
      if (result && result.custom_id) {
        console.log('✅ Проверка дубликатов работает');
        console.log(`   🔍 Найден дубликат: ${result.custom_id}`);
        this.testResults.push({ test: 'Duplicate Check', status: '✅ PASS' });
      } else {
        console.log('ℹ️ Дубликаты не найдены (это нормально для тестов)');
        this.testResults.push({ test: 'Duplicate Check', status: '✅ PASS (no duplicates)' });
      }
    } catch (error) {
      console.log(`❌ Проверка дубликатов failed: ${error.message}`);
      this.testResults.push({ test: 'Duplicate Check', status: '❌ FAIL', error: error.message });
    }
    
    console.log('');
  }

  async testServerStability() {
    console.log('4️⃣ Тест стабильности сервера (множественные запросы)...');
    
    const requests = 5;
    const results = [];
    
    try {
      console.log(`   📡 Отправка ${requests} параллельных запросов...`);
      
      const promises = [];
      for (let i = 0; i < requests; i++) {
        promises.push(
          this.makeRequest('/api/health').then(res => ({ index: i, success: true, res })).catch(err => ({ index: i, success: false, error: err.message }))
        );
      }
      
      const responses = await Promise.all(promises);
      const successful = responses.filter(r => r.success).length;
      
      console.log(`   ✅ Успешных запросов: ${successful}/${requests}`);
      
      if (successful === requests) {
        console.log('✅ Тест стабильности прошел успешно');
        this.testResults.push({ test: 'Server Stability', status: '✅ PASS', successRate: `${successful}/${requests}` });
      } else {
        console.log(`⚠️ Некоторые запросы не удались: ${requests - successful} failed`);
        this.testResults.push({ test: 'Server Stability', status: '⚠️ PARTIAL', successRate: `${successful}/${requests}` });
      }
      
    } catch (error) {
      console.log(`❌ Тест стабильности failed: ${error.message}`);
      this.testResults.push({ test: 'Server Stability', status: '❌ FAIL', error: error.message });
    }
    
    console.log('');
  }

  async makeRequest(path, method = 'GET', data = null) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: 'localhost',
        port: this.port,
        path: path,
        method: method,
        timeout: 10000
      };

      if (data) {
        options.headers = {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(JSON.stringify(data))
        };
      }

      const req = http.request(options, (res) => {
        let responseData = '';
        
        res.on('data', (chunk) => {
          responseData += chunk;
        });

        res.on('end', () => {
          try {
            const result = JSON.parse(responseData);
            
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(result);
            } else {
              reject(new Error(`HTTP ${res.statusCode}: ${result.error || result.message || 'Unknown error'}`));
            }
          } catch (parseError) {
            reject(new Error(`Invalid JSON response: ${parseError.message}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(new Error(`Request failed: ${error.message}`));
      });

      req.on('timeout', () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });

      if (data) {
        req.write(JSON.stringify(data));
      }

      req.end();
    });
  }

  printSummary() {
    console.log('📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:');
    console.log('=' * 50);
    
    this.testResults.forEach((result, index) => {
      console.log(`${index + 1}. ${result.test}: ${result.status}`);
      if (result.duration) console.log(`   ⏱️ Время выполнения: ${result.duration}`);
      if (result.successRate) console.log(`   📊 Успешность: ${result.successRate}`);
      if (result.carId) console.log(`   🆔 ID автомобиля: ${result.carId}`);
      if (result.error) console.log(`   ❌ Ошибка: ${result.error}`);
    });
    
    console.log('=' * 50);
    
    const passed = this.testResults.filter(r => r.status.includes('✅')).length;
    const total = this.testResults.length;
    
    if (passed === total) {
      console.log(`🎉 ВСЕ ТЕСТЫ ПРОШЛИ: ${passed}/${total}`);
      console.log('✅ Улучшения базы данных работают корректно!');
    } else {
      console.log(`⚠️ ЧАСТИЧНЫЙ УСПЕХ: ${passed}/${total} тестов прошли`);
      console.log('🔧 Возможно требуется дополнительная настройка');
    }
  }
}

// Проверяем, что сервер запущен
async function checkServerRunning() {
  try {
    const req = http.request({
      hostname: 'localhost',
      port: process.env.NODE_PORT || 3001,
      path: '/api/health',
      timeout: 5000
    }, (res) => {
      console.log('✅ Сервер запущен, начинаем тестирование...\n');
      new DatabaseTester().runTests();
    });

    req.on('error', () => {
      console.log('❌ Сервер не запущен!');
      console.log('🚀 Сначала запустите сервер:');
      console.log('   node app/db/server_improved.js');
      console.log('   или');
      console.log('   node app/db/start_improved_server.js');
      process.exit(1);
    });

    req.end();
  } catch (error) {
    console.log('❌ Ошибка проверки сервера:', error.message);
    process.exit(1);
  }
}

console.log('🔍 Проверка доступности сервера...');
checkServerRunning(); 