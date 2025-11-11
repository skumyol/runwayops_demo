import { AlertCircle, Bot, CheckCircle, Clock, DollarSign, Users, XCircle } from 'lucide-react';
import { AgenticAnalysisResponse } from '../hooks/useAgenticAnalysis';

interface AgenticAnalysisPanelProps {
  analysis: AgenticAnalysisResponse;
}

export function AgenticAnalysisPanel({ analysis }: AgenticAnalysisPanelProps) {
  const { agentic_analysis } = analysis;
  const { final_plan } = agentic_analysis;

  const getPriorityColor = (priority?: string) => {
    switch (priority) {
      case 'critical':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'high':
        return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-blue-600 bg-blue-50 border-blue-200';
    }
  };

  const getConfidenceIcon = (confidence: string) => {
    switch (confidence) {
      case 'high':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'medium':
        return <Clock className="w-4 h-4 text-yellow-600" />;
      default:
        return <AlertCircle className="w-4 h-4 text-orange-600" />;
    }
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-4 rounded-lg">
        <div className="flex items-center space-x-3">
          <Bot className="w-6 h-6" />
          <div>
            <h2 className="text-lg font-semibold">Agentic Disruption Analysis</h2>
            <p className="text-sm text-indigo-100">
              {analysis.airport} • {analysis.carrier} • {analysis.mode} mode
            </p>
          </div>
        </div>
        <div className="text-right">
          <div className="flex items-center space-x-2">
            {getConfidenceIcon(final_plan.confidence)}
            <span className="text-sm font-medium">
              {final_plan.confidence} confidence
            </span>
          </div>
        </div>
      </div>

      {/* Disruption Status */}
      <div
        className={`border rounded-lg p-4 ${
          final_plan.disruption_detected
            ? 'border-red-200 bg-red-50'
            : 'border-green-200 bg-green-50'
        }`}
      >
        <div className="flex items-start space-x-3">
          {final_plan.disruption_detected ? (
            <XCircle className="w-5 h-5 text-red-600 mt-0.5" />
          ) : (
            <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
          )}
          <div className="flex-1">
            <h3 className="font-semibold text-gray-900">
              {final_plan.disruption_detected
                ? 'Disruption Detected'
                : 'No Disruption Detected'}
            </h3>
            <p className="text-sm text-gray-700 mt-1">
              Recommended Action: <strong>{final_plan.recommended_action}</strong>
            </p>
            {final_plan.priority && (
              <span
                className={`inline-block mt-2 px-3 py-1 text-xs font-semibold rounded-full border ${getPriorityColor(
                  final_plan.priority
                )}`}
              >
                Priority: {final_plan.priority.toUpperCase()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Risk Assessment */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <div className="flex items-center space-x-2 text-red-600 mb-2">
            <AlertCircle className="w-5 h-5" />
            <h4 className="font-semibold text-sm">Risk Level</h4>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {(final_plan.risk_assessment.risk_probability * 100).toFixed(0)}%
          </p>
          {final_plan.risk_assessment.duration_minutes && (
            <p className="text-xs text-gray-600 mt-1">
              Est. {final_plan.risk_assessment.duration_minutes}min duration
            </p>
          )}
        </div>

        {/* Finance */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <div className="flex items-center space-x-2 text-green-600 mb-2">
            <DollarSign className="w-5 h-5" />
            <h4 className="font-semibold text-sm">Est. Cost</h4>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            ${(final_plan.finance_estimate.total_usd / 1000).toFixed(0)}K
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Comp: ${(final_plan.finance_estimate.compensation_usd / 1000).toFixed(0)}K
          </p>
        </div>

        {/* Rebooking */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <div className="flex items-center space-x-2 text-blue-600 mb-2">
            <Users className="w-5 h-5" />
            <h4 className="font-semibold text-sm">Pax Affected</h4>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {final_plan.rebooking_plan.estimated_pax}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            {final_plan.rebooking_plan.strategy.replace(/_/g, ' ')}
          </p>
        </div>

        {/* Crew */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <div className="flex items-center space-x-2 text-purple-600 mb-2">
            <Users className="w-5 h-5" />
            <h4 className="font-semibold text-sm">Crew Status</h4>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {final_plan.crew_rotation.crew_changes_needed ? 'Changes' : 'OK'}
          </p>
          <p className="text-xs text-gray-600 mt-1">
            Backup: {final_plan.crew_rotation.backup_crew_required}
          </p>
        </div>
      </div>

      {/* What-If Scenarios */}
      {final_plan.what_if_scenarios && final_plan.what_if_scenarios.length > 0 && (
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <h3 className="font-semibold text-gray-900 mb-3 flex items-center">
            <Bot className="w-4 h-4 mr-2 text-indigo-600" />
            What-If Scenarios
          </h3>
          <div className="space-y-3">
            {final_plan.what_if_scenarios.map((scenario, idx) => (
              <div
                key={idx}
                className="border-l-4 border-indigo-400 bg-indigo-50 p-3 rounded"
              >
                <h4 className="font-medium text-sm text-indigo-900">
                  {scenario.scenario.replace(/_/g, ' ')}
                </h4>
                <p className="text-sm text-gray-700 mt-1">
                  {scenario.plan.description}
                </p>
                {scenario.plan.actions && scenario.plan.actions.length > 0 && (
                  <ul className="mt-2 text-xs text-gray-600 space-y-1">
                    {scenario.plan.actions.map((action, actionIdx) => (
                      <li key={actionIdx} className="flex items-start">
                        <span className="mr-2">•</span>
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Detailed Plans */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Rebooking Details */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <h3 className="font-semibold text-gray-900 mb-3">Rebooking Plan</h3>
          <div className="space-y-2 text-sm">
            <p className="text-gray-700">{final_plan.rebooking_plan.reasoning}</p>
            {final_plan.rebooking_plan.actions.length > 0 && (
              <ul className="space-y-1 text-gray-600">
                {final_plan.rebooking_plan.actions.map((action, idx) => (
                  <li key={idx} className="flex items-start">
                    <span className="mr-2">•</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Risk Details */}
        <div className="border border-gray-200 rounded-lg p-4 bg-white">
          <h3 className="font-semibold text-gray-900 mb-3">Risk Assessment</h3>
          <div className="space-y-2 text-sm">
            <p className="text-gray-700">{final_plan.risk_assessment.reasoning}</p>
            {final_plan.risk_assessment.pax_impact && (
              <p className="text-gray-600">
                <strong>Impact:</strong> {final_plan.risk_assessment.pax_impact}
              </p>
            )}
            {final_plan.risk_assessment.regulatory_risk && (
              <p className="text-gray-600">
                <strong>Regulatory:</strong> {final_plan.risk_assessment.regulatory_risk}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Audit Trail Summary */}
      <div className="border border-gray-200 rounded-lg p-4 bg-gray-50">
        <h3 className="font-semibold text-gray-900 mb-2">Analysis Trail</h3>
        <p className="text-sm text-gray-600">
          {agentic_analysis.audit_log.length} agent reasoning steps logged
          {final_plan.generated_at && (
            <span className="ml-2">
              • Generated: {new Date(final_plan.generated_at).toLocaleString()}
            </span>
          )}
        </p>
      </div>
    </div>
  );
}
