import type { AgenticEngine } from '../types/agentic';

const trimTrailingSlash = (value: string) => value.replace(/\/$/, '');

export const AGENTIC_ENGINE_OPTIONS: Array<{
  value: AgenticEngine;
  label: string;
  helper: string;
}> = [
  {
    value: 'langgraph',
    label: 'LangGraph (v1)',
    helper: 'FastAPI-hosted graph used for hackathon + regression',
  },
  {
    value: 'apiv2',
    label: 'APIV2 (Google A2A)',
    helper: 'Gemini + Amadeus pipeline described in google_a2a_agents_apiV2',
  },
];

export const isAgenticEngine = (value: unknown): value is AgenticEngine => {
  return value === 'langgraph' || value === 'apiv2';
};

export const coerceAgenticEngine = (
  value?: string | null,
): AgenticEngine | null => {
  if (!value) return null;
  const normalized = value.toLowerCase();
  return isAgenticEngine(normalized) ? normalized : null;
};

export const getDefaultAgenticEngine = (): AgenticEngine => {
  const envValue = (import.meta.env.VITE_AGENTIC_DEFAULT_ENGINE as
    | string
    | undefined)?.toLowerCase();
  return coerceAgenticEngine(envValue) ?? 'langgraph';
};

export const resolveAgenticEngineBase = (
  engine: AgenticEngine,
): string | undefined => {
  if (engine !== 'apiv2') return undefined;
  const envValue = import.meta.env.VITE_AGENTIC_APIV2_BASE as
    | string
    | undefined;
  return envValue ? trimTrailingSlash(envValue) : undefined;
};

export const describeAgenticEngine = (engine: AgenticEngine): string => {
  if (engine === 'apiv2') {
    return 'APIV2 · Google A2A Agents (Gemini + Amadeus)';
  }
  return 'LangGraph v1 · FastAPI workflow';
};
