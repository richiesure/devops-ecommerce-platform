# User Service

Node.js microservice for user management and authentication.

## Features
- User registration and authentication
- JWT token management
- Redis session caching
- PostgreSQL database integration

## API Endpoints
- GET /health - Health check
- GET /api/users - Get all users
- GET /api/users/:id - Get user by ID
- POST /api/users - Create new user

## Environment Variables
- DB_HOST - PostgreSQL host
- DB_USER - Database user
- DB_PASS - Database password
- DB_NAME - Database name
- REDIS_HOST - Redis host
- PORT - Service port (default: 8080)
