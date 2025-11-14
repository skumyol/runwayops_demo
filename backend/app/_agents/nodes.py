"""Agent nodes for the disruption workflow.

Each node represents a specialized agent that processes part of the workflow.
Nodes update the shared AgentState and log their reasoning for transparency.
"""

from __future__ import annotations

import json
import logging
import random
from typing import Any, Dict

from langchain_core.messages import HumanMessage

from .llm_factory import get_llm
from .state import AgentState, log_reasoning
from ..services.predictive_signals import compute_predictive_signals
from .agent_logger import (
    log_agent_start, log_agent_thinking, log_agent_llm_call,
    log_agent_llm_response, log_agent_decision, log_agent_output,
    log_agent_complete, log_agent_communication
)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# -----------------------------
# Node 1: Predictive Signal Generator
# -----------------------------

def predictive_node(state: AgentState) -> AgentState:
    """Predictive node that surfaces weather/crew/aircraft driven risk."""
    logger.info("=" * 80)
    logger.info("🧠 PREDICTIVE AGENT: Starting disruption analysis...")
    logger.info("=" * 80)

    input_data = state["input_data"]

    result = compute_predictive_signals(input_data)

    logger.info(
        "🎯 Risk Probability: %.2f%% | Weather=%s | Aircraft=%s | Crew=%s",
        result["risk_probability"] * 100,
        result["signal_breakdown"]["weather"],
        result["signal_breakdown"]["aircraft"],
        result["signal_breakdown"]["crew"],
    )
    logger.info(
        "⚠️  Disruption %s",
        "DETECTED ✓" if result["disruption_detected"] else "NOT DETECTED ✗",
    )

    state = log_reasoning(state, "Predictive", input_data, result)
    state["disruption_detected"] = result["disruption_detected"]
    state["risk_assessment"] = result
    state["signal_breakdown"] = result.get("signal_breakdown", {})

    return state


def route_after_predictive(state: AgentState) -> str:
    """Conditional edge: Route to orchestrator if disruption detected."""
    if state["disruption_detected"]:
        return "orchestrator"
    else:
        return "end"


# -----------------------------
# Node 2: Orchestrator Agent (LLM)
# -----------------------------

def orchestrator_node(state: AgentState) -> AgentState:
    """LLM-powered orchestrator that decides disruption handling strategy.
    
    Simulates what-if scenarios and coordinates sub-agents.
    """
    log_agent_start("ORCHESTRATOR", f"Coordinating response based on disruption: {state['disruption_detected']}")
    
    llm = get_llm()
    
    input_summary = {
        "risk": state["risk_assessment"],
        "flight_data": {
            "airport": state["input_data"].get("airport"),
            "carrier": state["input_data"].get("carrier"),
            "stats": state["input_data"].get("stats"),
        }
    }
    
    log_agent_thinking("ORCHESTRATOR", f"Analyzing risk assessment: {state['risk_assessment'].get('likelihood', 'unknown')}")
    log_agent_communication("PREDICTIVE", "ORCHESTRATOR", f"Disruption detected: {state['disruption_detected']}")
    
    prompt = f"""You are an airline operations orchestrator analyzing a potential flight disruption.

Input Data:
{json.dumps(input_summary, indent=2)}

Task:
1. Assess if this is a significant disruption requiring intervention
2. Generate a main action plan
3. Simulate 2 what-if scenarios:
   - Scenario A: If delay extends beyond 3 hours
   - Scenario B: If crew becomes unavailable

Output a JSON with:
{{
  "requires_intervention": true/false,
  "severity": "low/medium/high/critical",
  "main_plan": {{"description": "...", "priority_actions": []}},
  "what_if_scenarios": [
    {{"scenario": "delay_3hr", "plan": {{"description": "...", "actions": []}}}},
    {{"scenario": "crew_unavailable", "plan": {{"description": "...", "actions": []}}}}
  ],
  "reasoning": "..."
}}
"""
    
    log_agent_llm_call("ORCHESTRATOR", "Requesting action plan and what-if scenarios", llm.model_name if hasattr(llm, 'model_name') else "LLM")
    
    response = None
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        
        log_agent_llm_response("ORCHESTRATOR", f"Received response (length: {len(content)} chars)")
        
        # Try to extract JSON from markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        output = json.loads(content)
        
        log_agent_decision("ORCHESTRATOR", 
                          f"Intervention: {output.get('requires_intervention')}, Severity: {output.get('severity')}")
        log_agent_output("ORCHESTRATOR", f"Generated {len(output.get('what_if_scenarios', []))} what-if scenarios")
        
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"❌ ORCHESTRATOR: LLM parsing error: {e}")
        # Fallback if LLM doesn't return valid JSON
        output = {
            "requires_intervention": state["disruption_detected"],
            "severity": "medium",
            "main_plan": {
                "description": "Automated fallback plan due to LLM parsing error",
                "priority_actions": ["Monitor situation", "Notify ops team"]
            },
            "what_if_scenarios": [],
            "reasoning": f"LLM response parsing failed: {e}",
            "raw_response": str(getattr(response, "content", ""))[:500],
        }
    
    state = log_reasoning(state, "Orchestrator", input_summary, output)
    state["simulation_results"] = output.get("what_if_scenarios", [])
    
    log_agent_communication("ORCHESTRATOR", "SUB-AGENTS", "Dispatching tasks to Risk, Rebooking, Finance, and Crew agents")
    log_agent_complete("ORCHESTRATOR")
    
    return state


# -----------------------------
# Node 3-6: Specialized Sub-Agents
# -----------------------------

def risk_node(state: AgentState) -> AgentState:
    """Risk assessment agent - analyzes likelihood and impact."""
    llm = get_llm()
    
    risk_data = state["risk_assessment"]
    
    prompt = f"""As a risk assessment specialist, analyze this disruption:

Risk Data:
{json.dumps(risk_data, indent=2)}

Provide:
1. Likelihood assessment (0-1)
2. Expected duration (minutes)
3. Passenger impact severity
4. Regulatory implications (EU261/HKCAD)

Output JSON:
{{
  "likelihood": 0.85,
  "duration_minutes": 180,
  "pax_impact": "high",
  "regulatory_risk": "EU261 compensation required",
  "reasoning": "..."
}}
"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
    except Exception:
        result = {
            "likelihood": risk_data.get("risk_probability", 0.75),
            "duration_minutes": 120,
            "pax_impact": "medium",
            "regulatory_risk": "Monitor for compensation thresholds",
            "reasoning": "Fallback risk assessment"
        }
    
    state = log_reasoning(state, "Risk", risk_data, result)
    state["risk_assessment"].update(result)
    
    return state


def rebooking_node(state: AgentState) -> AgentState:
    """Rebooking agent - handles passenger re-accommodation."""
    llm = get_llm()
    
    input_data = state["input_data"]
    flights = input_data.get("flights", [])
    
    # Find critical flights
    critical_flights = [f for f in flights if f.get("statusCategory") == "critical"]
    
    prompt = f"""As a passenger rebooking specialist, create a re-accommodation plan.

Critical Flights: {len(critical_flights)}
Sample flight: {json.dumps(critical_flights[0] if critical_flights else {}, indent=2)}

Provide:
1. Rebooking strategy (same day, next day, alternate route)
2. Hotel arrangements if needed
3. VIP passenger prioritization
4. Estimated affected passengers

Output JSON:
{{
  "strategy": "same_day_alternate",
  "hotel_required": true,
  "vip_priority": true,
  "estimated_pax": 200,
  "actions": [],
  "reasoning": "..."
}}
"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
    except Exception:
        result = {
            "strategy": "monitor_and_assess",
            "hotel_required": False,
            "vip_priority": True,
            "estimated_pax": len(critical_flights) * 200 if critical_flights else 0,
            "actions": ["Monitor flight status", "Prepare rebooking options"],
            "reasoning": "Fallback rebooking plan"
        }
    
    state = log_reasoning(state, "Rebooking", {"critical_flights": len(critical_flights)}, result)
    state["rebooking_plan"] = result
    
    return state


def finance_node(state: AgentState) -> AgentState:
    """Finance agent - estimates costs and compensation."""
    llm = get_llm()
    
    risk_data = state["risk_assessment"]
    rebooking = state.get("rebooking_plan", {})
    
    prompt = f"""As a financial analyst, estimate disruption costs.

Risk Assessment: {json.dumps(risk_data, indent=2)}
Rebooking Plan: {json.dumps(rebooking, indent=2)}

Calculate:
1. Compensation costs (EU261/HKCAD)
2. Hotel/meal costs
3. Operational costs (fuel, crew overtime)
4. Total estimated impact

Output JSON:
{{
  "compensation_usd": 50000,
  "hotel_meals_usd": 15000,
  "operational_usd": 20000,
  "total_usd": 85000,
  "breakdown": [],
  "reasoning": "..."
}}
"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
    except Exception:
        pax_impacted = state["input_data"].get("stats", {}).get("paxImpacted", 200)
        est_total = pax_impacted * 150 + random.randint(10000, 30000)
        result = {
            "compensation_usd": pax_impacted * 100,
            "hotel_meals_usd": pax_impacted * 50,
            "operational_usd": 20000,
            "total_usd": est_total,
            "breakdown": ["Fallback estimate"],
            "reasoning": "Fallback financial assessment"
        }
    
    state = log_reasoning(state, "Finance", {}, result)
    state["finance_estimate"] = result
    
    return state


def crew_node(state: AgentState) -> AgentState:
    """Crew management agent - handles crew scheduling and regulations."""
    llm = get_llm()
    
    input_data = state["input_data"]
    
    prompt = f"""As a crew scheduling specialist, assess crew impacts.

Flight Data: {json.dumps(input_data.get("stats", {}), indent=2)}

Consider:
1. Crew duty time limits
2. Rest requirements
3. Backup crew availability
4. Regulatory compliance

Output JSON:
{{
  "crew_changes_needed": true,
  "backup_crew_required": 2,
  "regulatory_issues": [],
  "actions": [],
  "reasoning": "..."
}}
"""
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content = response.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        result = json.loads(content)
    except Exception:
        result = {
            "crew_changes_needed": False,
            "backup_crew_required": 0,
            "regulatory_issues": [],
            "actions": ["Monitor crew duty times"],
            "reasoning": "Fallback crew assessment"
        }
    
    state = log_reasoning(state, "Crew", {}, result)
    state["crew_rotation"] = result
    
    return state


# -----------------------------
# Node 7: Simulation Aggregator
# -----------------------------

def aggregator_node(state: AgentState) -> AgentState:
    """Aggregates all agent outputs and what-if simulations into final plan."""
    
    final_plan = {
        "disruption_detected": state["disruption_detected"],
        "risk_assessment": state["risk_assessment"],
        "signal_breakdown": state.get("signal_breakdown", {}),
        "rebooking_plan": state["rebooking_plan"],
        "finance_estimate": state["finance_estimate"],
        "crew_rotation": state["crew_rotation"],
        "what_if_scenarios": state["simulation_results"],
        "recommended_action": "PROCEED" if state["disruption_detected"] else "MONITOR",
        "confidence": "high" if len(state["audit_log"]) > 5 else "medium",
        "generated_at": state["audit_log"][-1]["timestamp"] if state["audit_log"] else None,
    }
    
    # Calculate priority
    risk_likelihood = state["risk_assessment"].get("likelihood", 0)
    if risk_likelihood > 0.8:
        final_plan["priority"] = "critical"
    elif risk_likelihood > 0.6:
        final_plan["priority"] = "high"
    else:
        final_plan["priority"] = "medium"
    
    state = log_reasoning(state, "Aggregator", state["simulation_results"], final_plan)
    state["final_plan"] = final_plan
    
    return state
