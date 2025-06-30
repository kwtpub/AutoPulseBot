const express = require('express');
const bodyParser = require('body-parser');
const { saveCar, checkConnection, getCar, getAllCars } = require('./car');
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

// Get single car by custom_id
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
    console.error('Error getting car:', error);
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
    console.error('Error getting cars:', error);
    res.status(500).json({ 
      error: 'Internal server error',
      message: error.message 
    });
  }
});

// Add new car
app.post('/api/cars', async (req, res) => {
  try {
    const result = await saveCar(req.body);
    res.status(201).json({ 
      message: 'Car saved successfully', 
      car: result 
    });
  } catch (error) {
    console.error('Error saving car:', error);
    
    // Специфичная обработка ошибок
    if (error.code === '23505') { // duplicate key
      res.status(409).json({ 
        error: 'Car with this custom_id already exists',
        custom_id: req.body.custom_id 
      });
    } else if (error.code === 'ETIMEDOUT') {
      res.status(503).json({ 
        error: 'Database connection timeout',
        message: 'Please try again later' 
      });
    } else {
      res.status(500).json({ 
        error: 'Failed to save car',
        message: error.message 
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

// Initialize server
async function startServer() {
  try {
    // Проверяем подключение к БД при старте
    const dbConnected = await checkConnection();
    if (!dbConnected) {
      console.warn('⚠️  Database connection failed, but server will start anyway');
    }
    
    app.listen(PORT, () => {
      console.log(`🚀 Server running on port ${PORT}`);
      console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
      console.log(`🚗 Cars API: http://localhost:${PORT}/api/cars`);
    });
  } catch (error) {
    console.error('❌ Failed to start server:', error);
    process.exit(1);
  }
}

startServer();

module.exports = app; 