# Order Service

Python Flask microservice for order management.

## Features
- Order creation and tracking
- Integration with user and product services
- PostgreSQL database integration
- RESTful API design

## API Endpoints
- GET /health - Health check
- GET /api/orders - Get all orders
- GET /api/orders/:id - Get order by ID
- POST /api/orders - Create new order

## Environment Variables
- DB_HOST - PostgreSQL host
- DB_USER - Database user
- DB_PASS - Database password
- DB_NAME - Database name
- REDIS_HOST - Redis host

## Running Locally
```bash
pip install -r requirements.txt
python app.py
```
