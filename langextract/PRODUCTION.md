# Production Deployment Guide

This guide covers deploying LangExtract to production using Docker and WSGI for optimal performance.

## 🚀 Quick Start

### 1. Prepare Environment

```bash
# Copy production environment template
cp env.prod .env.prod

# Edit with your production values
nano .env.prod
```

### 2. Deploy

```bash
# Make deployment script executable
chmod +x deploy-prod.sh

# Run production deployment
./deploy-prod.sh
```

## 📋 Production Configuration

### Environment Variables (.env.prod)

```bash
# Django Settings
DEBUG=False
DJANGO_SECRET_KEY=your-long-random-secret-key
ALLOWED_HOSTS=your-domain.com,localhost,127.0.0.1

# OpenAI API
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=text-embedding-3-small

# API Settings
API_RATE_LIMIT=1000
MAX_TOKENS_PER_REQUEST=8000
```

### Gunicorn Configuration

The production setup uses Gunicorn with optimized settings:

- **Workers**: 4 (configurable via GUNICORN_WORKERS)
- **Worker Class**: sync (best for CPU-bound tasks)
- **Max Requests**: 1000 per worker (prevents memory leaks)
- **Timeout**: 30 seconds
- **Preload**: Enabled for faster startup

## 🔧 Performance Optimizations

### 1. Multi-Stage Docker Build

- Builder stage installs dependencies
- Production stage only contains runtime files
- Smaller final image size

### 2. WSGI Configuration

- **Workers**: 4 (adjust based on CPU cores)
- **Worker Connections**: 1000 per worker
- **Max Requests**: 1000 per worker (restart to prevent memory issues)
- **Keep-Alive**: 2 seconds for connection reuse

### 3. Resource Management

- Non-root user for security
- Health checks for monitoring
- Automatic restart policies
- Volume mounts for logs only (stateless API service)

## 📊 Monitoring

### Health Checks

- **Endpoint**: `/health/`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3

### Logs

```bash
# View container logs
docker-compose -f docker-compose.prod.yml logs -f web

# View logs from host
tail -f logs/langextract.log
```

### Static Files

This is a stateless API service - no static files are served or collected.

### Metrics

- **API Status**: `/api/status/`
- **Processing Stats**: `/api/stats/`
- **Health**: `/health/`

## 🔄 Deployment Commands

### Manual Deployment

```bash
# Build production image
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# View logs
docker-compose -f docker-compose.prod.yml logs -f web
```

### Using Deployment Script

```bash
# Full production deployment
./deploy-prod.sh

# Check status
docker-compose -f docker-compose.prod.yml ps
```

## 🚨 Troubleshooting

### Common Issues

1. **Port Already in Use**

   ```bash
   # Check what's using port 8000
   lsof -i :8000

   # Stop conflicting service
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Environment Variables Missing**

   ```bash
   # Verify .env.prod exists and has required values
   cat .env.prod
   ```

3. **Service Not Starting**

   ```bash
   # Check container logs
   docker-compose -f docker-compose.prod.yml logs web

   # Check health status
   curl http://localhost:8000/health/
   ```

### Performance Tuning

1. **Adjust Worker Count**

   ```bash
   # In .env.prod
   GUNICORN_WORKERS=8  # For 8+ CPU cores
   ```

2. **Memory Optimization**

   ```bash
   # In .env.prod
   GUNICORN_MAX_REQUESTS=500  # Lower for memory-constrained environments
   ```

3. **Timeout Adjustments**
   ```bash
   # In .env.prod
   GUNICORN_TIMEOUT=60  # Increase for longer processing tasks
   ```

## 🔒 Security Considerations

- **Non-root user**: Container runs as `appuser`
- **Environment variables**: Sensitive data in `.env.prod`
- **Health checks**: Prevents serving unhealthy instances
- **Port binding**: Only exposes necessary port 8000

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale to multiple instances
docker-compose -f docker-compose.prod.yml up -d --scale web=3
```

### Load Balancer Integration

- Point your load balancer to port 8000
- Use health check endpoint for backend health
- Configure sticky sessions if needed

## 🎯 Best Practices

1. **Always use `.env.prod` for production**
2. **Monitor logs regularly**
3. **Set up log rotation for production logs**
4. **Use health checks in your monitoring system**
5. **Regular container restarts to prevent memory leaks**
6. **Monitor OpenAI API usage and costs**

## 📞 Support

For production issues:

1. Check container logs
2. Verify environment variables
3. Test health endpoints
4. Review this guide
5. Check the main README.md for additional information
