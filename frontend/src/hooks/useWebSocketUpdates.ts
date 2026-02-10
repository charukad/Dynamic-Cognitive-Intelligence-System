/**
 * useWebSocketUpdates Hook
 * 
 * Custom React hook for real-time WebSocket updates.
 * Replaces setInterval polling with efficient WebSocket connections.
 */

import { useEffect, useState, useCallback, useRef } from 'react';

interface UseWebSocketUpdatesOptions {
    url: string;
    onMessage?: (data: any) => void;
    onError?: (error: Event) => void;
    reconnect?: boolean;
    reconnectInterval?: number;
}

export function useWebSocketUpdates<T = any>({
    url,
    onMessage,
    onError,
    reconnect = true,
    reconnectInterval = 3000,
}: UseWebSocketUpdatesOptions) {
    const [data, setData] = useState<T | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [error, setError] = useState<Event | null>(null);

    const wsRef = useRef<WebSocket | null>(null);
    const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const connect = useCallback(() => {
        try {
            const ws = new WebSocket(url);

            ws.onopen = () => {
                console.log(`WebSocket connected: ${url}`);
                setIsConnected(true);
                setError(null);
            };

            ws.onmessage = (event) => {
                try {
                    const parsedData = JSON.parse(event.data);
                    setData(parsedData);
                    onMessage?.(parsedData);
                } catch (err) {
                    console.error('Failed to parse WebSocket message:', err);
                }
            };

            ws.onerror = (event) => {
                console.error('WebSocket error:', event);
                setError(event);
                onError?.(event);
            };

            ws.onclose = () => {
                console.log('WebSocket disconnected');
                setIsConnected(false);

                // Attempt reconnect if enabled
                if (reconnect) {
                    reconnectTimeoutRef.current = setTimeout(() => {
                        console.log('Attempting to reconnect...');
                        connect();
                    }, reconnectInterval);
                }
            };

            wsRef.current = ws;
        } catch (err) {
            console.error('Failed to create WebSocket:', err);
        }
    }, [url, onMessage, onError, reconnect, reconnectInterval]);

    const disconnect = useCallback(() => {
        if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
        }
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    const send = useCallback((message: any) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
            wsRef.current.send(messageStr);
        } else {
            console.warn('WebSocket is not connected');
        }
    }, []);

    useEffect(() => {
        connect();

        return () => {
            disconnect();
        };
    }, [connect, disconnect]);

    return {
        data,
        isConnected,
        error,
        send,
        reconnect: connect,
        disconnect,
    };
}

/**
 * useMetricsWebSocket Hook
 * 
 * Specialized hook for metrics updates via WebSocket.
 * Falls back to polling if WebSocket is not available.
 */
export function useMetricsWebSocket<T = any>(endpoint: string, pollInterval: number = 5000) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [usePolling, setUsePolling] = useState(false);

    // Construct WebSocket URL
    const wsUrl = endpoint.startsWith('ws')
        ? endpoint
        : `ws://localhost:8008${endpoint}`;

    // Try WebSocket first
    const { data: wsData, isConnected } = useWebSocketUpdates<T>({
        url: wsUrl,
        reconnect: true,
        onError: () => {
            // Fallback to polling on WebSocket failure
            console.log('WebSocket failed, falling back to HTTP polling');
            setUsePolling(true);
        },
    });

    // Update data from WebSocket
    useEffect(() => {
        if (wsData && isConnected) {
            setData(wsData);
            setLoading(false);
            setUsePolling(false);
        }
    }, [wsData, isConnected]);

    // Fallback: HTTP polling
    useEffect(() => {
        if (!usePolling) return;

        const fetchData = async () => {
            try {
                // Add /api prefix for proxying
                const response = await fetch(`http://localhost:8008/api${endpoint}`);
                const result = await response.json();
                setData(result);
                setLoading(false);
            } catch (error) {
                console.error('Polling failed:', error);
            }
        };

        // Initial fetch
        fetchData();

        // Set up polling
        const interval = setInterval(fetchData, pollInterval);

        return () => clearInterval(interval);
    }, [usePolling, endpoint, pollInterval]);

    return { data, loading, isPolling: usePolling, isWebSocket: !usePolling && isConnected };
}
