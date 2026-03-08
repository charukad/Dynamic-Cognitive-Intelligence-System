import type { Page, Route } from '@playwright/test';

type Agent = {
  id: string;
  name: string;
  description: string;
};

type Session = {
  id: string;
  title: string;
  status: string;
  selected_agent_id: string | null;
  message_count: number;
  last_message: string;
  last_message_at: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
};

type Message = {
  id: string;
  session_id: string;
  sequence_number: number;
  role: string;
  sender: 'user' | 'agent' | 'system';
  content: string;
  status: 'completed' | 'streaming' | 'failed';
  agent_id?: string | null;
  agent_name?: string | null;
  error_message?: string | null;
  metadata: Record<string, unknown>;
  feedback?: {
    id: string;
    session_id: string;
    message_id: string;
    agent_id?: string | null;
    feedback_type: 'thumbs_up' | 'thumbs_down';
    rating?: number | null;
    metadata: Record<string, unknown>;
    created_at: string;
    updated_at: string;
  } | null;
  created_at: string;
  updated_at: string;
};

type FeedbackRequest = {
  session_id: string;
  message_id: string;
  agent_id?: string | null;
  feedback_type: 'thumbs_up' | 'thumbs_down';
  rating?: number;
};

type InstallOptions = {
  sessions?: Session[];
  messagesBySession?: Record<string, Message[]>;
  sendFailuresRemaining?: number;
};

const defaultAgents: Agent[] = [
  {
    id: 'designer',
    name: 'Designer',
    description: 'UI and UX specialist',
  },
  {
    id: 'coder',
    name: 'Coder',
    description: 'Engineering specialist',
  },
];

function isoAt(minute: number): string {
  return `2026-02-27T10:${String(minute).padStart(2, '0')}:00.000Z`;
}

function createSession(id: string, title: string, selectedAgentId: string | null, minute: number): Session {
  return {
    id,
    title,
    status: 'active',
    selected_agent_id: selectedAgentId,
    message_count: 0,
    last_message: '',
    last_message_at: null,
    metadata: {},
    created_at: isoAt(minute),
    updated_at: isoAt(minute),
  };
}

function createMessage(input: {
  id: string;
  sessionId: string;
  sequenceNumber: number;
  sender: 'user' | 'agent';
  content: string;
  agentId?: string | null;
  agentName?: string | null;
  minute: number;
}): Message {
  return {
    id: input.id,
    session_id: input.sessionId,
    sequence_number: input.sequenceNumber,
    role: input.sender === 'user' ? 'user' : 'assistant',
    sender: input.sender,
    content: input.content,
    status: 'completed',
    agent_id: input.agentId ?? null,
    agent_name: input.agentName ?? null,
    error_message: null,
    metadata: {},
    feedback: null,
    created_at: isoAt(input.minute),
    updated_at: isoAt(input.minute),
  };
}

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}

function fulfillJson(route: Route, body: unknown, status = 200) {
  return route.fulfill({
    status,
    contentType: 'application/json',
    body: JSON.stringify(body),
  });
}

function buildWorkspace(session: Session, messages: Message[]) {
  const assistantMessages = messages.filter((message) => message.sender === 'agent');
  const latestAssistant = assistantMessages[assistantMessages.length - 1] || null;
  const latestUser = [...messages].reverse().find((message) => message.sender === 'user') || null;
  const currentAgentId = session.selected_agent_id || latestAssistant?.agent_id || 'designer';
  const currentAgentName = currentAgentId === 'coder' ? 'Coder' : 'Designer';

  return {
    session,
    route: {
      source: session.selected_agent_id ? 'explicit' : 'auto',
      reason: session.selected_agent_id
        ? 'User explicitly selected the target agent'
        : 'Auto-routed using deterministic fallback',
      inferred_task_type: currentAgentId === 'coder' ? 'coding' : 'creative',
      inferred_agent_type: currentAgentId,
      mode: 'balanced',
      start_project_mode: false,
    },
    rooms: [
      {
        id: 'strategy',
        title: 'Strategy Center',
        label: 'Planning Room',
        status: latestUser ? 'active' : 'watching',
        detail: latestUser ? 'Routing the latest request.' : 'Incoming requests route here first.',
        metric: currentAgentId === 'coder' ? 'coding' : 'creative',
        description: 'Task decomposition and routing view.',
      },
      {
        id: 'execution',
        title: 'Active Pods',
        label: 'Execution',
        status: latestAssistant ? 'active' : 'idle',
        detail: latestAssistant ? `${currentAgentName} delivered the latest response.` : 'Execution remains on standby.',
        metric: `${assistantMessages.length} completions`,
        description: 'Execution surface for active responses and delivery state.',
      },
    ],
    activity_feed: [
      {
        id: 'evt-1',
        type: 'TASK_STARTED',
        description: latestUser?.content || 'Waiting for the first request.',
        timestamp: session.updated_at,
        severity: 'info',
      },
      ...(latestAssistant
        ? [
            {
              id: 'evt-2',
              type: 'FINAL_RESPONSE_SENT',
              description: latestAssistant.content,
              timestamp: latestAssistant.updated_at,
              severity: 'success',
            },
          ]
        : []),
    ],
    office_stats: [
      {
        label: 'Persisted Messages',
        value: String(messages.length),
        hint: 'Saved turns in this session',
      },
    ],
    task_stages: [
      {
        id: 'routing',
        title: 'Routing and Planning',
        status: latestUser ? 'done' : 'waiting',
        detail: latestUser ? 'The request has been routed.' : 'Waiting for the first request.',
      },
      {
        id: 'delivery',
        title: 'Delivery and Validation',
        status: latestAssistant ? 'done' : latestUser ? 'active' : 'waiting',
        detail: latestAssistant ? 'Latest response delivered successfully.' : 'Awaiting assistant output.',
      },
    ],
    replay: assistantMessages.map((message, index) => ({
      id: `replay-${index + 1}`,
      type: 'FINAL_RESPONSE_SENT',
      description: message.content,
      timestamp: message.updated_at,
    })),
    graph_nodes: [
      {
        id: 'strategy',
        label: 'Strategy Center',
        kind: 'room',
        status: 'watching',
        x: 0.35,
        y: 0.2,
      },
      {
        id: 'execution',
        label: 'Active Pods',
        kind: 'room',
        status: latestAssistant ? 'active' : 'idle',
        x: 0.65,
        y: 0.55,
      },
    ],
    graph_edges: [
      {
        id: 'front_desk:strategy',
        from_id: 'front_desk',
        to_id: 'strategy',
        label: 'TASK_STARTED',
        status: 'success',
      },
    ],
    room_timeline: [
      {
        id: 'evt-1',
        room_id: 'strategy',
        room_title: 'Strategy Center',
        type: 'TASK_STARTED',
        description: latestUser?.content || 'Waiting for the first request.',
        timestamp: session.updated_at,
        severity: 'info',
      },
    ],
    working_context: {
      selected_agent_name: currentAgentName,
    },
  };
}

function buildRoomDetail(session: Session, roomId: string, messages: Message[]) {
  if (roomId === 'execution') {
    const latestAssistant = [...messages].reverse().find((message) => message.sender === 'agent') || null;
    return {
      room: {
        id: 'execution',
        title: 'Active Pods',
        label: 'Execution',
        status: latestAssistant ? 'active' : 'idle',
        detail: latestAssistant ? 'The latest response has been delivered.' : 'Execution remains on standby.',
        metric: `${messages.filter((message) => message.sender === 'agent').length} completions`,
        description: 'Execution surface for active responses and delivery state.',
      },
      summary: latestAssistant
        ? 'Execution completed the latest response successfully.'
        : 'Execution has not started yet.',
      metrics: [
        {
          label: 'Delivered Responses',
          value: String(messages.filter((message) => message.sender === 'agent').length),
          hint: 'Assistant turns completed for this session',
        },
      ],
      highlights: ['Delivery path is ready for replay inspection.'],
      recent_events: [
        {
          id: 'evt-exec-1',
          room_id: 'execution',
          room_title: 'Active Pods',
          type: 'FINAL_RESPONSE_SENT',
          description: latestAssistant?.content || 'No response has been delivered yet.',
          timestamp: latestAssistant?.updated_at || session.updated_at,
          severity: latestAssistant ? 'success' : 'info',
        },
      ],
      related_messages: latestAssistant ? [latestAssistant] : [],
      actions: ['Open replay timeline'],
    };
  }

  return {
    room: {
      id: 'strategy',
      title: 'Strategy Center',
      label: 'Planning Room',
      status: 'watching',
      detail: 'Incoming requests route here first.',
      metric: session.selected_agent_id || 'creative',
      description: 'Task decomposition and routing view.',
    },
    summary: 'Strategy Center is preparing the latest route plan.',
    metrics: [
      {
        label: 'Route Source',
        value: session.selected_agent_id ? 'Manual Selection' : 'Auto Routing',
        hint: 'Routing source for the current session',
      },
    ],
    highlights: [
      `Task count: ${messages.filter((message) => message.sender === 'user').length}`,
    ],
    recent_events: [
      {
        id: 'evt-strategy-1',
        room_id: 'strategy',
        room_title: 'Strategy Center',
        type: 'TASK_STARTED',
        description: messages.find((message) => message.sender === 'user')?.content || 'Waiting for the first request.',
        timestamp: session.updated_at,
        severity: 'info',
      },
    ],
    related_messages: messages.slice(0, 2),
    actions: ['Open task DAG viewer'],
  };
}

function buildDag(sessionId: string) {
  return {
    session_id: sessionId,
    summary: 'Designer completed the latest delivery path.',
    latest_node_id: 'delivery',
    total_duration_ms: 2200,
    nodes: [
      {
        id: 'routing',
        title: 'Routing and Planning',
        room_id: 'strategy',
        status: 'done',
        detail: 'Routing is complete for the current task.',
        dependencies: ['intake'],
        started_at: isoAt(0),
        completed_at: isoAt(1),
        execution_time_ms: 120,
        assigned_agent: 'Designer',
        evaluation_score: null,
        retry_count: 0,
        model_used: null,
        event_ids: ['evt-1'],
      },
      {
        id: 'delivery',
        title: 'Delivery and Validation',
        room_id: 'execution',
        status: 'done',
        detail: 'Latest response delivered successfully.',
        dependencies: ['execution'],
        started_at: isoAt(2),
        completed_at: isoAt(4),
        execution_time_ms: 840,
        assigned_agent: 'Designer',
        evaluation_score: 1,
        retry_count: 0,
        model_used: 'demo-model',
        event_ids: ['evt-2'],
      },
    ],
    edges: [
      {
        id: 'execution:delivery',
        from_id: 'execution',
        to_id: 'delivery',
        label: 'depends_on',
        status: 'success',
      },
    ],
  };
}

function buildReplay(sessionId: string, messages: Message[]) {
  const latestAssistant = [...messages].reverse().find((message) => message.sender === 'agent') || null;
  return {
    session_id: sessionId,
    summary: latestAssistant
      ? 'Designer completed the response and returned it to the front desk.'
      : 'Replay will populate after the first assistant response.',
    current_index: latestAssistant ? 1 : 0,
    started_at: isoAt(0),
    ended_at: latestAssistant?.updated_at || isoAt(0),
    total_duration_ms: latestAssistant ? 1800 : 0,
    frames: [
      {
        id: 'evt-1',
        index: 0,
        type: 'TASK_STARTED',
        description: messages.find((message) => message.sender === 'user')?.content || 'Waiting for the first request.',
        timestamp: isoAt(0),
        severity: 'info',
        room_id: 'strategy',
        room_title: 'Strategy Center',
        agent_name: 'Designer',
        related_message_id: messages.find((message) => message.sender === 'user')?.id || null,
        focus_node_ids: ['strategy', 'front_desk'],
        focus_edge_id: 'front_desk:strategy:TASK_STARTED',
      },
      ...(latestAssistant
        ? [
            {
              id: 'evt-2',
              index: 1,
              type: 'FINAL_RESPONSE_SENT',
              description: latestAssistant.content,
              timestamp: latestAssistant.updated_at,
              severity: 'success',
              room_id: 'execution',
              room_title: 'Active Pods',
              agent_name: latestAssistant.agent_name || 'Designer',
              related_message_id: latestAssistant.id,
              focus_node_ids: ['execution', 'front_desk'],
              focus_edge_id: 'execution:front_desk:FINAL_RESPONSE_SENT',
            },
          ]
        : []),
    ],
  };
}

export async function installChatApiMocks(page: Page, options: InstallOptions = {}) {
  const sessions = clone(
    options.sessions || [createSession('session-1', 'New Conversation', null, 0)]
  );
  const messagesBySession: Record<string, Message[]> = clone(
    options.messagesBySession || { 'session-1': [] }
  );
  const feedbackRequests: FeedbackRequest[] = [];
  let sendFailuresRemaining = options.sendFailuresRemaining || 0;
  let sessionCounter = sessions.length;
  let messageCounter = Object.values(messagesBySession).flat().length;

  const state = {
    agents: clone(defaultAgents),
    sessions,
    messagesBySession,
    feedbackRequests,
  };

  function touchSession(sessionId: string, update: Partial<Session>) {
    const session = sessions.find((item) => item.id === sessionId);
    if (!session) {
      return;
    }
    Object.assign(session, update);
  }

  await page.route('**/api/v1/**', async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    const path = url.pathname;
    const method = request.method();

    if (path === '/api/v1/agents' && method === 'GET') {
      return fulfillJson(route, state.agents);
    }

    if (path === '/api/v1/chat/sessions' && method === 'GET') {
      const ordered = [...sessions].sort((left, right) =>
        right.updated_at.localeCompare(left.updated_at)
      );
      return fulfillJson(route, { sessions: ordered, count: ordered.length });
    }

    if (path === '/api/v1/chat/sessions' && method === 'POST') {
      sessionCounter += 1;
      const payload = request.postDataJSON() as { selected_agent_id?: string | null };
      const created = createSession(
        `session-${sessionCounter}`,
        'New Conversation',
        payload.selected_agent_id || null,
        sessionCounter
      );
      sessions.unshift(created);
      messagesBySession[created.id] = [];
      return fulfillJson(route, created);
    }

    const sessionMatch = path.match(/^\/api\/v1\/chat\/sessions\/([^/]+)$/);
    if (sessionMatch && method === 'GET') {
      const session = sessions.find((item) => item.id === sessionMatch[1]);
      return session
        ? fulfillJson(route, session)
        : fulfillJson(route, { detail: 'Chat session not found' }, 404);
    }

    if (sessionMatch && method === 'DELETE') {
      const sessionId = sessionMatch[1];
      const index = sessions.findIndex((item) => item.id === sessionId);
      if (index === -1) {
        return fulfillJson(route, { detail: 'Chat session not found' }, 404);
      }
      sessions.splice(index, 1);
      delete messagesBySession[sessionId];
      return fulfillJson(route, { deleted: true, session_id: sessionId });
    }

    const messagesMatch = path.match(/^\/api\/v1\/chat\/sessions\/([^/]+)\/messages$/);
    if (messagesMatch && method === 'GET') {
      const sessionId = messagesMatch[1];
      const messages = messagesBySession[sessionId] || [];
      return fulfillJson(route, {
        session_id: sessionId,
        messages,
        count: messages.length,
        limit: 100,
        before_sequence: null,
      });
    }

    const sendMatch = path.match(/^\/api\/v1\/chat\/sessions\/([^/]+)\/messages\/send$/);
    if (sendMatch && method === 'POST') {
      if (sendFailuresRemaining > 0) {
        sendFailuresRemaining -= 1;
        return fulfillJson(route, { detail: 'Model unavailable' }, 500);
      }

      const sessionId = sendMatch[1];
      const payload = request.postDataJSON() as {
        id: string;
        content: string;
        agent_id?: string | null;
      };
      const session = sessions.find((item) => item.id === sessionId);
      if (!session) {
        return fulfillJson(route, { detail: 'Chat session not found' }, 404);
      }

      const chosenAgentId = payload.agent_id || session.selected_agent_id || 'designer';
      const chosenAgentName = chosenAgentId === 'coder' ? 'Coder' : 'Designer';
      const existingMessages = messagesBySession[sessionId] || [];
      const nextSequence = existingMessages.length + 1;
      const userMessage = createMessage({
        id: payload.id,
        sessionId,
        sequenceNumber: nextSequence,
        sender: 'user',
        content: payload.content,
        agentId: chosenAgentId,
        agentName: chosenAgentName,
        minute: nextSequence,
      });
      messageCounter += 1;
      const assistantMessage = createMessage({
        id: `assistant-${messageCounter}`,
        sessionId,
        sequenceNumber: nextSequence + 1,
        sender: 'agent',
        content: `${chosenAgentName} handled: ${payload.content}`,
        agentId: chosenAgentId,
        agentName: chosenAgentName,
        minute: nextSequence + 1,
      });
      existingMessages.push(userMessage, assistantMessage);
      messagesBySession[sessionId] = existingMessages;
      touchSession(sessionId, {
        selected_agent_id: chosenAgentId,
        message_count: existingMessages.length,
        last_message: assistantMessage.content,
        last_message_at: assistantMessage.updated_at,
        updated_at: assistantMessage.updated_at,
      });

      return fulfillJson(route, {
        session: sessions.find((item) => item.id === sessionId),
        user_message: userMessage,
        assistant_message: assistantMessage,
      });
    }

    const roomMatch = path.match(/^\/api\/v1\/chat\/sessions\/([^/]+)\/workspace\/rooms\/([^/]+)$/);
    if (roomMatch && method === 'GET') {
      const sessionId = roomMatch[1];
      return fulfillJson(
        route,
        buildRoomDetail(
          sessions.find((item) => item.id === sessionId) || sessions[0],
          roomMatch[2],
          messagesBySession[sessionId] || []
        )
      );
    }

    const dagMatch = path.match(/^\/api\/v1\/chat\/sessions\/([^/]+)\/workspace\/dag$/);
    if (dagMatch && method === 'GET') {
      return fulfillJson(route, buildDag(dagMatch[1]));
    }

    const replayMatch = path.match(/^\/api\/v1\/chat\/sessions\/([^/]+)\/workspace\/replay$/);
    if (replayMatch && method === 'GET') {
      return fulfillJson(route, buildReplay(replayMatch[1], messagesBySession[replayMatch[1]] || []));
    }

    const workspaceMatch = path.match(/^\/api\/v1\/chat\/sessions\/([^/]+)\/workspace$/);
    if (workspaceMatch && method === 'GET') {
      const sessionId = workspaceMatch[1];
      const session = sessions.find((item) => item.id === sessionId);
      if (!session) {
        return fulfillJson(route, { detail: 'Chat session not found' }, 404);
      }
      return fulfillJson(route, buildWorkspace(session, messagesBySession[sessionId] || []));
    }

    if (path === '/api/v1/chat/feedback' && method === 'POST') {
      const payload = request.postDataJSON() as FeedbackRequest;
      feedbackRequests.push(payload);
      const messages = messagesBySession[payload.session_id] || [];
      const target = messages.find((message) => message.id === payload.message_id);
      if (target) {
        target.feedback = {
          id: `feedback-${feedbackRequests.length}`,
          session_id: payload.session_id,
          message_id: payload.message_id,
          agent_id: payload.agent_id || null,
          feedback_type: payload.feedback_type,
          rating: payload.rating || null,
          metadata: {},
          created_at: isoAt(50 + feedbackRequests.length),
          updated_at: isoAt(50 + feedbackRequests.length),
        };
      }
      return fulfillJson(route, {
        id: `feedback-${feedbackRequests.length}`,
        session_id: payload.session_id,
        message_id: payload.message_id,
        agent_id: payload.agent_id || null,
        feedback_type: payload.feedback_type,
        rating: payload.rating || null,
        metadata: {},
        created_at: isoAt(50 + feedbackRequests.length),
        updated_at: isoAt(50 + feedbackRequests.length),
      });
    }

    return fulfillJson(route, { detail: `Unhandled mock route: ${method} ${path}` }, 404);
  });

  return state;
}

export { createMessage, createSession };
