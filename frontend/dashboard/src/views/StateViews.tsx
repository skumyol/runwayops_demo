import React from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Skeleton } from '../components/ui/skeleton';
import { AlertCircle, Inbox, RefreshCw } from 'lucide-react';

export function EmptyState() {
  return (
    <div className="min-h-screen bg-[#EBEDEC] flex items-center justify-center">
      <Card className="p-12 rounded-[12px] max-w-md text-center">
        <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center mx-auto mb-4">
          <Inbox className="w-8 h-8 text-muted-foreground" />
        </div>
        <h2 className="text-[20px] font-semibold mb-2">No Active Disruptions</h2>
        <p className="text-[14px] text-muted-foreground mb-6">
          All flights are operating normally. This queue will populate automatically when an IROP event occurs.
        </p>
        <Button variant="outline">View Historical Events</Button>
      </Card>
    </div>
  );
}

export function LoadingState() {
  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      <div className="h-16 bg-white border-b border-border flex items-center px-8">
        <Skeleton className="h-8 w-64" />
      </div>
      
      <div className="p-8">
        <div className="grid grid-cols-4 gap-6 mb-8">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i} className="p-6 rounded-[12px]">
              <Skeleton className="h-4 w-32 mb-4" />
              <Skeleton className="h-10 w-24 mb-2" />
              <Skeleton className="h-3 w-20" />
            </Card>
          ))}
        </div>

        <div className="space-y-4">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6 rounded-[12px]">
              <Skeleton className="h-6 w-48 mb-4" />
              <div className="grid grid-cols-3 gap-6">
                <div>
                  <Skeleton className="h-4 w-20 mb-2" />
                  <div className="flex gap-2">
                    <Skeleton className="h-6 w-16" />
                    <Skeleton className="h-6 w-16" />
                  </div>
                </div>
                <div>
                  <Skeleton className="h-4 w-20 mb-2" />
                  <div className="flex gap-2">
                    <Skeleton className="h-6 w-12" />
                    <Skeleton className="h-6 w-12" />
                  </div>
                </div>
                <div>
                  <Skeleton className="h-4 w-20 mb-2" />
                  <Skeleton className="h-4 w-32" />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}

export function ErrorState({ onRetry }: { onRetry?: () => void }) {
  return (
    <div className="min-h-screen bg-[#EBEDEC] flex items-center justify-center">
      <Card className="p-12 rounded-[12px] max-w-md text-center">
        <div className="w-16 h-16 rounded-full bg-destructive/10 flex items-center justify-center mx-auto mb-4">
          <AlertCircle className="w-8 h-8 text-destructive" />
        </div>
        <h2 className="text-[20px] font-semibold mb-2">Unable to Load Data</h2>
        <p className="text-[14px] text-muted-foreground mb-6">
          There was an error connecting to the IROP system. Please check your connection and try again.
        </p>
        <Button onClick={onRetry}>
          <RefreshCw className="w-4 h-4 mr-2" />
          Retry
        </Button>
      </Card>
    </div>
  );
}

export function ReadOnlyMode() {
  return (
    <div className="h-12 bg-warning/10 border-y border-warning/20 flex items-center justify-center">
      <div className="flex items-center gap-2">
        <AlertCircle className="w-4 h-4 text-warning" />
        <span className="text-[14px] font-semibold text-warning">
          Read-Only Mode: Inventory is currently locked for system maintenance
        </span>
      </div>
    </div>
  );
}
