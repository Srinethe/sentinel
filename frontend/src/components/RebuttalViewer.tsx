'use client';

import { motion } from 'framer-motion';
import { FileText, MessageSquare, Copy, Check, Download } from 'lucide-react';
import { useState } from 'react';

interface RebuttalViewerProps {
  letter: string;
  talkingPoints: string[];
  caseId?: string | null;
}

export function RebuttalViewer({ letter, talkingPoints, caseId }: RebuttalViewerProps) {
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState<'letter' | 'p2p'>('letter');

  const copyToClipboard = async () => {
    await navigator.clipboard.writeText(letter);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadPDF = async () => {
    if (!caseId) {
      console.error('No case ID provided for PDF download');
      return;
    }
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${API_BASE}/api/case/${caseId}/rebuttal-pdf`);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error('Failed to download PDF:', response.status, errorText);
        alert(`Failed to download PDF: ${response.status === 404 ? 'Case not found' : response.status === 400 ? 'No rebuttal letter available' : 'Server error'}`);
        return;
      }
      
      const blob = await response.blob();
      
      // Check if blob is actually a PDF
      if (blob.type !== 'application/pdf' && blob.size === 0) {
        console.error('Invalid PDF blob received');
        alert('Failed to download PDF: Invalid file received');
        return;
      }
      
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rebuttal-letter-${caseId}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to download rebuttal PDF:', error);
      alert('Failed to download PDF. Please try again.');
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 overflow-hidden"
    >
      {/* Tabs */}
      <div className="flex border-b border-slate-800">
        <button
          onClick={() => setActiveTab('letter')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'letter'
              ? 'bg-cyan-500/10 text-cyan-400 border-b-2 border-cyan-400'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <FileText className="w-4 h-4 inline mr-2" />
          Appeal Letter
        </button>
        <button
          onClick={() => setActiveTab('p2p')}
          className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
            activeTab === 'p2p'
              ? 'bg-cyan-500/10 text-cyan-400 border-b-2 border-cyan-400'
              : 'text-slate-400 hover:text-white'
          }`}
        >
          <MessageSquare className="w-4 h-4 inline mr-2" />
          P2P Script
        </button>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'letter' ? (
          <div>
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">Generated Appeal Letter</h3>
              <div className="flex gap-2">
                {caseId && (
                  <button
                    onClick={downloadPDF}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-cyan-600 hover:bg-cyan-500 rounded-lg transition-colors text-white"
                  >
                    <Download className="w-4 h-4" />
                    Download PDF
                  </button>
                )}
                <button
                  onClick={copyToClipboard}
                  className="flex items-center gap-2 px-3 py-1.5 text-sm bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors"
                >
                  {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </div>
            <div className="prose prose-invert prose-sm max-w-none bg-slate-800/50 rounded-lg p-4 max-h-96 overflow-auto">
              <pre className="whitespace-pre-wrap text-slate-300 text-sm font-sans">{letter}</pre>
            </div>
          </div>
        ) : (
          <div>
            <h3 className="text-lg font-semibold text-white mb-4">Peer-to-Peer Talking Points</h3>
            <div className="space-y-3">
              {talkingPoints.map((point, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex gap-3 p-4 bg-slate-800/50 rounded-lg"
                >
                  <span className="flex-shrink-0 w-6 h-6 bg-cyan-500 text-white rounded-full flex items-center justify-center text-sm font-bold">
                    {index + 1}
                  </span>
                  <p className="text-slate-300">{point}</p>
                </motion.div>
              ))}
            </div>
          </div>
        )}
      </div>
    </motion.div>
  );
}
