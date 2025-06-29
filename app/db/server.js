const express = require('express');
const { addCar } = require('./car');
require('dotenv').config();

const app = express();
app.use(express.json());

app.post('/add-car', async (req, res) => {
  try {
    const car = await addCar(req.body);
    res.json({ success: true, car });
  } catch (err) {
    res.status(500).json({ success: false, error: err.message });
  }
});

const PORT = process.env.NODE_PORT || 3001;
app.listen(PORT, () => {
  console.log(`Node.js car API server running on port ${PORT}`);
}); 