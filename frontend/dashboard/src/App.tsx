import React, { useState } from 'react';
import { AgentPassengerPanel } from './views/AgentPassengerPanel';
import { IOCQueues } from './views/IOCQueues';
import { CohortDetail } from './views/CohortDetail';
import { Reports } from './views/Reports';
import { EmptyState, LoadingState, ErrorState, ReadOnlyMode } from './views/StateViews';
import { RealtimeFlightMonitor } from './views/RealtimeFlightMonitor';
import { Toaster } from './components/ui/sonner';
import { Button } from './components/ui/button';
import { Tabs, TabsList, TabsTrigger } from './components/ui/tabs';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator, DropdownMenuLabel } from './components/ui/dropdown-menu';
import { Users, BarChart3, User, Layers, Radar, Bug } from 'lucide-react';

type View = 'monitor' | 'agent' | 'queues' | 'cohort' | 'reports' | 'empty' | 'loading' | 'error';

export default function App() {
  const [currentView, setCurrentView] = useState<View>('monitor');
  const [selectedFlight, setSelectedFlight] = useState<string>('');
  const [isReadOnly] = useState(false);

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
      case 'queues':
        return <IOCQueues onNavigateToCohort={handleNavigateToCohort} />;
      case 'cohort':
        return <CohortDetail flightNumber={selectedFlight} onBack={handleBackToQueue} />;
      case 'reports':
        return <Reports />;
      case 'monitor':
        return <RealtimeFlightMonitor />;
      case 'empty':
        return <EmptyState />;
      case 'loading':
        return <LoadingState />;
      case 'error':
        return <ErrorState onRetry={() => setCurrentView('queues')} />;
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
            <DropdownMenuContent align="end" className="w-56">
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
