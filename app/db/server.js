const express = require('express');
const { saveCar } = require('./car');
require('dotenv').config({ path: '../../.env' });

const app = express();
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy', 
    message: 'Node.js API is running',
    timestamp: new Date().toISOString()
  });
});

app.post('/api/cars', async (req, res) => {
  try {
    const carData = req.body;
    const result = await saveCar(carData);
    res.status(201).json({ success: true, car: result });
  } catch (error) {
    console.error('Error saving car:', error);
    res.status(500).json({ 
      success: false, 
      error: error.message || 'Failed to save car' 
    });
  }
});

const PORT = process.env.NODE_PORT || 3001;
app.listen(PORT, () => {
  console.log(`Node.js API server running on port ${PORT}`);
}); 