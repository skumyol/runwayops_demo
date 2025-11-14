/**
 * Hook for AI-powered reaccommodation suggestions using the Google ADK (APIV2) agents.
 * 
 * This provides access to the multi-agent workflow analysis for specific flights,
 * giving real-time AI recommendations vs the static MongoDB options.
 */

import { useCallback, useState } from 'react';
import { fetchJson } from '../lib/api';

export interface AgentSuggestions {
  flightNumber: string;
  disruption_detected: boolean;
  recommended_action: string;
  priority: string;
  confidence: string;
  risk_level: string;
  estimated_cost: number;
  rebooking_strategy: string;
  affected_passengers: number;
  what_if_scenarios: Array<{
    scenario: string;
    plan: {
      description: string;
      actions: string[];
    };
  }>;
  reasoning: {
    risk: string;
    rebooking: string;
    finance: string;
  };
  passenger?: {
    pnr: string;
    name: string;
    tier: string;
    specific_recommendation: string;
  };
}

export interface AgentAnalysis {
  flightNumber: string;
  analysis: {
    final_plan: any;
    audit_log: Array<{
      agent: string;
      input: any;
      output: any;
      timestamp: string;
    }>;
    disruption_detected: boolean;
  };
  metadata: {
    provider: string;
    model: string;
    timestamp: string;
  };
}

export interface ComparisonResult {
  flightNumber: string;
  static: {
    source: string;
    count: number;
    options: any[];
  };
  ai_powered: {
    source: string;
    suggestions: AgentSuggestions;
  };
  comparison: {
    static_is_deterministic: boolean;
    ai_is_dynamic: boolean;
    ai_includes_reasoning: boolean;
    ai_includes_what_if: boolean;
  };
}

interface UseAgentReaccommodationResult {
  // State
  suggestions: AgentSuggestions | null;
  analysis: AgentAnalysis | null;
  comparison: ComparisonResult | null;
  loading: boolean;
  error: string | null;

  // Actions
  getSuggestions: (flightNumber: string, passengerPnr?: string) => Promise<void>;
  analyzeFlightWithAgents: (flightNumber: string, forceRefresh?: boolean) => Promise<void>;
  compareStaticVsAI: (flightNumber: string) => Promise<void>;
  clear: () => void;
}

export function useAgentReaccommodation(): UseAgentReaccommodationResult {
  const [suggestions, setSuggestions] = useState<AgentSuggestions | null>(null);
  const [analysis, setAnalysis] = useState<AgentAnalysis | null>(null);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getSuggestions = useCallback(async (flightNumber: string, passengerPnr?: string) => {
    setLoading(true);
    setError(null);
    setSuggestions(null);

    try {
      const url = passengerPnr
        ? `/api/agent-reaccommodation/suggestions/${flightNumber}?passenger_pnr=${passengerPnr}`
        : `/api/agent-reaccommodation/suggestions/${flightNumber}`;

      const result = await fetchJson<AgentSuggestions>(url);
      setSuggestions(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get AI suggestions';
      setError(message);
      console.error('Error getting agent suggestions:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const analyzeFlightWithAgents = useCallback(async (flightNumber: string, forceRefresh = false) => {
    setLoading(true);
    setError(null);
    setAnalysis(null);

    const startTime = performance.now();
    console.group('🤖 Agent Analysis Started');
    console.log('Flight:', flightNumber);
    console.log('Force Refresh:', forceRefresh);
    console.log('Time:', new Date().toLocaleTimeString());
    console.groupEnd();

    try {
      const url = forceRefresh
        ? `/api/agent-reaccommodation/analyze/${flightNumber}?force_refresh=true`
        : `/api/agent-reaccommodation/analyze/${flightNumber}`;

      const result = await fetchJson<AgentAnalysis>(url, {
        method: 'POST',
      });
      setAnalysis(result);

      const duration = ((performance.now() - startTime) / 1000).toFixed(1);
      const auditLog = result.analysis?.audit_log || [];
      
      console.group('✅ Agent Analysis Complete');
      console.log(`⏱️  Duration: ${duration}s`);
      console.log(`📊 Provider: ${result.metadata?.provider}/${result.metadata?.model}`);
      console.log(`🔢 Agents Executed: ${auditLog.length}`);
      console.log(`⚠️  Disruption: ${result.analysis?.disruption_detected ? 'DETECTED' : 'None'}`);
      console.log(`🎯 Final Plan:`, result.analysis?.final_plan);
      console.log('');
      console.log('📋 Agent Execution Flow:');
      auditLog.forEach((entry: any, idx: number) => {
        const icon = entry.agent === 'Predictive' ? '🧠' :
                    entry.agent === 'Orchestrator' ? '✨' :
                    entry.agent === 'Risk' ? '🛡️' :
                    entry.agent === 'Rebooking' ? '✈️' :
                    entry.agent === 'Finance' ? '💰' :
                    entry.agent === 'Crew' ? '👥' :
                    entry.agent === 'Aggregator' ? '📊' : '🤖';
        console.log(`  ${idx + 1}. ${icon} ${entry.agent}:`, entry.output?.reasoning || JSON.stringify(entry.output).slice(0, 100));
      });
      console.log('');
      console.log('💡 View full details in "View Agent Analysis" modal');
      console.groupEnd();

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to analyze with agents';
      setError(message);
      
      console.group('❌ Agent Analysis Failed');
      console.error('Error:', message);
      console.error('Details:', err);
      console.groupEnd();
    } finally {
      setLoading(false);
    }
  }, []);

  const compareStaticVsAI = useCallback(async (flightNumber: string) => {
    setLoading(true);
    setError(null);
    setComparison(null);

    try {
      const result = await fetchJson<ComparisonResult>(
        `/api/agent-reaccommodation/compare/${flightNumber}`
      );
      setComparison(result);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to compare options';
      setError(message);
      console.error('Error comparing static vs AI:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setSuggestions(null);
    setAnalysis(null);
    setComparison(null);
    setError(null);
  }, []);

  return {
    suggestions,
    analysis,
    comparison,
    loading,
    error,
    getSuggestions,
    analyzeFlightWithAgents,
    compareStaticVsAI,
    clear,
  };
}
