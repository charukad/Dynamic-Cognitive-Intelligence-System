# DCIS - API Documentation

**Version**: 1.0.0  
**Base URL**: `http://localhost:8000/api/v1`

---

## 📚 Table of Contents

1. [Authentication](#authentication)
2. [Specialized Agents](#specialized-agents)
3. [Advanced AI Services](#advanced-ai-services)
4. [WebSocket Endpoints](#websocket-endpoints)
5. [Error Handling](#error-handling)

---

## 🔐 Authentication

**Coming Soon**: JWT-based authentication

Currently, all endpoints are public for development.

---

## 🤖 Specialized Agents

### Data Analyst Agent

#### Profile Dataset
```bash
POST /agents/data-analyst/profile
```

**Request**:
```json
{
  "data": [
    {"col1": 1, "col2": "A"},
    {"col1": 2, "col2": "B"}
  ]
}
```

**Response**:
```json
{
  "num_rows": 2,
  "num_columns": 2,
  "columns": [
    {
      "name": "col1",
      "type": "int64",
      "null_count": 0,
      "null_percentage": 0.0
    }
  ]
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/agents/data-analyst/profile \
  -H "Content-Type: application/json" \
  -d '{"data": [{"x": 1}, {"x": 2}]}'
```

---

#### Statistical Analysis
```bash
POST /agents/data-analyst/analyze
```

**Request**:
```json
{
  "data": [100, 105, 98, 110, 95],
  "test_type": "t_test",
  "group2": [90, 88, 92, 85, 87]
}
```

**Response**:
```json
{
  "statistic": 4.123,
  "p_value": 0.002,
  "significant": true,
  "confidence_level": 0.95
}
```

---

#### Generate Visualization
```bash
POST /agents/data-analyst/visualize
```

**Request**:
```json
{
  "data": [{"value": 10}, {"value": 20}],
  "viz_type": "histogram",
  "column": "value"
}
```

**Response**:
```json
{
  "type": "histogram",
  "chart_data": {
    "bins": [0, 10, 20],
    "counts": [1, 1]
  }
}
```

---

#### SQL Generation
```bash
POST /agents/data-analyst/sql
```

**Request**:
```json
{
  "query": "show me all users older than 25",
  "schema": {
    "users": ["id", "name", "age", "email"]
  }
}
```

**Response**:
```json
{
  "sql": "SELECT * FROM users WHERE age > 25",
  "explanation": "Filters users table by age column",
  "tables_used": ["users"]
}
```

---

#### Anomaly Detection
```bash
POST /agents/data-analyst/anomalies
```

**Request**:
```json
{
  "data": [100, 102, 98, 105, 500, 101],
  "method": "iqr",
  "threshold": 1.5
}
```

**Response**:
```json
{
  "anomalies": [500],
  "anomaly_indices": [4],
  "method": "iqr",
  "num_anomalies": 1
}
```

---

### Designer Agent

#### Generate Color Palette
```bash
POST /agents/designer/colors
```

**Request**:
```json
{
  "base_color": "#667eea",
  "harmony": "complementary",
  "num_colors": 5
}
```

**Response**:
```json
{
  "colors": ["#667eea", "#ea7d66", "#66eadd", "#dd66ea", "#eadd66"],
  "harmony_type": "complementary",
  "base_color": "#667eea"
}
```

**Harmony Types**: `complementary`, `triadic`, `analogous`, `monochromatic`, `split-complementary`, `tetradic`

---

#### Optimize Layout
```bash
POST /agents/designer/layout
```

**Request**:
```json
{
  "width": 1920,
  "height": 1080,
  "algorithm": "golden_ratio"
}
```

**Response**:
```json
{
  "sections": [
    {"x": 0, "y": 0, "width": 1188, "height": 1080},
    {"x": 1188, "y": 0, "width": 732, "height": 1080}
  ],
  "algorithm": "golden_ratio"
}
```

**Algorithms**: `golden_ratio`, `grid`, `rule_of_thirds`

---

#### Design Critique
```bash
POST /agents/designer/critique
```

**Request**:
```json
{
  "design": {
    "background": "#ffffff",
    "text": "#000000",
    "elements": []
  }
}
```

**Response**:
```json
{
  "contrast_score": 21.0,
  "balance_score": 0.85,
  "suggestions": [
    "Consider adding visual hierarchy",
    "Good color contrast for accessibility"
  ]
}
```

---

### Translator Agent

#### Translate Text
```bash
POST /agents/translator/translate
```

**Request**:
```json
{
  "text": "Hello, how are you?",
  "source_language": "en",
  "target_language": "es",
  "context": "casual"
}
```

**Response**:
```json
{
  "translation": "Hola, ¿cómo estás?",
  "source_language": "en",
  "target_language": "es",
  "confidence": 0.98
}
```

---

#### Detect Language
```bash
POST /agents/translator/detect
```

**Request**:
```json
{
  "text": "Bonjour, comment allez-vous?"
}
```

**Response**:
```json
{
  "language": "fr",
  "confidence": 0.99,
  "alternatives": [
    {"language": "fr-CA", "confidence": 0.15}
  ]
}
```

---

#### Batch Translation
```bash
POST /agents/translator/batch
```

**Request**:
```json
{
  "texts": ["Hello", "Goodbye", "Thank you"],
  "source_language": "en",
  "target_language": "ja"
}
```

**Response**:
```json
{
  "translations": [
    {"index": 0, "translation": "こんにちは"},
    {"index": 1, "translation": "さようなら"},
    {"index": 2, "translation": "ありがとう"}
  ]
}
```

---

### Financial Advisor Agent

#### Analyze Portfolio
```bash
POST /agents/financial/portfolio/analyze
```

**Request**:
```json
{
  "portfolio": {
    "holdings": [
      {"symbol": "AAPL", "shares": 100, "purchase_price": 150.00}
    ],
    "cash": 10000.00
  },
  "current_prices": {
    "AAPL": 180.00
  }
}
```

**Response**:
```json
{
  "total_value": 28000.00,
  "total_gain_loss": 3000.00,
  "allocation": [
    {"symbol": "AAPL", "percentage": 64.29, "value": 18000.00}
  ],
  "sharpe_ratio": 1.25,
  "diversification_score": 0.3
}
```

---

#### Calculate Risk Metrics
```bash
POST /agents/financial/risk/var
```

**Request**:
```json
{
  "returns": [0.01, 0.02, -0.01, 0.03, -0.02],
  "confidence_level": 0.95
}
```

**Response**:
```json
{
  "var": -0.025,
  "confidence_level": 0.95,
  "interpretation": "95% confident max loss is 2.5%"
}
```

---

#### Optimize Allocation
```bash
POST /agents/financial/allocation/optimize
```

**Request**:
```json
{
  "assets": {
    "AAPL": {"expected_return": 0.12, "risk": 0.18},
    "GOOGL": {"expected_return": 0.15, "risk": 0.22}
  },
  "risk_tolerance": "moderate",
  "target_return": 0.13
}
```

**Response**:
```json
{
  "allocations": {
    "AAPL": 60.0,
    "GOOGL": 40.0
  },
  "expected_return": 0.13,
  "expected_risk": 0.19
}
```

---

## 🧠 Advanced AI Services

### Oneiroi Dreaming

#### Run Dream Cycle
```bash
POST /ai-services/dream/run
```

**Request**:
```json
{
  "agent_id": "agent_123",
  "num_experiences": 100,
  "focus_areas": ["decision_making", "pattern_recognition"]
}
```

**Response**:
```json
{
  "dream_cycle_id": "cycle_456",
  "agent_id": "agent_123",
  "experiences_processed": 100,
  "patterns_discovered": 15,
  "insights_generated": 8,
  "insights_applied": 5,
  "performance_improvement": 0.12,
  "timestamp": "2026-01-29T23:00:00Z"
}
```

---

#### Get Dream Insights
```bash
GET /ai-services/dream/insights/{agent_id}?limit=10
```

**Response**:
```json
{
  "insights": [
    {
      "insight_id": "insight_789",
      "pattern_type": "decision_optimization",
      "description": "Discovered faster path selection algorithm",
      "applicability_score": 0.89,
      "created_at": "2026-01-29T22:50:00Z"
    }
  ]
}
```

---

### GAIA Tournaments

#### Run Match
```bash
POST /ai-services/gaia/match
```

**Request**:
```json
{
  "agent_id": "agent_123",
  "opponent_type": "synthetic",
  "num_rounds": 5
}
```

**Response**:
```json
{
  "match_id": "match_abc",
  "agent_id": "agent_123",
  "opponent_type": "synthetic",
  "winner": "agent_123",
  "score": {
    "agent": 3,
    "opponent": 2
  },
  "elo_before": 1500,
  "elo_after": 1520,
  "elo_change": 20,
  "rounds_played": 5,
  "timestamp": "2026-01-29T23:00:00Z"
}
```

---

#### Get ELO Rating
```bash
GET /ai-services/gaia/elo/{agent_id}
```

**Response**:
```json
{
  "agent_id": "agent_123",
  "elo_rating": 1520,
  "rank": 42,
  "matches_played": 150
}
```

---

#### Get Match History
```bash
GET /ai-services/gaia/history/{agent_id}?limit=20
```

**Response**:
```json
{
  "matches": [
    {
      "match_id": "match_abc",
      "opponent_type": "peer",
      "winner": "agent_123",
      "elo_change": 15,
      "timestamp": "2026-01-29T22:00:00Z"
    }
  ]
}
```

---

### Multi-modal Processing

#### Process Image
```bash
POST /ai-services/multimodal/image
```

**Request**:
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUg...",
  "operations": ["caption", "detect", "ocr"]
}
```

**Response**:
```json
{
  "caption": "A modern office workspace",
  "objects": [
    {"label": "laptop", "confidence": 0.95, "bbox": [100, 200, 300, 400]},
    {"label": "desk", "confidence": 0.89, "bbox": [0, 500, 800, 600]}
  ],
  "text": "Meeting at 3pm",
  "embedding": [0.123, 0.456, ...]
}
```

---

#### Process Audio
```bash
POST /ai-services/multimodal/audio
```

**Request**:
```json
{
  "audio_base64": "UklGRiQAAABXQVZF...",
  "operations": ["transcribe", "diarize"]
}
```

**Response**:
```json
{
  "transcription": {
    "text": "Hello, this is a test recording.",
    "confidence": 0.96
  },
  "speakers": [
    {"speaker_id": "speaker_1", "start_time": 0.0, "end_time": 3.5}
  ],
  "embedding": [0.789, 0.012, ...]
}
```

---

#### Search Similar Content
```bash
POST /ai-services/multimodal/search
```

**Request**:
```json
{
  "query_embedding": [0.123, 0.456, ...],
  "modality": "image",
  "top_k": 5
}
```

**Response**:
```json
{
  "results": [
    {
      "id": "img_123",
      "similarity_score": 0.95,
      "metadata": {"filename": "office.jpg"}
    }
  ]
}
```

---

#### Get Service Status
```bash
GET /ai-services/status
```

**Response**:
```json
{
  "services": {
    "oneiroi": {
      "service_name": "Oneiroi Dreaming",
      "status": "online",
      "last_activity": "2026-01-29T23:00:00Z",
      "total_requests": 1543,
      "success_rate": 0.98
    },
    "gaia": {
      "service_name": "GAIA Tournaments",
      "status": "online",
      "last_activity": "2026-01-29T22:55:00Z",
      "total_requests": 892,
      "success_rate": 0.97
    }
  }
}
```

---

## 🔌 WebSocket Endpoints

### AI Services Real-time Updates

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/ai-services');
```

**Subscribe to Updates**:
```javascript
ws.send(JSON.stringify({
  type: 'subscribe',
  data: {
    types: ['dream_progress', 'match_progress']
  }
}));
```

**Message Types**:
- `dream_progress`: Dream cycle progress updates
- `dream_complete`: Dream cycle completion
- `match_progress`: Match round updates
- `match_complete`: Match completion
- `processing_progress`: Multi-modal processing
- `service_status`: Service health updates

**Example Message**:
```json
{
  "type": "dream_progress",
  "data": {
    "agent_id": "agent_123",
    "progress": 45.5,
    "status": "NREM phase - pattern mining"
  },
  "timestamp": "2026-01-29T23:00:00Z"
}
```

---

## ⚠️ Error Handling

### Error Response Format
```json
{
  "detail": {
    "error": "ValidationError",
    "message": "Invalid request parameters",
    "field": "num_experiences",
    "timestamp": "2026-01-29T23:00:00Z"
  }
}
```

### HTTP Status Codes

- `200`: Success
- `400`: Bad Request (validation error)
- `404`: Not Found
- `422`: Unprocessable Entity
- `500`: Internal Server Error
- `503`: Service Unavailable

---

## 📊 Rate Limits

**Coming Soon**: Rate limiting per API key

Currently unlimited for development.

---

## 🔗 Additional Resources

- [Component Documentation](./COMPONENTS.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Architecture Overview](../README.md)
