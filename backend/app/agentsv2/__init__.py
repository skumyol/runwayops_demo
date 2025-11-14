"""Google ADK-based multi-agent system for flight disruption management.

This package implements the same functionality as the LangGraph agents
but using Google's Agent Development Kit (ADK) for better scalability,
model-agnostic support, and Google ecosystem integration.
"""

from .workflow import DisruptionWorkflowADK

# Alias for compatibility with agentic service
APIV2Workflow = DisruptionWorkflowADK

__all__ = ["DisruptionWorkflowADK", "APIV2Workflow"]
