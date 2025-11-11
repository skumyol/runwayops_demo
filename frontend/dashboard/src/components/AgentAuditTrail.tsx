/**
 * AgentAuditTrail component - displays detailed LangGraph agent execution flow
 */

import React, { useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Button } from './ui/button';
import { 
  Bot, 
  ChevronDown, 
  ChevronRight, 
  Clock, 
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Brain,
  Shield,
  Plane,
  DollarSign,
  Users,
  TrendingUp
} from 'lucide-react';

interface AgentLogEntry {
  agent: string;
  input: any;
  output: any;
  timestamp: string;
}

interface AgentAuditTrailProps {
  auditLog: AgentLogEntry[];
  finalPlan?: any;
  metadata?: {
    provider: string;
    model: string;
    timestamp: string;
  };
}

const AGENT_ICONS: Record<string, any> = {
  Predictive: Brain,
  Orchestrator: Sparkles,
  Risk: Shield,
  Rebooking: Plane,
  Finance: DollarSign,
  Crew: Users,
  Aggregator: TrendingUp,
};

const AGENT_COLORS: Record<string, string> = {
  Predictive: 'text-purple-600 bg-purple-50 border-purple-200',
  Orchestrator: 'text-indigo-600 bg-indigo-50 border-indigo-200',
  Risk: 'text-red-600 bg-red-50 border-red-200',
  Rebooking: 'text-blue-600 bg-blue-50 border-blue-200',
  Finance: 'text-green-600 bg-green-50 border-green-200',
  Crew: 'text-orange-600 bg-orange-50 border-orange-200',
  Aggregator: 'text-teal-600 bg-teal-50 border-teal-200',
};

function AgentLogCard({ entry, index }: { entry: AgentLogEntry; index: number }) {
  const [expanded, setExpanded] = useState(false);
  const Icon = AGENT_ICONS[entry.agent] || Bot;
  const colorClass = AGENT_COLORS[entry.agent] || 'text-gray-600 bg-gray-50 border-gray-200';

  return (
    <Card className={`p-4 rounded-[12px] border ${colorClass}`}>
      <div 
        className="flex items-start justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-start gap-3 flex-1">
          <div className={`p-2 rounded-lg ${colorClass}`}>
            <Icon className="w-5 h-5" />
          </div>
          
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-1">
              <h4 className="text-[14px] font-semibold">{entry.agent} Agent</h4>
              <Badge variant="outline" className="text-[10px] h-5">
                Step {index + 1}
              </Badge>
            </div>
            
            <div className="flex items-center gap-2 text-[11px] text-muted-foreground">
              <Clock className="w-3 h-3" />
              <span>{new Date(entry.timestamp).toLocaleTimeString()}</span>
            </div>

            {!expanded && (
              <p className="text-[12px] text-muted-foreground mt-2 line-clamp-2">
                {entry.output?.reasoning || entry.output?.description || 
                 (entry.agent === 'Predictive' && entry.output?.disruption_detected !== undefined
                   ? `Disruption ${entry.output.disruption_detected ? 'detected' : 'not detected'}`
                   : 'View details...')}
              </p>
            )}
          </div>
        </div>

        <Button variant="ghost" size="sm" className="ml-2">
          {expanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
        </Button>
      </div>

      {expanded && (
        <div className="mt-4 space-y-3">
          <Separator />
          
          {/* Output Summary */}
          <div>
            <h5 className="text-[12px] font-semibold mb-2">Output</h5>
            <div className="text-[12px] space-y-2">
              {renderAgentOutput(entry.agent, entry.output)}
            </div>
          </div>

          {/* Reasoning */}
          {entry.output?.reasoning && (
            <div>
              <h5 className="text-[12px] font-semibold mb-2">Reasoning</h5>
              <p className="text-[11px] text-muted-foreground leading-relaxed">
                {entry.output.reasoning}
              </p>
            </div>
          )}

          {/* Raw Data Toggle */}
          <details className="text-[11px]">
            <summary className="cursor-pointer font-medium text-muted-foreground">
              View Raw Data
            </summary>
            <pre className="mt-2 p-2 bg-black/5 rounded text-[10px] overflow-x-auto max-h-40">
              {JSON.stringify(entry.output, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </Card>
  );
}

function renderAgentOutput(agent: string, output: any) {
  if (!output) return <p className="text-muted-foreground">No output</p>;

  switch (agent) {
    case 'Predictive':
      return (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            {output.disruption_detected ? (
              <CheckCircle2 className="w-4 h-4 text-green-600" />
            ) : (
              <AlertCircle className="w-4 h-4 text-gray-400" />
            )}
            <span className="font-medium">
              Disruption {output.disruption_detected ? 'Detected' : 'Not Detected'}
            </span>
          </div>
          {output.risk_probability !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Risk Probability:</span>
              <span className="font-semibold">{(output.risk_probability * 100).toFixed(0)}%</span>
            </div>
          )}
        </div>
      );

    case 'Risk':
      return (
        <div className="space-y-1">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Likelihood:</span>
            <Badge variant={output.likelihood === 'high' ? 'destructive' : 'secondary'}>
              {output.likelihood}
            </Badge>
          </div>
          {output.estimated_duration && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Duration:</span>
              <span className="font-semibold">{output.estimated_duration}</span>
            </div>
          )}
          {output.passenger_impact && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Impact:</span>
              <span className="font-semibold">{output.passenger_impact}</span>
            </div>
          )}
        </div>
      );

    case 'Rebooking':
      return (
        <div className="space-y-1">
          {output.strategy && (
            <div>
              <span className="text-muted-foreground">Strategy:</span>
              <p className="font-medium mt-1">{output.strategy}</p>
            </div>
          )}
          {output.affected_pax_count !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Affected:</span>
              <span className="font-semibold">{output.affected_pax_count} passengers</span>
            </div>
          )}
        </div>
      );

    case 'Finance':
      return (
        <div className="space-y-1">
          {output.compensation_cost !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Compensation:</span>
              <span className="font-semibold">${output.compensation_cost.toLocaleString()}</span>
            </div>
          )}
          {output.hotel_meals_cost !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Hotel & Meals:</span>
              <span className="font-semibold">${output.hotel_meals_cost.toLocaleString()}</span>
            </div>
          )}
          {output.total_estimate !== undefined && (
            <div className="flex justify-between border-t pt-1 mt-1">
              <span className="font-semibold">Total:</span>
              <span className="font-bold">${output.total_estimate.toLocaleString()}</span>
            </div>
          )}
        </div>
      );

    case 'Crew':
      return (
        <div className="space-y-1">
          {output.crew_changes_needed !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Changes Needed:</span>
              <Badge>{output.crew_changes_needed}</Badge>
            </div>
          )}
          {output.backup_crew_required !== undefined && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Backup Required:</span>
              <Badge variant="outline">{output.backup_crew_required}</Badge>
            </div>
          )}
        </div>
      );

    case 'Orchestrator':
      return (
        <div className="space-y-2">
          {output.main_plan?.description && (
            <div>
              <span className="text-muted-foreground">Main Plan:</span>
              <p className="font-medium mt-1">{output.main_plan.description}</p>
            </div>
          )}
          {output.what_if_scenarios?.length > 0 && (
            <div>
              <span className="text-muted-foreground">Scenarios:</span>
              <div className="mt-1 space-y-1">
                {output.what_if_scenarios.map((scenario: any, idx: number) => (
                  <Badge key={idx} variant="secondary" className="mr-1">
                    {scenario.scenario}
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </div>
      );

    case 'Aggregator':
      return (
        <div className="space-y-1">
          {output.recommended_action && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Action:</span>
              <Badge variant={output.recommended_action === 'PROCEED' ? 'default' : 'secondary'}>
                {output.recommended_action}
              </Badge>
            </div>
          )}
          {output.confidence && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Confidence:</span>
              <Badge variant="outline">{output.confidence}</Badge>
            </div>
          )}
          {output.priority && (
            <div className="flex justify-between">
              <span className="text-muted-foreground">Priority:</span>
              <Badge variant={output.priority === 'critical' ? 'destructive' : 'default'}>
                {output.priority}
              </Badge>
            </div>
          )}
        </div>
      );

    default:
      return (
        <pre className="text-[11px] text-muted-foreground max-h-32 overflow-auto">
          {JSON.stringify(output, null, 2)}
        </pre>
      );
  }
}

export function AgentAuditTrail({ auditLog, finalPlan, metadata }: AgentAuditTrailProps) {
  const [expandAll, setExpandAll] = useState(false);

  if (!auditLog || auditLog.length === 0) {
    return (
      <Card className="p-6 rounded-[12px] text-center text-muted-foreground">
        <Bot className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>No agent execution data available</p>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-[18px] leading-[24px] font-semibold flex items-center gap-2">
            <Bot className="w-5 h-5" />
            Agent Execution Flow
          </h3>
          <p className="text-[12px] text-muted-foreground mt-1">
            {auditLog.length} agents executed
            {metadata && ` • ${metadata.provider}/${metadata.model}`}
          </p>
        </div>
        
        <Button 
          variant="outline" 
          size="sm"
          onClick={() => setExpandAll(!expandAll)}
        >
          {expandAll ? 'Collapse All' : 'Expand All'}
        </Button>
      </div>

      {/* Timeline */}
      <div className="space-y-3">
        {auditLog.map((entry, index) => (
          <AgentLogCard key={index} entry={entry} index={index} />
        ))}
      </div>

      {/* Final Plan Summary */}
      {finalPlan && (
        <>
          <Separator className="my-6" />
          <Card className="p-4 rounded-[12px] bg-gradient-to-br from-indigo-50 to-purple-50 border-indigo-200">
            <div className="flex items-center gap-2 mb-3">
              <CheckCircle2 className="w-5 h-5 text-indigo-600" />
              <h4 className="text-[16px] font-semibold text-indigo-900">Final Recommendation</h4>
            </div>
            
            <div className="grid grid-cols-2 gap-3 text-[13px]">
              <div>
                <span className="text-muted-foreground">Action:</span>
                <p className="font-semibold">{finalPlan.recommended_action}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Priority:</span>
                <Badge variant={finalPlan.priority === 'critical' ? 'destructive' : 'default'}>
                  {finalPlan.priority}
                </Badge>
              </div>
              <div>
                <span className="text-muted-foreground">Confidence:</span>
                <Badge variant="outline">{finalPlan.confidence}</Badge>
              </div>
              {finalPlan.risk_assessment?.likelihood && (
                <div>
                  <span className="text-muted-foreground">Risk:</span>
                  <Badge variant="secondary">{finalPlan.risk_assessment.likelihood}</Badge>
                </div>
              )}
            </div>
          </Card>
        </>
      )}

      {/* Metadata */}
      {metadata && (
        <div className="text-[11px] text-muted-foreground text-center space-y-1">
          <p>Analysis completed at {new Date(metadata.timestamp).toLocaleString()}</p>
          <p>Provider: {metadata.provider} • Model: {metadata.model}</p>
        </div>
      )}
    </div>
  );
}
