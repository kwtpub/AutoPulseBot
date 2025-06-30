const { Pool } = require('pg');
require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });

const connectionString = process.env.DATABASE_URL
  .replace(/([&?])(sslmode|channel_binding)=require&?/g, '$1')
  .replace(/[?&]$/, '');

// Используем пул соединений вместо одного клиента
const pool = new Pool({
  connectionString,
  ssl: { rejectUnauthorized: false },
  max: 10, // максимум соединений в пуле
  idleTimeoutMillis: 30000, // время жизни неактивного соединения
  connectionTimeoutMillis: 2000, // таймаут на подключение
});

// Обработчик ошибок пула
pool.on('error', (err) => {
  console.error('Неожиданная ошибка клиента PostgreSQL:', err);
});

async function createTableIfNotExists() {
  const client = await pool.connect();
  try {
    const createTableQuery = `
      CREATE TABLE IF NOT EXISTS cars (
        id SERIAL PRIMARY KEY,
        custom_id VARCHAR(255) UNIQUE NOT NULL,
        source_message_id INTEGER,
        source_channel_name VARCHAR(255),
        target_channel_message_id INTEGER,
        brand VARCHAR(255),
        model VARCHAR(255),
        year INTEGER,
        price DECIMAL(10,2),
        description TEXT,
        photos JSONB,
        status VARCHAR(50) DEFAULT 'available',
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
      );
      
      -- Изменяем существующие колонки если таблица уже создана
      DO $$ 
      BEGIN
        -- Делаем year nullable если он был NOT NULL
        BEGIN
          ALTER TABLE cars ALTER COLUMN year DROP NOT NULL;
        EXCEPTION 
          WHEN others THEN NULL;
        END;
        
        -- Делаем price nullable если он был NOT NULL  
        BEGIN
          ALTER TABLE cars ALTER COLUMN price DROP NOT NULL;
        EXCEPTION 
          WHEN others THEN NULL;
        END;
      END $$;
    `;
    
    await client.query(createTableQuery);
    console.log('Таблица cars проверена/создана');
  } catch (err) {
    console.error('Ошибка при создании таблицы cars:', err);
    throw err;
  } finally {
    client.release(); // возвращаем соединение в пул
  }
}

async function addCar(car) {
  const client = await pool.connect();
  try {
    // Создаем таблицу если это первый запрос
    await createTableIfNotExists();
    
    const query = `
      INSERT INTO cars (
        custom_id, source_message_id, source_channel_name, target_channel_message_id,
        brand, model, year, price, description, photos, status, created_at
      ) VALUES (
        $1, $2, $3, $4,
        $5, $6, $7, $8, $9, $10, $11, NOW()
      ) RETURNING *;
    `;
    const values = [
      car.custom_id,
      car.source_message_id,
      car.source_channel_name,
      car.target_channel_message_id || null,
      car.brand,
      car.model,
      car.year,
      car.price,
      car.description,
      JSON.stringify(car.photos || []),
      car.status || 'available',
    ];
    
    const res = await client.query(query, values);
    console.log('Автомобиль успешно добавлен:', res.rows[0].custom_id);
    return res.rows[0];
  } catch (err) {
    console.error('Ошибка при добавлении автомобиля:', err);
    throw err;
  } finally {
    client.release(); // возвращаем соединение в пул
  }
}

// Функция для проверки подключения
async function checkConnection() {
  const client = await pool.connect();
  try {
    const result = await client.query('SELECT NOW()');
    console.log('PostgreSQL подключение активно:', result.rows[0].now);
    return true;
  } catch (err) {
    console.error('Ошибка проверки подключения:', err);
    return false;
  } finally {
    client.release();
  }
}

// Пример использования
if (require.main === module) {
  (async () => {
    // Проверяем подключение
    await checkConnection();
    
    const newCar = {
      custom_id: 'car-123',
      source_message_id: 456,
      source_channel_name: '@importdrive',
      target_channel_message_id: null,
      brand: 'Toyota',
      model: 'Camry',
      year: 2020,
      price: 20000,
      description: 'Отличное состояние, один владелец.',
      photos: ['https://example.com/photo1.jpg'],
      status: 'available',
    };
    try {
      const car = await addCar(newCar);
      console.log('Добавлено авто:', car);
    } catch (err) {
      console.error('Ошибка при добавлении авто:', err);
    }
  })();
}

module.exports = { saveCar: addCar, checkConnection }; 