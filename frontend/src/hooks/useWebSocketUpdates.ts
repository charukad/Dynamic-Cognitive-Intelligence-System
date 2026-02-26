/**
 * useWebSocketUpdates Hook
 *
 * Custom React hook for real-time WebSocket updates.
 * Replaces setInterval polling with efficient WebSocket connections.
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { apiPath, wsUrl } from '@/lib/runtime';

interface UseWebSocketUpdatesOptions<TMessage = unknown> {
  url: string;
  onMessage?: (data: TMessage) => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
}

export function useWebSocketUpdates<T = unknown>({
  url,
  onMessage,
  onError,
  reconnect = true,
  reconnectInterval = 3000,
}: UseWebSocketUpdatesOptions<T>) {
  const [data, setData] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Event | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectRef = useRef<(() => void) | null>(null);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const send = useCallback((message: unknown) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const payload = typeof message === 'string' ? message : JSON.stringify(message);
      wsRef.current.send(payload);
      return;
    }

    console.warn('WebSocket is not connected');
  }, []);

  useEffect(() => {
    let disposed = false;

    const connect = () => {
      try {
        const ws = new WebSocket(url);
        wsRef.current = ws;

        ws.onopen = () => {
          if (disposed) return;
          setIsConnected(true);
          setError(null);
        };

        ws.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data) as T;
            setData(parsed);
            onMessage?.(parsed);
          } catch (parseError) {
            console.error('Failed to parse WebSocket message:', parseError);
          }
        };

        ws.onerror = (event) => {
          if (disposed) return;
          setError(event);
          onError?.(event);
        };

        ws.onclose = () => {
          if (disposed) return;

          setIsConnected(false);

          if (reconnect) {
            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectRef.current?.();
            }, reconnectInterval);
          }
        };
      } catch (connectError) {
        console.error('Failed to create WebSocket:', connectError);
      }
    };

    reconnectRef.current = connect;
    connect();

    return () => {
      disposed = true;
      disconnect();
    };
  }, [url, reconnect, reconnectInterval, onMessage, onError, disconnect]);

  const reconnectNow = useCallback(() => {
    reconnectRef.current?.();
  }, []);

  return {
    data,
    isConnected,
    error,
    send,
    reconnect: reconnectNow,
    disconnect,
  };
}

/**
 * useMetricsWebSocket Hook
 *
 * Specialized hook for metrics updates via WebSocket.
 * Falls back to polling if WebSocket is not available.
 */
export function useMetricsWebSocket<T = unknown>(endpoint: string, pollInterval = 5000) {
  const [pollData, setPollData] = useState<T | null>(null);
  const [pollLoading, setPollLoading] = useState(false);
  const [usePolling, setUsePolling] = useState(false);

  const websocketEndpoint = endpoint.startsWith('ws')
    ? endpoint
    : wsUrl(endpoint.startsWith('/ws/') ? endpoint : `/ws${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`);

  const { data: wsData, isConnected } = useWebSocketUpdates<T>({
    url: websocketEndpoint,
    reconnect: true,
    onError: () => {
      setUsePolling(true);
    },
  });

  useEffect(() => {
    if (!usePolling) return;

    let cancelled = false;
    const fetchData = async () => {
      try {
        setPollLoading(true);
        const response = await fetch(apiPath(endpoint));
        const result = (await response.json()) as T;
        if (!cancelled) {
          setPollData(result);
        }
      } catch (pollError) {
        console.error('Polling failed:', pollError);
      } finally {
        if (!cancelled) {
          setPollLoading(false);
        }
      }
    };

    fetchData();
    const interval = setInterval(fetchData, pollInterval);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [usePolling, endpoint, pollInterval]);

  const data = usePolling ? pollData : (wsData ?? pollData);
  const loading = usePolling ? pollLoading : !isConnected && pollData === null;

  return {
    data,
    loading,
    isPolling: usePolling,
    isWebSocket: !usePolling && isConnected,
  };
}
