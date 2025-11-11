import { useCallback, useEffect, useState } from 'react';
import { fetchJson } from '../lib/api';
import {
  FlightManifestResponse,
  FlightQueueResponse,
  PassengerDetailResponse,
  FlightSummary,
} from '../types/reaccommodation';

interface AsyncState<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

const initialState = <T,>(): AsyncState<T> => ({
  data: null,
  loading: true,
  error: null,
});

export function useReaccommodationFlights() {
  const [state, setState] = useState<AsyncState<FlightSummary[]>>(() => initialState<FlightSummary[]>());

  const fetchFlights = useCallback(async () => {
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const response = await fetchJson<FlightQueueResponse>('/api/reaccommodation/flights');
      setState({ data: response.flights, loading: false, error: null });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load flights';
      setState({ data: [], loading: false, error: message });
    }
  }, []);

  useEffect(() => {
    fetchFlights();
  }, [fetchFlights]);

  return {
    flights: state.data ?? [],
    loading: state.loading,
    error: state.error,
    refresh: fetchFlights,
  };
}

export function useFlightManifest(flightNumber?: string | null) {
  const [state, setState] = useState<AsyncState<FlightManifestResponse>>(() => initialState<FlightManifestResponse>());

  const fetchManifest = useCallback(async () => {
    if (!flightNumber) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const response = await fetchJson<FlightManifestResponse>(`/api/reaccommodation/flights/${flightNumber}/manifest`);
      setState({ data: response, loading: false, error: null });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load manifest';
      setState({ data: null, loading: false, error: message });
    }
  }, [flightNumber]);

  useEffect(() => {
    fetchManifest();
  }, [fetchManifest]);

  return {
    manifest: state.data,
    loading: state.loading,
    error: state.error,
    refresh: fetchManifest,
  };
}

export function usePassengerDetail(pnr?: string | null) {
  const [state, setState] = useState<AsyncState<PassengerDetailResponse>>(() => initialState<PassengerDetailResponse>());

  const fetchPassenger = useCallback(async () => {
    if (!pnr) {
      setState({ data: null, loading: false, error: null });
      return;
    }
    setState((prev) => ({ ...prev, loading: true, error: null }));
    try {
      const response = await fetchJson<PassengerDetailResponse>(`/api/reaccommodation/passengers/${pnr}`);
      setState({ data: response, loading: false, error: null });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unable to load passenger detail';
      setState({ data: null, loading: false, error: message });
    }
  }, [pnr]);

  useEffect(() => {
    fetchPassenger();
  }, [fetchPassenger]);

  return {
    detail: state.data,
    loading: state.loading,
    error: state.error,
    refresh: fetchPassenger,
  };
}
