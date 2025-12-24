# Product Service

Node.js microservice for managing product catalog.

## Features
- CRUD operations for products
- Redis caching for improved performance
- PostgreSQL database integration
- RESTful API design

## API Endpoints
- GET /health - Health check
- GET /api/products - Get all products
- GET /api/products/:id - Get product by ID
- POST /api/products - Create new product

## Environment Variables
- DB_HOST - PostgreSQL host
- DB_USER - Database user
- DB_PASS - Database password
- DB_NAME - Database name
- REDIS_HOST - Redis host
- PORT - Service port (default: 3000)

## Running Locally
```bash
npm install
npm start
```

## Running with Docker
```bash
docker build -t product-service .
docker run -p 3000:3000 product-service
```
