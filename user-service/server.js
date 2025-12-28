const express = require('express');
const { Pool } = require('pg');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
const redis = require('redis');
const cors = require('cors');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 8080;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';

app.use(cors());
app.use(express.json());

// PostgreSQL connection

const pool = new Pool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASS,
  database: process.env.DB_NAME,
  port: 5432,
});

// Redis connection
const redisClient = redis.createClient({
  socket: {
    host: process.env.REDIS_HOST,
    port: 6379
  }
});

redisClient.connect().catch(console.error);

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    service: 'user-service',
    timestamp: new Date().toISOString()
  });
});

// Register new user
app.post('/api/users/register', async (req, res) => {
  try {
    const { username, email, password, full_name } = req.body;
    
    if (!username || !email || !password) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    // Hash password
    const password_hash = await bcrypt.hash(password, 10);
    
    const result = await pool.query(
      'INSERT INTO users (username, email, password_hash, full_name) VALUES ($1, $2, $3, $4) RETURNING id, username, email, full_name, created_at',
      [username, email, password_hash, full_name]
    );

    res.status(201).json({
      message: 'User created successfully',
      user: result.rows[0]
    });
  } catch (error) {
    if (error.code === '23505') { // Unique constraint violation
      return res.status(409).json({ error: 'Username or email already exists' });
    }
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Login
app.post('/api/users/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ error: 'Missing credentials' });
    }

    const result = await pool.query(
      'SELECT * FROM users WHERE username = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    const user = result.rows[0];
    const validPassword = await bcrypt.compare(password, user.password_hash);

    if (!validPassword) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Generate JWT token
    const token = jwt.sign(
      { user_id: user.id, username: user.username },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    // Cache session
    await redisClient.setEx(`session:${user.id}`, 86400, token);

    res.json({
      message: 'Login successful',
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        full_name: user.full_name
      }
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get user profile
app.get('/api/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    // Check cache
    const cacheKey = `user:${id}`;
    const cached = await redisClient.get(cacheKey);
    
    if (cached) {
      return res.json({
        source: 'cache',
        data: JSON.parse(cached)
      });
    }

    const result = await pool.query(
      'SELECT id, username, email, full_name, created_at FROM users WHERE id = $1',
      [id]
    );

    if (result.rows.length === 0) {
      return res.status(404).json({ error: 'User not found' });
    }

    await redisClient.setEx(cacheKey, 300, JSON.stringify(result.rows[0]));

    res.json({
      source: 'database',
      data: result.rows[0]
    });
  } catch (error) {
    console.error('Error fetching user:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Get all users
app.get('/api/users', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT id, username, email, full_name, created_at FROM users ORDER BY created_at DESC'
    );

    res.json({
      data: result.rows,
      count: result.rows.length
    });
  } catch (error) {
    console.error('Error fetching users:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`User Service running on port ${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
});
