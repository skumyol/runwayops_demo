import React from 'react';
import { Badge } from './ui/badge';
import { TierType } from '../types/reaccommodation';

interface TierTagProps {
  tier: TierType;
  className?: string;
}

const tierConfig: Record<TierType, { color: string; bgColor: string }> = {
  Green: { color: 'text-green-700', bgColor: 'bg-green-100 border-green-200' },
  Silver: { color: 'text-slate-700', bgColor: 'bg-slate-100 border-slate-200' },
  Gold: { color: 'text-amber-700', bgColor: 'bg-amber-100 border-amber-200' },
  Diamond: { color: 'text-cyan-700', bgColor: 'bg-cyan-100 border-cyan-200' },
};

export function TierTag({ tier, className = '' }: TierTagProps) {
  const config = tierConfig[tier];
  
  return (
    <Badge className={`${config.bgColor} ${config.color} border ${className}`} variant="outline">
      {tier}
    </Badge>
  );
}
