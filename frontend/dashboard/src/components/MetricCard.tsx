import React from 'react';
import { Card } from './ui/card';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  label: string;
  value: string | number;
  icon?: LucideIcon;
  trend?: string;
  trendUp?: boolean;
}

export function MetricCard({ label, value, icon: Icon, trend, trendUp }: MetricCardProps) {
  return (
    <Card className="p-6 rounded-[12px]">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-[14px] leading-[20px] text-muted-foreground mb-2">{label}</p>
          <p className="text-[32px] leading-[40px] font-semibold text-foreground">{value}</p>
          {trend && (
            <p className={`text-[12px] leading-[16px] mt-2 ${trendUp ? 'text-success' : 'text-destructive'}`}>
              {trend}
            </p>
          )}
        </div>
        {Icon && (
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            <Icon className="w-5 h-5 text-primary" />
          </div>
        )}
      </div>
    </Card>
  );
}
