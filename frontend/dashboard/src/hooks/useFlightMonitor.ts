import { useCallback, useEffect, useRef, useState } from 'react';
import { resolveApiBase } from '../lib/api';

export type StatusCategory = 'normal' | 'warning' | 'critical';
export type CrewReadinessState = 'ready' | 'standby' | 'hold';
export type CrewFatigueRisk = 'low' | 'medium' | 'high';

export interface FlightMonitorMilestone {
  label: string;
  state: 'complete' | 'active' | 'pending';
}

export interface FlightMonitorAlert {
  level: StatusCategory;
  flightNumber: string;
  message: string;
  gate: string;
  delayMinutes: number;
  paxImpacted: number;
  recommendedAction: string;
}

export interface FlightMonitorFlight {
  flightNumber: string;
  route: string;
  destination: string;
  status: string;
  statusCategory: StatusCategory;
  statusColor: string;
  scheduledDeparture: string;
  estimatedDeparture: string;
  estimatedArrival: string;
  gate: string;
  standbyGate: string;
  tailNumber: string;
  aircraft: string;
  paxCount: number;
  premiumPax: number;
  loadFactor: number;
  connections: { tight: number; missed: number; vip: number };
  delayMinutes: number;
  turnProgress: number;
  crewReady: boolean;
  aircraftReady: boolean;
  groundReady: boolean;
  paxImpacted: number;
  irregularOps: { reason: string; actions: string[] };
  milestones: FlightMonitorMilestone[];
  baggageStatus: string;
  fuelStatus: string;
  lastUpdated: string;
}

export interface FlightMonitorStats {
  totalFlights: number;
  onTime: number;
  delayed: number;
  critical: number;
  avgDelayMinutes: number;
  paxImpacted: number;
  crewReadyRate: number;
  aircraftReadyRate: number;
  turnReliability: number;
}

export interface FlightMonitorTrend {
  movementsPerHour: number[];
  avgDelay: number[];
  loadFactor: number[];
}

export type MonitorMode = 'synthetic' | 'realtime';

export interface CrewPanel {
  employeeId: string;
  name: string;
  rank: string;
  flightNumber: string;
  aircraftType: string;
  tailNumber: string | null;
  dutyStatus: string;
  readinessState: CrewReadinessState;
  currentDutyPhase: string;
  fatigueRisk: CrewFatigueRisk;
  fdpRemainingHours: number;
  base: string;
  contactPhone?: string | null;
  contactEmail?: string | null;
  availabilityNote?: string | null;
  statusNote?: string | null;
  commsPreference?: string | null;
  lastUpdated: string | null;
}

export interface AircraftPanel {
  tailNumber: string;
  type: string;
  status: string;
  statusCategory: StatusCategory;
  statusColor: string;
  flightNumber: string | null;
  gate: string | null;
  standbyGate: string | null;
  nextDeparture: string | null;
  lastACheck: string | null;
  lastCCheck: string | null;
  statusNotes: string | null;
  lastUpdated: string | null;
}

export interface FlightMonitorPayload {
  mode: MonitorMode;
  airport: string;
  carrier: string;
  timezone: string;
  generatedAt: string;
  nextUpdateSeconds: number;
  stats: FlightMonitorStats;
  alerts: FlightMonitorAlert[];
  flights: FlightMonitorFlight[];
  trend: FlightMonitorTrend;
  crewPanels: CrewPanel[];
  aircraftPanels: AircraftPanel[];
  crewPanelsNote?: string | null;
  aircraftPanelsNote?: string | null;
  fallbackReason?: string;
}

interface UseFlightMonitorArgs {
  airport: string;
  carrier: string;
  mode?: MonitorMode;
  apiBaseOverride?: string;
}

interface UseFlightMonitorResult {
  data: FlightMonitorPayload | null;
  loading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  lastUpdated: string | null;
  isRefreshing: boolean;
}

const REFRESH_INTERVAL_MS = 30_000;

export function useFlightMonitor({ airport, carrier, apiBaseOverride, mode }: UseFlightMonitorArgs): UseFlightMonitorResult {
  const [data, setData] = useState<FlightMonitorPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const controllerRef = useRef<AbortController | null>(null);
  const hasLoadedRef = useRef(false);

  const fetchData = useCallback(async () => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;

    setError(null);
    if (hasLoadedRef.current) {
      setIsRefreshing(true);
    } else {
      setLoading(true);
    }

    const base = resolveApiBase(apiBaseOverride);
    const params = new URLSearchParams({
      airport: airport.toUpperCase(),
      carrier: carrier.toUpperCase(),
    });
    if (mode) {
      params.append('mode', mode);
    }
    const url = `${base}/api/flight-monitor?${params.toString()}`;

    try {
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) {
        throw new Error(`API returned ${response.status}`);
      }
      const payload: FlightMonitorPayload = await response.json();
      setData(payload);
      setLastUpdated(payload.generatedAt);
      hasLoadedRef.current = true;
    } catch (err) {
      if ((err as DOMException)?.name === 'AbortError') {
        return;
      }
      const message = err instanceof Error ? err.message : 'Unable to load realtime data';
      setError(message);
    } finally {
      setLoading(false);
      setIsRefreshing(false);
    }
  }, [airport, carrier, apiBaseOverride, mode]);

  useEffect(() => {
    fetchData();
    const intervalId = window.setInterval(fetchData, REFRESH_INTERVAL_MS);
    return () => {
      controllerRef.current?.abort();
      window.clearInterval(intervalId);
    };
  }, [fetchData]);

  const handleManualRefresh = useCallback(async () => {
    await fetchData();
  }, [fetchData]);

  return {
    data,
    loading,
    error,
    refresh: handleManualRefresh,
    lastUpdated,
    isRefreshing,
  };
}
