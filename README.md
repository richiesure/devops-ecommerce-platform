# DevOps E-Commerce Platform

A complete microservices-based e-commerce platform demonstrating modern DevOps practices.

## Architecture

- VPC with public/private subnets across 2 availability zones
- Application Load Balancer for traffic distribution
- RDS PostgreSQL for data persistence
- ElastiCache Redis for caching
- Jenkins for CI/CD automation
- SonarQube for code quality analysis

## Services

### Product Service (Node.js)
- Port: 3000
- Features: Product catalog, Redis caching
- Health Check: /health

### User Service (Node.js)
- Port: 8080
- Features: User management, JWT authentication
- Health Check: /health

### Order Service (Python Flask)
- Port: 5000
- Features: Order processing, database integration
- Health Check: /health

### Frontend (HTML/CSS/JS)
- Port: 80 (Nginx)
- Features: Interactive dashboard for all services

## Infrastructure

All infrastructure is managed as code using Terraform. See `infrastructure/` directory.

## Deployment

CI/CD pipelines are configured in Jenkins. Each service has its own pipeline:
- product-service-pipeline
- user-service-pipeline
- order-service-pipeline

## URLs

- Application: http://devops-ecommerce-alb-1568390396.eu-west-2.elb.amazonaws.com
- Jenkins: http://devops-ecommerce-alb-1568390396.eu-west-2.elb.amazonaws.com:8080
- SonarQube: http://devops-ecommerce-alb-1568390396.eu-west-2.elb.amazonaws.com:9000
