'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText } from 'lucide-react';

import { AgentWorkflow } from '@/components/AgentWorkflow';
import { DenialAlert } from '@/components/DenialAlert';
import { RebuttalViewer } from '@/components/RebuttalViewer';
import { MetricsDashboard } from '@/components/MetricsDashboard';
import { LiveLogs } from '@/components/LiveLogs';
import { ClinicalDataPanel } from '@/components/ClinicalDataPanel';
import { DictationInput } from '@/components/DictationInput';
import { StepIndicator } from '@/components/StepIndicator';
import { 
  processDenialPDF, 
  processDictationText,
  processDictationAudio,
  type FullCaseResult 
} from '@/lib/api';

export default function Dashboard() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState<FullCaseResult | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [currentAgent, setCurrentAgent] = useState('');
  const [completedAgents, setCompletedAgents] = useState<string[]>([]);
  const [activeWorkflow, setActiveWorkflow] = useState<'dictation' | 'denial' | 'full' | null>(null);
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3 | 4>(1);
  const [caseId, setCaseId] = useState<string | null>(null);

  const addLog = (agent: string, status: string, message: string) => {
    setLogs((prev) => [...prev, { agent, status, message, timestamp: new Date().toISOString() }]);
  };

  const resetState = () => {
    setResult(null);
    setLogs([]);
    setCompletedAgents([]);
    setCurrentAgent('');
    setCurrentStep(1);
    setCaseId(null);
  };

  // Handle dictation input from user
  const handleDictationProcess = async (dictation: string, patientName: string, audioFile?: File) => {
    setIsProcessing(true);
    resetState();
    setActiveWorkflow('dictation');
    setCurrentStep(1);

    try {
      // Agent 1: The Ear
      setCurrentAgent('scribe');
      addLog('scribe', 'running', 'Processing physician dictation...');
      
      let response: FullCaseResult;
      if (audioFile) {
        response = await processDictationAudio(audioFile, patientName) as FullCaseResult;
      } else {
        response = await processDictationText(dictation, patientName) as FullCaseResult;
      }
      
      setCaseId(response.case_id);
      addLog('scribe', 'complete', `Extracted ${response.clinical_entities?.length || 0} clinical entities`);
      setCompletedAgents(['scribe']);

      // Agent 2: The Brain
      setCurrentAgent('coder');
      addLog('coder', 'running', 'Auditing against payer policies...');
      await new Promise((r) => setTimeout(r, 1000));
      
      const alertCount = response.preemptive_alerts?.length || 0;
      addLog('coder', 'complete', alertCount > 0 
        ? `⚠️ Found ${alertCount} preemptive alerts!` 
        : '✓ No policy gaps detected');
      setCompletedAgents(['scribe', 'coder']);

      setResult(response);
      setCurrentStep(2); // Move to step 2: View audit results
      setCurrentAgent('');
    } catch (error) {
      addLog('system', 'error', 'Processing failed');
      console.error(error);
    } finally {
      setIsProcessing(false);
    }
  };

  // Upload denial PDF (Step 3)
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsProcessing(true);
    setActiveWorkflow('denial');
    setCurrentStep(3);

    try {
      setCurrentAgent('intake');
      addLog('intake', 'running', 'Reading denial PDF...');
      
      const response = await processDenialPDF(file, result?.patient_name || 'Patient');
      
      // Merge with existing result if we have dictation data
      const mergedResult = result ? { ...result, ...response } : response as FullCaseResult;
      
      addLog('intake', 'complete', response.denial_detected ? '🚨 Denial detected!' : 'Document processed');
      setCompletedAgents([...completedAgents, 'intake']);

      if (response.denial_detected) {
        setCurrentAgent('rebuttal');
        addLog('rebuttal', 'running', 'Generating appeal...');
        await new Promise((r) => setTimeout(r, 1000));
        addLog('rebuttal', 'complete', '✅ Appeal letter and P2P script ready!');
        setCompletedAgents([...completedAgents, 'intake', 'rebuttal']);
        setCurrentStep(4); // Move to step 4: View rebuttal
      }

      setResult(mergedResult);
      setCurrentAgent('');
    } catch (error) {
      addLog('system', 'error', 'Processing failed');
      console.error(error);
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
            {/* Header actions removed - using step-by-step workflow instead */}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto p-6 space-y-6">
        {/* Step Indicator */}
        {activeWorkflow && (
          <StepIndicator currentStep={currentStep} />
        )}

        <div className="grid grid-cols-12 gap-6">
          {/* Left Panel - Agents & Metrics */}
          <div className="col-span-3 space-y-6">
            <AgentWorkflow currentAgent={currentAgent} completedAgents={completedAgents} />
            <MetricsDashboard />
          </div>

          {/* Center Panel - Results */}
          <div className="col-span-6 space-y-6">
          {/* Step 1: Dictation Input */}
          {currentStep === 1 && !result && (
            <DictationInput onProcess={handleDictationProcess} isProcessing={isProcessing} />
          )}

          {/* Step 2: Audit Results */}
          {currentStep >= 2 && result && (
            <>
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
                  caseId={caseId}
                  onContinue={() => setCurrentStep(3)}
                />
              )}
            </>
          )}

          {/* Step 3: Upload Denial PDF */}
          {currentStep === 3 && (
            <>
              {!isProcessing ? (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-6 space-y-4"
                >
                  <h2 className="text-xl font-bold text-white flex items-center gap-3">
                    <Upload className="w-6 h-6 text-cyan-400" />
                    Step 3: Upload Denial PDF
                  </h2>
                  <p className="text-sm text-slate-400">
                    Upload the denial letter from the insurance company to generate an appeal.
                  </p>
                  <label className="cursor-pointer">
                    <input 
                      type="file" 
                      accept=".pdf" 
                      onChange={handleFileUpload} 
                      className="hidden" 
                      disabled={isProcessing} 
                    />
                    <div className="flex items-center justify-center gap-2 px-6 py-4 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors border-2 border-dashed border-slate-700 cursor-pointer">
                      <Upload className="w-5 h-5 text-cyan-400" />
                      <span className="text-white font-medium">Click to Upload Denial PDF</span>
                    </div>
                  </label>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-12 space-y-6"
                >
                  <div className="flex flex-col items-center justify-center space-y-4">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                      className="w-16 h-16 border-4 border-cyan-500 border-t-transparent rounded-full"
                    />
                    <div className="text-center space-y-2">
                      <h3 className="text-xl font-bold text-white">Processing Denial PDF</h3>
                      <p className="text-sm text-slate-400">
                        {currentAgent === 'intake' && 'Reading denial document...'}
                        {currentAgent === 'rebuttal' && 'Generating appeal letter...'}
                        {!currentAgent && 'Analyzing document...'}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <div className="flex gap-1">
                        {['intake', 'rebuttal'].map((agent) => (
                          <div
                            key={agent}
                            className={`w-2 h-2 rounded-full ${
                              completedAgents.includes(agent)
                                ? 'bg-green-500'
                                : currentAgent === agent
                                ? 'bg-cyan-500 animate-pulse'
                                : 'bg-slate-600'
                            }`}
                          />
                        ))}
                      </div>
                      <span>
                        {completedAgents.includes('intake') && completedAgents.includes('rebuttal')
                          ? 'Complete'
                          : 'Processing...'}
                      </span>
                    </div>
                  </div>
                </motion.div>
              )}
            </>
          )}

          {/* Step 4: Rebuttal Viewer */}
          {currentStep >= 4 && result?.rebuttal_letter && (
            <>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 p-6"
              >
                <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-3">
                  <span className="text-2xl">✅</span>
                  Step 4: Appeal Letter Generated
                </h2>
                <p className="text-sm text-slate-400 mb-4">
                  Your evidence-based appeal letter and peer-to-peer talking points are ready.
                </p>
              </motion.div>
              <RebuttalViewer 
                letter={result.rebuttal_letter} 
                talkingPoints={result.talking_points || []}
                caseId={caseId}
              />
            </>
          )}

          {/* Empty State - Only show if no step is active */}
          {currentStep === 1 && !result && !isProcessing && activeWorkflow === null && (
            <div className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 border-dashed p-12 text-center">
              <FileText className="w-12 h-12 mx-auto text-slate-600 mb-4" />
              <h3 className="text-lg font-medium text-slate-400 mb-2">Ready to Process</h3>
              <p className="text-sm text-slate-500 mb-4">Enter a dictation above to start the workflow</p>
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
        </div>
      </main>
    </div>
  );
}
