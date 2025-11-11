/**
 * Hook for fetching AI-generated reaccommodation options
 */

import { useCallback, useEffect, useState } from 'react';
import { fetchJson } from '../lib/api';
import { ReaccommodationOption } from '../types/reaccommodation';

interface AgentOptionsResponse {
  flightNumber: string;
  options: ReaccommodationOption[];
  source: string;
  provider: string;
  model: string;
  analysis_summary: {
    disruption_detected: boolean;
    risk_level: string;
    recommended_action: string;
    confidence: string;
  };
  timestamp: string;
}

interface UseAgentOptionsResult {
  agentOptions: ReaccommodationOption[];
  loading: boolean;
  error: string | null;
  analysisSummary: AgentOptionsResponse['analysis_summary'] | null;
  fetchAgentOptions: (flightNumber: string, passengerPnr?: string) => Promise<void>;
  clear: () => void;
}

export function useAgentOptions(): UseAgentOptionsResult {
  const [agentOptions, setAgentOptions] = useState<ReaccommodationOption[]>([]);
  const [analysisSummary, setAnalysisSummary] = useState<AgentOptionsResponse['analysis_summary'] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAgentOptions = useCallback(async (flightNumber: string, passengerPnr?: string) => {
    setLoading(true);
    setError(null);

    const startTime = performance.now();
    console.group('🤖 AI Options Generation Started');
    console.log('Flight:', flightNumber);
    if (passengerPnr) console.log('Passenger:', passengerPnr);
    console.log('Time:', new Date().toLocaleTimeString());
    console.groupEnd();

    try {
      const url = passengerPnr
        ? `/api/agent-options/passengers/${passengerPnr}/options`
        : `/api/agent-options/flights/${flightNumber}`;

      const result = await fetchJson<AgentOptionsResponse>(url);
      setAgentOptions(result.options);
      setAnalysisSummary(result.analysis_summary);

      const duration = ((performance.now() - startTime) / 1000).toFixed(1);
      
      console.group('✅ AI Options Generated');
      console.log(`⏱️  Duration: ${duration}s`);
      console.log(`📊 Provider: ${result.provider}/${result.model}`);
      console.log(`🎯 Options: ${result.options.length}`);
      console.log(`⚠️  Disruption: ${result.analysis_summary.disruption_detected ? 'DETECTED' : 'None'}`);
      console.log(`🛡️  Risk: ${result.analysis_summary.risk_level}`);
      console.log(`✨ Action: ${result.analysis_summary.recommended_action}`);
      console.log(`💯 Confidence: ${result.analysis_summary.confidence}`);
      console.table(result.options.map(opt => ({
        id: opt.id,
        route: opt.route,
        cabin: opt.cabin,
        seats: opt.seats,
        score: opt.trvScore,
        badges: opt.badges?.join(', ')
      })));
      console.groupEnd();

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get AI-generated options';
      setError(message);
      setAgentOptions([]);
      setAnalysisSummary(null);
      
      console.group('❌ AI Options Generation Failed');
      console.error('Error:', message);
      console.error('Details:', err);
      console.groupEnd();
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setAgentOptions([]);
    setAnalysisSummary(null);
    setError(null);
  }, []);

  return {
    agentOptions,
    loading,
    error,
    analysisSummary,
    fetchAgentOptions,
    clear,
  };
}
