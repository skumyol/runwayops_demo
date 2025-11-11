import React from 'react';
import { Alert } from './ui/alert';
import { Info } from 'lucide-react';

interface PolicyCalloutProps {
  title?: string;
  message: string;
  className?: string;
}

export function PolicyCallout({ title, message, className = '' }: PolicyCalloutProps) {
  return (
    <Alert className={`bg-info/10 border-info/20 ${className}`}>
      <Info className="h-4 w-4 text-info" />
      <div className="ml-2">
        {title && <h4 className="text-[14px] leading-[20px] font-semibold mb-1">{title}</h4>}
        <p className="text-[14px] leading-[20px] text-foreground/80">{message}</p>
      </div>
    </Alert>
  );
}
