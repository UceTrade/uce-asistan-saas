# UceAsistan Deployment Guide

## İçindekiler

1. [Local Development](#local-development)
2. [Docker Deployment](#docker-deployment)
3. [Cloud Deployment (AWS)](#cloud-deployment-aws)
4. [Cloud Deployment (GCP)](#cloud-deployment-gcp)
5. [Production Checklist](#production-checklist)
6. [Monitoring Setup](#monitoring-setup)
7. [Backup Strategy](#backup-strategy)
8. [Troubleshooting](#troubleshooting)

---

## Local Development

### Prerequisites

```bash
# Python 3.11+
python --version

# MetaTrader 5 (Windows only)
# Download from https://www.metatrader5.com/
```

### Quick Start

```bash
# Clone repository
git clone https://github.com/yourorg/uceasistan.git
cd uceasistan

# Setup backend
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start server
python start_server.py
```

### Development Mode

```bash
# Enable debug logging
DEBUG=true python start_server.py

# Run REST API separately
uvicorn api:app --reload --port 8080
```

---

## Docker Deployment

### Build Images

```bash
# Build all images
docker-compose build

# Build specific service
docker build -f Dockerfile.backend -t uceasistan-backend:latest .
docker build -f Dockerfile.frontend -t uceasistan-frontend:latest .
```

### Run with Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Environment Variables

```bash
# Create .env file
cat > backend/.env << EOF
HOST=0.0.0.0
PORT=8766
DEBUG=false
GROQ_API_KEY=your_key_here
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id
EOF
```

> **Important:** MT5 requires Windows. For full functionality, run backend natively on Windows and containerize only frontend/support services.

---

## Cloud Deployment (AWS)

### Architecture

```
                    ┌─────────────────┐
                    │   CloudFront    │
                    │      (CDN)      │
                    └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │       ALB       │
                    │ (Load Balancer) │
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
    ┌────┴─────┐       ┌─────┴────┐       ┌─────┴────┐
    │  EC2 #1  │       │  EC2 #2  │       │  EC2 #3  │
    │ Frontend │       │ Backend  │       │  API     │
    │ (nginx)  │       │ (WS)     │       │ (FastAPI)│
    └──────────┘       └────┬─────┘       └────┬─────┘
                            │                  │
                       ┌────┴──────────────────┴────┐
                       │         RDS PostgreSQL      │
                       └─────────────────────────────┘
```

### Step 1: VPC Setup

```bash
# Create VPC with public/private subnets
aws ec2 create-vpc --cidr-block 10.0.0.0/16

# Create subnets
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.1.0/24 # public
aws ec2 create-subnet --vpc-id vpc-xxx --cidr-block 10.0.2.0/24 # private
```

### Step 2: EC2 Instance

```bash
# Launch instance
aws ec2 run-instances \
  --image-id ami-0abcdef1234567890 \
  --instance-type t3.medium \
  --key-name uceasistan-key \
  --security-groups sg-xxx \
  --user-data file://user-data.sh
```

### Step 3: RDS Database

```bash
# Create PostgreSQL instance
aws rds create-db-instance \
  --db-instance-identifier uceasistan-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username admin \
  --master-user-password CHANGE_ME \
  --allocated-storage 20
```

### Step 4: SSL Certificate

```bash
# Request certificate
aws acm request-certificate \
  --domain-name uceasistan.com \
  --validation-method DNS
```

---

## Cloud Deployment (GCP)

### Using Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/uceasistan-backend

# Deploy to Cloud Run
gcloud run deploy uceasistan-backend \
  --image gcr.io/PROJECT_ID/uceasistan-backend \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="HOST=0.0.0.0,PORT=8080"
```

### Using Compute Engine

```bash
# Create instance
gcloud compute instances create uceasistan-server \
  --machine-type=e2-medium \
  --image-project=windows-cloud \
  --image-family=windows-2022 \
  --boot-disk-size=50GB
```

---

## Production Checklist

### Security

- [ ] Change default JWT_SECRET
- [ ] Enable HTTPS (SSL certificates)
- [ ] Configure CORS properly
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Encrypt API keys in database
- [ ] Regular security audits

### Performance

- [ ] Enable gzip compression
- [ ] Set up CDN for static assets
- [ ] Configure database connection pooling
- [ ] Enable caching (Redis)
- [ ] Optimize Docker images

### Reliability

- [ ] Set up health checks
- [ ] Configure auto-scaling
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set up error alerting

### Monitoring

- [ ] Set up Prometheus metrics
- [ ] Configure Grafana dashboards
- [ ] Enable Sentry error tracking
- [ ] Set up uptime monitoring
- [ ] Configure PagerDuty/Slack alerts

---

## Monitoring Setup

### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'uceasistan-backend'
    static_configs:
      - targets: ['backend:8766']
    
  - job_name: 'uceasistan-api'
    static_configs:
      - targets: ['api:8080']
```

### Grafana Dashboard

Import dashboard ID: `12345` for UceAsistan monitoring.

### Sentry Integration

```python
# In start_server.py
import sentry_sdk
sentry_sdk.init(
    dsn="https://xxx@sentry.io/xxx",
    traces_sample_rate=0.1,
)
```

---

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d)
pg_dump -h localhost -U admin uceasistan > backup_$DATE.sql
aws s3 cp backup_$DATE.sql s3://uceasistan-backups/
```

### Strategy/Template Backups

```bash
# Backup user data
cp backend/user_templates.json backups/templates_$(date +%Y%m%d).json
```

---

## Troubleshooting

### Common Issues

#### MT5 Connection Failed
```
[ERROR] Failed to initialize MT5
```
**Solution:** Ensure MT5 terminal is running and logged in.

#### WebSocket Connection Refused
```
WebSocket connection failed
```
**Solution:** Check firewall, ensure port 8766 is open.

#### AI API Rate Limited
```
Rate limit exceeded
```
**Solution:** Wait 60 seconds or upgrade API tier.

### Logs Location

| Service | Log Location |
|---------|-------------|
| Backend | `backend/logs/uceasistan.log` |
| Docker | `docker-compose logs backend` |
| Nginx | `/var/log/nginx/access.log` |

### Getting Help

- GitHub Issues: https://github.com/yourorg/uceasistan/issues
- Email: support@uceasistan.com
- Discord: https://discord.gg/uceasistan
