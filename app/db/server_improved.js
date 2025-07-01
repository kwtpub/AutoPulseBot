/**
 * Express Server - улучшенная версия с надежной обработкой ошибок
 * Включает health monitoring, graceful shutdown и auto-restart логику
 */

const express = require('express');
const bodyParser = require('body-parser');
require('dotenv').config({ path: require('path').resolve(__dirname, '../../.env') });

// Используем улучшенные модули
const { 
  saveCar, 
  checkConnection, 
  getCar, 
  getAllCars, 
  checkDuplicate,
  updateCar,
  deleteCar 
} = require('./car_improved');

const dbPool = require('./database_pool');

const app = express();
const PORT = process.env.NODE_PORT || 3001;

// Переменные для мониторинга здоровья сервера
let serverHealth = {
  status: 'starting',
  uptime: 0,
  requests: 0,
  errors: 0,
  lastError: null,
  dbConnected: false
};

// Middleware
app.use(bodyParser.json({ limit: '10mb' }));
app.use(bodyParser.urlencoded({ extended: true, limit: '10mb' }));

// Middleware для подсчета запросов
app.use((req, res, next) => {
  serverHealth.requests++;
  next();
});

// Health check endpoint с расширенной информацией
app.get('/api/health', async (req, res) => {
  try {
    const dbConnected = await checkConnection();
    serverHealth.dbConnected = dbConnected;
    
    // Статистика пула соединений
    const poolStats = dbPool.getPoolStats();
    
    const healthInfo = {
      server: {
        status: serverHealth.status,
        uptime: Math.floor(process.uptime()),
        requests: serverHealth.requests,
        errors: serverHealth.errors,
        memory: process.memoryUsage(),
        timestamp: new Date().toISOString()
      },
      database: {
        connected: dbConnected,
        pool: poolStats,
        lastError: serverHealth.lastError
      }
    };
    
    res.json(healthInfo);
  } catch (error) {
    serverHealth.errors++;
    serverHealth.lastError = {
      message: error.message,
      timestamp: new Date().toISOString()
    };
    
    res.status(500).json({ 
      server: { status: 'error' },
      database: { connected: false },
      error: error.message,
      timestamp: new Date().toISOString() 
    });
  }
});

// Get single car by custom_id с retry логикой
app.get('/api/cars/:custom_id', async (req, res) => {
  try {
    const { custom_id } = req.params;
    const car = await getCar(custom_id);
    
    if (!car) {
      return res.status(404).json({ 
        error: 'Car not found',
        custom_id 
      });
    }
    
    res.json(car);
  } catch (error) {
    serverHealth.errors++;
    serverHealth.lastError = {
      message: error.message,
      endpoint: req.path,
      timestamp: new Date().toISOString()
    };
    
    console.error('❌ Error getting car:', error.message);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
});

// Get all cars with pagination
app.get('/api/cars', async (req, res) => {
  try {
    const page = parseInt(req.query.page) || 1;
    const limit = parseInt(req.query.limit) || 10;
    const offset = (page - 1) * limit;
    
    const { cars, total } = await getAllCars(limit, offset);
    
    res.json({
      cars,
      pagination: {
        page,
        limit,
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    serverHealth.errors++;
    serverHealth.lastError = {
      message: error.message,
      endpoint: req.path,
      timestamp: new Date().toISOString()
    };
    
    console.error('❌ Error getting cars:', error.message);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
});

// Check for duplicate car by source message ID and channel
app.get('/api/cars/check-duplicate/:message_id/:channel', async (req, res) => {
  try {
    const { message_id, channel } = req.params;
    const duplicate = await checkDuplicate(parseInt(message_id), channel);
    
    if (duplicate) {
      res.json(duplicate);
    } else {
      res.json(null);
    }
  } catch (error) {
    serverHealth.errors++;
    serverHealth.lastError = {
      message: error.message,
      endpoint: req.path,
      timestamp: new Date().toISOString()
    };
    
    console.error('❌ Error checking duplicate:', error.message);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
});

// Add new car с улучшенной обработкой ошибок
app.post('/api/cars', async (req, res) => {
  const startTime = Date.now();
  
  try {
    console.log(`🚗 POST /api/cars - добавление автомобиля ${req.body.custom_id}`);
    
    const result = await saveCar(req.body);
    
    const duration = Date.now() - startTime;
    console.log(`✅ Автомобиль добавлен за ${duration}мс`);
    
    res.status(201).json({ 
      message: 'Car saved successfully', 
      car: result,
      duration: `${duration}ms`
    });
    
  } catch (error) {
    const duration = Date.now() - startTime;
    serverHealth.errors++;
    serverHealth.lastError = {
      message: error.message,
      custom_id: req.body.custom_id,
      endpoint: req.path,
      duration: `${duration}ms`,
      timestamp: new Date().toISOString()
    };
    
    console.error(`❌ Error saving car (${duration}ms):`, error.message);
    
    // Специфичная обработка различных типов ошибок
    if (error.code === '23505' || error.message.includes('уже существует')) {
      res.status(409).json({ 
        error: 'Car with this custom_id already exists',
        custom_id: req.body.custom_id,
        duration: `${duration}ms`
      });
    } else if (error.message.includes('Connection terminated') || 
               error.message.includes('connection timeout') ||
               error.code === 'ETIMEDOUT') {
      
      // Логируем проблему с соединением
      console.error('🔴 Database connection issue detected, attempting recovery...');
      
      res.status(503).json({ 
        error: 'Database connection timeout',
        message: 'The server is experiencing connectivity issues. Please try again in a moment.',
        duration: `${duration}ms`,
        retry_after: '5s'
      });
    } else {
      res.status(500).json({ 
        error: 'Failed to save car',
        message: error.message,
        duration: `${duration}ms`
      });
    }
  }
});

// Update car endpoint
app.put('/api/cars/:custom_id', async (req, res) => {
  try {
    const { custom_id } = req.params;
    const updates = req.body;
    
    const updatedCar = await updateCar(custom_id, updates);
    
    res.json({ 
      message: 'Car updated successfully', 
      car: updatedCar 
    });
  } catch (error) {
    serverHealth.errors++;
    console.error('❌ Error updating car:', error.message);
    
    if (error.message.includes('не найден')) {
      res.status(404).json({ 
        error: 'Car not found',
        custom_id: req.params.custom_id 
      });
    } else {
      res.status(500).json({ 
        error: 'Failed to update car',
        message: error.message 
      });
    }
  }
});

// Delete car endpoint
app.delete('/api/cars/:custom_id', async (req, res) => {
  try {
    const { custom_id } = req.params;
    
    const deletedCar = await deleteCar(custom_id);
    
    res.json({ 
      message: 'Car deleted successfully', 
      car: deletedCar 
    });
  } catch (error) {
    serverHealth.errors++;
    console.error('❌ Error deleting car:', error.message);
    
    if (error.message.includes('не найден')) {
      res.status(404).json({ 
        error: 'Car not found',
        custom_id: req.params.custom_id 
      });
    } else {
      res.status(500).json({ 
        error: 'Failed to delete car',
        message: error.message 
      });
    }
  }
});

// Global error handling middleware
app.use((error, req, res, next) => {
  serverHealth.errors++;
  serverHealth.lastError = {
    message: error.message,
    stack: error.stack,
    timestamp: new Date().toISOString()
  };
  
  console.error('🔴 Unhandled error:', error);
  
  if (!res.headersSent) {
    res.status(500).json({ 
      success: false, 
      error: 'Internal server error',
      timestamp: new Date().toISOString()
    });
  }
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    path: req.path,
    method: req.method
  });
});

// Health monitoring - периодическая проверка БД
async function healthMonitor() {
  try {
    const connected = await checkConnection();
    serverHealth.dbConnected = connected;
    
    if (!connected) {
      console.warn('⚠️ Database connection lost, but server continues running');
    }
  } catch (error) {
    console.error('❌ Health monitor error:', error.message);
    serverHealth.dbConnected = false;
  }
}

// Initialize server with improved startup
async function startServer() {
  try {
    console.log('🚀 Starting Express server...');
    
    // Проверяем подключение к БД при старте
    console.log('🔍 Checking database connection...');
    const dbConnected = await checkConnection();
    serverHealth.dbConnected = dbConnected;
    
    if (!dbConnected) {
      console.warn('⚠️ Database connection failed, but server will start anyway');
      console.warn('⚠️ Database retry logic will handle reconnection attempts');
    } else {
      console.log('✅ Database connection established');
    }
    
    // Запускаем сервер
    const server = app.listen(PORT, () => {
      serverHealth.status = 'running';
      console.log(`🚀 Server running on port ${PORT}`);
      console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
      console.log(`🚗 Cars API: http://localhost:${PORT}/api/cars`);
      console.log(`💾 Database: ${dbConnected ? '✅ Connected' : '❌ Disconnected (will retry)'}`);
    });
    
    // Запускаем health monitor каждые 30 секунд
    setInterval(healthMonitor, 30000);
    
    // Graceful shutdown
    process.on('SIGTERM', async () => {
      console.log('🛑 SIGTERM received, shutting down gracefully...');
      serverHealth.status = 'shutting_down';
      
      server.close(async () => {
        console.log('🔒 HTTP server closed');
        await dbPool.close();
        console.log('👋 Server shutdown complete');
        process.exit(0);
      });
    });
    
    process.on('SIGINT', async () => {
      console.log('🛑 SIGINT received, shutting down gracefully...');
      serverHealth.status = 'shutting_down';
      
      server.close(async () => {
        console.log('🔒 HTTP server closed');
        await dbPool.close();
        console.log('👋 Server shutdown complete');
        process.exit(0);
      });
    });
    
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    serverHealth.status = 'failed';
    process.exit(1);
  }
}

// Запуск сервера
startServer();

module.exports = app; 