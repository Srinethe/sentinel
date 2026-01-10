'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, Mic, Zap } from 'lucide-react';

import { AgentWorkflow } from '@/components/AgentWorkflow';
import { DenialAlert } from '@/components/DenialAlert';
import { RebuttalViewer } from '@/components/RebuttalViewer';
import { MetricsDashboard } from '@/components/MetricsDashboard';
import { LiveLogs } from '@/components/LiveLogs';
import { ClinicalDataPanel } from '@/components/ClinicalDataPanel';
import { 
  processDenialPDF, 
  runDictationDemo, 
  runFullDemo,
  type FullCaseResult 
} from '@/lib/api';

export default function Dashboard() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<FullCaseResult | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [currentAgent, setCurrentAgent] = useState('');
  const [completedAgents, setCompletedAgents] = useState<string[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<'dictation' | 'denial' | 'full' | null>(null);

  const addLog = (agent: string, status: string, message: string) => {
    setLogs((prev) => [...prev, { agent, status, message, timestamp: new Date().toISOString() }]);
  };

  const resetState = () => {
    setResult(null);
    setLogs([]);
    setCompletedAgents([]);
    setCurrentAgent('');
  };

  // Demo 1: Dictation Only (Ear -> Brain)
  const handleDictationDemo = async () => {
    setIsProcessing(true);
    resetState();
    setActiveWorkflow('dictation');

    try {
      // Agent 1: The Ear
      setCurrentAgent('scribe');
      addLog('scribe', 'running', 'Listening to physician dictation...');
      await new Promise((r) => setTimeout(r, 800));
      addLog('scribe', 'running', 'Extracting clinical entities...');
      await new Promise((r) => setTimeout(r, 600));
      
      const response = await runDictationDemo();
      
      addLog('scribe', 'complete', `Extracted ${response.clinical_entities?.length || 0} clinical entities`);
      setCompletedAgents(['scribe']);
      
      // Agent 2: The Brain
      setCurrentAgent('coder');
      addLog('coder', 'running', 'Auditing against payer policies...');
      await new Promise((r) => setTimeout(r, 700));
      addLog('coder', 'running', 'Checking medical necessity criteria...');
      await new Promise((r) => setTimeout(r, 500));
      
      const alertCount = response.preemptive_alerts?.length || 0;
      addLog('coder', 'complete', alertCount > 0 
        ? `⚠️ Found ${alertCount} preemptive alerts!` 
        : '✓ No policy gaps detected');
      setCompletedAgents(['scribe', 'coder']);

      setResult(response as FullCaseResult);
      setCurrentAgent('');
    } catch (error) {
      addLog('system', 'error', 'Processing failed');
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Demo 2: Full Workflow (All 4 Agents)
  const handleFullDemo = async () => {
    setIsProcessing(true);
    resetState();
    setActiveWorkflow('full');

    try {
      // Agent 1: The Ear
      setCurrentAgent('scribe');
      addLog('scribe', 'running', 'Processing physician dictation...');
      await new Promise((r) => setTimeout(r, 800));
      addLog('scribe', 'complete', 'Clinical data extracted');
      setCompletedAgents(['scribe']);

      // Agent 2: The Brain  
      setCurrentAgent('coder');
      addLog('coder', 'running', 'Running policy audit...');
      await new Promise((r) => setTimeout(r, 700));
      addLog('coder', 'complete', '⚠️ Denial risk: MEDIUM - K+ below threshold');
      setCompletedAgents(['scribe', 'coder']);

      // Agent 3: The Sorter
      setCurrentAgent('intake');
      addLog('intake', 'running', 'Analyzing denial document...');
      await new Promise((r) => setTimeout(r, 600));
      
      const response = await runFullDemo();
      
      addLog('intake', 'complete', '🚨 DENIAL DETECTED!');
      setCompletedAgents(['scribe', 'coder', 'intake']);

      // Agent 4: The Negotiator
      setCurrentAgent('rebuttal');
      addLog('rebuttal', 'running', 'Synthesizing clinical evidence...');
      await new Promise((r) => setTimeout(r, 500));
      addLog('rebuttal', 'running', 'Generating appeal letter...');
      await new Promise((r) => setTimeout(r, 600));
      addLog('rebuttal', 'complete', '✅ Appeal letter and P2P script ready!');
      setCompletedAgents(['scribe', 'coder', 'intake', 'rebuttal']);

      setResult(response);
      setCurrentAgent('');
    } catch (error) {
      addLog('system', 'error', 'Processing failed');
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Upload denial PDF
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    resetState();
    setActiveWorkflow('denial');

    try {
      setCurrentAgent('intake');
      addLog('intake', 'running', 'Reading denial PDF...');
      
      const response = await processDenialPDF(file);
      
      addLog('intake', 'complete', response.denial_detected ? '🚨 Denial detected!' : 'Document processed');
      setCompletedAgents(['intake']);

      if (response.denial_detected) {
        setCurrentAgent('rebuttal');
        addLog('rebuttal', 'running', 'Generating appeal...');
        await new Promise((r) => setTimeout(r, 500));
        addLog('rebuttal', 'complete', 'Appeal ready!');
        setCompletedAgents(['intake', 'rebuttal']);
      }

      setResult(response as FullCaseResult);
      setCurrentAgent('');
    } catch (error) {
      addLog('system', 'error', 'Processing failed');
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950">
      {/* Header */}
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center">
              <span className="text-xl">🏥</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Project Sentinel</h1>
              <p className="text-sm text-slate-400">4-Agent Healthcare AI System</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Upload PDF */}
            <label className="cursor-pointer">
              <input type="file" accept=".pdf" onChange={handleFileUpload} className="hidden" disabled={isProcessing} />
              <div className={`flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors text-sm ${isProcessing ? 'opacity-50' : ''}`}>
                <Upload className="w-4 h-4" />
                Upload Denial
              </div>
            </label>

            {/* Dictation Demo */}
            <button
              onClick={handleDictationDemo}
              disabled={isProcessing}
              className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded-lg text-sm transition-colors disabled:opacity-50"
            >
              <Mic className="w-4 h-4" />
              Dictation Demo
            </button>

            {/* Full Demo */}
            <button
              onClick={handleFullDemo}
              disabled={isProcessing}
              className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 rounded-lg font-semibold transition-all disabled:opacity-50"
            >
              {isProcessing ? (
                <motion.div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full" animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }} />
              ) : (
                <Zap className="w-4 h-4" />
              )}
              {isProcessing ? 'Processing...' : 'Full Demo'}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6 grid grid-cols-12 gap-6">
        {/* Left Panel - Agents & Metrics */}
        <div className="col-span-3 space-y-6">
          <AgentWorkflow currentAgent={currentAgent} completedAgents={completedAgents} />
          <MetricsDashboard />
        </div>

        {/* Center Panel - Results */}
        <div className="col-span-6 space-y-6">
          {/* Denial Alert */}
          {result?.denial_detected && result.denial_reason && (
            <DenialAlert reason={result.denial_reason} deadline={result.peer_to_peer_deadline || null} />
          )}

          {/* Clinical Data Panel (from Scribe + Coder) */}
          {(result?.soap_note || result?.clinical_entities?.length || result?.preemptive_alerts?.length) && (
            <ClinicalDataPanel
              soapNote={result.soap_note}
              clinicalEntities={result.clinical_entities}
              icdCodes={result.icd_codes}
              preemptiveAlerts={result.preemptive_alerts}
              policyGaps={result.policy_gaps}
              denialRisk={result.denial_risk}
              medicalNecessityScore={result.medical_necessity_score}
            />
          )}

          {/* Rebuttal Viewer */}
          {result?.rebuttal_letter && (
            <RebuttalViewer letter={result.rebuttal_letter} talkingPoints={result.talking_points || []} />
          )}

          {/* Empty State */}
          {!result && !isProcessing && (
            <div className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 border-dashed p-12 text-center">
              <FileText className="w-12 h-12 mx-auto text-slate-600 mb-4" />
              <h3 className="text-lg font-medium text-slate-400 mb-2">Ready to Process</h3>
              <p className="text-sm text-slate-500 mb-4">Choose a demo to see the 4-agent system in action</p>
              <div className="flex justify-center gap-4 text-xs text-slate-600">
                <span>👂 Ear: Voice → Data</span>
                <span>🧠 Brain: Policy Audit</span>
                <span>📂 Sorter: PDF Triage</span>
                <span>⚔️ Negotiator: Appeals</span>
              </div>
            </div>
          )}
        </div>

        {/* Right Panel - Logs */}
        <div className="col-span-3">
          <div className="h-[calc(100vh-180px)]">
            <LiveLogs logs={logs} />
          </div>
        </div>
      </main>
    </div>
  );
}
