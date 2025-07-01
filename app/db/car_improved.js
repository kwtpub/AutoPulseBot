/**
 * Car Database Operations - улучшенная версия с retry логикой
 * Использует новый DatabasePool для надежного соединения с БД
 */

const dbPool = require('./database_pool');

async function createTableIfNotExists() {
  console.log('🔧 Проверка/создание таблицы cars...');
  
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
  
  try {
    await dbPool.executeQuery(createTableQuery);
    console.log('✅ Таблица cars проверена/создана успешно');
  } catch (err) {
    console.error('❌ Ошибка при создании таблицы cars:', err.message);
    throw err;
  }
}

async function addCar(car) {
  console.log(`🚗 Добавление автомобиля с ID: ${car.custom_id}`);
  
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
    
    const result = await dbPool.executeQuery(query, values);
    console.log('✅ Автомобиль успешно добавлен:', result.rows[0].custom_id);
    return result.rows[0];
    
  } catch (err) {
    if (err.code === '23505') {
      console.warn(`⚠️ Автомобиль с ID ${car.custom_id} уже существует`);
      throw new Error(`Автомобиль с ID ${car.custom_id} уже существует в базе данных`);
    }
    
    console.error('❌ Ошибка при добавлении автомобиля:', err.message);
    throw err;
  }
}

// Функция для получения автомобиля по custom_id
async function getCar(custom_id) {
  console.log(`🔍 Поиск автомобиля с ID: ${custom_id}`);
  
  try {
    const query = 'SELECT * FROM cars WHERE custom_id = $1';
    const result = await dbPool.executeQuery(query, [custom_id]);
    
    if (result.rows.length === 0) {
      console.log(`ℹ️ Автомобиль с ID ${custom_id} не найден`);
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
        console.error('❌ Ошибка парсинга photos для автомобиля', custom_id, ':', parseError.message);
        console.error('Содержимое photos:', car.photos);
        // Если не удалось парсить, устанавливаем пустой массив
        car.photos = [];
      }
    } else {
      car.photos = [];
    }
    
    console.log(`✅ Автомобиль найден: ${car.brand} ${car.model}`);
    return car;
    
  } catch (err) {
    console.error('❌ Ошибка при получении автомобиля:', err.message);
    throw err;
  }
}

// Функция для получения всех автомобилей с пагинацией
async function getAllCars(limit = 10, offset = 0) {
  console.log(`📋 Получение списка автомобилей (limit: ${limit}, offset: ${offset})`);
  
  try {
    // Получаем автомобили с пагинацией
    const carsQuery = `
      SELECT * FROM cars 
      ORDER BY created_at DESC 
      LIMIT $1 OFFSET $2
    `;
    const carsResult = await dbPool.executeQuery(carsQuery, [limit, offset]);
    
    // Получаем общее количество
    const countQuery = 'SELECT COUNT(*) FROM cars';
    const countResult = await dbPool.executeQuery(countQuery);
    
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
          console.error('❌ Ошибка парсинга photos для автомобиля', car.custom_id, ':', parseError.message);
          // Если не удалось парсить, устанавливаем пустой массив
          car.photos = [];
        }
      } else {
        car.photos = [];
      }
      return car;
    });
    
    const total = parseInt(countResult.rows[0].count);
    console.log(`✅ Получено ${cars.length} автомобилей из ${total} общих`);
    
    return {
      cars,
      total
    };
    
  } catch (err) {
    console.error('❌ Ошибка при получении списка автомобилей:', err.message);
    throw err;
  }
}

async function checkConnection() {
  console.log('🔍 Проверка соединения с базой данных...');
  
  try {
    const connected = await dbPool.checkConnection();
    
    if (connected) {
      console.log('✅ Соединение с базой данных активно');
      
      // Дополнительно показываем статистику пула
      const stats = dbPool.getPoolStats();
      if (stats) {
        console.log(`📊 Статистика пула: active=${stats.totalCount}, idle=${stats.idleCount}, waiting=${stats.waitingCount}`);
      }
    }
    
    return connected;
    
  } catch (err) {
    console.error('❌ Ошибка проверки соединения:', err.message);
    return false;
  }
}

async function checkDuplicate(source_message_id, source_channel_name) {
  console.log(`🔍 Проверка дубликата: message_id=${source_message_id}, channel=${source_channel_name}`);
  
  try {
    const query = `
      SELECT * FROM cars 
      WHERE source_message_id = $1 AND source_channel_name = $2 
      LIMIT 1
    `;
    
    const result = await dbPool.executeQuery(query, [source_message_id, source_channel_name]);
    
    if (result.rows.length > 0) {
      const duplicate = result.rows[0];
      console.log(`⚠️ Найден дубликат: автомобиль ${duplicate.custom_id}`);
      return duplicate;
    }
    
    console.log('✅ Дубликат не найден');
    return null;
    
  } catch (err) {
    console.error('❌ Ошибка при проверке дубликата:', err.message);
    throw err;
  }
}

// Функция для обновления автомобиля
async function updateCar(custom_id, updates) {
  console.log(`📝 Обновление автомобиля ${custom_id}`);
  
  try {
    // Строим динамический запрос обновления
    const updateFields = [];
    const values = [];
    let paramIndex = 1;
    
    for (const [key, value] of Object.entries(updates)) {
      if (key === 'photos' && value) {
        updateFields.push(`${key} = $${paramIndex}`);
        values.push(JSON.stringify(value));
      } else if (value !== undefined) {
        updateFields.push(`${key} = $${paramIndex}`);
        values.push(value);
      }
      paramIndex++;
    }
    
    if (updateFields.length === 0) {
      throw new Error('Нет полей для обновления');
    }
    
    updateFields.push(`updated_at = NOW()`);
    values.push(custom_id);
    
    const query = `
      UPDATE cars 
      SET ${updateFields.join(', ')}
      WHERE custom_id = $${paramIndex}
      RETURNING *;
    `;
    
    const result = await dbPool.executeQuery(query, values);
    
    if (result.rows.length === 0) {
      throw new Error(`Автомобиль с ID ${custom_id} не найден`);
    }
    
    console.log('✅ Автомобиль успешно обновлен');
    return result.rows[0];
    
  } catch (err) {
    console.error('❌ Ошибка при обновлении автомобиля:', err.message);
    throw err;
  }
}

// Функция для удаления автомобиля
async function deleteCar(custom_id) {
  console.log(`🗑️ Удаление автомобиля ${custom_id}`);
  
  try {
    const query = 'DELETE FROM cars WHERE custom_id = $1 RETURNING *';
    const result = await dbPool.executeQuery(query, [custom_id]);
    
    if (result.rows.length === 0) {
      throw new Error(`Автомобиль с ID ${custom_id} не найден`);
    }
    
    console.log('✅ Автомобиль успешно удален');
    return result.rows[0];
    
  } catch (err) {
    console.error('❌ Ошибка при удалении автомобиля:', err.message);
    throw err;
  }
}

// Экспорт функций (совместимость со старым API)
module.exports = {
  addCar,
  saveCar: addCar, // alias для совместимости
  getCar,
  getAllCars,
  checkConnection,
  checkDuplicate,
  updateCar,
  deleteCar,
  createTableIfNotExists
}; 