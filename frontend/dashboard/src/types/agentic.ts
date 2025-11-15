import { MonitorMode } from '../hooks/useFlightMonitor';

export type AgenticEngine = 'apiv2';

export interface AuditLogEntry {
  agent: string;
  input: any;
  output: any;
  timestamp: string;
}

export interface PredictiveBreakdownEntry {
  category: string;
  score: number;
  evidence: string;
  impact_count: number;
}

export interface SignalBreakdownMap {
  [key: string]: {
    score: number;
    evidence: string;
    impact_count: number;
  };
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
  signal_breakdown?: SignalBreakdownMap;
  drivers?: PredictiveBreakdownEntry[];
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
  signal_breakdown?: SignalBreakdownMap;
}

export interface AgenticAnalysisResult {
  engine?: AgenticEngine | string;
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
  mode: MonitorMode | string;
  engine?: AgenticEngine | string;
  agentic_analysis: AgenticAnalysisResult;
  original_data: {
    stats: any;
    alerts: any[];
  };
  scenario?: string | null;
}

export interface AgenticStatus {
  enabled: boolean;
  current_engine?: AgenticEngine | string;
  available_engines?: string[];
  current_provider?: string;
  current_model?: string;
  temperature?: number;
  llm_model?: string;
  llm_temperature?: number;
  provider_configured?: boolean;
  api_key_configured?: boolean;
  mongo_configured?: boolean;
  providers?: Record<string, unknown>;
  apiv2_proxy?: {
    enabled: boolean;
    base_url?: string;
    analyze_path?: string;
    timeout?: number;
  };
}
