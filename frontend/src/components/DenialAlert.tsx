'use client';

import { motion } from 'framer-motion';
import { AlertTriangle, Clock } from 'lucide-react';

interface DenialAlertProps {
  reason: string;
  deadline: string | null;
}

export function DenialAlert({ reason, deadline }: DenialAlertProps) {
  const hoursRemaining = deadline
    ? Math.max(0, Math.floor((new Date(deadline).getTime() - Date.now()) / (1000 * 60 * 60)))
    : null;

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      className="relative overflow-hidden rounded-xl border border-red-500/50 bg-gradient-to-r from-red-500/10 to-orange-500/10 p-6"
    >
      <motion.div
        className="absolute inset-0 bg-red-500/5"
        animate={{ opacity: [0.1, 0.2, 0.1] }}
        transition={{ duration: 2, repeat: Infinity }}
      />

      <div className="relative">
        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-red-500/20">
            <AlertTriangle className="w-6 h-6 text-red-400" />
          </div>

          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 text-xs font-bold bg-red-500 text-white rounded">
                P0 DENIAL DETECTED
              </span>
            </div>

            <p className="text-slate-200 mb-4">{reason}</p>

            {hoursRemaining !== null && (
              <div className="flex items-center gap-2 text-sm">
                <Clock className="w-4 h-4 text-yellow-400" />
                <span className="text-yellow-400 font-semibold">
                  {hoursRemaining}h remaining for Peer-to-Peer Review
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
