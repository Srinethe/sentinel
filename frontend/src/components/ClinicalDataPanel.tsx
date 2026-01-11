'use client';

import { motion } from 'framer-motion';
import { Stethoscope, AlertTriangle, FileCode, Activity, Download, ArrowRight } from 'lucide-react';
import type { SOAPNote, ClinicalEntity, PreemptiveAlert, ICDCode, PolicyGap } from '@/lib/api';

interface ClinicalDataPanelProps {
  soapNote?: SOAPNote;
  clinicalEntities?: ClinicalEntity[];
  icdCodes?: ICDCode[];
  preemptiveAlerts?: PreemptiveAlert[];
  policyGaps?: PolicyGap[];
  denialRisk?: string;
  medicalNecessityScore?: number;
  caseId?: string | null;
  onContinue?: () => void;
}

export function ClinicalDataPanel({
  soapNote,
  clinicalEntities,
  icdCodes,
  preemptiveAlerts,
  policyGaps,
  denialRisk,
  medicalNecessityScore,
  caseId,
  onContinue,
}: ClinicalDataPanelProps) {
  const hasData = soapNote || clinicalEntities?.length || icdCodes?.length;
  
  if (!hasData) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-slate-900/50 backdrop-blur rounded-xl border border-slate-800 overflow-hidden"
    >
      {/* Header with risk indicator */}
      <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Stethoscope className="w-5 h-5 text-cyan-400" />
          <h3 className="font-semibold text-white">Clinical Analysis</h3>
        </div>
        
        {denialRisk && (
          <div className={`px-3 py-1 rounded-full text-xs font-bold ${
            denialRisk === 'high' ? 'bg-red-500/20 text-red-400' :
            denialRisk === 'medium' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-green-500/20 text-green-400'
          }`}>
            {denialRisk.toUpperCase()} DENIAL RISK
          </div>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* Preemptive Alerts - Most Important! */}
        {preemptiveAlerts && preemptiveAlerts.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-orange-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Preemptive Alerts ({preemptiveAlerts.length})
            </h4>
            {preemptiveAlerts.map((alert, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.1 }}
                className={`p-3 rounded-lg border ${
                  alert.urgency === 'immediate' 
                    ? 'bg-red-500/10 border-red-500/30' 
                    : 'bg-yellow-500/10 border-yellow-500/30'
                }`}
              >
                <div className="flex items-start gap-2">
                  <span className={`px-2 py-0.5 text-xs rounded ${
                    alert.alert_type === 'THRESHOLD_NOT_MET' ? 'bg-red-500/30 text-red-300' :
                    alert.alert_type === 'MISSING_DATA' ? 'bg-yellow-500/30 text-yellow-300' :
                    'bg-orange-500/30 text-orange-300'
                  }`}>
                    {alert.alert_type.replace(/_/g, ' ')}
                  </span>
                </div>
                <p className="text-sm text-slate-200 mt-2">{alert.message}</p>
                <p className="text-xs text-cyan-400 mt-1">→ {alert.action_required}</p>
              </motion.div>
            ))}
          </div>
        )}

        {/* SOAP Note */}
        {soapNote && Object.keys(soapNote).length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-400">SOAP Note</h4>
            <div className="grid grid-cols-2 gap-3">
              {['subjective', 'objective', 'assessment', 'plan'].map((key) => (
                soapNote[key as keyof SOAPNote] && (
                  <div key={key} className="bg-slate-800/50 rounded-lg p-3">
                    <div className="text-xs text-cyan-400 uppercase mb-1">{key}</div>
                    <div className="text-sm text-slate-300 line-clamp-3">
                      {soapNote[key as keyof SOAPNote]}
                    </div>
                  </div>
                )
              ))}
            </div>
          </div>
        )}

        {/* Clinical Entities */}
        {clinicalEntities && clinicalEntities.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Extracted Clinical Data ({clinicalEntities.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {clinicalEntities.slice(0, 10).map((entity, i) => (
                <span
                  key={i}
                  className={`px-2 py-1 text-xs rounded-full ${
                    entity.type === 'lab_value' ? 'bg-purple-500/20 text-purple-300' :
                    entity.type === 'diagnosis' ? 'bg-red-500/20 text-red-300' :
                    entity.type === 'medication' ? 'bg-blue-500/20 text-blue-300' :
                    entity.type === 'vital_sign' ? 'bg-green-500/20 text-green-300' :
                    'bg-slate-700 text-slate-300'
                  }`}
                >
                  {entity.name}: {entity.value} {entity.unit || ''}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ICD Codes */}
        {icdCodes && icdCodes.length > 0 && (
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-400 flex items-center gap-2">
              <FileCode className="w-4 h-4" />
              Suggested ICD Codes
            </h4>
            <div className="space-y-2">
              {icdCodes.slice(0, 5).map((code, i) => (
                <div key={i} className="flex items-center gap-3 text-sm">
                  <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 rounded font-mono">
                    {code.code}
                  </span>
                  <span className="text-slate-400">{code.description}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Medical Necessity Score */}
        {medicalNecessityScore !== undefined && (
          <div className="pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-400">Medical Necessity Score</span>
              <div className="flex items-center gap-2">
                <div className="w-32 h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div 
                    className={`h-full rounded-full ${
                      medicalNecessityScore >= 0.7 ? 'bg-green-500' :
                      medicalNecessityScore >= 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${medicalNecessityScore * 100}%` }}
                  />
                </div>
                <span className="text-sm font-mono text-white">
                  {(medicalNecessityScore * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="pt-4 border-t border-slate-800 flex gap-3">
          {caseId && (
            <button
              onClick={async () => {
                try {
                  const response = await fetch(`http://localhost:8000/api/case/${caseId}/audit-report`);
                  const blob = await response.blob();
                  const url = window.URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `audit-report-${caseId}.pdf`;
                  a.click();
                  window.URL.revokeObjectURL(url);
                } catch (error) {
                  console.error('Failed to download audit report:', error);
                }
              }}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm font-medium text-white transition-colors"
            >
              <Download className="w-4 h-4" />
              Download Audit Report PDF
            </button>
          )}
          {onContinue && (
            <button
              onClick={onContinue}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-600 hover:to-blue-700 rounded-lg text-sm font-semibold text-white transition-all"
            >
              Continue to Step 3
              <ArrowRight className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
