import { useState, useEffect, useCallback } from 'react';

interface AgentUpdate {
  agent: string;
  status: string;
  message: string;
  data?: Record<string, any>;
  timestamp: string;
}

export function useWebSocket(caseId: string | null) {
  const [logs, setLogs] = useState<AgentUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback((id: string) => {
    const ws = new WebSocket(`ws://localhost:8000/ws/cases/${id}`);

    ws.onopen = () => {
      setIsConnected(true);
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      const update: AgentUpdate = JSON.parse(event.data);
      setLogs((prev) => [...prev, update]);
    };

    ws.onclose = () => {
      setIsConnected(false);
      console.log('WebSocket disconnected');
    };

    return ws;
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
  }, []);

  return { logs, isConnected, connect, clearLogs };
}
