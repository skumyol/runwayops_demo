import React from 'react';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { X } from 'lucide-react';

export interface FilterOption {
  label: string;
  value: string;
}

export interface Filter {
  id: string;
  label: string;
  type: 'select' | 'chip';
  options?: FilterOption[];
  value?: string;
  onValueChange?: (value: string) => void;
  onRemove?: () => void;
}

interface FilterBarProps {
  filters: Filter[];
}

export function FilterBar({ filters }: FilterBarProps) {
  return (
    <div className="flex items-center gap-3 px-8 py-4 bg-white border-b border-border">
      {filters.map((filter) => (
        <div key={filter.id}>
          {filter.type === 'select' && filter.options && (
            <Select value={filter.value} onValueChange={filter.onValueChange}>
              <SelectTrigger className="w-[180px] h-10">
                <SelectValue placeholder={filter.label} />
              </SelectTrigger>
              <SelectContent>
                {filter.options.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          )}
          
          {filter.type === 'chip' && filter.value && (
            <Badge 
              variant="secondary" 
              className="h-8 px-3 gap-2 cursor-pointer hover:bg-secondary/80"
              onClick={filter.onRemove}
            >
              {filter.label}: {filter.value}
              <X className="w-3 h-3" />
            </Badge>
          )}
        </div>
      ))}
    </div>
  );
}
