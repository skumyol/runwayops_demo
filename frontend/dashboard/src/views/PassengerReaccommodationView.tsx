import React, { useEffect, useState } from 'react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Separator } from '../components/ui/separator';
import { Skeleton } from '../components/ui/skeleton';
import { User, Plane, Clock, MapPin, Mail } from 'lucide-react';
import { usePassengerDetail } from '../hooks/useReaccommodation';
import { OptionCard } from '../components/OptionCard';
import type { ReaccommodationOption } from '../types/reaccommodation';
import { toast } from 'sonner';

interface PassengerReaccommodationViewProps {
  pnr: string | null;
}

export function PassengerReaccommodationView({ pnr }: PassengerReaccommodationViewProps) {
  const { detail, loading, error } = usePassengerDetail(pnr);
  const passenger = detail?.passenger ?? null;
  const options = (detail?.options ?? []) as ReaccommodationOption[];
  const [selectedOptionId, setSelectedOptionId] = useState<string | null>(options[0]?.id ?? null);

  useEffect(() => {
    if (!options.length) {
      setSelectedOptionId(null);
      return;
    }
    if (!selectedOptionId || !options.some((opt) => opt.id === selectedOptionId)) {
      setSelectedOptionId(options[0].id);
    }
  }, [options, selectedOptionId]);

  const handleConfirm = () => {
    if (!passenger || !selectedOptionId) return;
    toast.success('Option confirmed', {
      description: `You have selected option ${selectedOptionId} for ${passenger.name}. An agent will complete the ticketing if required.`,
    });
  };

  const passengerEmail =
    (passenger?.basePassenger?.contactInfo as { email?: string } | undefined)?.email ?? 'customer@cathay.com';

  if (!pnr) {
    return (
      <div className="min-h-screen bg-[#EBEDEC] flex items-center justify-center">
        <Card className="p-8 max-w-md w-full text-center">
          <h1 className="text-xl font-semibold mb-2">Passenger link incomplete</h1>
          <p className="text-sm text-muted-foreground mb-4">
            This link is missing a passenger reference (PNR). Please use the link sent by our agents or contact support.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#EBEDEC]">
      <div className="h-16 bg-white border-b border-border flex items-center justify-between px-8">
        <div>
          <h1 className="text-[22px] leading-[28px] font-semibold">Passenger Re-accommodation</h1>
          <p className="text-[12px] text-muted-foreground">
            This page shows your options for a disrupted flight. You can review and confirm one option.
          </p>
        </div>
        <Badge variant="outline" className="text-[11px] px-2 py-0.5">
          Passenger View
        </Badge>
      </div>

      <div className="flex flex-col md:flex-row h-[calc(100vh-64px)]">
        <div className="w-full md:w-[340px] bg-white border-b md:border-b-0 md:border-r border-border p-6 overflow-y-auto space-y-4">
          {loading && (
            <Card className="p-4 rounded-[12px]">
              <Skeleton className="h-5 w-2/3 mb-3" />
              <Skeleton className="h-4 w-1/2 mb-2" />
              <Skeleton className="h-20 w-full" />
            </Card>
          )}

          {error && !loading && (
            <Card className="p-4 rounded-[12px] text-[13px] text-destructive">
              {error}
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
                  <Badge variant="outline" className="text-[12px]">Cabin {passenger.cabin}</Badge>
                </div>

                <div className="text-[13px] text-muted-foreground space-y-1">
                  <div className="flex items-center gap-2">
                    <Plane className="w-4 h-4" />
                    <span>{passenger.originalFlight}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4" />
                    <span>{passenger.originalRoute}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4" />
                    <span>Scheduled: {passenger.originalTime}</span>
                  </div>
                </div>
              </Card>

              <Card className="p-4 rounded-[12px]">
                <h4 className="text-[14px] font-semibold mb-2">Contact</h4>
                <div className="space-y-2 text-[13px]">
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-muted-foreground" />
                    <span>{passengerEmail}</span>
                  </div>
                </div>
              </Card>
            </>
          )}
        </div>

        <div className="flex-1 p-6 overflow-y-auto">
          <div className="max-w-[800px] mx-auto space-y-4">
            <div className="space-y-1 mb-4">
              <h2 className="text-[18px] leading-[24px] font-semibold">Your re-accommodation options</h2>
              <p className="text-[12px] text-muted-foreground">
                Choose the option that works best for you. Final ticketing and any hotel or compensation will be handled by our agents.
              </p>
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

            {!loading && !options.length && !error && (
              <Card className="p-6 rounded-[12px] border border-dashed text-center text-muted-foreground text-[13px]">
                There are no alternative options available for this disruption yet. Please try again later or contact our agents.
              </Card>
            )}

            {options.map((option) => (
              <OptionCard
                key={option.id}
                {...option}
                optionId={option.id}
                selected={selectedOptionId === option.id}
                onClick={() => setSelectedOptionId(option.id)}
              />
            ))}

            {!!options.length && (
              <>
                <Separator className="my-4" />
                <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3">
                  <p className="text-[12px] text-muted-foreground">
                    When you confirm, we will record your preferred option and an agent may contact you if any details need to be adjusted.
                  </p>
                  <Button
                    className="w-full md:w-auto h-11"
                    onClick={handleConfirm}
                    disabled={!selectedOptionId || !passenger}
                  >
                    Confirm selected option
                  </Button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
