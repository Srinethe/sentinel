'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Mic, FileText, User } from 'lucide-react';

interface DictationInputProps {
  onProcess: (dictation: string, patientName: string, audioFile?: File) => void;
  isProcessing?: boolean;
}

export function DictationInput({ onProcess, isProcessing = false }: DictationInputProps) {
  const [dictationText, setDictationText] = useState('');
  const [patientName, setPatientName] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [inputMode, setInputMode] = useState<'text' | 'audio'>('text');

  const handleSubmit = () => {
    if (inputMode === 'text' && dictationText.trim()) {
      onProcess(dictationText, patientName || 'Patient');
    } else if (inputMode === 'audio' && audioFile) {
      onProcess('', patientName || 'Patient', audioFile);
    }
  };

  const canSubmit = inputMode === 'text' 
    ? dictationText.trim().length > 0 
    : audioFile !== null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-6 space-y-6"
    >
      <div className="flex items-center gap-3 mb-4">
        <Mic className="w-6 h-6 text-cyan-400" />
        <h2 className="text-xl font-bold text-white">Step 1: Enter Dictation</h2>
      </div>

      {/* Patient Name Input */}
      <div className="space-y-2">
        <label className="text-sm font-medium text-slate-300 flex items-center gap-2">
          <User className="w-4 h-4" />
          Patient Name
        </label>
        <input
          type="text"
          value={patientName}
          onChange={(e) => setPatientName(e.target.value)}
          placeholder="Enter patient name (optional)"
          className="w-full px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500"
          disabled={isProcessing}
        />
      </div>

      {/* Input Mode Toggle */}
      <div className="flex gap-2 p-1 bg-slate-800 rounded-lg">
        <button
          onClick={() => setInputMode('text')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all ${
            inputMode === 'text'
              ? 'bg-cyan-500 text-white'
              : 'text-slate-400 hover:text-white'
          }`}
          disabled={isProcessing}
        >
          <FileText className="w-4 h-4 inline mr-2" />
          Text Input
        </button>
        <button
          onClick={() => setInputMode('audio')}
          className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition-all ${
            inputMode === 'audio'
              ? 'bg-cyan-500 text-white'
              : 'text-slate-400 hover:text-white'
          }`}
          disabled={isProcessing}
        >
          <Mic className="w-4 h-4 inline mr-2" />
          Audio Upload
        </button>
      </div>

      {/* Text Input Mode */}
      {inputMode === 'text' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-2"
        >
          <label className="text-sm font-medium text-slate-300">
            Dictation Text
          </label>
          <textarea
            value={dictationText}
            onChange={(e) => setDictationText(e.target.value)}
            placeholder="Paste or type physician dictation here...

Example:
Patient is a 67-year-old male presenting with weakness and fatigue. 
Labs show potassium of 6.1 mmol/L. EKG shows peaked T waves.
Assessment: Acute hyperkalemia. Plan: Admit for monitoring."
            rows={12}
            className="w-full px-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500 resize-none font-mono text-sm"
            disabled={isProcessing}
          />
          <p className="text-xs text-slate-500">
            {dictationText.length} characters
          </p>
        </motion.div>
      )}

      {/* Audio Input Mode */}
      {inputMode === 'audio' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="space-y-2"
        >
          <label className="text-sm font-medium text-slate-300">
            Audio File
          </label>
          <div className="border-2 border-dashed border-slate-700 rounded-lg p-6 text-center hover:border-cyan-500 transition-colors">
            <input
              type="file"
              accept="audio/*,.wav,.mp3,.m4a"
              onChange={(e) => setAudioFile(e.target.files?.[0] || null)}
              className="hidden"
              id="audio-upload"
              disabled={isProcessing}
            />
            <label
              htmlFor="audio-upload"
              className="cursor-pointer flex flex-col items-center gap-2"
            >
              <Mic className="w-8 h-8 text-slate-500" />
              <span className="text-sm text-slate-400">
                {audioFile ? audioFile.name : 'Click to upload audio file'}
              </span>
              <span className="text-xs text-slate-500">
                WAV, MP3, or M4A format
              </span>
            </label>
          </div>
        </motion.div>
      )}

      {/* Submit Button */}
      <button
        onClick={handleSubmit}
        disabled={!canSubmit || isProcessing}
        className={`w-full px-6 py-3 rounded-lg font-semibold transition-all ${
          canSubmit && !isProcessing
            ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white hover:from-cyan-600 hover:to-blue-700 shadow-lg shadow-cyan-500/25'
            : 'bg-slate-700 text-slate-500 cursor-not-allowed'
        }`}
      >
        {isProcessing ? (
          <span className="flex items-center justify-center gap-2">
            <span className="animate-spin">⏳</span>
            Processing...
          </span>
        ) : (
          'Process Dictation →'
        )}
      </button>
    </motion.div>
  );
}
