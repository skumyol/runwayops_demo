import React from 'react';

interface TopNavProps {
  title: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export function TopNav({ title, subtitle, actions }: TopNavProps) {
  return (
    <div className="h-16 border-b border-border bg-white flex items-center justify-between px-8">
      <div>
        <h1 className="text-[24px] leading-[32px] font-semibold text-foreground">{title}</h1>
        {subtitle && <p className="text-[14px] leading-[20px] text-muted-foreground">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-3">{actions}</div>}
    </div>
  );
}
