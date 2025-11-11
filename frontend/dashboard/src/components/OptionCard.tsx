import React from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from './ui/accordion';
import { Plane, MapPin, Clock, Armchair, Leaf, Shield } from 'lucide-react';

export interface WhyReason {
  text: string;
  type?: 'tier' | 'time' | 'risk' | 'revenue' | 'policy';
}

export interface OptionCardProps {
  optionId: string;
  departureTime: string;
  arrivalTime: string;
  route: string;
  cabin: string;
  seats: number;
  trvScore: number;
  arrivalDelta?: string;
  badges?: ('Greener' | 'Protected' | 'Fastest')[];
  whyReasons: WhyReason[];
  onClick?: () => void;
  selected?: boolean;
}

export function OptionCard({
  optionId,
  departureTime,
  arrivalTime,
  route,
  cabin,
  seats,
  trvScore,
  arrivalDelta,
  badges = [],
  whyReasons,
  onClick,
  selected = false,
}: OptionCardProps) {
  const getTrvColor = (score: number) => {
    if (score >= 85) return 'bg-success text-white';
    if (score >= 70) return 'bg-warning text-white';
    return 'bg-muted-foreground text-white';
  };

  return (
    <Card 
      className={`p-6 rounded-[12px] cursor-pointer transition-all ${
        selected ? 'ring-2 ring-primary' : 'hover:shadow-md'
      }`}
      onClick={onClick}
    >
      <div className="space-y-4">
        {/* Header with TRV Score */}
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-[12px] font-mono text-muted-foreground">Option {optionId}</span>
              <Badge className={`${getTrvColor(trvScore)} text-[12px] px-2 py-0.5`}>
                TRV {trvScore}
              </Badge>
            </div>
            
            {/* Time and Route */}
            <div className="flex items-center gap-4 mb-3">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-muted-foreground" />
                <span className="text-[16px] font-semibold">{departureTime}</span>
                <span className="text-muted-foreground">→</span>
                <span className="text-[16px] font-semibold">{arrivalTime}</span>
              </div>
              {arrivalDelta && (
                <span className="text-[12px] text-success">({arrivalDelta})</span>
              )}
            </div>
            
            <div className="flex items-center gap-2 text-[14px] text-muted-foreground">
              <MapPin className="w-4 h-4" />
              <span>{route}</span>
            </div>
          </div>
        </div>

        {/* Cabin and Seats */}
        <div className="flex items-center gap-4 py-3 border-y border-border">
          <div className="flex items-center gap-2">
            <Armchair className="w-4 h-4 text-muted-foreground" />
            <span className="text-[14px]">Cabin {cabin}</span>
          </div>
          <div className="flex items-center gap-2">
            <Plane className="w-4 h-4 text-muted-foreground" />
            <span className="text-[14px]">{seats} seats available</span>
          </div>
        </div>

        {/* Badges */}
        {badges.length > 0 && (
          <div className="flex items-center gap-2">
            {badges.map((badge) => (
              <Badge key={badge} variant="outline" className="text-[12px] gap-1">
                {badge === 'Greener' && <Leaf className="w-3 h-3 text-success" />}
                {badge === 'Protected' && <Shield className="w-3 h-3 text-primary" />}
                {badge}
              </Badge>
            ))}
          </div>
        )}

        {/* WHY Accordion */}
        <Accordion type="single" collapsible>
          <AccordionItem value="why" className="border-0">
            <AccordionTrigger className="py-2 text-[14px] font-semibold text-primary hover:no-underline">
              WHY this option?
            </AccordionTrigger>
            <AccordionContent>
              <ul className="space-y-2 mt-2">
                {whyReasons.map((reason, index) => (
                  <li key={index} className="text-[14px] leading-[20px] text-foreground/80 flex items-start gap-2">
                    <span className="text-primary mt-1">•</span>
                    <span>{reason.text}</span>
                  </li>
                ))}
              </ul>
            </AccordionContent>
          </AccordionItem>
        </Accordion>
      </div>
    </Card>
  );
}
