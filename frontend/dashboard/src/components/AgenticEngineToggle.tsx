import React from 'react';
import { AlertCircle } from 'lucide-react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { cn } from './ui/utils';
import { useAgenticContext } from '../context/AgenticContext';
import type { AgenticEngine } from '../types/agentic';
import { AGENTIC_ENGINE_OPTIONS, describeAgenticEngine } from '../lib/agentic';

interface AgenticEngineToggleProps {
  className?: string;
  selectedEngineAvailable?: boolean;
  warningMessage?: string;
}

export function AgenticEngineToggle({
  className,
  selectedEngineAvailable = true,
  warningMessage,
}: AgenticEngineToggleProps) {
  const { agenticEngine, setAgenticEngine } = useAgenticContext();

  const handleChange = (value: string) => {
    setAgenticEngine(value as AgenticEngine);
  };

  return (
    <div className={cn('text-left space-y-1', className)}>
      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
        Agent runtime
      </p>
      <Select value={agenticEngine} onValueChange={handleChange}>
        <SelectTrigger className="w-[230px]">
          <SelectValue placeholder="Select runtime" />
        </SelectTrigger>
        <SelectContent>
          {AGENTIC_ENGINE_OPTIONS.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              <div className="flex flex-col">
                <span>{option.label}</span>
                <span className="text-[11px] text-muted-foreground">
                  {option.helper}
                </span>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      <p className="text-[11px] text-muted-foreground">
        {describeAgenticEngine(agenticEngine)}
      </p>
      {!selectedEngineAvailable && (
        <div className="flex items-center gap-1 text-[11px] text-destructive">
          <AlertCircle className="w-3 h-3" />
          {warningMessage || 'Selected engine unavailable on backend.'}
        </div>
      )}
    </div>
  );
}
