import { useCallback, useEffect, useState } from 'react';
import { resolveApiBase } from '../lib/api';
import {
  AgenticAnalysisResponse,
  AgenticStatus,
  AgenticEngine,
} from '../types/agentic';
import { MonitorMode } from './useFlightMonitor';

interface UseAgenticAnalysisArgs {
  airport: string;
  carrier: string;
  mode?: MonitorMode | string;
  apiBaseOverride?: string;
  engine?: AgenticEngine | string;
  suspended?: boolean;
  suspendedReason?: string;
}

export interface RunAnalysisOptions {
  scenario?: string | null;
}

interface UseAgenticAnalysisResult {
  analysis: AgenticAnalysisResponse | null;
  loading: boolean;
  error: string | null;
  runAnalysis: (options?: RunAnalysisOptions) => Promise<void>;
  status: AgenticStatus | null;
  checkStatus: () => Promise<void>;
}

export function useAgenticAnalysis({
  airport,
  carrier,
  mode,
  apiBaseOverride,
  engine,
  suspended = false,
  suspendedReason,
}: UseAgenticAnalysisArgs): UseAgenticAnalysisResult {
  const [analysis, setAnalysis] = useState<AgenticAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<AgenticStatus | null>(null);

  useEffect(() => {
    setAnalysis(null);
    setError(null);
    setStatus(null);
  }, [apiBaseOverride, engine]);

  const checkStatus = useCallback(async () => {
    if (suspended) {
      setStatus(null);
      setError(
        suspendedReason ?? 'Agentic analysis is temporarily unavailable',
      );
      return;
    }

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
  }, [apiBaseOverride, suspended, suspendedReason]);

  const runAnalysis = useCallback(async (options?: RunAnalysisOptions) => {
    if (suspended) {
      setAnalysis(null);
      setError(
        suspendedReason ?? 'Agentic analysis is temporarily unavailable',
      );
      setLoading(false);
      return;
    }

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
    if (options?.scenario) {
      params.append('scenario', options.scenario);
    }
    if (engine) {
      params.append('engine', engine);
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
  }, [airport, carrier, mode, apiBaseOverride, suspended, suspendedReason]);

  return {
    analysis,
    loading,
    error,
    runAnalysis,
    status,
    checkStatus,
  };
}
