const express = require('express');
const bodyParser = require('body-parser');
const { saveCar, checkConnection } = require('./car');
require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });

const app = express();
const PORT = process.env.NODE_PORT || 3001;

// Middleware
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// Health check endpoint
app.get('/api/health', async (req, res) => {
  try {
    const dbConnected = await checkConnection();
    res.json({ 
      status: 'ok', 
      database: dbConnected ? 'connected' : 'disconnected',
      timestamp: new Date().toISOString() 
    });
  } catch (error) {
    res.status(500).json({ 
      status: 'error', 
      database: 'error',
      error: error.message,
      timestamp: new Date().toISOString() 
    });
  }
});

// Add car endpoint
app.post('/api/cars', async (req, res) => {
  try {
    console.log('Получен запрос на добавление автомобиля:', req.body);
    const result = await saveCar(req.body);
    res.json({ success: true, car: result });
  } catch (error) {
    console.error('Error saving car:', error);
    
    // Определяем тип ошибки для лучшего ответа
    if (error.code === 'ETIMEDOUT') {
      res.status(503).json({ 
        success: false, 
        error: 'Database connection timeout. Please try again.',
        code: 'DB_TIMEOUT'
      });
    } else if (error.code === '23505') { // duplicate key
      res.status(409).json({ 
        success: false, 
        error: 'Car with this ID already exists.',
        code: 'DUPLICATE_KEY'
      });
    } else {
      res.status(500).json({ 
        success: false, 
        error: error.message,
        code: error.code || 'UNKNOWN_ERROR'
      });
    }
  }
});

// Error handling middleware
app.use((error, req, res, next) => {
  console.error('Unhandled error:', error);
  res.status(500).json({ 
    success: false, 
    error: 'Internal server error',
    timestamp: new Date().toISOString()
  });
});

app.listen(PORT, () => {
  console.log(`🚗 Car API сервер запущен на порту ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
  console.log(`🔗 API endpoint: http://localhost:${PORT}/api/cars`);
  
  // Проверяем подключение к БД при старте
  setTimeout(async () => {
    try {
      const connected = await checkConnection();
      if (connected) {
        console.log('✅ PostgreSQL подключение успешно проверено');
      } else {
        console.log('❌ Проблема с подключением к PostgreSQL');
      }
    } catch (error) {
      console.log('❌ Ошибка проверки подключения к PostgreSQL:', error.message);
    }
  }, 1000);
});

module.exports = app; 