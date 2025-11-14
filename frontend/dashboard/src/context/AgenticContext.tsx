import React, { createContext, useContext, useState } from 'react';
import { AgenticAnalysisResponse, AgenticEngine } from '../types/agentic';
import {
  coerceAgenticEngine,
  getDefaultAgenticEngine,
} from '../lib/agentic';
import { MonitorMode } from '../hooks/useFlightMonitor';

interface AgenticContextValue {
  latestAnalysis: AgenticAnalysisResponse | null;
  setLatestAnalysis: (analysis: AgenticAnalysisResponse | null) => void;
  agenticEngine: AgenticEngine;
  setAgenticEngine: (engine: AgenticEngine) => void;
  monitorAirport: string;
  setMonitorAirport: (airport: string) => void;
  monitorCarrier: string;
  setMonitorCarrier: (carrier: string) => void;
  monitorMode: MonitorMode;
  setMonitorMode: (mode: MonitorMode) => void;
}

const AgenticContext = createContext<AgenticContextValue | undefined>(undefined);

const DEFAULT_AIRPORT =
  (import.meta.env.VITE_DEFAULT_AIRPORT as string | undefined)?.toUpperCase() ||
  'HKG';
const DEFAULT_CARRIER =
  (import.meta.env.VITE_DEFAULT_CARRIER as string | undefined)?.toUpperCase() ||
  'CX';
const DEFAULT_MONITOR_MODE = (
  import.meta.env.VITE_DEFAULT_MONITOR_MODE as MonitorMode | undefined
)?.toLowerCase() === 'realtime'
  ? 'realtime'
  : 'synthetic';

const storageKeys = {
  engine: 'agentic-engine',
  airport: 'agentic-monitor-airport',
  carrier: 'agentic-monitor-carrier',
  mode: 'agentic-monitor-mode',
} as const;

const readStorage = (key: string): string | null => {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
};

const writeStorage = (key: string, value: string) => {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    // Ignore quota errors
  }
};

export function AgenticProvider({ children }: { children: React.ReactNode }) {
  const [latestAnalysis, setLatestAnalysis] = useState<AgenticAnalysisResponse | null>(null);
  const [agenticEngine, setAgenticEngineState] = useState<AgenticEngine>(() => {
    if (typeof window !== 'undefined') {
      try {
        const stored = coerceAgenticEngine(readStorage(storageKeys.engine));
        if (stored) {
          return stored;
        }
      } catch {
        // Ignore storage read errors and fall back to defaults
      }
    }
    return getDefaultAgenticEngine();
  });
  const [monitorAirport, setMonitorAirportState] = useState<string>(() => {
    return readStorage(storageKeys.airport)?.toUpperCase() || DEFAULT_AIRPORT;
  });
  const [monitorCarrier, setMonitorCarrierState] = useState<string>(() => {
    return readStorage(storageKeys.carrier)?.toUpperCase() || DEFAULT_CARRIER;
  });
  const [monitorMode, setMonitorModeState] = useState<MonitorMode>(() => {
    const stored = readStorage(storageKeys.mode);
    return stored === 'realtime' ? 'realtime' : DEFAULT_MONITOR_MODE;
  });

  const setAgenticEngine = (engine: AgenticEngine) => {
    setAgenticEngineState(engine);
    writeStorage(storageKeys.engine, engine);
  };

  const setMonitorAirport = (airport: string) => {
    const value = airport.trim().toUpperCase() || DEFAULT_AIRPORT;
    setMonitorAirportState(value);
    writeStorage(storageKeys.airport, value);
  };

  const setMonitorCarrier = (carrier: string) => {
    const value = carrier.trim().toUpperCase() || DEFAULT_CARRIER;
    setMonitorCarrierState(value);
    writeStorage(storageKeys.carrier, value);
  };

  const setMonitorMode = (mode: MonitorMode) => {
    const normalized = mode === 'realtime' ? 'realtime' : 'synthetic';
    setMonitorModeState(normalized);
    writeStorage(storageKeys.mode, normalized);
  };

  return (
    <AgenticContext.Provider
      value={{
        latestAnalysis,
        setLatestAnalysis,
        agenticEngine,
        setAgenticEngine,
        monitorAirport,
        setMonitorAirport,
        monitorCarrier,
        setMonitorCarrier,
        monitorMode,
        setMonitorMode,
      }}
    >
      {children}
    </AgenticContext.Provider>
  );
}

export function useAgenticContext(): AgenticContextValue {
  const ctx = useContext(AgenticContext);
  if (!ctx) {
    throw new Error('useAgenticContext must be used within an AgenticProvider');
  }
  return ctx;
}
