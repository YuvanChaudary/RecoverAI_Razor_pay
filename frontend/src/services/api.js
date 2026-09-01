/**
 * API Service Abstraction Layer for RecoverAI Command Center
 * Interacts with FastAPI backend endpoints (/health, /ready, /metrics)
 * Provides deterministic simulation and demo data adapters when offline or in demo mode.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { status: 'unhealthy', error: err.message, timestamp: new Date().toISOString() };
  }
}

export async function fetchReadiness() {
  try {
    const res = await fetch(`${API_BASE_URL}/ready`);
    return { status: res.ok ? 'ready' : 'degraded', code: res.status };
  } catch (err) {
    return { status: 'offline', error: err.message };
  }
}

export async function fetchMetrics() {
  try {
    const res = await fetch(`${API_BASE_URL}/metrics`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const text = await res.text();
    return { status: 'available', raw: text };
  } catch (err) {
    return { status: 'unavailable', error: err.message };
  }
}

export async function resetDemoState() {
  try {
    const res = await fetch(`${API_BASE_URL}/demo/reset`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { success: true, state: 'READY', revenue_at_risk_paise: 0, recovered_amount_paise: 0 };
  }
}

export async function startDemoTransaction() {
  try {
    const res = await fetch(`${API_BASE_URL}/demo/start`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function fetchDemoStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/demo/status`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { success: true, state: 'READY', revenue_at_risk_paise: 0, recovered_amount_paise: 0 };
  }
}

export async function processAnotherTransaction() {
  try {
    const res = await fetch(`${API_BASE_URL}/demo/transaction`, { method: 'POST' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    return { success: false, error: err.message };
  }
}

export async function fetchDemoCases(page = 1, pageSize = 20, search = '', status = 'ALL') {
  try {
    const query = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
      search: search || '',
      status: status || 'ALL'
    });
    const res = await fetch(`${API_BASE_URL}/demo/cases?${query.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    // Fallback to static synthetic cases if backend endpoint unreachable
    const allSynthetic = getSyntheticRecoveryCases();
    return {
      success: true,
      items: allSynthetic,
      page: 1,
      page_size: pageSize,
      total: allSynthetic.length,
      total_pages: 1
    };
  }
}

/**
 * Phase 10 Deterministic Simulation Data Adapter
 */
export function getSimulationMetrics() {
  return {
    seed: 42,
    total_cases: 500,
    total_revenue_at_risk_paise: 2523842632, // ₹25,238,426.32
    simulated_recovered_paise: 856574532,    // ₹8,565,745.32
    recovery_rate_pct: 33.94,
    average_risk_per_case_paise: 5047685,     // ₹50,476.85
    average_recovered_per_case_paise: 1713149,// ₹17,131.49
    governance_allowed: 307,
    governance_denied: 193,
    allowed_rate_pct: 61.4,
    denied_rate_pct: 38.6,
    terminal_declines: 36,
    duplicate_events_tested: 50,
    double_recoveries: 0,
    unsafe_recovery_claims: 0,
    invariants_passed: true,
    failure_distribution: [
      { category: 'LIQUIDITY_FRICTION', count: 194, pct: 38.8, label: 'Liquidity Friction (Insufficient Balance)' },
      { category: 'TRANSIENT_INFRASTRUCTURE', count: 94, pct: 18.8, label: 'Transient Bank Network Timeout' },
      { category: 'INSTRUMENT_INVALIDATION', count: 76, pct: 15.2, label: 'Expired / Invalid Payment Instrument' },
      { category: 'MANDATE_COMPLIANCE_LOCK', count: 62, pct: 12.4, label: 'Mandate Limit / Compliance Lock' },
      { category: 'BANK_RISK_BLOCK', count: 42, pct: 8.4, label: 'Bank Risk Block / Hard Fraud Guard' },
      { category: 'UNKNOWN', count: 32, pct: 6.4, label: 'Uncategorized Gateway Error' },
    ],
    rule_violations: [
      { rule_id: 'RULE-001', name: 'Max Retries Exceeded (>=3)', violations: 40 },
      { rule_id: 'RULE-002', name: 'Cooldown Violation (<24h)', violations: 66 },
      { rule_id: 'RULE-003', name: 'Terminal Decline Retry Prohibited', violations: 36 },
      { rule_id: 'RULE-004', name: 'Low AI Confidence Score (<0.70)', violations: 24 },
      { rule_id: 'RULE-005', name: 'Pre-Debit Notice Requirement Missing', violations: 27 },
    ]
  };
}

/**
 * Representative Synthetic Recovery Cases (Read-Only)
 */
export function getSyntheticRecoveryCases() {
  const baseCategories = [
    { cat: 'LIQUIDITY_FRICTION', action: 'RETRY_SCHEDULED', opa: 'ALLOW', state: 'AWAITING_SETTLEMENT', amt: 1250000, conf: 0.94 },
    { cat: 'INSTRUMENT_INVALIDATION', action: 'CUSTOMER_REMINDER', opa: 'ALLOW', state: 'ACTION_EXECUTED', amt: 849000, conf: 0.88 },
    { cat: 'BANK_RISK_BLOCK', action: 'RETRY_SCHEDULED', opa: 'DENY', state: 'BLOCKED', amt: 4500000, conf: 0.99 },
    { cat: 'TRANSIENT_INFRASTRUCTURE', action: 'RETRY_SCHEDULED', opa: 'ALLOW', state: 'RECOVERED', amt: 499900, conf: 0.96 },
    { cat: 'MANDATE_COMPLIANCE_LOCK', action: 'RETRY_SCHEDULED', opa: 'DENY', state: 'BLOCKED', amt: 1850000, conf: 0.62 },
  ];

  const cases = [];
  for (let i = 1; i <= 20; i++) {
    const tmpl = baseCategories[(i - 1) % baseCategories.length];
    const caseNum = 1000 + i;
    const isRecovered = tmpl.state === 'RECOVERED';
    cases.push({
      case_id: `RC-${caseNum}`,
      payment_id: `pay_synth_${caseNum}`,
      customer_id: `cust_${80000 + i}`,
      failure_category: tmpl.cat,
      amount_paise: tmpl.amt + (i * 10000),
      ai_confidence: tmpl.conf,
      proposed_action: tmpl.action,
      opa_decision: tmpl.opa,
      current_state: tmpl.state,
      risk_tier: tmpl.amt > 2000000 ? 'HIGH' : 'MEDIUM',
      cooldown_hours: 24.0,
      retry_count: tmpl.opa === 'DENY' ? 5 : 1,
      timestamp: `2026-08-30T${10 - (i % 8)}:${(i * 3) % 60}:00Z`,
      recovered_amount_paise: isRecovered ? (tmpl.amt + (i * 10000)) : 0,
      waiting_reason: tmpl.opa === 'DENY' ? 'OPA Policy Veto' : 'Authoritative Razorpay settlement'
    });
  }
  return cases;
}


/**
 * immudb Synthetic Verification Receipt Data
 */
export function getImmudbProofRecords() {
  return [
    {
      event_id: 'evt_audit_001_p16',
      key: 'recoverai/audit/evt_audit_001_p16',
      type: 'STATE_TRANSITION',
      case_id: 'RC-1004',
      previous_state: 'AWAITING_SETTLEMENT',
      new_state: 'RECOVERED',
      payload_hash: 'f3b385434a4cc0a58f77d39659408a1386809e39b0db033f6e258b6da1f89dd9',
      integrity: 'VALID',
      timestamp: '2026-08-30T07:11:05Z'
    },
    {
      event_id: 'evt_audit_002_p16',
      key: 'recoverai/audit/evt_audit_002_p16',
      type: 'GOVERNANCE_DENIAL',
      case_id: 'RC-1003',
      previous_state: 'DIAGNOSED',
      new_state: 'BLOCKED',
      payload_hash: '9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b',
      integrity: 'VALID',
      timestamp: '2026-08-30T08:30:02Z'
    }
  ];
}
