'use client';

import { motion } from 'framer-motion';

interface Metric {
  label: string;
  value: string;
  subtext: string;
  highlight?: boolean;
}

const metrics: Metric[] = [
  { label: 'Manual Process', value: '4 hrs', subtext: 'Average case time' },
  { label: 'With Sentinel', value: '32 sec', subtext: 'AI-driven synthesis', highlight: true },
  { label: 'Time Saved', value: '99.8%', subtext: 'Per case', highlight: true },
  { label: 'Appeal Success', value: '73%', subtext: 'Denial reversal rate' },
];

export function MetricsDashboard() {
  return (
    <div className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-6">
      <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-4">
        Impact Metrics
      </h3>

      <div className="grid grid-cols-2 gap-3">
        {metrics.map((metric, i) => (
          <motion.div
            key={metric.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.1 }}
            className={`p-4 rounded-lg ${
              metric.highlight
                ? 'bg-gradient-to-br from-cyan-500/20 to-blue-600/20 border border-cyan-500/30'
                : 'bg-slate-800/50'
            }`}
          >
            <div className={`text-2xl font-bold ${metric.highlight ? 'text-cyan-400' : 'text-white'}`}>
              {metric.value}
            </div>
            <div className="text-sm text-slate-400">{metric.label}</div>
            <div className="text-xs text-slate-500">{metric.subtext}</div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
