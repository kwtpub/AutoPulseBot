/**
 * Database Pool Manager - улучшенное управление соединениями с PostgreSQL
 * Включает retry логику, graceful recovery и мониторинг соединений
 */

const { Pool } = require('pg');
require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });

class DatabasePool {
  constructor() {
    this.pool = null;
    this.isConnecting = false;
    this.retryCount = 0;
    this.maxRetries = 5;
    this.retryDelay = 1000; // начальная задержка в мс
    this.initialized = false;
    
    this.createPool();
  }

  createPool() {
    if (this.pool) {
      this.pool.end();
    }

    const connectionString = process.env.DATABASE_URL
      .replace(/([&?])(sslmode|channel_binding)=require&?/g, '$1')
      .replace(/[?&]$/, '');

    this.pool = new Pool({
      connectionString,
      ssl: { rejectUnauthorized: false },
      
      // Увеличенные таймауты для стабильности
      max: 20, // больше соединений в пуле
      idleTimeoutMillis: 60000, // 1 минута для idle соединений
      connectionTimeoutMillis: 10000, // 10 секунд на подключение
      acquireTimeoutMillis: 15000, // 15 секунд на получение соединения из пула
      
      // Дополнительные настройки для стабильности
      keepAlive: true,
      keepAliveInitialDelayMillis: 10000,
      allowExitOnIdle: false
    });

    this.setupEventHandlers();
  }

  setupEventHandlers() {
    // Обработка ошибок пула
    this.pool.on('error', (err) => {
      console.error('🔴 Критическая ошибка PostgreSQL pool:', err.message);
      this.handlePoolError(err);
    });

    // Мониторинг соединений
    this.pool.on('connect', (client) => {
      console.log('🟢 Новое соединение с PostgreSQL установлено');
      this.retryCount = 0; // сбрасываем счетчик при успешном подключении
    });

    this.pool.on('acquire', () => {
      console.log('🔵 Соединение получено из пула');
    });

    this.pool.on('remove', () => {
      console.log('🟡 Соединение удалено из пула');
    });
  }

  async handlePoolError(err) {
    console.error(`🔴 Ошибка пула соединений (попытка ${this.retryCount + 1}/${this.maxRetries}):`, err.message);
    
    if (this.retryCount < this.maxRetries && !this.isConnecting) {
      this.isConnecting = true;
      this.retryCount++;
      
      const delay = this.retryDelay * Math.pow(2, this.retryCount - 1); // экспоненциальная задержка
      console.log(`🔄 Попытка переподключения через ${delay}мс...`);
      
      setTimeout(() => {
        this.createPool();
        this.isConnecting = false;
      }, delay);
    } else {
      console.error('🔴 Превышено максимальное количество попыток переподключения');
    }
  }

  async getConnection() {
    let attempt = 0;
    const maxAttempts = 3;
    
    while (attempt < maxAttempts) {
      try {
        const client = await this.pool.connect();
        
        // Проверяем активность соединения
        await client.query('SELECT 1');
        
        return client;
      } catch (err) {
        attempt++;
        console.warn(`⚠️ Попытка получения соединения ${attempt}/${maxAttempts} неудачна:`, err.message);
        
        if (attempt >= maxAttempts) {
          throw new Error(`Не удалось получить соединение после ${maxAttempts} попыток: ${err.message}`);
        }
        
        // Небольшая задержка перед повторной попыткой
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }

  async executeQuery(queryText, params = []) {
    let client;
    let attempt = 0;
    const maxAttempts = 3;
    
    while (attempt < maxAttempts) {
      try {
        client = await this.getConnection();
        const result = await client.query(queryText, params);
        return result;
      } catch (err) {
        attempt++;
        console.error(`❌ Ошибка выполнения запроса (попытка ${attempt}/${maxAttempts}):`, err.message);
        
        if (client) {
          client.release();
          client = null;
        }
        
        // Если это ошибка соединения, пересоздаем пул
        if (err.message.includes('Connection terminated') || 
            err.message.includes('connection timeout') ||
            err.code === 'ENOTFOUND' ||
            err.code === 'ETIMEDOUT') {
          
          console.log('🔄 Пересоздаем пул соединений из-за ошибки соединения...');
          this.createPool();
          await new Promise(resolve => setTimeout(resolve, 2000)); // ждем восстановления
        }
        
        if (attempt >= maxAttempts) {
          throw err;
        }
        
        // Увеличиваем задержку с каждой попыткой
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      } finally {
        if (client) {
          client.release();
        }
      }
    }
  }

  async checkConnection() {
    try {
      await this.executeQuery('SELECT NOW() as current_time');
      console.log('✅ Соединение с базой данных активно');
      return true;
    } catch (err) {
      console.error('❌ Проверка соединения не удалась:', err.message);
      return false;
    }
  }

  async close() {
    if (this.pool) {
      console.log('🔒 Закрываем пул соединений...');
      await this.pool.end();
      this.pool = null;
    }
  }

  // Статистика пула
  getPoolStats() {
    if (!this.pool) return null;
    
    return {
      totalCount: this.pool.totalCount,
      idleCount: this.pool.idleCount,
      waitingCount: this.pool.waitingCount,
      retryCount: this.retryCount,
      isConnecting: this.isConnecting
    };
  }
}

// Создаем singleton instance
const dbPool = new DatabasePool();

// Graceful shutdown
process.on('SIGTERM', async () => {
  console.log('🛑 Получен SIGTERM, закрываем пул соединений...');
  await dbPool.close();
  process.exit(0);
});

process.on('SIGINT', async () => {
  console.log('🛑 Получен SIGINT, закрываем пул соединений...');
  await dbPool.close();
  process.exit(0);
});

module.exports = dbPool; 