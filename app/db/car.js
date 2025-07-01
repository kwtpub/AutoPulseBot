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

// Функция для получения автомобиля по custom_id
async function getCar(custom_id) {
  const client = await pool.connect();
  try {
    const query = 'SELECT * FROM cars WHERE custom_id = $1';
    const result = await client.query(query, [custom_id]);
    
    if (result.rows.length === 0) {
      return null;
    }
    
    const car = result.rows[0];
    
    // Безопасно парсим JSON поле photos
    if (car.photos) {
      try {
        // Если photos уже объект (JSONB), используем как есть
        if (typeof car.photos === 'object') {
          // Уже распарсено PostgreSQL
        } else if (typeof car.photos === 'string') {
          // Если строка, пытаемся парсить
          car.photos = JSON.parse(car.photos);
        }
      } catch (parseError) {
        console.error('Ошибка парсинга photos для автомобиля', custom_id, ':', parseError.message);
        console.error('Содержимое photos:', car.photos);
        // Если не удалось парсить, устанавливаем пустой массив
        car.photos = [];
      }
    } else {
      car.photos = [];
    }
    
    return car;
  } catch (err) {
    console.error('Ошибка при получении автомобиля:', err);
    throw err;
  } finally {
    client.release();
  }
}

// Функция для получения всех автомобилей с пагинацией
async function getAllCars(limit = 10, offset = 0) {
  const client = await pool.connect();
  try {
    // Получаем автомобили с пагинацией
    const carsQuery = `
      SELECT * FROM cars 
      ORDER BY created_at DESC 
      LIMIT $1 OFFSET $2
    `;
    const carsResult = await client.query(carsQuery, [limit, offset]);
    
    // Получаем общее количество
    const countQuery = 'SELECT COUNT(*) FROM cars';
    const countResult = await client.query(countQuery);
    
    const cars = carsResult.rows.map(car => {
      // Безопасно парсим JSON поле photos
      if (car.photos) {
        try {
          // Если photos уже объект (JSONB), используем как есть
          if (typeof car.photos === 'object') {
            // Уже распарсено PostgreSQL
          } else if (typeof car.photos === 'string') {
            // Если строка, пытаемся парсить
            car.photos = JSON.parse(car.photos);
          }
        } catch (parseError) {
          console.error('Ошибка парсинга photos для автомобиля', car.custom_id, ':', parseError.message);
          // Если не удалось парсить, устанавливаем пустой массив
          car.photos = [];
        }
      } else {
        car.photos = [];
      }
      return car;
    });
    
    return {
      cars,
      total: parseInt(countResult.rows[0].count)
    };
  } catch (err) {
    console.error('Ошибка при получении списка автомобилей:', err);
    throw err;
  } finally {
    client.release();
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

// Функция для проверки дубликатов по source_message_id и source_channel_name
async function checkDuplicate(source_message_id, source_channel_name) {
  let client;
  try {
    client = await pool.connect();
    const query = `
      SELECT custom_id, brand, model, year, created_at 
      FROM cars 
      WHERE source_message_id = $1 AND source_channel_name = $2
    `;
    const result = await client.query(query, [source_message_id, source_channel_name]);
    
    if (result.rows.length > 0) {
      const existingCar = result.rows[0];
      console.log(`🔍 Найден дубликат: ${existingCar.custom_id} (${existingCar.brand} ${existingCar.model} ${existingCar.year})`);
      return existingCar;
    }
    
    return null;
  } catch (err) {
    console.error('Ошибка при проверке дубликатов:', err);
    // При ошибке подключения возвращаем null (как будто дубликата нет)
    // Это позволит продолжить обработку даже при проблемах с БД
    return null;
  } finally {
    if (client) {
      client.release();
    }
  }
}

module.exports = { 
  saveCar: addCar, 
  checkConnection, 
  getCar, 
  getAllCars,
  checkDuplicate
}; 