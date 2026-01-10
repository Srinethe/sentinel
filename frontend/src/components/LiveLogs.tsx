'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useEffect, useRef } from 'react';

interface LogEntry {
  agent: string;
  status: string;
  message: string;
  timestamp: string;
}

interface LiveLogsProps {
  logs: LogEntry[];
}

export function LiveLogs({ logs }: LiveLogsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'bg-yellow-500';
      case 'complete':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-slate-500';
    }
  };

  const getAgentColor = (agent: string) => {
    switch (agent) {
      case 'intake':
        return 'text-purple-400';
      case 'coder':
        return 'text-blue-400';
      case 'rebuttal':
        return 'text-cyan-400';
      default:
        return 'text-slate-400';
    }
  };

  return (
    <div className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-4 h-full flex flex-col">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
        Agent Activity
      </h3>

      <div ref={scrollRef} className="flex-1 overflow-auto space-y-2">
        <AnimatePresence>
          {logs.map((log, i) => (
            <motion.div
              key={`${log.timestamp}-${i}`}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              className="text-sm flex items-start gap-2"
            >
              <span
                className={`inline-block w-2 h-2 rounded-full mt-1.5 ${getStatusColor(log.status)} ${
                  log.status === 'running' ? 'animate-pulse' : ''
                }`}
              />
              <div>
                <span className={`font-mono ${getAgentColor(log.agent)}`}>[{log.agent}]</span>
                <span className="text-slate-300 ml-2">{log.message}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {logs.length === 0 && (
          <div className="text-slate-500 text-sm text-center py-8">
            Waiting for agent activity...
          </div>
        )}
      </div>
    </div>
  );
}
