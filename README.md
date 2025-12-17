# Online Library System - Microservices

A microservices-based online library management system built with Docker.

## Services
- **Catalog Service** (Python/Flask + PostgreSQL)
- **User Service** (Python/Flask + MySQL)
- **Order Service** (PHP + MySQL)

## Setup
```bash
docker-compose up --build
```

## Access
- Catalog: http://localhost:6000/catalog
- Users: http://localhost:6001/users
- Orders: http://localhost:6002/orders
