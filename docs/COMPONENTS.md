# DCIS - Component Documentation

**Frontend Components Guide**

---

## 📚 Table of Contents

1. [Multi-modal Viewer](#multi-modal-viewer)
2. [Tournament Bracket](#tournament-bracket)
3. [Performance Dashboard](#performance-dashboard)
4. [Chat Interface](#chat-interface)

---

## 🖼️ Multi-modal Viewer

**Location**: `frontend/src/components/multimodal/MultiModalViewer.tsx`

### Overview
Upload and analyze images/audio with AI-powered processing.

### Props
```typescript
interface MultiModalViewerProps {
  onAnalysisComplete?: (result: AnalysisResult) => void;
  maxFileSize?: number; // Default: 10MB
  acceptedFormats?: string[]; // Default: ['image/*', 'audio/*']
}
```

### Usage
```tsx
import { MultiModalViewer } from '@/components/multimodal/MultiModalViewer';

function MyPage() {
  const handleComplete = (result) => {
    console.log('Analysis:', result);
  };

  return (
    <MultiModalViewer
      onAnalysisComplete={handleComplete}
      maxFileSize={20 * 1024 * 1024} // 20MB
    />
  );
}
```

### Features
- Drag-and-drop file upload
- Real-time AI analysis
- Image: caption, object detection, OCR, segmentation
- Audio: transcription, speaker diarization, classification
- Progress indicators
- Results visualization

---

## 🏆 Tournament Bracket

**Location**: `frontend/src/components/gaia/TournamentBracket.tsx`

### Overview
Dynamic tournament bracket visualization with real-time updates.

### Props
```typescript
interface TournamentBracketProps {
  tournamentId?: string;
  initialMatches?: Match[];
  onMatchComplete?: (match: Match) => void;
  enableZoom?: boolean; // Default: true
  showStats?: boolean; // Default: true
}
```

### Usage
```tsx
import { TournamentBracket } from '@/components/gaia/TournamentBracket';

function TournamentPage() {
  return (
    <TournamentBracket
      tournamentId="tournament_123"
      enableZoom={true}
      showStats={true}
    />
  );
}
```

### Features
- SVG-based bracket rendering
- Framer Motion animations
- Real-time match updates (WebSocket)
- Zoom and pan controls
- Export to PNG
- Match history modal
- ELO rating display

---

## 📊 Performance Dashboard

**Location**: `frontend/src/components/analytics/PerformanceDashboard.tsx`

### Overview
3D visualization of agent performance metrics.

### Props
```typescript
interface PerformanceDashboardProps {
  agentId?: string;
  refreshInterval?: number; // Default: 5000ms
  show3DGlobe?: boolean; // Default: true
  showLeaderboard?: boolean; // Default: true
}
```

### Usage
```tsx
import { PerformanceDashboard } from '@/components/analytics/PerformanceDashboard';

function AnalyticsPage() {
  return (
    <PerformanceDashboard
      agentId="agent_123"
      refreshInterval={10000}
      show3DGlobe={true}
    />
  );
}
```

### Features
- 3D globe visualization (React Three Fiber)
- Real-time metrics charts (Recharts)
- Performance history line chart
- Agent comparison radar chart
- Leaderboard table
- Stat cards with trends
- WebGL-accelerated rendering

---

## 💬 Chat Interface

**Location**: `frontend/src/components/chat/ChatInterface.tsx`

### Overview
Real-time chat with AI agents supporting markdown and code.

### Props
```typescript
interface ChatInterfaceProps {
  agentId?: string;
  initialMessages?: Message[];
  onMessageSend?: (message: string) => void;
  showAgentSelector?: boolean; // Default: true
  enableMarkdown?: boolean; // Default: true
}
```

### Usage
```tsx
import { ChatInterface } from '@/components/chat/ChatInterface';

function ChatPage() {
  return (
    <ChatInterface
      agentId="agent_123"
      showAgentSelector={true}
      enableMarkdown={true}
    />
  );
}
```

### Features
- WebSocket real-time messaging
- Markdown rendering (react-markdown)
- Syntax highlighting (Prism.js)
- Typing indicators
- Agent selector dropdown
- Message status (sending, sent, error)
- Auto-scroll to new messages
- Message history persistence

---

## 🎨 Styling

All components use dedicated CSS files:

- `MultiModalViewer.css`
- `TournamentBracket.css`
- `PerformanceDashboard.css`
- `ChatInterface.css`

### Common Styling Features
- Glassmorphism effects
- Gradient animations
- Responsive design
- Dark theme optimized
- Smooth transitions
- Professional color palette

---

## 🔧 Custom Hooks

### useAdvancedAI
```typescript
import { useAdvancedAI } from '@/lib/api/hooks/useAdvancedAI';

function MyComponent() {
  const { dream, gaia, multimodal, status } = useAdvancedAI('agent_123');

  const runDream = async () => {
    await dream.runCycle({ num_experiences: 100 });
  };

  return <button onClick={runDream}>Run Dream Cycle</button>;
}
```

### useWebSocketUpdates
```typescript
import { useWebSocketUpdates } from '@/lib/api/hooks/useWebSocketUpdates';

function MyComponent() {
  const ws = useWebSocketUpdates();

  useEffect(() => {
    const unsubscribe = ws.subscribe('dream_progress', (data) => {
      console.log('Progress:', data.progress);
    });

    return unsubscribe;
  }, [ws]);

  return <div>Connected: {ws.isConnected}</div>;
}
```

---

## 🚀 Best Practices

### Performance
```tsx
// Use React.memo for expensive components
const ExpensiveComponent = React.memo(({ data }) => {
  // Component logic
});

// Use useMemo for expensive calculations
const processedData = useMemo(() => {
  return heavyProcessing(data);
}, [data]);

// Use useCallback for event handlers
const handleClick = useCallback(() => {
  // Handler logic
}, [dependencies]);
```

### Error Boundaries
```tsx
import { ErrorBoundary } from '@/components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary fallback={<ErrorFallback />}>
      <MyComponent />
    </ErrorBoundary>
  );
}
```

### Loading States
```tsx
function MyComponent() {
  const { data, isLoading, error } = useQuery();

  if (isLoading) return <Skeleton />;
  if (error) return <ErrorMessage error={error} />;

  return <DataDisplay data={data} />;
}
```

---

## 📦 Dependencies

**Core**:
- React 19
- Next.js 16
- TypeScript 5

**Visualization**:
- React Three Fiber
- Framer Motion
- Recharts

**UI**:
- Lucide React (icons)
- react-markdown
- react-syntax-highlighter

---

## 🔗 Additional Resources

- [API Documentation](./API.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Architecture Overview](../README.md)
