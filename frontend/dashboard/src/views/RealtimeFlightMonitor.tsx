import React, { useEffect, useMemo, useState } from 'react';
import { Activity, AlertTriangle, ArrowLeft, Bell, Bot, Clock, Info, Plane, Radar, RefreshCw, Users, UsersRound, TrendingUp } from 'lucide-react';

import { TopNav } from '../components/TopNav';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Card } from '../components/ui/card';
import { Progress } from '../components/ui/progress';
import { Skeleton } from '../components/ui/skeleton';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import {
  FlightMonitorAlert,
  FlightMonitorFlight,
  StatusCategory,
  useFlightMonitor,
  CrewPanel,
  AircraftPanel,
  MonitorMode,
} from '../hooks/useFlightMonitor';
import { useAgenticAnalysis } from '../hooks/useAgenticAnalysis';
import { AgenticAnalysisPanel } from '../components/AgenticAnalysisPanel';
import { useAgenticContext } from '../context/AgenticContext';
import { describeAgenticEngine, resolveAgenticEngineBase } from '../lib/agentic';
import { usePredictiveAlerts } from '../hooks/usePredictiveAlerts';

const statusStyles: Record<StatusCategory, string> = {
  normal: 'border border-emerald-100 bg-emerald-50 text-emerald-700',
  warning: 'border border-amber-100 bg-amber-50 text-amber-800',
  critical: 'border border-red-100 bg-red-50 text-red-700',
};

const formatClock = (iso: string) =>
  new Intl.DateTimeFormat('en-HK', { hour: '2-digit', minute: '2-digit' }).format(new Date(iso));

const formatRelativeTime = (iso: string | null) => {
  if (!iso) return 'waiting for first update';
  const diff = Date.now() - new Date(iso).getTime();
  if (diff < 60_000) return 'updated just now';
  const minutes = Math.round(diff / 60_000);
  return `updated ${minutes} min ago`;
};

type MonitorTab = 'flights' | 'crew' | 'aircraft' | 'agentic';

export function RealtimeFlightMonitor() {
  const {
    latestAnalysis,
    setLatestAnalysis,
    agenticEngine,
    monitorAirport,
    monitorCarrier,
    monitorMode,
  } = useAgenticContext();
  const [selectedFlight, setSelectedFlight] = useState<FlightMonitorFlight | null>(null);
  const [alertFlight, setAlertFlight] = useState<FlightMonitorFlight | null>(null);
  const [activeTab, setActiveTab] = useState<MonitorTab>('flights');
  const airport = monitorAirport;
  const carrier = monitorCarrier;
  const sourceMode = monitorMode;

  const { data, loading, error, refresh, lastUpdated, isRefreshing } = useFlightMonitor({ airport, carrier, mode: sourceMode });
  const effectiveMode = data?.mode ?? sourceMode;
  const sourceMismatch = data && data.mode !== sourceMode;

  const agenticBaseOverride = resolveAgenticEngineBase(agenticEngine);

  // Agentic analysis integration
  const {
    analysis: agenticAnalysis,
    loading: agenticLoading,
    error: agenticError,
    runAnalysis,
    status: agenticStatus,
    checkStatus,
  } = useAgenticAnalysis({
    airport,
    carrier,
    mode: sourceMode,
    engine: agenticEngine,
    apiBaseOverride: agenticBaseOverride,
  });

  const activeAnalysis = agenticAnalysis ?? latestAnalysis;
  const engineDescription = describeAgenticEngine(agenticEngine);
  const enginePanelTitle = 'APIV2 Agentic Analysis';
  const engineAvailable =
    agenticStatus?.available_engines?.includes(agenticEngine) ?? true;
  const agenticSuspended = !engineAvailable;
  const agenticSuspendedReason = agenticSuspended
    ? `Backend does not expose the ${agenticEngine.toUpperCase()} engine`
    : undefined;
  const agenticTabEnabled = agenticStatus?.enabled ?? true;
  const canRunAgentic =
    !agenticSuspended && (agenticStatus?.enabled ?? true);

  useEffect(() => {
    if (agenticAnalysis) {
      setLatestAnalysis(agenticAnalysis);
    }
  }, [agenticAnalysis, setLatestAnalysis]);

  // Check agentic status on mount
  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  const summaryMetrics = useMemo(() => {
    if (!data) return [];
    const { stats, trend, nextUpdateSeconds } = data;
    const latestMovement = trend.movementsPerHour.at(-1) ?? 0;
    const latestDelay = trend.avgDelay.at(-1) ?? stats.avgDelayMinutes;
    return [
      {
        label: 'Flights',
        value: stats.totalFlights,
        helper: `${stats.onTime} on track`,
        icon: Radar,
        accent: 'from-sky-50 to-white',
      },
      {
        label: 'Avg delay',
        value: `${stats.avgDelayMinutes}m`,
        helper: `${stats.critical} critical`,
        icon: Clock,
        accent: 'from-amber-50 to-white',
      },
      {
        label: 'Impacted pax',
        value: stats.paxImpacted,
        helper: `${stats.delayed} flights`,
        icon: UsersRound,
        accent: 'from-rose-50 to-white',
      },
      {
        label: 'Turn health',
        value: `${Math.round(stats.turnReliability * 100)}%`,
        helper: `Crew ${(stats.crewReadyRate * 100).toFixed(0)}%`,
        icon: Activity,
        accent: 'from-emerald-50 to-white',
      },
      {
        label: 'Ops cadence',
        value: `${latestMovement.toFixed(2)} movements / hr`,
        helper: `Avg delay ${latestDelay}m · refresh in ${nextUpdateSeconds}s`,
        icon: Radar,
        accent: 'from-indigo-50 via-white to-indigo-100',
        span: 2,
      },
    ];
  }, [data]);

  const handleRefresh = async () => {
    await refresh();
  };

  const handleTabChange = (value: MonitorTab) => {
    setActiveTab(value);
    if (value !== 'flights') {
      setSelectedFlight(null);
    }
  };

  const modeLabel = effectiveMode === 'realtime' ? 'Realtime feed' : 'Synthetic scenario';
  const subtitle = data
    ? `${data.airport} · ${data.carrier} · ${data.flights.length} active departures · ${modeLabel}`
    : 'Hong Kong · Cathay Pacific';

  return (
    <div className="min-h-screen bg-[#EBEDEC] pb-10">
      <TopNav
        title="Realtime Flight Monitor"
        subtitle={subtitle}
        actions={
          <div className="flex flex-wrap items-center gap-4">
            <div className="flex flex-col text-xs text-white/80">
              <span className="text-sm font-medium text-white">
                {airport} · {carrier}
              </span>
              <span className="uppercase tracking-wide">
                {sourceMode === 'realtime' ? 'Realtime feed' : 'Synthetic scenario'}
              </span>
            </div>

            <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isRefreshing || loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Refreshing' : 'Refresh'}
            </Button>

            {(agenticStatus?.enabled ?? true) && (
              <Button
                variant="default"
                size="sm"
                onClick={() => runAnalysis()}
                disabled={agenticLoading || !data || agenticSuspended}
                className="bg-indigo-600 hover:bg-indigo-700"
              >
                <Bot className={`w-4 h-4 mr-2 ${agenticLoading ? 'animate-pulse' : ''}`} />
                {agenticLoading ? 'Analyzing...' : 'Run AI Analysis'}
              </Button>
            )}

            <AlertsDropdown
              alerts={data?.alerts ?? []}
              onSelectAlert={(flightNumber) => {
                const matchingFlight = data?.flights.find(
                  (flight) => flight.flightNumber === flightNumber
                );
                if (matchingFlight) {
                  setAlertFlight(matchingFlight);
                }
              }}
            />

            {data && (
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="text-[12px] capitalize">
                  Source: {effectiveMode}
                </Badge>
                <Badge variant="outline" className="text-[12px]">
                  {formatRelativeTime(lastUpdated)}
                </Badge>
              </div>
            )}
          </div>
        }
      />

      <div className="p-8 space-y-6">
        {sourceMismatch && (
          <Card className="border-amber-200 bg-amber-50/60 p-4 flex items-center gap-3">
            <Info className="w-4 h-4 text-amber-600" />
            <div className="text-[13px]">
              Backend responded with <strong>{data?.mode}</strong> while <strong>{sourceMode}</strong> was requested.
            </div>
          </Card>
        )}

        {data?.fallbackReason && (
          <Card className="border border-amber-300 bg-white p-4 flex items-center gap-3">
            <Info className="w-4 h-4 text-amber-600" />
            <div className="text-[13px]">
              Fallback to synthetic data: {data.fallbackReason}
            </div>
          </Card>
        )}

        {error && (
          <Card className="border-destructive/40 bg-destructive/5 p-6 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-destructive" />
              <div>
                <p className="text-[16px] font-semibold text-destructive">Unable to reach the realtime feed</p>
                <p className="text-[14px] text-muted-foreground">{error}</p>
              </div>
            </div>
            <Button variant="outline" onClick={handleRefresh} size="sm">Retry</Button>
          </Card>
        )}

        {loading && <MonitorSkeleton />}

        {!loading && data && (
          selectedFlight ? (
            <FlightDetailPage
              flight={selectedFlight}
              onBack={() => setSelectedFlight(null)}
              onOpenAlerts={(flight) => setAlertFlight(flight)}
            />
          ) : (
            <Tabs value={activeTab} onValueChange={(value) => handleTabChange(value as MonitorTab)} className="space-y-6">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="flights" className="flex items-center gap-2">
                  <Radar className="w-4 h-4" />
                  Flights ({data.flights.length})
                </TabsTrigger>
                <TabsTrigger value="crew" className="flex items-center gap-2">
                  <Users className="w-4 h-4" />
                  Crew ({data.crewPanels.length})
                </TabsTrigger>
                <TabsTrigger value="aircraft" className="flex items-center gap-2">
                  <Plane className="w-4 h-4" />
                  Aircraft ({data.aircraftPanels.length})
                </TabsTrigger>
                {agenticTabEnabled && (
                <TabsTrigger value="agentic" className="flex items-center gap-2">
                  <Bot className="w-4 h-4" />
                  AI Analysis {activeAnalysis && '✓'}
                </TabsTrigger>
              )}
              </TabsList>

              <TabsContent value="flights" className="space-y-6">
                <SummaryRow metrics={summaryMetrics} />
                <FlightGrid
                  flights={data.flights}
                  onOpenDetail={(flight) => {
                    setSelectedFlight(flight);
                  }}
                  onOpenAlerts={(flight) => {
                    setAlertFlight(flight);
                  }}
                />
              </TabsContent>

              <TabsContent value="crew" className="space-y-6">
                <CrewGrid crew={data.crewPanels} note={data.crewPanelsNote} />
              </TabsContent>

              <TabsContent value="aircraft" className="space-y-6">
                <AircraftGrid aircraft={data.aircraftPanels} note={data.aircraftPanelsNote} />
              </TabsContent>

              {agenticTabEnabled && (
                <TabsContent value="agentic" className="space-y-6">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <Badge variant="outline" className="w-fit">
                      {engineDescription}
                    </Badge>
                    {agenticStatus?.llm_temperature !== undefined && (
                      <span className="text-xs text-muted-foreground">
                        Temp: {agenticStatus.llm_temperature}
                      </span>
                    )}
                  </div>

                  {agenticSuspended && (
                    <Card className="border-amber-200 bg-amber-50/80 p-4 flex items-center gap-3">
                      <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
                      <div className="text-sm text-muted-foreground">
                        APIV2 is selected, but <code className="font-mono">VITE_AGENTIC_APIV2_BASE</code> is not set.
                        Point it to your google_a2a_agents_apiV2 service to enable the Gemini + Amadeus workflow.
                      </div>
                    </Card>
                  )}

                  {agenticError && (
                    <Card className="border-destructive/40 bg-destructive/5 p-6 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-destructive" />
                        <div>
                          <p className="text-[16px] font-semibold text-destructive">Agentic Analysis Error</p>
                          <p className="text-[14px] text-muted-foreground">{agenticError}</p>
                        </div>
                      </div>
                      <Button variant="outline" onClick={() => runAnalysis()} size="sm">Retry</Button>
                    </Card>
                  )}
                  
                  {agenticLoading && (
                    <Card className="p-8">
                      <div className="flex flex-col items-center justify-center space-y-4">
                        <Bot className="w-12 h-12 text-indigo-600 animate-pulse" />
                        <p className="text-lg font-semibold">Running Multi-Agent Analysis...</p>
                        <p className="text-sm text-muted-foreground">
                APIV2 workflow executing via Google ADK Agents (predictive → orchestrator → Gemini tools)
                        </p>
                      </div>
                    </Card>
                  )}
                  
                  {!agenticLoading && !agenticAnalysis && !agenticError && (
                    <Card className="p-8 text-center">
                      <Bot className="w-16 h-16 text-indigo-600 mx-auto mb-4" />
                      <h3 className="text-xl font-semibold mb-2">{enginePanelTitle}</h3>
                      <p className="text-muted-foreground mb-6">
                        Route the payload into google_a2a_agents_apiV2 for Gemini-orchestrated plans (Amadeus, crew legality, finance).
                      </p>
                      <Button
                        onClick={() => runAnalysis()}
                        disabled={!canRunAgentic}
                        className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-60"
                      >
                        <Bot className="w-4 h-4 mr-2" />
                        {canRunAgentic ? 'Run Analysis' : 'Configure Runtime'}
                      </Button>
                    </Card>
                  )}
                  
                  {activeAnalysis && <AgenticAnalysisPanel analysis={activeAnalysis} />}
                </TabsContent>
              )}
            </Tabs>
          )
        )}
      </div>

      <FlightAlertsModal
        flight={alertFlight}
        airport={airport}
        carrier={carrier}
        mode={sourceMode}
        onOpenChange={(open) => {
          if (!open) {
            setAlertFlight(null);
          }
        }}
      />
    </div>
  );
}

function SummaryRow({
  metrics,
}: {
  metrics: {
    label: string;
    value: string | number;
    helper: string;
    icon: React.ComponentType<{ className?: string }>;
    accent: string;
    span?: number;
  }[];
}) {
  return (
    <div className="overflow-x-auto">
      <div className="min-w-max flex gap-3 pr-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const widthClass = metric.span === 2 ? 'min-w-[320px]' : 'min-w-[200px]';
          return (
            <div
              key={metric.label}
              className={`rounded-2xl p-4 bg-gradient-to-br ${metric.accent} flex flex-col gap-3 shadow-sm ${widthClass}`}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="text-left">
                  <p className="text-[11px] uppercase text-muted-foreground tracking-wide">{metric.label}</p>
                  <p className="text-[20px] font-semibold leading-tight">{metric.value}</p>
                  <p className="text-[12px] text-muted-foreground">{metric.helper}</p>
                </div>
                <div className="w-10 h-10 rounded-full bg-white/60 flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-primary" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function FlightGrid({
  flights,
  onOpenDetail,
  onOpenAlerts,
}: {
  flights: FlightMonitorFlight[];
  onOpenDetail: (flight: FlightMonitorFlight) => void;
  onOpenAlerts: (flight: FlightMonitorFlight) => void;
}) {
  return (
    <div className="grid gap-4 flight-grid">
      {flights.map((flight) => (
        <Card
          key={flight.flightNumber}
          className="flight-card p-3 rounded-2xl shadow-sm hover:shadow-md transition-all cursor-pointer space-y-3"
          onClick={() => onOpenDetail(flight)}
        >
          <div className="flex items-start justify-between gap-2">
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-[16px] font-semibold">{flight.flightNumber}</h3>
                <Badge variant="outline" className="text-[10px]">{flight.route}</Badge>
              </div>
              <p className="text-[11px] text-muted-foreground">{flight.destination}</p>
              <p className="text-[11px] text-muted-foreground">
                {flight.aircraft} · Tail {flight.tailNumber}
              </p>
            </div>
            {flight.statusCategory !== 'normal' && (
              <Button
                size="icon"
                variant="ghost"
                className="text-amber-600 hover:text-amber-700"
                onClick={(e) => {
                  e.stopPropagation();
                  onOpenAlerts(flight);
                }}
              >
                <AlertTriangle className="w-4 h-4" />
              </Button>
            )}
          </div>
          <div className={`inline-flex text-[11px] px-2 py-0.5 rounded-full ${statusStyles[flight.statusCategory]}`}>
            {flight.status}
          </div>
          <div className="grid grid-cols-3 gap-2 text-[11px]">
            <div>
              <p className="text-muted-foreground">Gate</p>
              <p className="font-semibold text-[12px]">{flight.gate}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Sched</p>
              <p className="font-semibold text-[12px]">{formatClock(flight.scheduledDeparture)}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Est</p>
              <p className="font-semibold text-[12px]">{formatClock(flight.estimatedDeparture)}</p>
            </div>
          </div>
          <div>
            <Progress value={flight.turnProgress} />
            <div className="flex justify-between text-[10px] text-muted-foreground mt-1">
              <span>{flight.turnProgress}% turn</span>
              <span>Load {Math.round(flight.loadFactor * 100)}%</span>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-between text-[11px] gap-2">
            <p className="text-muted-foreground">Pax {flight.paxCount} • Tight {flight.connections.tight} • Missed {flight.connections.missed}</p>
            <div className="flex gap-1">
              <StatusDot ready={flight.crewReady} label="C" />
              <StatusDot ready={flight.aircraftReady} label="A" />
              <StatusDot ready={flight.groundReady} label="G" />
            </div>
          </div>
          <p className="text-[10px] text-muted-foreground">Updated {formatRelativeTime(flight.lastUpdated)}</p>
        </Card>
      ))}
    </div>
  );
}

function CrewGrid({ crew, note }: { crew: CrewPanel[]; note?: string | null }) {
  if (crew.length === 0) {
    return (
      <Card className="p-6">
        <p className="text-center text-muted-foreground">{note || 'No crew data available'}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {note && (
        <Card className="border-amber-200 bg-amber-50/60 p-4 flex items-center gap-3">
          <Info className="w-4 h-4 text-amber-600" />
          <div className="text-[13px]">{note}</div>
        </Card>
      )}
      <div className="grid gap-4">
        {crew.map((member) => (
          <Card key={member.employeeId} className="p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-[16px] font-semibold">{member.name}</h3>
                  <Badge variant="outline" className="text-[10px]">{member.rank}</Badge>
                  <Badge variant="secondary" className="text-[10px]">{member.employeeId}</Badge>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {member.flightNumber} · {member.aircraftType} · Tail {member.tailNumber || 'TBD'}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  {member.base} base · {member.fdpRemainingHours}h FDP remaining
                </p>
              </div>
              <div className="text-right">
                <Badge 
                  variant={member.dutyStatus === 'ON_DUTY' ? 'default' : 'secondary'} 
                  className="text-[10px]"
                >
                  {member.dutyStatus}
                </Badge>
                <p className="text-[10px] text-muted-foreground mt-1">
                  {member.readinessState}
                </p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-[11px]">
              <div>
                <p className="text-muted-foreground">Fatigue Risk</p>
                <p className="font-semibold text-[12px] capitalize">{member.fatigueRisk}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Duty Phase</p>
                <p className="font-semibold text-[12px]">{member.currentDutyPhase}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Phone</p>
                <p className="font-semibold text-[12px]">{member.contactPhone || 'N/A'}</p>
              </div>
              <div>
                <p className="text-muted-foreground">Email</p>
                <p className="font-semibold text-[12px]">{member.contactEmail || 'N/A'}</p>
              </div>
            </div>

            {member.availabilityNote && (
              <p className="text-[10px] text-muted-foreground">
                Available: {member.availabilityNote}
              </p>
            )}

            {member.statusNote && (
              <p className="text-[10px] text-amber-600">
                Status: {member.statusNote}
              </p>
            )}

            <p className="text-[10px] text-muted-foreground">
              Updated {formatRelativeTime(member.lastUpdated)}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}

function AircraftGrid({ aircraft, note }: { aircraft: AircraftPanel[]; note?: string | null }) {
  if (aircraft.length === 0) {
    return (
      <Card className="p-6">
        <p className="text-center text-muted-foreground">{note || 'No aircraft data available'}</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {note && (
        <Card className="border-amber-200 bg-amber-50/60 p-4 flex items-center gap-3">
          <Info className="w-4 h-4 text-amber-600" />
          <div className="text-[13px]">{note}</div>
        </Card>
      )}
      <div className="grid gap-4">
        {aircraft.map((plane) => (
          <Card key={plane.tailNumber} className="p-4 space-y-3">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-[16px] font-semibold">{plane.tailNumber}</h3>
                  <Badge variant="outline" className="text-[10px]">{plane.type}</Badge>
                  <Badge variant="secondary" className="text-[10px]">{plane.status}</Badge>
                </div>
                <p className="text-[11px] text-muted-foreground">
                  {plane.flightNumber || 'Not assigned'}
                </p>
                <p className="text-[11px] text-muted-foreground">
                  Gate {plane.gate || 'TBD'} · Standby {plane.standbyGate || 'TBD'}
                </p>
              </div>
              <div 
                className="w-4 h-4 rounded-full"
                style={{ backgroundColor: plane.statusColor }}
                title={plane.statusCategory}
              />
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-[11px]">
              <div>
                <p className="text-muted-foreground">Next Departure</p>
                <p className="font-semibold text-[12px]">
                  {plane.nextDeparture ? formatClock(plane.nextDeparture) : 'Not scheduled'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Last A-Check</p>
                <p className="font-semibold text-[12px]">
                  {plane.lastACheck ? formatRelativeTime(plane.lastACheck) : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Last C-Check</p>
                <p className="font-semibold text-[12px]">
                  {plane.lastCCheck ? formatRelativeTime(plane.lastCCheck) : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-muted-foreground">Status</p>
                <p className="font-semibold text-[12px] capitalize">{plane.statusCategory}</p>
              </div>
            </div>

            {plane.statusNotes && (
              <p className="text-[10px] text-amber-600">
                Notes: {plane.statusNotes}
              </p>
            )}

            <p className="text-[10px] text-muted-foreground">
              Updated {formatRelativeTime(plane.lastUpdated)}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}

function StatusDot({ ready, label }: { ready: boolean; label: string }) {
  return (
    <span
      className={`w-5 h-5 rounded-full text-[10px] flex items-center justify-center ${
        ready ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
      }`}
    >
      {label}
    </span>
  );
}

function AlertsDropdown({
  alerts,
  onSelectAlert,
}: {
  alerts: FlightMonitorAlert[];
  onSelectAlert?: (flightNumber: string) => void;
}) {
  const count = alerts.length;
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button className="relative bg-red-600 text-white hover:bg-red-700">
          <Bell className="w-4 h-4 mr-2" />
          Alerts
          {count > 0 && (
            <span className="ml-2 px-2 py-0.5 rounded-full bg-white text-red-600 text-[12px] font-semibold">
              {count}
            </span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80 p-0">
        <div className="p-3 border-b text-sm font-semibold">Active alerts</div>
        <div className="max-h-80 overflow-y-auto">
          {count === 0 ? (
            <div className="p-4 text-sm text-muted-foreground">No high-severity alerts.</div>
          ) : (
            alerts.map((alert) => (
              <DropdownMenuItem
                key={`${alert.flightNumber}-${alert.message}`}
                className="flex flex-col items-start gap-1 rounded-none border-b px-4 py-3 text-left last:border-b-0 focus:bg-slate-50"
                onSelect={() => onSelectAlert?.(alert.flightNumber)}
              >
                <div className="flex w-full items-center justify-between">
                  <div>
                    <p className="text-sm font-semibold">{alert.flightNumber}</p>
                    <p className="text-xs text-muted-foreground">
                      Gate {alert.gate} · +{alert.delayMinutes}m
                    </p>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {alert.paxImpacted} pax
                  </Badge>
                </div>
                <p className="text-sm">{alert.message}</p>
                <p className="text-xs text-muted-foreground">Next: {alert.recommendedAction}</p>
                <p className="text-[11px] uppercase text-muted-foreground tracking-wide">
                  Tap to view predictive insights
                </p>
              </DropdownMenuItem>
            ))
          )}
        </div>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function FlightDetailPage({
  flight,
  onBack,
  onOpenAlerts,
}: {
  flight: FlightMonitorFlight;
  onBack: () => void;
  onOpenAlerts: (flight: FlightMonitorFlight) => void;
}) {
  const readinessSnapshot = [
    { label: 'Crew', ready: flight.crewReady },
    { label: 'Ground', ready: flight.groundReady },
    { label: 'Aircraft', ready: flight.aircraftReady },
  ];

  return (
    <div className="space-y-6">
      <Button variant="ghost" className="gap-2" onClick={onBack}>
        <ArrowLeft className="w-4 h-4" />
        Back to flights
      </Button>

      <Card className="p-6 space-y-6">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm text-muted-foreground">{flight.route}</p>
            <p className="text-2xl font-semibold">{flight.flightNumber}</p>
            <p className="text-sm text-muted-foreground">{flight.destination}</p>
            <p className="text-sm text-muted-foreground">
              {flight.aircraft} · Tail {flight.tailNumber}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline" className="text-xs capitalize">
              {flight.status}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              Gate {flight.gate}
            </Badge>
            {flight.statusCategory !== 'normal' && (
              <Button
                size="sm"
                variant="destructive"
                className="gap-2"
                onClick={() => onOpenAlerts(flight)}
              >
                <AlertTriangle className="w-4 h-4" />
                View alerts
              </Button>
            )}
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          <DetailStat label="Scheduled" value={formatClock(flight.scheduledDeparture)} />
          <DetailStat label="Estimated" value={formatClock(flight.estimatedDeparture)} />
          <DetailStat label="Passengers" value={`${flight.paxCount}`} />
          <DetailStat label="Premium pax" value={`${flight.premiumPax}`} />
          <DetailStat label="Standby gate" value={flight.standbyGate} />
          <DetailStat label="Updated" value={formatRelativeTime(flight.lastUpdated)} />
        </div>

        <div>
          <p className="text-sm text-muted-foreground mb-1">Turn progress</p>
          <Progress value={flight.turnProgress} />
          <p className="text-xs text-muted-foreground mt-1">
            {flight.turnProgress}% complete · Baggage {flight.baggageStatus} · Fuel {flight.fuelStatus}
          </p>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <div className="rounded-2xl border bg-white p-4 shadow-sm lg:col-span-2 space-y-3">
            <p className="text-sm font-semibold">Milestones</p>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
              {flight.milestones.map((milestone) => (
                <div key={`${flight.flightNumber}-${milestone.label}`}>
                  <div
                    className={`h-1 rounded-full ${
                      milestone.state === 'complete'
                        ? 'bg-emerald-500'
                        : milestone.state === 'active'
                          ? 'bg-amber-500'
                          : 'bg-slate-200'
                    }`}
                  />
                  <p className="text-[12px] font-semibold mt-2">{milestone.label}</p>
                  <p className="text-[11px] uppercase tracking-wide text-muted-foreground">{milestone.state}</p>
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border bg-white p-4 shadow-sm space-y-3">
            <p className="text-sm font-semibold">Operational snapshot</p>
            <div className="text-sm space-y-1 text-muted-foreground">
              <p>Tight connections: {flight.connections.tight}</p>
              <p>Missed connections: {flight.connections.missed}</p>
              <p>VIP connections: {flight.connections.vip}</p>
              <p>Load factor: {Math.round(flight.loadFactor * 100)}%</p>
              <p>
                Readiness:{' '}
                {readinessSnapshot
                  .map((item) => `${item.label} ${item.ready ? 'Ready' : 'Hold'}`)
                  .join(' · ')}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border bg-white p-4 shadow-sm space-y-3">
          <p className="text-sm font-semibold">Irregular ops</p>
          <p className="text-sm text-muted-foreground">{flight.irregularOps.reason}</p>
          <ul className="list-disc pl-5 space-y-1 text-sm">
            {flight.irregularOps.actions.map((action) => (
              <li key={action}>{action}</li>
            ))}
          </ul>
        </div>
      </Card>
    </div>
  );
}

function FlightAlertsModal({
  flight,
  airport,
  carrier,
  mode,
  onOpenChange,
}: {
  flight: FlightMonitorFlight | null;
  airport: string;
  carrier: string;
  mode: MonitorMode;
  onOpenChange: (open: boolean) => void;
}) {
  const { alertData, loading, fetchAlerts } = usePredictiveAlerts();

  // Fetch predictive alerts when flight changes
  useEffect(() => {
    if (flight?.flightNumber) {
      fetchAlerts(flight.flightNumber, airport, carrier, mode);
    }
  }, [airport, carrier, mode, flight?.flightNumber, fetchAlerts]);

  const hasPredictiveAlert = alertData?.hasPredictiveAlert && alertData?.alert;

  return (
    <Dialog open={Boolean(flight)} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Alerts — {flight?.flightNumber}</DialogTitle>
          <DialogDescription>
            {flight
              ? `Review operational status, predictive insights, and recommended actions for ${flight.flightNumber}.`
              : 'Select a flight with alerts to review passenger impact and recommended actions.'}
          </DialogDescription>
        </DialogHeader>
        {flight ? (
          <div className="space-y-4 text-sm">
            {/* Operational Status */}
            <Card className={`p-4 ${statusStyles[flight.statusCategory]}`}>
              <p className="font-semibold mb-1">{flight.status}</p>
              <p className="text-xs text-muted-foreground">Gate {flight.gate} · {flight.paxImpacted} pax impacted</p>
            </Card>

            {/* Predictive Signals Section */}
            {loading && (
              <Card className="p-4 border-indigo-100 bg-indigo-50/50">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 animate-pulse text-indigo-600" />
                  <p className="text-sm text-indigo-900">Loading predictive insights...</p>
                </div>
              </Card>
            )}

            {hasPredictiveAlert && alertData.alert && (
              <Card className="p-4 border-indigo-200 bg-gradient-to-br from-indigo-50 to-white">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-indigo-600" />
                    <h4 className="font-semibold text-indigo-900">Predictive Signals</h4>
                  </div>
                  <Badge 
                    variant={
                      alertData.alert.severity === 'high' 
                        ? 'destructive' 
                        : alertData.alert.severity === 'medium'
                        ? 'default'
                        : 'secondary'
                    }
                    className="text-xs"
                  >
                    {alertData.alert.severity.toUpperCase()} RISK
                  </Badge>
                </div>

                {(alertData.alert.prediction || alertData.alert.reasoning) && (
                  <div className="mb-4 rounded-lg border border-indigo-100 bg-white/70 p-3">
                    <div className="flex items-start gap-3">
                      <Bot className="w-5 h-5 text-indigo-600 mt-0.5" />
                      <div>
                        <p className="text-xs uppercase text-muted-foreground">Predictive agent</p>
                        <p className="text-sm font-semibold text-indigo-900">
                          {alertData.alert.prediction || 'Predictive agent context unavailable'}
                        </p>
                        {alertData.alert.reasoning && (
                          <p className="text-sm text-slate-600 mt-1">
                            {alertData.alert.reasoning}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Risk Probability */}
                <div className="mb-4">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-muted-foreground">Disruption Probability</span>
                    <span className="text-sm font-semibold">
                      {Math.round(alertData.alert.riskProbability * 100)}%
                    </span>
                  </div>
                  <Progress value={alertData.alert.riskProbability * 100} className="h-2" />
                </div>

                {/* Risk Drivers */}
                <div className="mb-4">
                  <p className="text-xs uppercase text-muted-foreground mb-2">Risk Drivers</p>
                  <div className="space-y-2">
                    {alertData.alert.drivers.map((driver, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs">
                        <div className="flex-shrink-0 w-16">
                          <Badge variant="outline" className="text-[10px]">
                            {driver.category}
                          </Badge>
                        </div>
                        <div className="flex-1">
                          <p className="text-muted-foreground">{driver.evidence}</p>
                          <Progress 
                            value={driver.score * 100} 
                            className="h-1 mt-1" 
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* AI Recommendations */}
                <div>
                  <p className="text-xs uppercase text-muted-foreground mb-2">AI Recommendations</p>
                  <ul className="space-y-1.5">
                    {alertData.alert.recommendations.map((rec, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-indigo-600 mt-0.5">•</span>
                        <span className="text-sm">{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <p className="text-[10px] text-muted-foreground mt-3">
                  Generated {new Date(alertData.alert.timestamp).toLocaleTimeString()}
                </p>
              </Card>
            )}

            {/* Standard Operational Actions */}
            <div>
              <p className="text-xs uppercase text-muted-foreground mb-2">Operational Actions</p>
              <ul className="list-disc pl-5 space-y-1">
                {flight.irregularOps.actions.map((action) => (
                  <li key={action}>{action}</li>
                ))}
              </ul>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No flight selected.</p>
        )}
      </DialogContent>
    </Dialog>
  );
}

function DetailStat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs uppercase text-muted-foreground">{label}</p>
      <p className="text-sm font-semibold">{value}</p>
    </div>
  );
}

function MonitorSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex gap-3 overflow-x-auto pr-4">
        {Array.from({ length: 5 }).map((_, index) => (
          <Card key={`metric-skeleton-${index}`} className="p-3 min-w-[180px]">
            <Skeleton className="h-4 w-24 mb-2" />
            <Skeleton className="h-6 w-16 mb-1" />
            <Skeleton className="h-3 w-20" />
          </Card>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {Array.from({ length: 3 }).map((_, index) => (
          <Card key={`flight-skeleton-${index}`} className="p-4 space-y-4">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-2 w-full" />
            <Skeleton className="h-4 w-24" />
          </Card>
        ))}
      </div>
    </div>
  );
}
