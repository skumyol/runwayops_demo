import { ReactNode } from 'react';
import { AlertTriangle, Bot, CloudLightning, Plane, Users } from 'lucide-react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { PredictiveSignals } from '../hooks/useFlightMonitor';

const driverIconMap: Record<string, ReactNode> = {
  weather: <CloudLightning className="w-4 h-4" />,
  aircraft: <Plane className="w-4 h-4" />,
  crew: <Users className="w-4 h-4" />,
};

interface PredictiveInsightCardProps {
  signals?: PredictiveSignals | null;
  onRunAnalysis?: () => void;
  showRunCta?: boolean;
}

export function PredictiveInsightCard({ signals, onRunAnalysis, showRunCta }: PredictiveInsightCardProps) {
  if (!signals) return null;

  const percent = Math.round((signals.risk_probability ?? 0) * 100);
  const drivers = (signals.drivers ?? []).slice(0, 3);

  const statusLabel = signals.disruption_detected ? 'Disruption likely' : 'Monitoring';
  const statusVariant = signals.disruption_detected ? 'destructive' : 'secondary';

  return (
    <Card className="p-6 border border-indigo-100 bg-white">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Badge variant={statusVariant} className="text-xs">
              {statusLabel}
            </Badge>
            <span className="text-sm text-muted-foreground">Predictive signal</span>
          </div>
          <h3 className="text-2xl font-semibold text-gray-900">
            {percent}% risk probability
          </h3>
          <p className="text-sm text-muted-foreground max-w-2xl mt-1">
            {signals.reasoning}
          </p>
        </div>
        {showRunCta && onRunAnalysis && (
          <Button onClick={onRunAnalysis} className="bg-indigo-600 hover:bg-indigo-700">
            <Bot className="w-4 h-4 mr-2" />
            Run AI Analysis
          </Button>
        )}
      </div>

      <div className="grid gap-4 mt-6 md:grid-cols-3">
        {drivers.map((driver) => (
          <div key={driver.category} className="p-4 border border-slate-100 rounded-lg bg-slate-50">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase text-slate-600">
              {driverIconMap[driver.category.toLowerCase()] ?? <AlertTriangle className="w-4 h-4" />}
              {driver.category}
            </div>
            <p className="text-lg font-bold text-slate-900 mt-2">{Math.round(driver.score * 100)}%</p>
            <Progress value={driver.score * 100} className="mt-2 h-1.5" />
            <p className="text-xs text-slate-600 mt-2">{driver.evidence}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
