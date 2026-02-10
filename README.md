# DCIS - Dynamic Cognitive Intelligence System

> **Enterprise AI Orchestration Platform with Advanced Multi-modal Capabilities**

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/your-org/dcis)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-yellow.svg)](https://python.org)
[![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)](https://www.typescriptlang.org/)

---

## 📋 Overview

DCIS is a production-ready, enterprise-grade AI orchestration platform featuring:

- **4 Specialized AI Agents** for domain-specific tasks
- **Advanced AI Systems** (Oneiroi Dreaming, GAIA Tournaments, Multi-modal Processing)
- **Immersive 3D Visualizations** with React Three Fiber
- **Real-time Communications** via WebSocket
- **60+ API Endpoints** for comprehensive functionality
- **35,500+ LOC** of production-ready code

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Frontend (React/Next.js)                   │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ │
│  │ Multi-modal│ │Tournament  │ │Performance │ │   Chat   │ │
│  │   Viewer   │ │  Bracket   │ │ Dashboard  │ │Interface │ │
│  └────────────┘ └────────────┘ └────────────┘ └──────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend (Python)                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        Specialized Agents (4)                        │   │
│  │  Data Analyst | Designer | Translator | Financial   │   │
│  └─────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         Advanced AI Services                         │   │
│  │  Oneiroi Dreams | GAIA Tournaments | Multi-modal    │   │
│  └─────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
┌──────────────┐  ┌──────────┐  ┌────────────┐
│    Neo4j     │  │ ChromaDB │  │   Redis    │
│ Knowledge    │  │  Vector  │  │   Cache    │
│    Graph     │  │   Store  │  │            │
└──────────────┘  └──────────┘  └────────────┘
```

---

## ✨ Features

### 🤖 Specialized Agents

#### Data Analyst Agent
- Dataset profiling & statistical analysis
- Data visualization (histogram, scatter, bar)
- SQL query generation
- Anomaly detection (IQR, Z-score)

#### Designer Agent
- AI design generation
- Color palette creation (6 harmony types)
- Layout optimization (golden ratio, grid)
- Design critique & suggestions

#### Translator Agent
- 50+ language support
- Auto language detection
- Cultural localization
- Translation memory & caching

#### Financial Advisor Agent
- Portfolio analysis & optimization
- Risk assessment (VaR, Beta, volatility)
- Market forecasting & trend analysis
- Asset allocation (MPT)

### 🧠 Advanced AI Systems

#### Oneiroi Dreaming
- Self-improvement through experience replay
- Pattern mining & insight generation
- REM/NREM cycle simulation
- Performance enhancement tracking

#### GAIA Tournaments
- Competitive agent training
- ELO rating system
- Multi-opponent types (synthetic, peer, self)
- Match history & analytics

#### Multi-modal Processing
- Image AI: caption, detect, OCR, segment
- Audio AI: transcribe, diarize, classify
- Vector similarity search
- Embedding generation

### 🎨 Frontend Components

- **Multi-modal Viewer**: Drag-drop file analysis
- **Tournament Bracket**: Live SVG visualization
- **Performance Dashboard**: 3D metrics with WebGL
- **Chat Interface**: Real-time agent communication

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker 24+
- 8GB+ RAM

### Local Development

```bash
# 1. Clone repository
git clone https://github.com/your-org/dcis.git
cd dcis

# 2. Backend setup
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Frontend setup
cd ../frontend
npm install

# 4. Start services
# Terminal 1: Backend
cd backend && uvicorn src.main:app --reload

# Terminal 2: Frontend  
cd frontend && npm run dev
```

**Access**:
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

---

## 📚 Documentation

### Core Guides
- **[API Documentation](docs/API.md)** - All 60+ endpoints with examples
- **[Component Guide](docs/COMPONENTS.md)** - Frontend components & hooks
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Production deployment

### Additional Resources
- [Architecture Overview](../complete_ai_architecture.md)
- [Project Information](../project_information.md)
- [Implementation Workflow](../implementation_workflow.md)

---

## 🧪 Testing

```bash
# Backend tests (110+ test cases)
cd backend
pytest tests/ -v --cov=src

# Frontend tests
cd frontend
npm run test

# E2E tests
npm run test:e2e
```

**Test Coverage**: 90%+ for core modules

---

## 📦 Tech Stack

### Backend
- **Framework**: FastAPI 0.109+
- **AI/ML**: OpenAI, Anthropic, Transformers
- **Data**: pandas, numpy, scipy, statsmodels
- **Databases**: Neo4j 5.16+, ChromaDB, Redis
- **Multi-modal**: pillow, librosa, opencv

### Frontend
- **Framework**: Next.js 16, React 19
- **Language**: TypeScript 5
- **3D**: React Three Fiber, Three.js
- **Animation**: Framer Motion
- **Charts**: Recharts
- **UI**: Lucide React, TailwindCSS

### Infrastructure
- **Containerization**: Docker, Docker Compose
- **Orchestration**: Kubernetes
- **Monitoring**: Prometheus, Grafana
- **Logging**: ELK Stack / Loki

---

## 📊 Project Statistics

- **Total LOC**: 35,500+
- **Backend**: 20,000+ LOC (Python)
- **Frontend**: 12,000+ LOC (TypeScript/React)
- **Tests**: 110+ test cases
- **API Endpoints**: 60+
- **Components**: 12 major components
- **Agents**: 4 specialized agents
- **Advanced AI**: 3 systems

---

## 🛣️ Roadmap

### v1.1 (Planned)
- [ ] Authentication & authorization (JWT)
- [ ] Rate limiting per API key
- [ ] Enhanced error boundaries
- [ ] PWA support

### v1.2 (Future)
- [ ] GraphQL API
- [ ] Multi-tenancy
- [ ] Advanced analytics
- [ ] Internationalization (i18n)

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

---

## 👥 Team

Built with ❤️ by the DCIS Team

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/dcis/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/dcis/discussions)

---

**Made with cutting-edge AI technology** 🚀
