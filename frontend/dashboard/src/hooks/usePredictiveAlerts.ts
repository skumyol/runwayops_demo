import { useState, useCallback } from 'react';

export interface PredictiveDriver {
  category: string;
  score: number;
  evidence: string;
}

export interface PredictiveAlert {
  riskProbability: number;
  severity: 'low' | 'medium' | 'high';
  drivers: PredictiveDriver[];
  recommendations: string[];
  timestamp: string;
  prediction?: string;
  reasoning?: string;
}

export interface PredictiveAlertResponse {
  flightNumber: string;
  hasPredictiveAlert: boolean;
  alert?: PredictiveAlert;
  flightStatus?: {
    statusCategory: string;
    status: string;
    delayMinutes: number;
    paxImpacted: number;
  };
  message?: string;
  generalSignals?: any;
}

export function usePredictiveAlerts() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alertData, setAlertData] = useState<PredictiveAlertResponse | null>(null);

  const fetchAlerts = useCallback(
    async (flightNumber: string, airport: string = 'HKG', carrier: string = 'CX', mode: string = 'synthetic') => {
      setLoading(true);
      setError(null);

      try {
        const apiBase = (import.meta as any).env?.VITE_MONITOR_API || 'http://localhost:8000';
        const url = `${apiBase}/api/predictive-alerts/${flightNumber}?airport=${airport}&carrier=${carrier}&mode=${mode}`;

        const response = await fetch(url);

        if (!response.ok) {
          throw new Error(`Failed to fetch predictive alerts: ${response.statusText}`);
        }

        const data: PredictiveAlertResponse = await response.json();
        setAlertData(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Unknown error occurred';
        setError(message);
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    loading,
    error,
    alertData,
    fetchAlerts,
  };
}
