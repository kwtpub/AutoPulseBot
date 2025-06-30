const axios = require('axios');

async function testAddCar() {
  const car = {
    custom_id: 'test-001',
    source_message_id: 123,
    source_channel_name: '@testchannel',
    target_channel_message_id: null,
    brand: 'TestBrand',
    model: 'TestModel',
    year: 2022,
    price: 10000,
    description: 'Тестовая машина',
    photos: ['https://example.com/photo1.jpg'],
    status: 'available',
  };

  try {
    const res = await axios.post('http://localhost:3001/add-car', car);
    console.log('Ответ сервера:', res.data);
  } catch (err) {
    if (err.response) {
      console.error('Ошибка ответа сервера:', err.response.data);
    } else {
      console.error('Ошибка запроса:', err.message);
    }
  }
}

testAddCar();