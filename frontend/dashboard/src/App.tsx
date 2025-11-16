import React, { useState } from 'react';
import { AgentPassengerPanel } from './views/AgentPassengerPanel';
import { PassengerReaccommodationView } from './views/PassengerReaccommodationView';
import { IOCQueues } from './views/IOCQueues';
import { CohortDetail } from './views/CohortDetail';
import { Reports } from './views/Reports';
import { EmptyState, LoadingState, ErrorState, ReadOnlyMode } from './views/StateViews';
import { RealtimeFlightMonitor } from './views/RealtimeFlightMonitor';
import { AgenticDebugPanel } from './views/AgenticDebugPanel';
import { WhatIfScenario } from './views/WhatIfScenario';
import { Toaster } from './components/ui/sonner';
import { Button } from './components/ui/button';
import { Tabs, TabsList, TabsTrigger } from './components/ui/tabs';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
  DropdownMenuLabel,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from './components/ui/dropdown-menu';
import { Users, BarChart3, User, Layers, Radar, Bug, FlaskConical } from 'lucide-react';
import { AgenticProvider, useAgenticContext } from './context/AgenticContext';
import type { AgenticEngine } from './types/agentic';
import {
  AGENTIC_ENGINE_OPTIONS,
  describeAgenticEngine,
  resolveAgenticEngineBase,
} from './lib/agentic';
import { MonitorMode } from './hooks/useFlightMonitor';

type View = 'monitor' | 'agent' | 'queues' | 'cohort' | 'reports' | 'whatif' | 'empty' | 'loading' | 'error' | 'debug';

export default function App() {
  return (
    <AgenticProvider>
      <AppShell />
    </AgenticProvider>
  );
}

const monitorModeOptions: Array<{ value: MonitorMode; label: string }> = [
  { value: 'synthetic', label: 'Synthetic (playbook)' },
  { value: 'realtime', label: 'Realtime (aviationstack)' },
];

function AppShell() {
  const searchParams = typeof window !== 'undefined' ? new URLSearchParams(window.location.search) : null;
  const role = searchParams?.get('role');
  const passengerPnr = searchParams?.get('pnr');

  if (role === 'passenger') {
    return <PassengerReaccommodationView pnr={passengerPnr ?? null} />;
  }

  const [currentView, setCurrentView] = useState<View>('monitor');
  const [selectedFlight, setSelectedFlight] = useState<string>('');
  const [isReadOnly] = useState(false);
  const [whatIfResults, setWhatIfResults] = useState<any | null>(null);
  const [whatIfProgress, setWhatIfProgress] = useState<any[]>([]);
  const {
    agenticEngine,
    setAgenticEngine,
    monitorAirport,
    setMonitorAirport,
    monitorCarrier,
    setMonitorCarrier,
    monitorMode,
    setMonitorMode,
  } = useAgenticContext();
  const agenticBase = resolveAgenticEngineBase(agenticEngine);
  const agenticDescription = describeAgenticEngine(agenticEngine);

  const handleAgenticEngineChange = (value: string) => {
    setAgenticEngine(value as AgenticEngine);
  };

  const handleNavigateToCohort = (flightNumber: string) => {
    setSelectedFlight(flightNumber);
    setCurrentView('cohort');
  };

  const handleBackToQueue = () => {
    setCurrentView('queues');
    setSelectedFlight('');
  };

  const renderView = () => {
    switch (currentView) {
      case 'agent':
        return <AgentPassengerPanel />;
      case 'cohort':
        return <CohortDetail flightNumber={selectedFlight} onBack={handleBackToQueue} />;
      case 'reports':
        return <Reports />;
      case 'whatif':
        return null;
      case 'monitor':
        return <RealtimeFlightMonitor />;
      case 'debug':
        return <AgenticDebugPanel />;
      case 'empty':
        return <EmptyState />;
      case 'loading':
        return <LoadingState />;
      case 'error':
        return <ErrorState onRetry={() => setCurrentView('queues')} />;
      case 'queues':
        return null;
      default:
        return <RealtimeFlightMonitor />;
    }
  };

  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      {isReadOnly && <ReadOnlyMode />}
      
      {/* Global Navigation */}
      <div className="h-14 bg-primary border-b border-border flex items-center justify-between px-8">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded bg-white flex items-center justify-center">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="#006564"/>
              <path d="M2 17L12 22L22 17" stroke="#006564" strokeWidth="2"/>
              <path d="M2 12L12 17L22 12" stroke="#006564" strokeWidth="2"/>
            </svg>
          </div>
          <span className="text-white text-[16px] font-semibold">Cathay Pacific IROP</span>
        </div>
        
        <Tabs value={currentView} onValueChange={(v: string) => setCurrentView(v as View)}>
          <TabsList className="bg-primary/20 border border-white/10">
            <TabsTrigger 
              value="monitor" 
              className="text-white/70 data-[state=active]:bg-white/10 data-[state=active]:text-white"
            >
              <Radar className="w-4 h-4 mr-2" />
              Realtime Monitor
            </TabsTrigger>
            <TabsTrigger 
              value="queues" 
              className="text-white/70 data-[state=active]:bg-white/10 data-[state=active]:text-white"
            >
              <Layers className="w-4 h-4 mr-2" />
              IOC Dashboard
            </TabsTrigger>
            <TabsTrigger 
              value="agent" 
              className="text-white/70 data-[state=active]:bg-white/10 data-[state=active]:text-white"
            >
              <User className="w-4 h-4 mr-2" />
              Agent Console
            </TabsTrigger>
            <TabsTrigger 
              value="whatif" 
              className="text-white/70 data-[state=active]:bg-white/10 data-[state=active]:text-white"
            >
              <FlaskConical className="w-4 h-4 mr-2" />
              What-If Analysis
            </TabsTrigger>
            <TabsTrigger 
              value="reports" 
              className="text-white/70 data-[state=active]:bg-white/10 data-[state=active]:text-white"
            >
              <BarChart3 className="w-4 h-4 mr-2" />
              Reports
            </TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="flex items-center gap-3">
          {/* Dev Tools Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button 
                variant="ghost" 
                size="sm"
                className="text-white/70 hover:text-white hover:bg-white/10"
              >
                <Bug className="w-4 h-4 mr-2" />
                Dev Tools
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72 space-y-2">
              <DropdownMenuLabel>Agent runtime</DropdownMenuLabel>
              <DropdownMenuRadioGroup
                value={agenticEngine}
                onValueChange={handleAgenticEngineChange}
              >
                {AGENTIC_ENGINE_OPTIONS.map((option) => (
                  <DropdownMenuRadioItem key={option.value} value={option.value}>
                    <div className="flex flex-col">
                      <span>{option.label}</span>
                      <span className="text-[11px] text-muted-foreground">
                        {option.helper}
                      </span>
                    </div>
                  </DropdownMenuRadioItem>
                ))}
              </DropdownMenuRadioGroup>
              <div className="px-2 pb-2 text-[11px] text-muted-foreground">
                {agenticDescription}
                {agenticBase && (
                  <span className="block text-[10px] text-muted-foreground/80">
                    APIV2 base: {agenticBase}
                  </span>
                )}
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>Flight data inputs</DropdownMenuLabel>
              <div className="px-2 pb-2 space-y-3 text-[11px] text-muted-foreground">
                <label className="flex flex-col gap-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                  Airport
                  <input
                    className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                    value={monitorAirport}
                    onChange={(event) => setMonitorAirport(event.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                  Carrier
                  <input
                    className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                    value={monitorCarrier}
                    onChange={(event) => setMonitorCarrier(event.target.value)}
                  />
                </label>
                <label className="flex flex-col gap-1 text-[10px] uppercase tracking-wide text-muted-foreground">
                  Data source
                  <select
                    className="w-full rounded-md border border-border bg-background px-2 py-1 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/30"
                    value={monitorMode}
                    onChange={(event) =>
                      setMonitorMode(event.target.value as MonitorMode)
                    }
                  >
                    {monitorModeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <p className="text-[10px] text-muted-foreground/80">
                  Applies to flight monitor + agentic analysis requests.
                </p>
              </div>
              <DropdownMenuSeparator />
              <DropdownMenuLabel>UI State Testing</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setCurrentView('empty')}>
                <span className="text-muted-foreground mr-2">📭</span>
                Empty State
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setCurrentView('loading')}>
                <span className="text-muted-foreground mr-2">⏳</span>
                Loading State
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => setCurrentView('error')}>
                <span className="text-muted-foreground mr-2">⚠️</span>
                Error State
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setCurrentView('debug')}>
                <span className="text-muted-foreground mr-2">🧪</span>
                Agentic Debug Panel
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => setCurrentView('monitor')}>
                <span className="text-muted-foreground mr-2">↩️</span>
                Back to Monitor
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
          
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center">
            <Users className="w-4 h-4 text-white" />
          </div>
        </div>
      </div>

      <div className={currentView === 'queues' ? 'block' : 'hidden'} aria-hidden={currentView !== 'queues'}>
        <IOCQueues onNavigateToCohort={handleNavigateToCohort} />
      </div>

      <div className={currentView === 'whatif' ? 'block' : 'hidden'} aria-hidden={currentView !== 'whatif'}>
        <WhatIfScenario
          initialResults={whatIfResults}
          initialProgress={whatIfProgress}
          onResultsChange={setWhatIfResults}
          onProgressChange={setWhatIfProgress}
        />
      </div>

      {renderView()}

      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: 'white',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            borderRadius: '12px',
          },
        }}
      />
    </div>
  );
}
