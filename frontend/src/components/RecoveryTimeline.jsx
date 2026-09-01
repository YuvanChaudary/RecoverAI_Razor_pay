import React from 'react';
import { CheckCircle2, Clock, ShieldCheck, Zap, AlertTriangle, Lock } from 'lucide-react';

export default function RecoveryTimeline({ selectedCase }) {
  if (!selectedCase) return null;

  const steps = [
    {
      id: 'DETECTED',
      name: 'Payment Failure Ingested',
      desc: 'Ingested via Razorpay HMAC Webhook & persisted in PostgreSQL',
      completed: true,
      icon: Zap
    },
    {
      id: 'DIAGNOSED',
      name: 'Revenue Risk & AI Diagnosis',
      desc: `Category: ${selectedCase.failure_category} | AI Confidence: ${(selectedCase.ai_confidence * 100).toFixed(0)}%`,
      completed: true,
      icon: CheckCircle2
    },
    {
      id: 'GOVERNANCE',
      name: 'OPA Rego Policy Enforcement',
      desc: selectedCase.opa_decision === 'ALLOW' 
        ? 'OPA Evaluated: ALLOWED (Compliant with retry limits & cooldowns)' 
        : `OPA Evaluated: DENIED (${selectedCase.denial_reasons?.[0] || 'Vetoed'})`,
      completed: true,
      status: selectedCase.opa_decision === 'ALLOW' ? 'success' : 'blocked',
      icon: ShieldCheck
    },
    {
      id: 'ACTION_EXECUTED',
      name: 'Outbound API Action Executed',
      desc: selectedCase.opa_decision === 'ALLOW' 
        ? `Outbound action triggered: ${selectedCase.proposed_action}` 
        : 'Execution blocked by RegTech firewall',
      completed: selectedCase.opa_decision === 'ALLOW',
      status: selectedCase.opa_decision === 'ALLOW' ? 'success' : 'blocked',
      icon: Zap
    },
    {
      id: 'AWAITING_SETTLEMENT',
      name: 'Durable Sleep & Settlement Wait',
      desc: 'Temporal durable timer active. Waiting for external settlement evidence.',
      completed: selectedCase.current_state === 'RECOVERED' || selectedCase.current_state === 'AWAITING_SETTLEMENT',
      status: selectedCase.current_state === 'RECOVERED' ? 'success' : 'pending',
      icon: Clock
    },
    {
      id: 'RECOVERED',
      name: 'Authoritative Settlement Webhook',
      desc: selectedCase.current_state === 'RECOVERED'
        ? `Confirmed via payment.captured webhook. Recovered: ₹${(selectedCase.recovered_amount_paise / 100).toLocaleString('en-IN')}`
        : 'Awaiting verified payment.captured / invoice.paid signature payload',
      completed: selectedCase.current_state === 'RECOVERED',
      status: selectedCase.current_state === 'RECOVERED' ? 'success' : 'waiting',
      icon: Lock
    }
  ];

  return (
    <div className="space-y-6">
      
      {/* Demo Critical Disclaimer Banner */}
      <div className={`p-4 rounded-xl border flex items-start space-x-3 ${
        selectedCase.current_state === 'RECOVERED'
          ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
          : selectedCase.current_state === 'BLOCKED'
          ? 'bg-rose-500/10 border-rose-500/30 text-rose-300'
          : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
      }`}>
        <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
        <div className="text-xs space-y-1">
          <span className="font-bold uppercase tracking-wider block">
            Financial Authority & State Invariant Status
          </span>
          {selectedCase.current_state === 'RECOVERED' ? (
            <p>
              Authoritative recovery established via verified Razorpay settlement webhook payload (<code className="font-mono text-emerald-200">payment.captured</code>). 
              Recovered Amount: <strong className="font-mono font-bold text-emerald-200">₹{(selectedCase.recovered_amount_paise / 100).toLocaleString('en-IN')}</strong>.
            </p>
          ) : selectedCase.current_state === 'BLOCKED' ? (
            <p>
              Financial execution strictly blocked by OPA Rego governance firewall. AI confidence score ({selectedCase.ai_confidence * 100}%) cannot bypass OPA policies. 
              Recovered Amount: <strong className="font-mono font-bold text-rose-200">₹0.00</strong>.
            </p>
          ) : (
            <p>
              Outbound action executed successfully (<code className="font-mono text-amber-200">ACTION_EXECUTED</code>). 
              <strong> Recovery is NOT confirmed</strong> until an authoritative webhook is received. 
              Current Recovered Amount: <strong className="font-mono font-bold text-amber-200">₹0.00</strong>.
            </p>
          )}
        </div>
      </div>

      {/* Vertical Timeline Steps */}
      <div className="relative pl-6 space-y-6 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-800">
        {steps.map((step, idx) => {
          const StepIcon = step.icon;
          let dotColor = 'bg-slate-800 border-slate-700 text-slate-500';
          if (step.status === 'blocked') {
            dotColor = 'bg-rose-500/20 border-rose-500 text-rose-400 ring-4 ring-rose-500/10';
          } else if (step.completed) {
            dotColor = 'bg-emerald-500/20 border-emerald-500 text-emerald-400 ring-4 ring-emerald-500/10';
          } else if (step.status === 'pending') {
            dotColor = 'bg-amber-500/20 border-amber-500 text-amber-400 animate-pulse ring-4 ring-amber-500/10';
          }

          return (
            <div key={step.id} className="relative flex items-start space-x-4">
              <div className={`absolute -left-6 top-0 w-6 h-6 rounded-full border flex items-center justify-center ${dotColor}`}>
                <StepIcon className="w-3.5 h-3.5" />
              </div>
              <div className="glass-card p-3.5 rounded-lg flex-1 border border-slate-800">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-semibold text-slate-200">{step.name}</h4>
                  <span className="text-[10px] font-mono text-slate-500 uppercase">Step {idx + 1}</span>
                </div>
                <p className="text-[11px] text-slate-400 mt-1 font-sans">{step.desc}</p>
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
}
