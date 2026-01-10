'use client';

import { motion } from 'framer-motion';

interface Agent {
  id: string;
  name: string;
  icon: string;
  description: string;
}

const agents: Agent[] = [
  { id: 'scribe', name: 'The Ear', icon: '👂', description: 'Ambient Scribe - Voice to Clinical Data' },
  { id: 'coder', name: 'The Brain', icon: '🧠', description: 'Policy Auditor - Preemptive Alerts' },
  { id: 'intake', name: 'The Sorter', icon: '📂', description: 'PDF Triage - Denial Detection' },
  { id: 'rebuttal', name: 'The Negotiator', icon: '⚔️', description: 'Appeal Generator - Win the Fight' },
];

interface AgentWorkflowProps {
  currentAgent: string;
  completedAgents: string[];
}

export function AgentWorkflow({ currentAgent, completedAgents }: AgentWorkflowProps) {
  return (
    <div className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-6">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-6">
        Sentinel Swarm - 4 Agent System
      </h3>

      <div className="space-y-3">
        {agents.map((agent, index) => {
          const isActive = currentAgent === agent.id;
          const isComplete = completedAgents.includes(agent.id);

          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`relative p-4 rounded-lg border transition-all duration-500 ${
                isActive
                  ? 'bg-cyan-500/10 border-cyan-500/50 glow-cyan'
                  : isComplete
                  ? 'bg-green-500/10 border-green-500/30'
                  : 'bg-slate-800/30 border-slate-700/50'
              }`}
            >
              {isActive && (
                <motion.div
                  className="absolute inset-0 rounded-lg bg-cyan-400/10"
                  animate={{ opacity: [0.2, 0.4, 0.2] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                />
              )}

              <div className="relative flex items-center gap-4">
                <div className={`text-2xl ${isActive ? 'animate-bounce' : ''}`}>
                  {isComplete ? '✅' : agent.icon}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="font-medium text-white">{agent.name}</div>
                  <div className="text-xs text-slate-400 truncate">{agent.description}</div>
                </div>

                {isActive && (
                  <motion.div
                    className="w-5 h-5 border-2 border-cyan-400 border-t-transparent rounded-full"
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                  />
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
      
      {/* Workflow indicator */}
      <div className="mt-4 pt-4 border-t border-slate-800">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Dictation Flow</span>
          <span className="text-slate-600">→</span>
          <span>Ear → Brain</span>
        </div>
        <div className="flex items-center justify-between text-xs text-slate-500 mt-1">
          <span>Denial Flow</span>
          <span className="text-slate-600">→</span>
          <span>Sorter → Negotiator</span>
        </div>
      </div>
    </div>
  );
}
