import React, { useEffect, useState } from 'react';
import { TopNav } from '../components/TopNav';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { AgenticAnalysisPanel } from '../components/AgenticAnalysisPanel';
import { useAgenticAnalysis } from '../hooks/useAgenticAnalysis';
import { useAgenticContext } from '../context/AgenticContext';
import { AlertTriangle, Bot, RefreshCw } from 'lucide-react';
import { AgenticEngineToggle } from '../components/AgenticEngineToggle';
import { describeAgenticEngine, resolveAgenticEngineBase } from '../lib/agentic';

const scenarios = [
  {
    id: 'delay_3hr',
    title: '3hr delay program',
    description: 'Force weather-driven ground delay to test finance and risk outputs.',
  },
  {
    id: 'crew_out',
    title: 'Crew unavailable',
    description: 'Simulate multiple crews timing out to validate crew agent resiliency.',
  },
  {
    id: 'weather_groundstop',
    title: 'Weather ground stop',
    description: 'Inject typhoon band warnings and evaluate contingency planning.',
  },
];

export function AgenticDebugPanel() {
  const [scenario, setScenario] = useState<string>('delay_3hr');
  const {
    latestAnalysis,
    setLatestAnalysis,
    agenticEngine,
    monitorAirport,
    monitorCarrier,
    monitorMode,
  } = useAgenticContext();
  const agenticBaseOverride = resolveAgenticEngineBase(agenticEngine);
  const { analysis, loading, error, runAnalysis, status, checkStatus } = useAgenticAnalysis({
    airport: monitorAirport,
    carrier: monitorCarrier,
    mode: monitorMode,
    engine: agenticEngine,
    apiBaseOverride: agenticBaseOverride,
  });
  const activeAnalysis = analysis ?? latestAnalysis;
  const engineDescription = describeAgenticEngine(agenticEngine);
  const statusModelLabel = status?.current_model ?? status?.llm_model ?? 'n/a';
  const engineAvailable =
    status?.available_engines?.includes(agenticEngine) ?? true;
  const agenticSuspended = !engineAvailable;
  const agenticSuspendedReason = agenticSuspended
    ? `Backend does not expose the ${agenticEngine.toUpperCase()} engine`
    : undefined;

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  useEffect(() => {
    if (analysis) {
      setLatestAnalysis(analysis);
    }
  }, [analysis, setLatestAnalysis]);

  const handleRun = () => runAnalysis({ scenario });
  const subtitle = `${monitorAirport} · ${monitorCarrier} · ${
    monitorMode === 'synthetic' ? 'Synthetic payloads' : 'Realtime provider'
  }`;

  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      <TopNav
        title="Agentic Debug Panel"
        subtitle={subtitle}
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <AgenticEngineToggle
              selectedEngineAvailable={!agenticSuspended}
              warningMessage={agenticSuspendedReason}
            />
            {status && (
              <Badge variant={status.enabled ? 'secondary' : 'outline'}>
                {status.enabled ? `Model: ${statusModelLabel}` : 'Agentic disabled'}
              </Badge>
            )}
            <Button
              onClick={handleRun}
              disabled={loading || agenticSuspended}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Bot className="w-4 h-4 mr-2" />
              )}
              {loading ? 'Running' : 'Run scenario'}
            </Button>
          </div>
        }
      />

      <div className="p-8 space-y-6">
        <Badge variant="outline" className="w-fit">{engineDescription}</Badge>

        {agenticSuspended && (
          <Card className="p-4 border-amber-200 bg-amber-50/80 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            <p className="text-sm text-muted-foreground">
              {agenticSuspendedReason ??
                'Selected agent engine not available on backend. Switch engines or update backend configuration.'}
            </p>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-3">
          {scenarios.map((item) => (
            <Card
              key={item.id}
              onClick={() => setScenario(item.id)}
              className={`p-4 cursor-pointer border ${scenario === item.id ? 'border-indigo-400 shadow-md' : 'border-border'}`}
            >
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">{item.title}</h3>
                {scenario === item.id && <Badge variant="default">Selected</Badge>}
              </div>
              <p className="text-sm text-muted-foreground mt-2">{item.description}</p>
            </Card>
          ))}
        </div>

        {error && (
          <Card className="p-4 border border-destructive/40 bg-destructive/10">
            <p className="text-sm text-destructive">{error}</p>
          </Card>
        )}

        {activeAnalysis ? (
          <>
            {activeAnalysis.scenario && (
              <Badge variant="outline" className="uppercase tracking-wide text-xs">
                Scenario: {activeAnalysis.scenario}
              </Badge>
            )}
            <AgenticAnalysisPanel analysis={activeAnalysis} />

            {activeAnalysis.agentic_analysis.simulation_results.length > 0 && (
              <Card className="p-6">
                <h3 className="text-lg font-semibold mb-4">What-if outputs</h3>
                <div className="grid gap-4 md:grid-cols-2">
                  {activeAnalysis.agentic_analysis.simulation_results.map((sim) => (
                    <div key={sim.scenario} className="border border-indigo-100 rounded-lg p-4 bg-indigo-50/50">
                      <p className="text-xs uppercase text-indigo-600 font-semibold">{sim.scenario}</p>
                      <p className="text-sm text-gray-900 mt-1">{sim.plan.description}</p>
                      <ul className="text-xs text-gray-700 mt-2 space-y-1">
                        {sim.plan.actions.map((action) => (
                          <li key={action}>• {action}</li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </Card>
            )}
          </>
        ) : (
          <Card className="p-6 text-center border-dashed border-indigo-200">
            <p className="text-muted-foreground">
              Choose a scenario and run the workflow to inspect per-agent reasoning.
            </p>
          </Card>
        )}
      </div>
    </div>
  );
}
