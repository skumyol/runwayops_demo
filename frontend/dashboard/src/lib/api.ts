const trimTrailingSlash = (value: string) => value.replace(/\/$/, '');

export const resolveApiBase = (override?: string) => {
  if (override) return trimTrailingSlash(override);
  const envValue = import.meta.env.VITE_MONITOR_API as string | undefined;
  if (envValue) return trimTrailingSlash(envValue);
  if (typeof window !== 'undefined') return trimTrailingSlash(window.location.origin);
  return '';
};

export async function fetchJson<T>(path: string, init?: RequestInit, baseOverride?: string): Promise<T> {
  const base = resolveApiBase(baseOverride);
  const url = `${base}${path}`;
  const response = await fetch(url, init);
  if (!response.ok) {
    throw new Error(`Request failed with ${response.status}`);
  }
  return response.json() as Promise<T>;
}
