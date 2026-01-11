'use client';

import { motion } from 'framer-motion';
import { Check } from 'lucide-react';

interface StepIndicatorProps {
  currentStep: number;
  totalSteps?: number;
  steps?: string[];
}

export function StepIndicator({ currentStep, totalSteps = 4, steps }: StepIndicatorProps) {
  const stepLabels = steps || [
    'Enter Dictation',
    'View Audit Report',
    'Upload Denial PDF',
    'View Rebuttal'
  ];

  return (
    <div className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-6">
      <div className="flex items-center justify-between">
        {stepLabels.map((label, index) => {
          const stepNum = index + 1;
          const isCompleted = stepNum < currentStep;
          const isCurrent = stepNum === currentStep;
          const isPending = stepNum > currentStep;

          return (
            <div key={stepNum} className="flex items-center flex-1">
              {/* Step Circle */}
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all ${
                    isCompleted
                      ? 'bg-green-500 text-white'
                      : isCurrent
                      ? 'bg-cyan-500 text-white ring-4 ring-cyan-500/20'
                      : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {isCompleted ? <Check className="w-5 h-5" /> : stepNum}
                </div>
                <span
                  className={`mt-2 text-xs font-medium text-center ${
                    isCurrent ? 'text-cyan-400' : isCompleted ? 'text-green-400' : 'text-slate-500'
                  }`}
                >
                  {label}
                </span>
              </div>

              {/* Connector Line */}
              {index < stepLabels.length - 1 && (
                <div
                  className={`h-0.5 flex-1 mx-2 transition-all ${
                    isCompleted ? 'bg-green-500' : 'bg-slate-700'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Progress Bar */}
      <div className="mt-6">
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${(currentStep / totalSteps) * 100}%` }}
            transition={{ duration: 0.5 }}
            className="h-full bg-gradient-to-r from-cyan-500 to-blue-600"
          />
        </div>
        <div className="mt-2 text-xs text-slate-400 text-center">
          Step {currentStep} of {totalSteps}
        </div>
      </div>
    </div>
  );
}
