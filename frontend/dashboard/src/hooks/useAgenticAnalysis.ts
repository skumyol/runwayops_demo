import { useCallback, useState } from 'react';
import { resolveApiBase } from '../lib/api';

export interface AuditLogEntry {
  agent: string;
  input: any;
  output: any;
  timestamp: string;
}

export interface RiskAssessment {
  risk_probability: number;
  likelihood?: number;
  duration_minutes?: number;
  pax_impact?: string;
  regulatory_risk?: string;
  reasoning: string;
  metrics?: {
    total_flights: number;
    delayed_flights: number;
    critical_flights: number;
    avg_delay_minutes: number;
  };
}

export interface RebookingPlan {
  strategy: string;
  hotel_required: boolean;
  vip_priority: boolean;
  estimated_pax: number;
  actions: string[];
  reasoning: string;
}

export interface FinanceEstimate {
  compensation_usd: number;
  hotel_meals_usd: number;
  operational_usd: number;
  total_usd: number;
  breakdown: string[];
  reasoning: string;
}

export interface CrewRotation {
  crew_changes_needed: boolean;
  backup_crew_required: number;
  regulatory_issues: string[];
  actions: string[];
  reasoning: string;
}

export interface WhatIfScenario {
  scenario: string;
  plan: {
    description: string;
    actions: string[];
  };
}

export interface FinalPlan {
  disruption_detected: boolean;
  risk_assessment: RiskAssessment;
  rebooking_plan: RebookingPlan;
  finance_estimate: FinanceEstimate;
  crew_rotation: CrewRotation;
  what_if_scenarios: WhatIfScenario[];
  recommended_action: string;
  confidence: string;
  priority?: string;
  generated_at: string | null;
}

export interface AgenticAnalysisResult {
  final_plan: FinalPlan;
  audit_log: AuditLogEntry[];
  disruption_detected: boolean;
  risk_assessment: RiskAssessment;
  rebooking_plan: RebookingPlan;
  finance_estimate: FinanceEstimate;
  crew_rotation: CrewRotation;
  simulation_results: WhatIfScenario[];
}

export interface AgenticAnalysisResponse {
  airport: string;
  carrier: string;
  mode: string;
  agentic_analysis: AgenticAnalysisResult;
  original_data: {
    stats: any;
    alerts: any[];
  };
}

export interface AgenticStatus {
  enabled: boolean;
  llm_model: string;
  llm_temperature: number;
  api_key_configured: boolean;
  mongo_configured: boolean;
}

interface UseAgenticAnalysisArgs {
  airport: string;
  carrier: string;
  mode?: string;
  apiBaseOverride?: string;
}

interface UseAgenticAnalysisResult {
  analysis: AgenticAnalysisResponse | null;
  loading: boolean;
  error: string | null;
  runAnalysis: () => Promise<void>;
  status: AgenticStatus | null;
  checkStatus: () => Promise<void>;
}

export function useAgenticAnalysis({
  airport,
  carrier,
  mode,
  apiBaseOverride,
}: UseAgenticAnalysisArgs): UseAgenticAnalysisResult {
  const [analysis, setAnalysis] = useState<AgenticAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<AgenticStatus | null>(null);

  const checkStatus = useCallback(async () => {
    const base = resolveApiBase(apiBaseOverride);
    const url = `${base}/api/agentic/status`;

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Status check failed: ${response.status}`);
      }
      const statusData: AgenticStatus = await response.json();
      setStatus(statusData);
    } catch (err) {
      console.error('Failed to check agentic status:', err);
      const message = err instanceof Error ? err.message : 'Unable to check status';
      setError(message);
    }
  }, [apiBaseOverride]);

  const runAnalysis = useCallback(async () => {
    setLoading(true);
    setError(null);

    const base = resolveApiBase(apiBaseOverride);
    const params = new URLSearchParams({
      airport: airport.toUpperCase(),
      carrier: carrier.toUpperCase(),
    });
    if (mode) {
      params.append('mode', mode);
    }
    const url = `${base}/api/agentic/analyze?${params.toString()}`;

    try {
      const response = await fetch(url, { method: 'POST' });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          errorData.detail || `Analysis failed: ${response.status}`
        );
      }
      const result: AgenticAnalysisResponse = await response.json();
      setAnalysis(result);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : 'Unable to run agentic analysis';
      setError(message);
      setAnalysis(null);
    } finally {
      setLoading(false);
    }
  }, [airport, carrier, mode, apiBaseOverride]);

  return {
    analysis,
    loading,
    error,
    runAnalysis,
    status,
    checkStatus,
  };
}
