# DCIS - Deployment Guide

**Production Deployment Guide for Dynamic Cognitive Intelligence System**

---

## 📚 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Local Development](#local-development)
4. [Docker Deployment](#docker-deployment)
5. [Kubernetes Deployment](#kubernetes-deployment)
6. [Environment Variables](#environment-variables)
7. [Database Setup](#database-setup)
8. [Monitoring & Logging](#monitoring--logging)

---

## 🔧 Prerequisites

### Required Software
- **Python**: 3.11+
- **Node.js**: 20+
- **Docker**: 24+
- **Kubernetes**: 1.28+ (for production)
- **PostgreSQL**: 15+ (optional)
- **Neo4j**: 5.0+
- **Redis**: 7+

### Hardware Requirements

**Development**:
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB

**Production**:
- CPU: 16+ cores
- RAM: 32GB+
- Storage: 100GB+ SSD
- GPU: NVIDIA (for inference, optional)

---

## 🌍 Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/dcis.git
cd dcis
```

### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies
pip install -r requirements-test.txt
```

### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# or with yarn
yarn install
```

---

## 💻 Local Development

### Start Services Individually

**Backend**:
```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm run dev
```

**Access**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

---

### Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services Included**:
- Backend API (port 8000)
- Frontend (port 3000)
- Neo4j (port 7474, 7687)
- Redis (port 6379)
- ChromaDB (port 8001)

---

## 🐳 Docker Deployment

### Build Images

**Backend**:
```bash
cd backend
docker build -t dcis-backend:latest .
```

**Frontend**:
```bash
cd frontend
docker build -t dcis-frontend:latest .
```

### Push to Registry
```bash
# Tag images
docker tag dcis-backend:latest your-registry/dcis-backend:v1.0.0
docker tag dcis-frontend:latest your-registry/dcis-frontend:v1.0.0

# Push
docker push your-registry/dcis-backend:v1.0.0
docker push your-registry/dcis-frontend:v1.0.0
```

### Docker Compose Production

Create `docker-compose.prod.yml`:
```yaml
version: '3.8'

services:
  backend:
    image: your-registry/dcis-backend:v1.0.0
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - REDIS_URL=redis://redis:6379
      - CHROMA_HOST=chromadb
    depends_on:
      - neo4j
      - redis
      - chromadb
    restart: always

  frontend:
    image: your-registry/dcis-frontend:v1.0.0
    ports:
      - "80:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
    depends_on:
      - backend
    restart: always

  neo4j:
    image: neo4j:5.16.0
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/yourpassword
    volumes:
      - neo4j_data:/data
    restart: always

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: always

  chromadb:
    image: chromadb/chroma:latest
    ports:
      - "8001:8000"
    volumes:
      - chroma_data:/chroma/chroma
    restart: always

volumes:
  neo4j_data:
  redis_data:
  chroma_data:
```

**Start**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

---

## ☸️ Kubernetes Deployment

### Prerequisites
```bash
# Install kubectl
kubectl version --client

# Configure cluster access
kubectl config use-context your-cluster
```

### Deploy Services

**1. Create Namespace**:
```bash
kubectl create namespace dcis
```

**2. Deploy Databases**:
```bash
kubectl apply -f infrastructure/k8s/databases.yaml -n dcis
```

**3. Deploy Backend**:
```bash
kubectl apply -f infrastructure/k8s/backend-deployment.yaml -n dcis
kubectl apply -f infrastructure/k8s/backend-service.yaml -n dcis
```

**4. Deploy Frontend**:
```bash
kubectl apply -f infrastructure/k8s/frontend-deployment.yaml -n dcis
kubectl apply -f infrastructure/k8s/frontend-service.yaml -n dcis
```

**5. Create Ingress**:
```bash
kubectl apply -f infrastructure/k8s/ingress.yaml -n dcis
```

### Verify Deployment
```bash
# Check pods
kubectl get pods -n dcis

# Check services
kubectl get svc -n dcis

# Check ingress
kubectl get ingress -n dcis

# View logs
kubectl logs -f deployment/dcis-backend -n dcis
```

### Scale Deployment
```bash
# Scale backend
kubectl scale deployment dcis-backend --replicas=5 -n dcis

# Scale frontend
kubectl scale deployment dcis-frontend --replicas=3 -n dcis
```

---

## 🔐 Environment Variables

### Backend (.env)

```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000,https://your-domain.com

# Database Connections
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=yourpassword

MONGODB_URI=mongodb://localhost:27017
MONGODB_DB=dcis

REDIS_URL=redis://localhost:6379

CHROMA_HOST=localhost
CHROMA_PORT=8001

# AI Services
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# vLLM Inference (optional)
VLLM_HOST=localhost
VLLM_PORT=8080

# Security
JWT_SECRET=your-super-secret-key-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION=24  # hours

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Monitoring
PROMETHEUS_PORT=9090
```

### Frontend (.env.local)

```bash
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Feature Flags
NEXT_PUBLIC_ENABLE_3D=true
NEXT_PUBLIC_ENABLE_ANALYTICS=true

# Analytics (optional)
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```

---

## 🗄️ Database Setup

### Neo4j Configuration

**1. Start Neo4j**:
```bash
docker run -d \
  --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/yourpassword \
  -v neo4j_data:/data \
  neo4j:5.16.0
```

**2. Access Browser**: http://localhost:7474

**3. Run Migrations**:
```bash
cd backend
python scripts/init_neo4j.py
```

### ChromaDB Setup

**Start ChromaDB**:
```bash
docker run -d \
  --name chromadb \
  -p 8001:8000 \
  -v chroma_data:/chroma/chroma \
  chromadb/chroma:latest
```

### Redis Setup

**Start Redis**:
```bash
docker run -d \
  --name redis \
  -p 6379:6379 \
  -v redis_data:/data \
  redis:7-alpine
```

---

## 📊 Monitoring & Logging

### Prometheus Metrics

**Backend exposes metrics at**: `http://localhost:8000/metrics`

**Prometheus config** (`prometheus.yml`):
```yaml
scrape_configs:
  - job_name: 'dcis-backend'
    static_configs:
      - targets: ['backend:8000']
```

### Grafana Dashboards

**Import Dashboard**:
1. Access Grafana: http://localhost:3001
2. Import `infrastructure/grafana/dcis-dashboard.json`

### Log Aggregation

**Using ELK Stack**:
```bash
# Start ELK
docker-compose -f docker-compose.elk.yml up -d

# View logs in Kibana
http://localhost:5601
```

**Using Loki**:
```bash
# Configure Promtail
kubectl apply -f infrastructure/k8s/promtail-config.yaml
```

---

## 🧪 Health Checks

### API Health
```bash
curl http://localhost:8000/health
```

**Response**:
```json
{
  "status": "healthy",
  "services": {
    "api": "online",
    "neo4j": "online",
    "redis": "online"
  }
}
```

### Kubernetes Probes

Already configured in `backend-deployment.yaml`:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

## 🚀 Production Checklist

- [ ] Set strong passwords for all databases
- [ ] Configure SSL/TLS certificates
- [ ] Set up firewall rules
- [ ] Enable rate limiting
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Review security settings
- [ ] Test disaster recovery
- [ ] Document runbooks
- [ ] Train operations team

---

## 🔗 Additional Resources

- [API Documentation](./API.md)
- [Component Documentation](./COMPONENTS.md)
- [Architecture Overview](../README.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
