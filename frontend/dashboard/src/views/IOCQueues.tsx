import React, { useMemo, useState } from 'react';
import { TopNav } from '../components/TopNav';
import { FilterBar, Filter } from '../components/FilterBar';
import { MetricCard } from '../components/MetricCard';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { TierTag } from '../components/TierTag';
import { Switch } from '../components/ui/switch';
import { Label } from '../components/ui/label';
import { Users, Clock, DollarSign, TrendingUp, AlertCircle, ChevronRight, RefreshCw } from 'lucide-react';
import { TierType } from '../types/reaccommodation';
import { Skeleton } from '../components/ui/skeleton';
import { useReaccommodationFlights } from '../hooks/useReaccommodation';
import { toast } from 'sonner@2.0.3';

interface IOCQueuesProps {
  onNavigateToCohort?: (flightNumber: string) => void;
}

export function IOCQueues({ onNavigateToCohort }: IOCQueuesProps) {
  const [station, setStation] = useState('HKG');
  const [protectPremium, setProtectPremium] = useState(true);
  const [selectedFlights, setSelectedFlights] = useState<string[]>([]);
  const { flights, loading, error, refresh } = useReaccommodationFlights();
  const activeFlightNumbers = useMemo(() => new Set(flights.map((flight) => flight.flightNumber)), [flights]);
  const metrics = useMemo(() => {
    if (!flights.length) {
      return [
        { label: 'Active cohorts', value: '0', icon: Users, trend: 'Awaiting data', trendUp: false },
        { label: 'Impacted pax', value: '0', icon: Clock, trend: '', trendUp: false },
        { label: 'Avg suitability', value: '0%', icon: DollarSign, trend: '', trendUp: false },
        { label: 'Exceptions flagged', value: '0', icon: TrendingUp, trend: '', trendUp: false },
      ];
    }
    const totalPassengers = flights.reduce((sum, flight) => sum + flight.affectedCount, 0);
    const avgSuitability = Math.round(
      flights.reduce((sum, flight) => sum + flight.defaultSuitability, 0) / flights.length
    );
    const exceptions = flights.reduce((sum, flight) => sum + flight.exceptions, 0);
    const premiumPax = flights.reduce((sum, flight) => {
      const premium = flight.tierBreakdown.filter((tier) => tier.tier !== 'Green');
      return sum + premium.reduce((tierSum, tier) => tierSum + tier.count, 0);
    }, 0);
    return [
      { label: 'Active cohorts', value: flights.length.toString(), icon: Users, trend: `${premiumPax} premium pax`, trendUp: true },
      { label: 'Impacted pax', value: totalPassengers.toString(), icon: Clock, trend: `${Math.max(...flights.map((f) => f.affectedCount))} max`, trendUp: true },
      { label: 'Avg suitability', value: `${avgSuitability}%`, icon: DollarSign, trend: 'Default fit score', trendUp: avgSuitability >= 80 },
      { label: 'Exceptions flagged', value: exceptions.toString(), icon: TrendingUp, trend: 'Needs manual action', trendUp: exceptions < totalPassengers * 0.2 },
    ];
  }, [flights]);

  const filters: Filter[] = [
    {
      id: 'station',
      label: 'Station',
      type: 'select',
      options: [
        { label: 'Hong Kong (HKG)', value: 'HKG' },
        { label: 'Los Angeles (LAX)', value: 'LAX' },
        { label: 'London (LHR)', value: 'LHR' },
        { label: 'San Francisco (SFO)', value: 'SFO' },
      ],
      value: station,
      onValueChange: setStation,
    },
    {
      id: 'severity',
      label: 'Severity',
      type: 'select',
      options: [
        { label: 'All', value: 'all' },
        { label: 'High', value: 'high' },
        { label: 'Medium', value: 'medium' },
        { label: 'Low', value: 'low' },
      ],
    },
    {
      id: 'cabin',
      label: 'Cabin',
      type: 'select',
      options: [
        { label: 'All Cabins', value: 'all' },
        { label: 'First (F)', value: 'F' },
        { label: 'Business (J)', value: 'J' },
        { label: 'Premium Economy (W)', value: 'W' },
        { label: 'Economy (Y)', value: 'Y' },
      ],
    },
  ];

  const handleBulkAction = (action: string) => {
    if (selectedFlights.length === 0) {
      toast.error('No flights selected');
      return;
    }
    toast.success(`${action} applied to ${selectedFlights.length} flight(s)`);
    setSelectedFlights([]);
  };

  const toggleFlightSelection = (flightNumber: string) => {
    if (!activeFlightNumbers.has(flightNumber)) return;
    setSelectedFlights((prev) =>
      prev.includes(flightNumber)
        ? prev.filter((f) => f !== flightNumber)
        : [...prev, flightNumber]
    );
  };

  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      <TopNav 
        title="IROP Recovery Dashboard" 
        subtitle="Integrated Operations Center"
        actions={
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Switch 
                id="protect-premium" 
                checked={protectPremium}
                onCheckedChange={setProtectPremium}
              />
              <Label htmlFor="protect-premium" className="text-[14px] cursor-pointer">
                Protect premium inventory
              </Label>
            </div>
          </div>
        }
      />
      
      <FilterBar filters={filters} />

      <div className="p-8">
        <div className="grid grid-cols-4 gap-6 mb-8">
          {metrics.map((metric) => (
            <MetricCard
              key={metric.label}
              label={metric.label}
              value={metric.value}
              icon={metric.icon}
              trend={metric.trend}
              trendUp={metric.trendUp}
            />
          ))}
        </div>

        {error && (
          <Card className="p-4 mb-6 border border-destructive/40 bg-destructive/10 flex items-center justify-between">
            <span className="text-[14px] text-destructive">{error}</span>
            <Button variant="outline" size="sm" onClick={refresh}>
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </Card>
        )}

        {/* Flight Queue List */}
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-[18px] leading-[24px] font-semibold">Affected Flights</h2>
            {selectedFlights.length > 0 && (
              <div className="flex items-center gap-3">
                <span className="text-[14px] text-muted-foreground">
                  {selectedFlights.length} selected
                </span>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleBulkAction('Default options applied')}
                >
                  Apply Default
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => handleBulkAction('Offers sent')}
                >
                  Send Offers
                </Button>
                <Button 
                  size="sm"
                  onClick={() => handleBulkAction('Cohort opened')}
                >
                  Open Cohort
                </Button>
              </div>
            )}
          </div>

          {loading && !flights.length && (
            <>
              {Array.from({ length: 3 }).map((_, idx) => (
                <Card key={`skeleton-${idx}`} className="p-6 rounded-[12px]">
                  <Skeleton className="h-6 w-1/3 mb-4" />
                  <Skeleton className="h-4 w-1/2 mb-4" />
                  <div className="grid grid-cols-3 gap-4">
                    {Array.from({ length: 3 }).map((__, innerIdx) => (
                      <Skeleton key={innerIdx} className="h-16 w-full" />
                    ))}
                  </div>
                </Card>
              ))}
            </>
          )}

          {!loading && !flights.length && !error && (
            <Card className="p-8 text-center border-dashed border-muted-foreground/40">
              <p className="text-muted-foreground mb-4">No disrupted flights for the selected filters.</p>
              <Button variant="outline" onClick={refresh}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh data
              </Button>
            </Card>
          )}

          {flights.map((flight) => (
            <Card 
              key={flight.flightNumber}
              className={`p-6 rounded-[12px] transition-all cursor-pointer ${
                selectedFlights.includes(flight.flightNumber) ? 'ring-2 ring-primary' : ''
              }`}
              onClick={() => toggleFlightSelection(flight.flightNumber)}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-4 mb-4">
                    <h3 className="text-[20px] font-semibold">{flight.flightNumber}</h3>
                    <span className="text-[16px] text-muted-foreground">{flight.route}</span>
                    <Badge 
                      variant={flight.severity === 'High' ? 'destructive' : 'secondary'}
                      className="text-[12px]"
                    >
                      {flight.severity}
                    </Badge>
                    <span className="text-[14px] text-muted-foreground">
                      {flight.affectedCount} affected
                    </span>
                  </div>

                  <div className="grid grid-cols-3 gap-6">
                    {/* Tier Breakdown */}
                    <div>
                      <h4 className="text-[12px] text-muted-foreground mb-2">By Tier</h4>
                      <div className="flex flex-wrap gap-2">
                        {flight.tierBreakdown.map((item) => (
                          <div key={item.tier} className="flex items-center gap-2">
                            <TierTag tier={item.tier as TierType} />
                            <span className="text-[14px]">{item.count}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* Cabin Breakdown */}
                    <div>
                      <h4 className="text-[12px] text-muted-foreground mb-2">By Cabin</h4>
                      <div className="flex flex-wrap gap-2">
                        {flight.cabinBreakdown.map((item) => (
                          <Badge key={item.cabin} variant="outline" className="text-[12px]">
                            {item.cabin}: {item.count}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Stats */}
                    <div>
                      <h4 className="text-[12px] text-muted-foreground mb-2">Status</h4>
                      <div className="space-y-1 text-[14px]">
                        <div className="flex items-center gap-2">
                          <span className="text-success">✓</span>
                          <span>{flight.defaultSuitability}% default suitable</span>
                        </div>
                        {flight.exceptions > 0 && (
                          <div className="flex items-center gap-2">
                            <AlertCircle className="w-4 h-4 text-destructive" />
                            <span className="text-destructive">{flight.exceptions} exceptions</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onNavigateToCohort?.(flight.flightNumber);
                  }}
                >
                  View Details <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
