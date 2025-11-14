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

export function WhatIfScenario() {
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
  const [results, setResults] = useState<any>(null);

  const flights = data?.flights || [];
  const selectedFlightData = flights.find(f => f.flightNumber === selectedFlight);

  const handleAnalyze = async () => {
    if (!selectedFlight) {
      toast.error('Please select a flight');
      return;
    }

    setAnalyzing(true);
    setResults(null);

    try {
      const apiBase = (import.meta as any).env?.VITE_MONITOR_API || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/api/whatif/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...scenario, flight_number: selectedFlight }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data);
      toast.success('What-if analysis complete!');
    } catch (error) {
      console.error('What-if analysis failed:', error);
      toast.error('Analysis failed. Check console for details.');
    } finally {
      setAnalyzing(false);
    }
  };

  const handleReset = () => {
    setScenario({ flight_number: selectedFlight });
    setResults(null);
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
                    <Label>Additional Delay (minutes): {scenario.delay_minutes || 0}</Label>
                    <Slider
                      value={[scenario.delay_minutes || 0]}
                      onValueChange={(val: number[]) => setScenario({ ...scenario, delay_minutes: val[0] })}
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
                    <Label>Crew Unavailable: {scenario.crew_unavailable || 0}</Label>
                    <Slider
                      value={[scenario.crew_unavailable || 0]}
                      onValueChange={(val: number[]) => setScenario({ ...scenario, crew_unavailable: val[0] })}
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
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
}
