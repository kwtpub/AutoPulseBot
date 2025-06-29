const { Client } = require('pg');
require('dotenv').config();

const connectionString = process.env.DATABASE_URL
  .replace(/([&?])(sslmode|channel_binding)=require&?/g, '$1')
  .replace(/[?&]$/, '');

const client = new Client({
  connectionString,
  ssl: { rejectUnauthorized: false },
});

async function addCar(car) {
  await client.connect();
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
  await client.end();
  return res.rows[0];
}

// Пример использования
if (require.main === module) {
  (async () => {
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

module.exports = { addCar }; 