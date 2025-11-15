import React, { useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Label } from '../components/ui/label';
import { Slider } from '../components/ui/slider';
import { Badge } from '../components/ui/badge';
import { AlertTriangle, TrendingUp, DollarSign, Users, Zap, RefreshCw } from 'lucide-react';
import { useFlightMonitor } from '../hooks/useFlightMonitor';
import { toast } from 'sonner';

interface WhatIfScenario {
  flight_number: string;
  delay_minutes?: number;
  weather_impact?: 'none' | 'minor' | 'moderate' | 'severe';
  crew_unavailable?: number;
  aircraft_issue?: boolean;
  passenger_count_change?: number;
  connection_pressure?: 'low' | 'medium' | 'high';
}

interface WhatIfScenarioProps {
  initialResults?: any | null;
  initialProgress?: any[];
  onResultsChange?: (results: any | null) => void;
  onProgressChange?: (updates: any[]) => void;
}

export function WhatIfScenario({
  initialResults = null,
  initialProgress = [],
  onResultsChange,
  onProgressChange,
}: WhatIfScenarioProps) {
  const { data, loading } = useFlightMonitor({
    airport: 'HKG',
    carrier: 'CX',
    mode: 'synthetic',
  });
  const [selectedFlight, setSelectedFlight] = useState<string>('');
  const [scenario, setScenario] = useState<WhatIfScenario>({
    flight_number: '',
  });
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState<any>(initialResults ?? null);
  const [progressUpdates, setProgressUpdates] = useState<any[]>(initialProgress ?? []);
  const agenticAnalysis = results?.agentic_analysis || null;
  const timelineUpdates = progressUpdates.length > 0
    ? progressUpdates
    : agenticAnalysis?.progress_updates || [];
  const agentTimeline = React.useMemo(() => {
    const latestByAgent: Record<string, any> = {};
    for (const item of timelineUpdates) {
      if (!item || !item.agent) continue;
      latestByAgent[item.agent] = item;
    }
    const order = [
      'Workflow',
      'PredictiveAgent',
      'OrchestratorAgent',
      'SubAgents',
      'RiskAgent',
      'RebookingAgent',
      'FinanceAgent',
      'CrewAgent',
      'AggregatorAgent',
    ];
    const entries = Object.values(latestByAgent);
    return entries.sort((a: any, b: any) => {
      const ai = order.indexOf(a.agent);
      const bi = order.indexOf(b.agent);
      if (ai === -1 && bi === -1) return 0;
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });
  }, [timelineUpdates]);

  const flights = data?.flights || [];
  const selectedFlightData = flights.find(f => f.flightNumber === selectedFlight);

  const baselineDelay = selectedFlightData?.delayMinutes || 0;
  const baselinePax = selectedFlightData?.paxImpacted || 0;
  const extraDelay = scenario.delay_minutes || 0;
  const paxDelta = scenario.passenger_count_change || 0;
  const effectiveDelay = baselineDelay + extraDelay;
  const effectivePax = Math.max(0, baselinePax + paxDelta);

  const weatherDescriptions: Record<NonNullable<WhatIfScenario['weather_impact']>, string> = {
    none: 'None (no additional weather risk)',
    minor: 'Minor (light weather impact, minimal risk)',
    moderate: 'Moderate (significant WX, monitor closely)',
    severe: 'Severe (major WX disruption likely)',
  };

  const connectionDescriptions: Record<NonNullable<WhatIfScenario['connection_pressure']>, string> = {
    low: 'Low (few tight connections)',
    medium: 'Medium (some tight / at-risk connections)',
    high: 'High (many tight/missed connections)',
  };

  const handleAnalyze = async () => {
    if (!selectedFlight) {
      toast.error('Please select a flight');
      return;
    }

    setAnalyzing(true);
    setResults(null);
    setProgressUpdates([]);
    if (onResultsChange) onResultsChange(null);
    if (onProgressChange) onProgressChange([]);

    try {
      const apiBase = (import.meta as any).env?.VITE_MONITOR_API || 'http://localhost:8000';
      
      // Build query params with scenario data
      const params = new URLSearchParams({
        flight_number: selectedFlight,
        airport: 'HKG',
        carrier: 'CX',
        mode: 'synthetic',
      });
      
      // Add optional scenario params
      if (scenario.delay_minutes) params.append('delay_minutes', scenario.delay_minutes.toString());
      if (scenario.weather_impact) params.append('weather_impact', scenario.weather_impact);
      if (scenario.crew_unavailable) params.append('crew_unavailable', scenario.crew_unavailable.toString());
      if (scenario.aircraft_issue) params.append('aircraft_issue', 'true');
      if (scenario.passenger_count_change) params.append('passenger_count_change', scenario.passenger_count_change.toString());
      if (scenario.connection_pressure) params.append('connection_pressure', scenario.connection_pressure);
      
      // Create SSE connection
      console.log('🔗 Connecting to SSE:', `${apiBase}/api/whatif/analyze-stream?${params.toString()}`);
      const eventSource = new EventSource(
        `${apiBase}/api/whatif/analyze-stream?${params.toString()}`
      );
      
      // Store progress updates as they arrive (in state)
      eventSource.addEventListener('start', (event) => {
        console.log('🚀 Analysis started:', event.data);
        toast.info('Analysis started...');
      });
      
      eventSource.addEventListener('progress', (event) => {
        const progress = JSON.parse(event.data);
        console.log('📊 Progress:', progress);
        setProgressUpdates((prev) => {
          const next = [...prev, progress];
          console.log('🔄 progressUpdates length =', next.length);
          if (onProgressChange) onProgressChange(next);
          return next;
        });
        
        // Show toast for major milestones
        if (progress.agent === 'PredictiveAgent' && progress.status === 'complete') {
          toast.info('Risk analysis complete');
        } else if (progress.agent === 'FinanceAgent' && progress.status === 'complete') {
          toast.info('Cost calculation complete');
        }
      });
      
      eventSource.addEventListener('complete', (event) => {
        const data = JSON.parse(event.data);
        console.log('✅ Analysis complete:', data);
        console.log('📈 Final progress updates:', data?.agentic_analysis?.progress_updates);
        setResults(data);
        setProgressUpdates(data?.agentic_analysis?.progress_updates || []);
        if (onResultsChange) onResultsChange(data);
        if (onProgressChange) onProgressChange(data?.agentic_analysis?.progress_updates || []);
        toast.success('What-if analysis complete!');
        setAnalyzing(false);
        eventSource.close();
      });
      
      eventSource.addEventListener('error', (event: any) => {
        console.error('❌ SSE error:', event);
        if (event.data) {
          try {
            const error = JSON.parse(event.data);
            toast.error(error.error || 'Analysis failed');
          } catch {
            toast.error('Analysis failed. Check console for details.');
          }
        } else {
          toast.error('Connection error. Please try again.');
        }
        setAnalyzing(false);
        eventSource.close();
      });
      
    } catch (error) {
      console.error('What-if analysis failed:', error);
      toast.error('Analysis failed. Check console for details.');
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setScenario({ flight_number: selectedFlight });
    setResults(null);
    setProgressUpdates([]);
    if (onResultsChange) onResultsChange(null);
    if (onProgressChange) onProgressChange([]);
  };

  return (
    <div className="min-h-screen bg-[#EBEDEC] p-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">What-If Scenario Analysis</h1>
            <p className="text-muted-foreground mt-1">
              Test different scenarios and see predicted outcomes without affecting actual flights
            </p>
          </div>
          <Badge variant="outline" className="text-lg px-4 py-2">
            <Zap className="w-4 h-4 mr-2" />
            AI-Powered Simulation
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Scenario Configuration */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Configure Scenario</h2>

            <div className="space-y-4">
              {/* Flight Selection */}
              <div>
                <Label>Select Flight</Label>
                <Select value={selectedFlight} onValueChange={setSelectedFlight}>
                  <SelectTrigger>
                    <SelectValue placeholder="Choose a flight" />
                  </SelectTrigger>
                  <SelectContent>
                    {flights.map((flight: any) => (
                      <SelectItem key={flight.flightNumber} value={flight.flightNumber}>
                        {flight.flightNumber} → {flight.destination} ({flight.statusCategory})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              {selectedFlight && selectedFlightData && (
                <>
                  {/* Baseline Info */}
                  <Card className="p-4 bg-muted">
                    <h3 className="font-semibold text-sm mb-2">Baseline Status</h3>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>Status: <Badge variant={selectedFlightData.statusCategory === 'critical' ? 'destructive' : 'secondary'}>{selectedFlightData.statusCategory}</Badge></div>
                      <div>Delay: {selectedFlightData.delayMinutes || 0}min</div>
                      <div>Passengers: {selectedFlightData.paxImpacted || 0}</div>
                      <div>Departure: {selectedFlightData.scheduledDeparture}</div>
                    </div>
                  </Card>

                  {/* Additional Delay */}
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <Label>Additional Delay (minutes)</Label>
                      <input
                        type="number"
                        min={0}
                        max={180}
                        step={15}
                        className="w-20 border rounded px-2 py-1 text-right text-xs"
                        value={scenario.delay_minutes ?? 0}
                        onChange={(e) => {
                          const val = Number(e.target.value || 0);
                          setScenario({ ...scenario, delay_minutes: Math.max(0, Math.min(180, val)) });
                        }}
                      />
                    </div>
                    <Slider
                      value={[scenario.delay_minutes ?? 0]}
                      onValueChange={(val: number[]) => setScenario({ ...scenario, delay_minutes: val[0] })}
                      min={0}
                      max={180}
                      step={15}
                      className="mt-2"
                    />
                  </div>

                  {/* Weather Impact */}
                  <div>
                    <Label>Weather Impact</Label>
                    <Select
                      value={scenario.weather_impact || 'none'}
                      onValueChange={(val: 'none' | 'minor' | 'moderate' | 'severe') => setScenario({ ...scenario, weather_impact: val })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">None</SelectItem>
                        <SelectItem value="minor">Minor</SelectItem>
                        <SelectItem value="moderate">Moderate</SelectItem>
                        <SelectItem value="severe">Severe</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Crew Issues */}
                  <div>
                    <div className="flex items-center justify-between gap-2">
                      <Label>Crew Unavailable</Label>
                      <input
                        type="number"
                        min={0}
                        max={10}
                        step={1}
                        className="w-16 border rounded px-2 py-1 text-right text-xs"
                        value={scenario.crew_unavailable ?? 0}
                        onChange={(e) => {
                          const val = Number(e.target.value || 0);
                          setScenario({ ...scenario, crew_unavailable: Math.max(0, Math.min(10, val)) });
                        }}
                      />
                    </div>
                    <Slider
                      value={[scenario.crew_unavailable ?? 0]}
                      onValueChange={(val: number[]) => setScenario({ ...scenario, crew_unavailable: val[0] })}
                      min={0}
                      max={10}
                      step={1}
                      className="mt-2"
                    />
                  </div>

                  {/* Aircraft Issue */}
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={scenario.aircraft_issue || false}
                      onChange={(e) => setScenario({ ...scenario, aircraft_issue: e.target.checked })}
                      className="w-4 h-4"
                    />
                    <Label>Simulate Aircraft Maintenance Issue</Label>
                  </div>

                  {/* Connection Pressure */}
                  <div>
                    <Label>Connection Pressure</Label>
                    <Select
                      value={scenario.connection_pressure || 'low'}
                      onValueChange={(val: 'low' | 'medium' | 'high') => setScenario({ ...scenario, connection_pressure: val })}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Passenger Count Change */}
                  <div>
                    <Label>
                      Passenger Count Change: {scenario.passenger_count_change || 0}
                    </Label>
                    <Slider
                      value={[scenario.passenger_count_change || 0]}
                      onValueChange={(val: number[]) =>
                        setScenario({ ...scenario, passenger_count_change: val[0] })
                      }
                      min={-100}
                      max={100}
                      step={10}
                      className="mt-2"
                    />
                    <p className="text-xs text-muted-foreground mt-1">
                      Negative values simulate fewer impacted passengers; positive values
                      simulate more misconnects or added groups.
                    </p>
                  </div>

                  {/* Scenario Summary */}
                  <Card className="p-4 bg-background/60 border-dashed mt-2">
                    <h3 className="font-semibold text-sm mb-2">Scenario Summary</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      <div>
                        <div className="text-muted-foreground">Effective delay</div>
                        <div className="font-semibold">{effectiveDelay} min</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Effective impacted pax</div>
                        <div className="font-semibold">{effectivePax}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Weather</div>
                        <div className="font-semibold">
                          {weatherDescriptions[scenario.weather_impact || 'none']}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Connection pressure</div>
                        <div className="font-semibold">
                          {connectionDescriptions[scenario.connection_pressure || 'low']}
                        </div>
                      </div>
                    </div>
                  </Card>

                  {/* Actions */}
                  <div className="flex gap-2 pt-4">
                    <Button onClick={handleAnalyze} disabled={analyzing} className="flex-1">
                      {analyzing ? (
                        <>
                          <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                          Analyzing...
                        </>
                      ) : (
                        <>
                          <TrendingUp className="w-4 h-4 mr-2" />
                          Run Analysis
                        </>
                      )}
                    </Button>
                    <Button onClick={handleReset} variant="outline">
                      Reset
                    </Button>
                  </div>
                </>
              )}
            </div>
          </Card>

          {/* Agent Progress Timeline - Show DURING and AFTER analysis (REAL-TIME!) */}
          {agentTimeline && agentTimeline.length > 0 && (
            <Card className="p-6 mb-4 border-2 border-blue-500">
              <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Zap className="w-5 h-5 text-blue-600" />
                Analysis Timeline ({agentTimeline.length} agents)
              </h2>
              <div className="flex gap-3 overflow-x-auto pb-2">
                {agentTimeline.map((progress: any, idx: number) => (
                  <div
                    key={idx}
                    className={`min-w-[180px] flex-shrink-0 p-3 rounded-lg border transition-all ${
                      progress.status === 'complete'
                        ? 'bg-green-50 text-green-900 border-green-200'
                        : progress.status === 'started'
                        ? 'bg-blue-50 text-blue-900 border-blue-200'
                        : 'bg-gray-50 text-gray-700 border-gray-200'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <div className="flex items-center gap-1">
                        {progress.status === 'complete' && (
                          <Zap className="w-4 h-4 text-green-600" />
                        )}
                        {progress.status === 'started' && (
                          <AlertTriangle className="w-4 h-4 text-blue-600" />
                        )}
                        <div className="font-semibold text-sm truncate">
                          {progress.agent}
                        </div>
                      </div>
                      <Badge
                        variant={progress.status === 'complete' ? 'default' : 'secondary'}
                        className="text-[10px] uppercase"
                      >
                        {progress.status}
                      </Badge>
                    </div>
                    <div className="text-[11px] opacity-75 line-clamp-2">
                      {progress.message}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Results */}
          <Card className="p-6">
            <h2 className="text-xl font-semibold mb-4">Predicted Outcome</h2>

            {!results ? (
              <div className="flex flex-col items-center justify-center h-64 text-muted-foreground">
                <TrendingUp className="w-16 h-16 mb-4 opacity-20" />
                <p>Configure a scenario and run analysis to see predictions</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Disruption Detection */}
                <Card className={`p-4 ${results.predicted_outcome.disruption_detected ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                  <div className="flex items-center gap-2">
                    <AlertTriangle className={`w-5 h-5 ${results.predicted_outcome.disruption_detected ? 'text-red-600' : 'text-green-600'}`} />
                    <span className="font-semibold">
                      {results.predicted_outcome.disruption_detected ? 'Disruption Likely' : 'No Disruption Expected'}
                    </span>
                  </div>
                </Card>

                {/* Risk Comparison */}
                <div>
                  <h3 className="font-semibold mb-2">Risk Level</h3>
                  <div className="flex items-center gap-4">
                    <div>
                      <div className="text-xs text-muted-foreground">Baseline</div>
                      <Badge variant="secondary">{results.comparison.risk_change.baseline}</Badge>
                    </div>
                    <span className="text-2xl">→</span>
                    <div>
                      <div className="text-xs text-muted-foreground">Predicted</div>
                      <Badge variant="destructive">{results.comparison.risk_change.predicted}</Badge>
                    </div>
                  </div>
                </div>

                {/* Financial Impact */}
                {results.comparison.financial_impact > 0 && (
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-5 h-5 text-amber-600" />
                    <span className="font-semibold">Financial Impact:</span>
                    <span>${results.comparison.financial_impact.toLocaleString()}</span>
                  </div>
                )}

                {/* Passengers Affected */}
                {results.comparison.passengers_affected > 0 && (
                  <div className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-blue-600" />
                    <span className="font-semibold">Passengers Affected:</span>
                    <span>{results.comparison.passengers_affected}</span>
                  </div>
                )}

                {/* Recommended Actions */}
                {results.comparison.recommended_actions?.length > 0 && (
                  <div>
                    <h3 className="font-semibold mb-2">Recommended Actions</h3>
                    <ul className="space-y-1">
                      {results.comparison.recommended_actions.map((action: string, idx: number) => (
                        <li key={idx} className="text-sm flex items-start gap-2">
                          <span className="text-primary">•</span>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Agent Decisions & What-If Scenarios from ADK workflow */}
                {agenticAnalysis && (
                  <div className="pt-4 space-y-4">
                    <h3 className="font-semibold mb-2">Agent Decisions</h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {/* Risk Agent */}
                      {agenticAnalysis.risk_assessment && Object.keys(agenticAnalysis.risk_assessment).length > 0 && (
                        <Card className="p-3">
                          <h4 className="font-semibold text-sm mb-1">Risk Agent</h4>
                          <div className="text-xs space-y-1">
                            {typeof agenticAnalysis.risk_assessment.risk_probability === 'number' && (
                              <div>Probability: {(agenticAnalysis.risk_assessment.risk_probability * 100).toFixed(0)}%</div>
                            )}
                            {typeof agenticAnalysis.risk_assessment.likelihood === 'number' && (
                              <div>Likelihood: {(agenticAnalysis.risk_assessment.likelihood * 100).toFixed(0)}%</div>
                            )}
                            {agenticAnalysis.risk_assessment.duration_minutes && (
                              <div>Duration: {agenticAnalysis.risk_assessment.duration_minutes} min</div>
                            )}
                            {agenticAnalysis.risk_assessment.pax_impact && (
                              <div>Passenger impact: {agenticAnalysis.risk_assessment.pax_impact}</div>
                            )}
                            {agenticAnalysis.risk_assessment.regulatory_risk && (
                              <div>Regulatory: {agenticAnalysis.risk_assessment.regulatory_risk}</div>
                            )}
                          </div>
                        </Card>
                      )}

                      {/* Rebooking Agent */}
                      {agenticAnalysis.rebooking_plan && Object.keys(agenticAnalysis.rebooking_plan).length > 0 && (
                        <Card className="p-3">
                          <h4 className="font-semibold text-sm mb-1">Rebooking Agent</h4>
                          <div className="text-xs space-y-1">
                            {agenticAnalysis.rebooking_plan.strategy && (
                              <div>Strategy: {agenticAnalysis.rebooking_plan.strategy}</div>
                            )}
                            {typeof agenticAnalysis.rebooking_plan.estimated_pax === 'number' && (
                              <div>Passengers: {agenticAnalysis.rebooking_plan.estimated_pax}</div>
                            )}
                            {typeof agenticAnalysis.rebooking_plan.hotel_required === 'boolean' && (
                              <div>Hotel required: {agenticAnalysis.rebooking_plan.hotel_required ? 'Yes' : 'No'}</div>
                            )}
                            {Array.isArray(agenticAnalysis.rebooking_plan.actions) && agenticAnalysis.rebooking_plan.actions.length > 0 && (
                              <div>
                                Actions:
                                <ul className="list-disc list-inside">
                                  {agenticAnalysis.rebooking_plan.actions.slice(0, 3).map((a: string, idx: number) => (
                                    <li key={idx}>{a}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </Card>
                      )}

                      {/* Finance Agent */}
                      {agenticAnalysis.finance_estimate && Object.keys(agenticAnalysis.finance_estimate).length > 0 && (
                        <Card className="p-3">
                          <h4 className="font-semibold text-sm mb-1">Finance Agent</h4>
                          <div className="text-xs space-y-1">
                            {typeof agenticAnalysis.finance_estimate.total_usd === 'number' && (
                              <div>Total cost: ${agenticAnalysis.finance_estimate.total_usd.toLocaleString()}</div>
                            )}
                            {Array.isArray(agenticAnalysis.finance_estimate.breakdown) && agenticAnalysis.finance_estimate.breakdown.length > 0 && (
                              <div>
                                Breakdown:
                                <ul className="list-disc list-inside">
                                  {agenticAnalysis.finance_estimate.breakdown.slice(0, 3).map((b: string, idx: number) => (
                                    <li key={idx}>{b}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </Card>
                      )}

                      {/* Crew Agent */}
                      {agenticAnalysis.crew_rotation && Object.keys(agenticAnalysis.crew_rotation).length > 0 && (
                        <Card className="p-3">
                          <h4 className="font-semibold text-sm mb-1">Crew Agent</h4>
                          <div className="text-xs space-y-1">
                            {typeof agenticAnalysis.crew_rotation.crew_changes_needed === 'boolean' && (
                              <div>
                                Crew changes: {agenticAnalysis.crew_rotation.crew_changes_needed ? 'Required' : 'Not needed'}
                              </div>
                            )}
                            {typeof agenticAnalysis.crew_rotation.backup_crew_required === 'number' && (
                              <div>Backup crew: {agenticAnalysis.crew_rotation.backup_crew_required}</div>
                            )}
                            {Array.isArray(agenticAnalysis.crew_rotation.regulatory_issues) && agenticAnalysis.crew_rotation.regulatory_issues.length > 0 && (
                              <div>
                                Regulatory issues:
                                <ul className="list-disc list-inside">
                                  {agenticAnalysis.crew_rotation.regulatory_issues.slice(0, 3).map((r: string, idx: number) => (
                                    <li key={idx}>{r}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </Card>
                      )}
                    </div>

                    {/* Orchestrator what-if scenarios */}
                    {Array.isArray(agenticAnalysis.simulation_results) && agenticAnalysis.simulation_results.length > 0 && (
                      <div>
                        <h4 className="font-semibold mb-1">What-If Scenarios (from Orchestrator)</h4>
                        <ul className="space-y-1 text-sm">
                          {agenticAnalysis.simulation_results.map((sim: any, idx: number) => (
                            <li key={idx} className="flex items-start gap-2">
                              <span className="text-primary">•</span>
                              <span>
                                <span className="font-semibold mr-1">{sim.scenario || 'scenario'}</span>
                                {sim.plan?.description && <span>— {sim.plan.description}</span>}
                              </span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Aggregated final plan & audit trail */}
                    {agenticAnalysis.final_plan && Object.keys(agenticAnalysis.final_plan).length > 0 && (
                      <div className="text-xs space-y-1">
                        <h4 className="font-semibold mb-1">Aggregator Agent</h4>
                        <div>Recommended action: {agenticAnalysis.final_plan.recommended_action || 'N/A'}</div>
                        <div>Priority: {agenticAnalysis.final_plan.priority || 'N/A'}</div>
                        <div>Confidence: {agenticAnalysis.final_plan.confidence || 'N/A'}</div>
                      </div>
                    )}

                    {Array.isArray(agenticAnalysis.audit_log) && agenticAnalysis.audit_log.length > 0 && (
                      <div className="text-xs text-muted-foreground">
                        <h4 className="font-semibold mb-1">Agent Reasoning (last 3 steps)</h4>
                        <ul className="space-y-1">
                          {agenticAnalysis.audit_log.slice(-3).map((entry: any, idx: number) => (
                            <li key={idx}>
                              <span className="font-semibold">{entry.agent}</span>
                              {entry.output?.reasoning && `: ${entry.output.reasoning}`}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
