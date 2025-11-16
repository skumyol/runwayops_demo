import React, { useEffect, useMemo, useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { TierTag } from '../components/TierTag';
import { OptionCard } from '../components/OptionCard';
import { PolicyCallout } from '../components/PolicyCallout';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { User, Phone, Mail, Plane, Clock, MapPin, DollarSign, RefreshCw, Users, Bot, Sparkles, FileText, X, Zap, Radar } from 'lucide-react';
import { toast } from 'sonner';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Skeleton } from '../components/ui/skeleton';
import { usePassengerDetail, useReaccommodationFlights, useFlightManifest } from '../hooks/useReaccommodation';
import { useAgentReaccommodation } from '../hooks/useAgentReaccommodation';
import { useAgentOptions } from '../hooks/useAgentOptions';
import { AgentAuditTrail } from '../components/AgentAuditTrail';
import { ReaccommodationOption } from '../types/reaccommodation';

export function AgentPassengerPanel() {
  const { flights, loading: flightsLoading } = useReaccommodationFlights();
  const [selectedFlight, setSelectedFlight] = useState<string | null>(null);
  const { suggestions, analysis, loading: aiLoading, error: aiError, getSuggestions, analyzeFlightWithAgents } = useAgentReaccommodation();
  const { agentOptions, loading: agentOptionsLoading, error: agentOptionsError, analysisSummary, fetchAgentOptions } = useAgentOptions();
  const [showAgentDetails, setShowAgentDetails] = useState(false);
  const [useAIOptions, setUseAIOptions] = useState(false);
  const { manifest, loading: manifestLoading } = useFlightManifest(selectedFlight);
  const passengerSummaries = manifest?.passengers ?? [];
  const [selectedPassengerPnr, setSelectedPassengerPnr] = useState<string | null>(null);
  const { detail, loading: passengerLoading, error: passengerError, refresh: refreshPassenger } = usePassengerDetail(selectedPassengerPnr);
  const passenger = detail?.passenger ?? passengerSummaries.find((p) => p.pnr === selectedPassengerPnr) ?? null;
  // Use AI options if toggle is on and they're available, otherwise use static
  const staticOptions = (detail?.options ?? manifest?.manifest.options ?? []) as ReaccommodationOption[];
  const options = useAIOptions && agentOptions.length > 0 ? agentOptions : staticOptions;
  const crew = detail?.crew ?? manifest?.crew ?? [];
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const cohortEntry = useMemo(
    () => manifest?.manifest.cohortPassengers.find((entry) => entry.pnr === passenger?.pnr),
    [manifest, passenger?.pnr]
  );
  const defaultOptionId = cohortEntry?.defaultOption ?? options[0]?.id ?? null;
  const confidenceValue = cohortEntry?.confidence ?? 0;

  useEffect(() => {
    if (!selectedFlight && flights.length) {
      setSelectedFlight(flights[0].flightNumber);
    }
  }, [flights, selectedFlight]);

  useEffect(() => {
    if (!passengerSummaries.length) {
      setSelectedPassengerPnr(null);
      return;
    }
    if (!selectedPassengerPnr || !passengerSummaries.some((p) => p.pnr === selectedPassengerPnr)) {
      setSelectedPassengerPnr(passengerSummaries[0].pnr);
    }
  }, [passengerSummaries, selectedPassengerPnr]);

  useEffect(() => {
    if (!options.length) {
      setSelectedOption(null);
      return;
    }
    const fallback = defaultOptionId ?? options[0].id;
    if (!selectedOption || !options.some((option) => option.id === selectedOption)) {
      setSelectedOption(fallback);
    }
  }, [options, defaultOptionId, selectedOption]);

  const passengerEmail =
    (detail?.passenger.basePassenger?.contactInfo as { email?: string } | undefined)?.email ?? 'ops@cathay.com';

  const loading = flightsLoading || manifestLoading || passengerLoading;

  const handleAcceptTicket = () => {
    if (!passenger || !selectedOption) return;
    toast.success(`Re-accommodation accepted for ${passenger.name}`, {
      description: `Option ${selectedOption} has been ticketed`,
    });
  };

  const noData = !loading && (!flights.length || !passenger);
  const noFlights = !loading && !flights.length;

  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      <div className="h-16 bg-white border-b border-border flex items-center justify-between px-8">
        <div>
          <h1 className="text-[24px] leading-[32px] font-semibold">Ops Agent Re-accommodation Console</h1>
          <p className="text-[12px] text-muted-foreground">
            Internal console for operations and contact centre agents. Passengers see only their own re-accommodation screen.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="text-[11px] px-2 py-0.5">
            Ops / Agent View
          </Badge>
          {passengerError && (
            <div className="flex items-center gap-2 text-sm text-destructive">
              {passengerError}
              <Button variant="outline" size="sm" onClick={refreshPassenger}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Retry
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Configuration Required Message */}
      {noFlights && (
        <div className="p-8 max-w-4xl mx-auto">
          <Card className="p-8 border-amber-200 bg-gradient-to-br from-amber-50 to-white">
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0">
                <User className="w-6 h-6 text-amber-600" />
              </div>
              <div className="flex-1">
                <h2 className="text-xl font-semibold mb-2">Agent Console Configuration Required</h2>
                <p className="text-muted-foreground mb-4">
                  The Agent Re-accommodation Console requires passenger manifest data to function. 
                  This feature is designed for individual passenger reaccommodation workflows.
                </p>
                
                <div className="bg-white rounded-lg p-4 border border-amber-100 mb-4">
                  <h3 className="font-semibold text-sm mb-2">What this console provides:</h3>
                  <ul className="space-y-2 text-sm text-muted-foreground">
                    <li className="flex items-start gap-2">
                      <span className="text-amber-600 mt-0.5">•</span>
                      <span>Individual passenger details and special service requests (SSRs)</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-600 mt-0.5">•</span>
                      <span>Multiple reaccommodation options comparison with TRV scores</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-600 mt-0.5">•</span>
                      <span><strong>"WHY this option?"</strong> - AI reasoning for each recommendation</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-600 mt-0.5">•</span>
                      <span>Policy callouts, waivers, and tier-based protections</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-amber-600 mt-0.5">•</span>
                      <span>One-click re-accommodation with agent audit trails</span>
                    </li>
                  </ul>
                </div>

                <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 mb-4">
                  <h3 className="font-semibold text-sm mb-2">Required configuration:</h3>
                  <div className="space-y-2 text-sm text-muted-foreground font-mono">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px]">GET</Badge>
                      <code>/api/reaccommodation/flights</code>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px]">GET</Badge>
                      <code>/api/reaccommodation/manifest/:flightNumber</code>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px]">GET</Badge>
                      <code>/api/reaccommodation/passenger/:pnr</code>
                    </div>
                  </div>
                  <p className="text-xs text-muted-foreground mt-3">
                    Configure these endpoints in the backend or generate mock passenger data using <code className="bg-white px-1 py-0.5 rounded">scripts/generate_mock_data.py</code>
                  </p>
                </div>

                <div className="flex items-center gap-3">
                  <Button variant="outline" onClick={() => window.location.href = '/'}>
                    <Radar className="w-4 h-4 mr-2" />
                    Go to Flight Monitor
                  </Button>
                  <Button variant="outline" asChild>
                    <a href="https://github.com/your-repo/docs/agent-console" target="_blank" rel="noopener noreferrer">
                      <FileText className="w-4 h-4 mr-2" />
                      View Documentation
                    </a>
                  </Button>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Main Content - Only show if flights are available */}
      {!noFlights && (
      <div className="flex h-[calc(100vh-64px)]">
        <div className="w-[320px] bg-white border-r border-border p-6 overflow-y-auto space-y-4">
          <div className="space-y-2">
            <label className="text-[12px] font-semibold text-muted-foreground">Flight</label>
            <Select value={selectedFlight ?? ''} onValueChange={setSelectedFlight} disabled={!flights.length}>
              <SelectTrigger>
                <SelectValue placeholder="Select flight" />
              </SelectTrigger>
              <SelectContent>
                {flights.map((flight) => (
                  <SelectItem key={flight.flightNumber} value={flight.flightNumber}>
                    {flight.flightNumber} · {flight.destination}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <label className="text-[12px] font-semibold text-muted-foreground">Passenger</label>
            <Select
              value={selectedPassengerPnr ?? ''}
              onValueChange={setSelectedPassengerPnr}
              disabled={!passengerSummaries.length}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select passenger" />
              </SelectTrigger>
              <SelectContent>
                {passengerSummaries.map((pax) => (
                  <SelectItem key={pax.pnr} value={pax.pnr}>
                    {pax.name} ({pax.pnr})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {loading && (
            <Card className="p-4 rounded-[12px]">
              <Skeleton className="h-5 w-2/3 mb-3" />
              <Skeleton className="h-4 w-1/2 mb-2" />
              <Skeleton className="h-20 w-full" />
            </Card>
          )}

          {noData && (
            <Card className="p-4 rounded-[12px] text-[13px] text-muted-foreground">
              No passenger data available for the selected flight.
            </Card>
          )}

          {passenger && (
            <>
              <Card className="p-4 rounded-[12px] bg-primary/5 border-primary/20">
                <div className="flex items-center gap-2 mb-3">
                  <User className="w-5 h-5 text-primary" />
                  <span className="text-[12px] font-mono text-muted-foreground">PNR: {passenger.pnr}</span>
                </div>
                
                <h3 className="text-[18px] leading-[24px] font-semibold mb-2">{passenger.name}</h3>
                
                <div className="flex items-center gap-2 mb-3">
                  <TierTag tier={passenger.tier} />
                  <Badge variant="outline" className="text-[12px]">Cabin {passenger.cabin}</Badge>
                </div>
                
                <div className="flex items-center gap-2 text-[14px] mb-2">
                  <DollarSign className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Value:</span>
                  <span className="font-semibold">${passenger.value.toLocaleString()}</span>
                </div>
              </Card>

              <div className="space-y-4">
                <div>
                  <h4 className="text-[14px] font-semibold mb-2">SSRs</h4>
                  <div className="flex flex-wrap gap-2">
                    {passenger.ssrs.length ? (
                      passenger.ssrs.map((ssr) => (
                        <Badge key={ssr} variant="secondary" className="text-[12px]">
                          {ssr}
                        </Badge>
                      ))
                    ) : (
                      <span className="text-[12px] text-muted-foreground">None</span>
                    )}
                  </div>
                </div>

                <Separator />

                <div>
                  <h4 className="text-[14px] font-semibold mb-2">Contact</h4>
                  <div className="space-y-2 text-[13px]">
                    <div className="flex items-center gap-2">
                      <Phone className="w-4 h-4 text-muted-foreground" />
                      <span>{passenger.contact}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Mail className="w-4 h-4 text-muted-foreground" />
                      <span>{passengerEmail}</span>
                    </div>
                  </div>
                </div>

                <Separator />

                <div>
                  <h4 className="text-[14px] font-semibold mb-3">Original Itinerary</h4>
                  <Card className="p-3 rounded-[8px] bg-destructive/5 border-destructive/20">
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-[14px]">
                        <Plane className="w-4 h-4 text-destructive" />
                        <span className="font-semibold text-destructive">{passenger.originalFlight}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
                        <MapPin className="w-3 h-3" />
                        <span>{passenger.originalRoute}</span>
                      </div>
                      <div className="flex items-center gap-2 text-[12px] text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>Scheduled: {passenger.originalTime}</span>
                      </div>
                      <Badge variant="destructive" className="text-[10px] mt-2">CANCELLED</Badge>
                    </div>
                  </Card>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-[800px] mx-auto space-y-4">
            <div className="space-y-3 mb-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-[18px] leading-[24px] font-semibold">
                    Re-accommodation Options
                  </h2>
                  <p className="text-[12px] text-muted-foreground">
                    {options.length} options {useAIOptions ? 'generated by AI agents' : 'from MongoDB'}
                    {analysisSummary && ` • ${analysisSummary.confidence} confidence`}
                  </p>
                </div>
                <Badge variant="outline" className="text-[12px]">
                  Crew ready: {crew.length}
                </Badge>
              </div>

              {/* AI Options Toggle */}
              <Card className={`p-3 rounded-[8px] ${useAIOptions ? 'bg-indigo-50 border-indigo-200' : 'bg-muted border-border'}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className={`w-4 h-4 ${useAIOptions ? 'text-indigo-600' : 'text-muted-foreground'}`} />
                    <div>
                      <p className="text-[13px] font-medium">
                        {useAIOptions ? 'AI-Powered Options' : 'Use AI-Powered Options'}
                      </p>
                      <p className="text-[11px] text-muted-foreground">
                        {useAIOptions 
                          ? 'Options generated by APIV2 (ADK) agents in real-time'
                          : 'Switch to dynamic agent-generated recommendations'
                        }
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={async () => {
                      if (!useAIOptions && selectedFlight) {
                        setUseAIOptions(true);
                        // Skip prediction since we're in reaccommodation view (disruption already confirmed)
                        await fetchAgentOptions(selectedFlight, selectedPassengerPnr || undefined, true);
                      } else {
                        setUseAIOptions(false);
                      }
                    }}
                    variant={useAIOptions ? 'default' : 'outline'}
                    size="sm"
                    disabled={!selectedFlight || agentOptionsLoading}
                    className={useAIOptions ? 'bg-indigo-600 hover:bg-indigo-700' : ''}
                  >
                    {agentOptionsLoading ? (
                      <>
                        <Bot className="w-3 h-3 mr-2 animate-pulse" />
                        Generating...
                      </>
                    ) : useAIOptions ? (
                      <>
                        <Zap className="w-3 h-3 mr-2" />
                        AI Mode
                      </>
                    ) : (
                      'Enable AI'
                    )}
                  </Button>
                </div>

                {agentOptionsError && (
                  <p className="text-[11px] text-destructive mt-2">{agentOptionsError}</p>
                )}

                {useAIOptions && analysisSummary && (
                  <div className="flex items-center gap-2 mt-2 pt-2 border-t border-indigo-200">
                    <Badge variant={analysisSummary.disruption_detected ? 'destructive' : 'secondary'} className="text-[10px]">
                      {analysisSummary.disruption_detected ? 'Disruption Detected' : 'Normal'}
                    </Badge>
                    <Badge variant="outline" className="text-[10px]">
                      Risk: {analysisSummary.risk_level}
                    </Badge>
                    <Badge variant="outline" className="text-[10px]">
                      {analysisSummary.recommended_action}
                    </Badge>
                  </div>
                )}
              </Card>
            </div>

            {loading && (
              <div className="space-y-4">
                {Array.from({ length: 2 }).map((_, idx) => (
                  <Card key={`option-skeleton-${idx}`} className="p-6 rounded-[12px]">
                    <Skeleton className="h-5 w-1/3 mb-3" />
                    <Skeleton className="h-4 w-2/3 mb-2" />
                    <Skeleton className="h-40 w-full" />
                  </Card>
                ))}
              </div>
            )}

            {!loading && !options.length && (
              <Card className="p-6 rounded-[12px] border border-dashed text-center text-muted-foreground">
                No options available for this passenger.
              </Card>
            )}

            {options.map((option) => (
              <OptionCard
                key={option.id}
                {...option}
                optionId={option.id}
                selected={selectedOption === option.id}
                onClick={() => setSelectedOption(option.id)}
              />
            ))}
          </div>
        </div>

        <div className="w-[360px] bg-white border-l border-border p-6 overflow-y-auto">
          <h3 className="text-[18px] leading-[24px] font-semibold mb-4">Actions</h3>
          
          <div className="space-y-3">
            <Button 
              className="w-full h-12 bg-primary hover:bg-primary/90"
              onClick={handleAcceptTicket}
              disabled={!passenger || !selectedOption}
            >
              Accept & Ticket
            </Button>
            
            <Button variant="outline" className="w-full h-12">
              Swap for Incentive
            </Button>
            
            <Button variant="outline" className="w-full h-12">
              Hold Seat
            </Button>
            
            <Button
              variant="outline"
              className="w-full h-12"
              disabled={!passenger}
              onClick={() => {
                if (!passenger) return;
                const url = new URL(window.location.href);
                url.searchParams.set('role', 'passenger');
                url.searchParams.set('pnr', passenger.pnr);
                window.open(url.toString(), '_blank', 'noopener,noreferrer');
              }}
            >
              Send Link to Passenger
            </Button>
            
            <Button variant="outline" className="w-full h-12 border-destructive text-destructive hover:bg-destructive/10">
              Escalate
            </Button>
          </div>

          <Separator className="my-6" />

          {/* AI Suggestions Section */}
          <div className="space-y-3">
            <Button
              onClick={() => selectedFlight && getSuggestions(selectedFlight, selectedPassengerPnr || undefined)}
              disabled={!selectedFlight || aiLoading}
              className="w-full h-12 bg-indigo-600 hover:bg-indigo-700"
            >
              <Bot className="w-4 h-4 mr-2" />
              {aiLoading ? 'Running AI Analysis...' : 'Get AI Suggestions'}
            </Button>

            {aiError && (
              <Card className="p-3 rounded-[8px] bg-destructive/5 border-destructive/20">
                <p className="text-[12px] text-destructive">{aiError}</p>
              </Card>
            )}

            {suggestions && (
              <Card className="p-4 rounded-[12px] bg-indigo-50 border-indigo-200">
                <div className="flex items-center gap-2 mb-3">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <h4 className="text-[14px] font-semibold text-indigo-900">AI Recommendations</h4>
                </div>
                
                <div className="space-y-2 text-[13px]">
                  <div>
                    <span className="text-muted-foreground">Strategy:</span>
                    <p className="font-medium text-foreground">{suggestions.rebooking_strategy}</p>
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Priority:</span>
                    <Badge variant={suggestions.priority === 'critical' ? 'destructive' : 'default'}>
                      {suggestions.priority}
                    </Badge>
                    <span className="text-muted-foreground">·</span>
                    <span className="text-muted-foreground">Confidence:</span>
                    <Badge variant="outline">{suggestions.confidence}</Badge>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Est. Cost:</span>
                    <span className="font-semibold">${suggestions.estimated_cost?.toLocaleString() ?? 'N/A'}</span>
                  </div>
                  
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Affected Pax:</span>
                    <span className="font-semibold">{suggestions.affected_passengers ?? 'N/A'}</span>
                  </div>

                  {suggestions.passenger && (
                    <>
                      <Separator className="my-2" />
                      <div>
                        <span className="text-[11px] font-semibold text-muted-foreground uppercase">For {suggestions.passenger.name}</span>
                        <p className="text-[12px] mt-1">{suggestions.passenger.specific_recommendation}</p>
                      </div>
                    </>
                  )}
                </div>

                {suggestions.reasoning && (
                  <details className="mt-3">
                    <summary className="cursor-pointer text-[12px] font-medium text-indigo-700">
                      View AI Reasoning
                    </summary>
                    <div className="mt-2 text-[11px] space-y-2 text-muted-foreground">
                      {suggestions.reasoning.risk && (
                        <div>
                          <strong className="text-foreground">Risk:</strong> {suggestions.reasoning.risk}
                        </div>
                      )}
                      {suggestions.reasoning.rebooking && (
                        <div>
                          <strong className="text-foreground">Rebooking:</strong> {suggestions.reasoning.rebooking}
                        </div>
                      )}
                      {suggestions.reasoning.finance && (
                        <div>
                          <strong className="text-foreground">Finance:</strong> {suggestions.reasoning.finance}
                        </div>
                      )}
                    </div>
                  </details>
                )}
                
                {/* View Full Agent Details Button */}
                <Button
                  onClick={async () => {
                    if (!analysis && selectedFlight) {
                      await analyzeFlightWithAgents(selectedFlight);
                    }
                    setShowAgentDetails(true);
                  }}
                  variant="outline"
                  size="sm"
                  className="w-full mt-3"
                  disabled={aiLoading}
                >
                  <FileText className="w-3 h-3 mr-2" />
                  View Full Agent Analysis
                </Button>
              </Card>
            )}
          </div>

          <Separator className="my-6" />

          <div className="space-y-4">
            <PolicyCallout 
              title="Policy Waiver"
              message="Overnight hotel accommodation approved for this disruption. WCHR assistance pre-arranged for new flight."
            />

            <Card className="p-4 rounded-[12px] bg-success/5 border-success/20">
              <h4 className="text-[14px] font-semibold mb-2">Compensation</h4>
              <p className="text-[12px] text-muted-foreground mb-3">
                Tier-driven benefits triggered automatically.
              </p>
              <div className="space-y-1 text-[12px]">
                <div className="flex justify-between">
                  <span>Miles credit</span>
                  <span className="font-semibold">15,000</span>
                </div>
                <div className="flex justify-between">
                  <span>Lounge voucher</span>
                  <span className="font-semibold">✓</span>
                </div>
                <div className="flex justify-between">
                  <span>Priority rebooking</span>
                  <span className="font-semibold">✓</span>
                </div>
              </div>
            </Card>
          </div>

          <div className="mt-6 p-4 bg-muted rounded-lg space-y-2 text-[12px] text-muted-foreground">
            <div className="flex justify-between">
              <span>Confidence</span>
              <span className="font-semibold text-foreground">
                {confidenceValue}%
              </span>
            </div>
            <div className="flex justify-between">
              <span>Inventory Protected</span>
              <span className="font-semibold text-foreground">{passenger?.cabin ?? '—'}</span>
            </div>
            <div className="flex items-center justify-between">
              <span>Crew Ready</span>
              <span className="flex items-center gap-1 font-semibold text-foreground">
                <Users className="w-3 h-3" />
                {crew.length}
              </span>
            </div>
          </div>
        </div>
      </div>
      )}

      {/* Agent Details Modal */}
      {showAgentDetails && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="p-6 border-b border-border flex items-center justify-between">
              <div>
                <h2 className="text-[20px] font-semibold flex items-center gap-2">
                  <Bot className="w-5 h-5" />
                  Agent Execution Details
                </h2>
                <p className="text-[13px] text-muted-foreground mt-1">
                  Complete APIV2 (ADK) workflow audit trail for {selectedFlight}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAgentDetails(false)}
              >
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto flex-1">
              {aiLoading && (
                <div className="flex flex-col items-center justify-center py-12">
                  <Bot className="w-12 h-12 text-indigo-600 animate-pulse mb-4" />
                  <p className="text-lg font-semibold">Running Agent Analysis...</p>
                  <p className="text-sm text-muted-foreground">
                    This may take 5-15 seconds
                  </p>
                </div>
              )}

              {aiError && (
                <Card className="p-6 bg-destructive/5 border-destructive/20">
                  <p className="text-destructive">{aiError}</p>
                  <Button
                    onClick={() => selectedFlight && analyzeFlightWithAgents(selectedFlight)}
                    variant="outline"
                    className="mt-4"
                  >
                    Retry Analysis
                  </Button>
                </Card>
              )}

              {!aiLoading && !aiError && analysis && (
                <AgentAuditTrail
                  auditLog={analysis.analysis?.audit_log || []}
                  finalPlan={analysis.analysis?.final_plan}
                  metadata={analysis.metadata}
                />
              )}

              {!aiLoading && !aiError && !analysis && (
                <div className="text-center py-12">
                  <Bot className="w-16 h-16 text-muted-foreground mx-auto mb-4 opacity-50" />
                  <p className="text-muted-foreground mb-4">
                    No agent analysis available yet
                  </p>
                  <Button
                    onClick={() => selectedFlight && analyzeFlightWithAgents(selectedFlight)}
                    className="bg-indigo-600 hover:bg-indigo-700"
                  >
                    <Bot className="w-4 h-4 mr-2" />
                    Run Agent Analysis
                  </Button>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-border flex justify-end gap-2">
              <Button variant="outline" onClick={() => setShowAgentDetails(false)}>
                Close
              </Button>
              {analysis && (
                <Button
                  onClick={() => selectedFlight && analyzeFlightWithAgents(selectedFlight, true)}
                  disabled={aiLoading}
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Re-run Analysis
                </Button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
