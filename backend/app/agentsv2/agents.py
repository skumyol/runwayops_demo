"""ADK agent definitions for flight disruption management.

This module defines all agents in the disruption workflow using Google's
Agent Development Kit (ADK). Agents are organized hierarchically with
specialized roles.
"""

import json
import logging
from typing import Any, Dict, List

from langchain_core.messages import HumanMessage

from .llm import LLMProviderError, get_llm
from .state import DisruptionState, log_reasoning, record_decision
from .tools import (
    predictive_signal_tool,
    rebooking_tool,
    finance_tool,
    crew_scheduling_tool,
)


logger = logging.getLogger(__name__)


def _content_to_text(content: Any) -> str:
    """Normalize LangChain responses into a string."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _parse_json_block(text: str) -> Dict[str, Any] | None:
    """Extract and parse JSON from an LLM response."""
    snippet = text.strip()
    if "```json" in snippet:
        snippet = snippet.split("```json", 1)[1]
        snippet = snippet.split("```", 1)[0]
    elif snippet.startswith("```"):
        snippet = snippet.strip("`")
    snippet = snippet.strip()
    if not snippet:
        return None
    try:
        return json.loads(snippet)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON response: %s", snippet[:200])
        return None


class LLMBackedAgent:
    """Mixin that wires ADK agents to the configured LLM provider."""

    def __init__(self):
        self._llm = None
        self._llm_failed = False

    def _ensure_llm(self):
        if self._llm_failed:
            return None
        if self._llm is None:
            try:
                self._llm = get_llm()
            except LLMProviderError as exc:
                self._llm_failed = True
                logger.warning("%s unavailable: %s", getattr(self, "name", "LLMAgent"), exc)
                return None
        return self._llm

    async def _invoke_llm_json(self, prompt: str) -> Dict[str, Any] | None:
        llm = self._ensure_llm()
        if not llm:
            return None

        messages = [HumanMessage(content=prompt)]
        try:
            if hasattr(llm, "ainvoke"):
                response = await llm.ainvoke(messages)  # type: ignore[attr-defined]
            else:
                response = llm.invoke(messages)  # type: ignore[call-arg]
        except Exception as exc:  # pragma: no cover - network failures
            logger.error("%s LLM call failed: %s", getattr(self, "name", "LLMAgent"), exc)
            return None

        content = getattr(response, "content", response)
        text = _content_to_text(content)
        return _parse_json_block(text)


class PredictiveAgent:
    """Predictive agent for disruption detection using signals.
    
    This agent analyzes weather, aircraft, and crew signals to detect
    potential disruptions before they occur.
    """
    
    def __init__(self):
        self.name = "PredictiveAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Execute predictive analysis on flight data.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with risk assessment
        """
        logger.info("=" * 80)
        logger.info("🧠 PREDICTIVE AGENT (ADK): Starting disruption analysis...")
        logger.info("=" * 80)
        
        input_data = state.input_data
        stats = input_data.get("stats", {})
        
        # If a confirmed disruption is present in the input payload (e.g. from
        # Mongo-backed reaccommodation flows), treat that as ground truth and
        # skip heuristic prediction.
        disruption = input_data.get("disruption")
        if disruption:
            disruption_type = disruption.get("type", "disruption") if isinstance(disruption, dict) else "disruption"
            reasoning = f"Confirmed disruption: {disruption_type}"
            logger.info("⚠️  Confirmed disruption present in input payload - skipping predictive heuristic")
            state.disruption_detected = True
            state.risk_assessment = {
                "risk_probability": 1.0,
                "reasoning": reasoning,
            }
            state.signal_breakdown = {}
            state = log_reasoning(state, self.name, input_data, state.risk_assessment)
            return state

        # Call predictive tool
        result = await predictive_signal_tool(
            airport=input_data.get("airport", "HKG"),
            carrier=input_data.get("carrier", "CX"),
            weather_score=stats.get("weatherScore", 0.5),
            aircraft_score=stats.get("aircraftScore", 0.5),
            crew_score=stats.get("crewScore", 0.5)
        )
        
        logger.info(
            f"🎯 Risk Probability: {result['risk_probability']:.2%} | "
            f"Disruption: {'DETECTED ✓' if result['disruption_detected'] else 'NOT DETECTED ✗'}"
        )
        
        state.disruption_detected = result["disruption_detected"]
        state.risk_assessment = result
        state.signal_breakdown = result.get("signal_breakdown", {})
        
        state = log_reasoning(state, self.name, input_data, result)
        scenarios = ["delay_3hr", "crew_unavailable"] if state.disruption_detected else ["global"]
        state = record_decision(
            state,
            self.name,
            "Calculated predictive disruption risk",
            category="prediction",
            scenarios=scenarios,
            data={
                "risk_probability": result["risk_probability"],
                "disruption_detected": state.disruption_detected,
            },
        )
        
        return state


class OrchestratorAgent(LLMBackedAgent):
    """Orchestrator agent for coordinating disruption response.
    
    This LLM-powered agent analyzes disruptions, creates action plans,
    and simulates what-if scenarios.
    """
    
    def __init__(self):
        super().__init__()
        self.name = "OrchestratorAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Coordinate disruption response strategy.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with orchestration plan and scenarios
        """
        logger.info("🎯 ORCHESTRATOR AGENT (ADK): Coordinating response...")
        
        risk = state.risk_assessment
        prompt = self._orchestrator_prompt(state)
        output = await self._invoke_llm_json(prompt)
        if not output:
            output = self._fallback_plan(state, risk)
        
        state.what_if_templates = output.get("what_if_scenarios", [])
        logger.info(
            f"⚡ Decision: Intervention={'Yes' if output['requires_intervention'] else 'No'}, "
            f"Severity={output['severity']}"
        )
        
        state = log_reasoning(state, self.name, {"risk": risk}, output)
        state = record_decision(
            state,
            self.name,
            "Coordinated disruption response plan",
            category="orchestration",
            scenarios=["delay_3hr", "crew_unavailable"],
            data={
                "requires_intervention": output.get("requires_intervention"),
                "severity": output.get("severity"),
                "main_plan": output.get("main_plan", {}),
            },
        )
        
        return state
    
    def _calculate_severity(self, risk_prob: float) -> str:
        """Calculate severity level from risk probability."""
        if risk_prob > 0.8:
            return "critical"
        elif risk_prob > 0.6:
            return "high"
        elif risk_prob > 0.4:
            return "medium"
        else:
            return "low"

    def _orchestrator_prompt(self, state: DisruptionState) -> str:
        input_summary = {
            "risk": state.risk_assessment,
            "flight_data": {
                "airport": state.input_data.get("airport"),
                "carrier": state.input_data.get("carrier"),
                "stats": state.input_data.get("stats"),
            },
        }
        return (
            "You are an airline operations orchestrator analyzing a potential disruption.\n\n"
            "Input Data:\n"
            f"{json.dumps(input_summary, indent=2)}\n\n"
            "Task:\n"
            "1. Assess whether intervention is required\n"
            "2. Produce a main action plan with priority actions\n"
            "3. Simulate two what-if scenarios:\n"
            "   - delay_3hr: delay extends beyond three hours\n"
            "   - crew_unavailable: relief crew cannot report in time\n\n"
            "Return ONLY JSON with:\n"
            "{\n"
            '  "requires_intervention": true/false,\n'
            '  "severity": "low|medium|high|critical",\n'
            '  "main_plan": {"description": "...", "priority_actions": []},\n'
            '  "what_if_scenarios": [\n'
            '    {"scenario": "delay_3hr", "plan": {"description": "...", "actions": []}},\n'
            '    {"scenario": "crew_unavailable", "plan": {"description": "...", "actions": []}}\n'
            "  ],\n"
            '  "reasoning": "..."\n'
            "}"
        )

    def _fallback_plan(self, state: DisruptionState, risk: Dict[str, Any]) -> Dict[str, Any]:
        logger.warning("⚠️ Orchestrator falling back to heuristic plan")
        return {
            "requires_intervention": state.disruption_detected,
            "severity": self._calculate_severity(risk.get("risk_probability", 0)),
            "main_plan": {
                "description": "Coordinate multi-agent response to disruption",
                "priority_actions": [
                    "Assess passenger impact",
                    "Calculate financial implications",
                    "Review crew availability",
                ],
            },
            "what_if_scenarios": [
                {
                    "scenario": "delay_3hr",
                    "plan": {
                        "description": "Extended delay requiring hotels",
                        "actions": [
                            "Book hotels",
                            "Arrange meals",
                            "Issue EU261/HKCAD compensation",
                        ],
                    },
                },
                {
                    "scenario": "crew_unavailable",
                    "plan": {
                        "description": "Crew duty limit exceeded",
                        "actions": [
                            "Assign backup crew",
                            "Reschedule departures",
                            "Notify rostering center",
                        ],
                    },
                },
            ],
            "reasoning": (
                f"Heuristic fallback with probability {risk.get('risk_probability', 0):.2%}"
            ),
        }


class RiskAgent(LLMBackedAgent):
    """Risk assessment specialist agent."""
    
    def __init__(self):
        super().__init__()
        self.name = "RiskAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Assess disruption risk in detail.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with enhanced risk assessment
        """
        logger.info("⚠️  RISK AGENT (ADK): Assessing likelihood and impact...")
        
        risk_data = state.risk_assessment
        prompt = self._risk_prompt(risk_data)
        result = await self._invoke_llm_json(prompt)
        if not result:
            result = {
                "likelihood": risk_data.get("risk_probability", 0.75),
                "duration_minutes": self._estimate_duration(risk_data),
                "pax_impact": self._assess_pax_impact(risk_data),
                "regulatory_risk": self._assess_regulatory_risk(risk_data),
                "reasoning": "Heuristic fallback risk assessment"
            }
        
        # Update state risk assessment with enhanced data
        state.risk_assessment.update(result)
        state = log_reasoning(state, self.name, risk_data, result)
        state = record_decision(
            state,
            self.name,
            "Quantified disruption likelihood and impact",
            category="risk",
            scenarios=["delay_3hr", "crew_unavailable"],
            data=result,
        )
        
        logger.info(
            f"📊 Risk: Likelihood={result['likelihood']:.2%}, "
            f"Duration={result['duration_minutes']}min, Impact={result['pax_impact']}"
        )
        
        return state
    
    def _estimate_duration(self, risk_data: Dict) -> int:
        """Estimate disruption duration from risk data."""
        risk_prob = risk_data.get("risk_probability", 0.5)
        if risk_prob > 0.8:
            return 240  # 4 hours
        elif risk_prob > 0.6:
            return 180  # 3 hours
        else:
            return 120  # 2 hours
    
    def _assess_pax_impact(self, risk_data: Dict) -> str:
        """Assess passenger impact severity."""
        risk_prob = risk_data.get("risk_probability", 0.5)
        if risk_prob > 0.7:
            return "high"
        elif risk_prob > 0.5:
            return "medium"
        else:
            return "low"
    
    def _assess_regulatory_risk(self, risk_data: Dict) -> str:
        """Assess regulatory compliance risk."""
        risk_prob = risk_data.get("risk_probability", 0.5)
        if risk_prob > 0.7:
            return "EU261/HKCAD compensation required"
        else:
            return "Monitor for compensation thresholds"

    def _risk_prompt(self, risk_data: Dict[str, Any]) -> str:
        return (
            "You are an airline risk officer. Analyze the following risk snapshot "
            "and provide a JSON payload that estimates likelihood, duration, "
            "passenger impact, and regulatory exposure.\n\n"
            f"Risk Data:\n{json.dumps(risk_data, indent=2)}\n\n"
            "JSON schema:\n"
            "{\n"
            '  "likelihood": 0.0 - 1.0,\n'
            '  "duration_minutes": int,\n'
            '  "pax_impact": "low|medium|high",\n'
            '  "regulatory_risk": "...",\n'
            '  "reasoning": "..."\n'
            "}"
        )


class RebookingAgent(LLMBackedAgent):
    """Passenger re-accommodation specialist agent."""
    
    def __init__(self):
        super().__init__()
        self.name = "RebookingAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Create passenger re-accommodation plan.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with rebooking plan
        """
        logger.info("✈️  REBOOKING AGENT (ADK): Planning re-accommodation...")
        
        input_data = state.input_data
        flights = input_data.get("flights", [])
        risk = state.risk_assessment
        
        # Find critical flights
        critical_flights = [f for f in flights if f.get("statusCategory") == "critical"]
        
        # Estimate passenger count
        pax_count = input_data.get("stats", {}).get("paxImpacted", 200)
        delay_minutes = risk.get("duration_minutes", 120)
        
        # Extract flight details for Amadeus API
        origin = input_data.get("airport", "HKG")
        
        # Try to extract destination from first critical flight
        destination = "LAX"  # Default
        departure_date = None
        
        if critical_flights:
            first_flight = critical_flights[0]
            # Try to extract destination from flight data
            if "route" in first_flight:
                destination = first_flight["route"].split("-")[-1].strip()
            elif "destination" in first_flight:
                destination = first_flight["destination"]
            
            # Try to extract departure date
            if "scheduledDeparture" in first_flight:
                # Parse date from ISO format
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(first_flight["scheduledDeparture"].replace("Z", "+00:00"))
                    departure_date = dt.strftime("%Y-%m-%d")
                except:
                    pass
        
        # Use rebooking tool with flight details
        tool_plan = await rebooking_tool(
            flight_id=critical_flights[0].get("id", "CX888") if critical_flights else "UNKNOWN",
            pax_count=pax_count,
            delay_minutes=delay_minutes,
            vip_count=int(pax_count * 0.1),  # Assume 10% VIPs
            disruption_type="delay",
            origin=origin,
            destination=destination,
            departure_date=departure_date
        )
        
        prompt = self._rebooking_prompt(tool_plan, critical_flights)
        llm_plan = await self._invoke_llm_json(prompt)
        result = tool_plan.copy()
        if llm_plan:
            result.update({k: v for k, v in llm_plan.items() if v is not None})
        
        state.rebooking_plan = result
        state = log_reasoning(
            state,
            self.name,
            {"pax_count": pax_count, "critical_flights": len(critical_flights)},
            result,
        )
        state = record_decision(
            state,
            self.name,
            "Prepared passenger re-accommodation plan",
            category="rebooking",
            scenarios=["delay_3hr"],
            data=result,
        )
        
        logger.info(
            f"🎫 Rebooking: {result['strategy']}, "
            f"Hotel={result['hotel_required']}, PAX={pax_count}"
        )
        
        return state

    def _rebooking_prompt(self, tool_plan: Dict[str, Any], flights: List[Dict[str, Any]]) -> str:
        sample = flights[0] if flights else {}
        return (
            "You are the passenger disruption lead. Refine the draft rebooking plan "
            "generated by our tools and ensure the output stays in JSON.\n\n"
            f"Tool Plan:\n{json.dumps(tool_plan, indent=2)}\n\n"
            f"Sample Critical Flight:\n{json.dumps(sample, indent=2)}\n\n"
            "Return JSON with the same fields (strategy, hotel_required, vip_priority, "
            "estimated_pax, vip_count, delay_minutes, actions, reasoning)."
        )


class FinanceAgent(LLMBackedAgent):
    """Financial impact assessment agent."""
    
    def __init__(self):
        super().__init__()
        self.name = "FinanceAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Calculate financial impact of disruption.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with finance estimate
        """
        logger.info("💰 FINANCE AGENT (ADK): Calculating costs...")
        
        rebooking = state.rebooking_plan
        risk = state.risk_assessment
        
        pax_count = rebooking.get("estimated_pax", 200)
        delay_minutes = risk.get("duration_minutes", 120)
        hotel_required = rebooking.get("hotel_required", False)
        
        # Use finance tool
        tool_estimate = await finance_tool(
            pax_count=pax_count,
            delay_minutes=delay_minutes,
            hotel_required=hotel_required,
            flight_distance="medium"
        )
        
        prompt = self._finance_prompt(tool_estimate, risk, rebooking)
        llm_estimate = await self._invoke_llm_json(prompt)
        result = tool_estimate.copy()
        if llm_estimate:
            result.update({k: v for k, v in llm_estimate.items() if v is not None})
        
        state.finance_estimate = result
        state = log_reasoning(state, self.name, {"pax_count": pax_count}, result)
        state = record_decision(
            state,
            self.name,
            "Calculated total financial impact",
            category="finance",
            scenarios=["delay_3hr", "crew_unavailable"],
            data=result,
        )
        
        logger.info(f"💵 Total Cost: ${result['total_usd']:,}")
        
        return state

    def _finance_prompt(
        self,
        tool_estimate: Dict[str, Any],
        risk: Dict[str, Any],
        rebooking: Dict[str, Any],
    ) -> str:
        payload = {
            "tool_estimate": tool_estimate,
            "risk": risk,
            "rebooking": rebooking,
        }
        return (
            "You are an airline finance controller. Cross-check the disruption "
            "estimate from our deterministic tool and adjust if needed. Keep the "
            "same JSON keys (compensation_usd, hotel_meals_usd, operational_usd, "
            "total_usd, breakdown, reasoning).\n\n"
            f"Context:\n{json.dumps(payload, indent=2)}"
        )


class CrewAgent(LLMBackedAgent):
    """Crew scheduling and management agent."""
    
    def __init__(self):
        super().__init__()
        self.name = "CrewAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Assess crew scheduling impacts.
        
        Args:
            state: Current disruption state
            
        Returns:
            Updated state with crew rotation plan
        """
        logger.info("👥 CREW AGENT (ADK): Managing crew schedules...")
        
        input_data = state.input_data
        risk = state.risk_assessment
        
        flight_count = len(input_data.get("flights", []))
        delay_minutes = risk.get("duration_minutes", 120)
        
        # Use crew scheduling tool
        tool_plan = await crew_scheduling_tool(
            flight_count=flight_count,
            delay_minutes=delay_minutes,
            crew_available=10
        )
        
        prompt = self._crew_prompt(tool_plan, input_data)
        llm_plan = await self._invoke_llm_json(prompt)
        result = tool_plan.copy()
        if llm_plan:
            result.update({k: v for k, v in llm_plan.items() if v is not None})
        
        state.crew_rotation = result
        state = log_reasoning(state, self.name, {"flights": flight_count}, result)
        state = record_decision(
            state,
            self.name,
            "Issued crew rotation guidance",
            category="crew",
            scenarios=["crew_unavailable"],
            data=result,
        )
        
        logger.info(
            f"👔 Crew: Changes={'Required' if result['crew_changes_needed'] else 'Not needed'}, "
            f"Backup={result['backup_crew_required']}"
        )
        
        return state

    def _crew_prompt(self, tool_plan: Dict[str, Any], input_data: Dict[str, Any]) -> str:
        return (
            "You are a crew scheduling expert reviewing system recommendations. "
            "Adjust the JSON plan if needed while preserving the same keys "
            "(crew_changes_needed, backup_crew_required, regulatory_issues, "
            "actions, reasoning).\n\n"
            f"Tool Recommendation:\n{json.dumps(tool_plan, indent=2)}\n\n"
            f"Flight Stats:\n{json.dumps(input_data.get('stats', {}), indent=2)}"
        )


class AggregatorAgent:
    """Aggregator agent for synthesizing all outputs."""
    
    def __init__(self):
        self.name = "AggregatorAgent"
    
    async def run(self, state: DisruptionState) -> DisruptionState:
        """Aggregate all agent outputs into final plan.
        
        Args:
            state: Current disruption state with all agent outputs
            
        Returns:
            Updated state with final plan
        """
        logger.info("📋 AGGREGATOR AGENT (ADK): Synthesizing final plan...")
        
        final_plan = {
            "disruption_detected": state.disruption_detected,
            "risk_assessment": state.risk_assessment,
            "signal_breakdown": state.signal_breakdown,
            "rebooking_plan": state.rebooking_plan,
            "finance_estimate": state.finance_estimate,
            "crew_rotation": state.crew_rotation,
            "recommended_action": "PROCEED" if state.disruption_detected else "MONITOR",
            "confidence": "high" if len(state.audit_log) > 5 else "medium",
            "generated_at": state.audit_log[-1]["timestamp"] if state.audit_log else None,
            "decision_count": len(state.decision_log),
        }
        
        # Calculate priority
        risk_likelihood = state.risk_assessment.get("likelihood", 0)
        if risk_likelihood > 0.8:
            final_plan["priority"] = "critical"
        elif risk_likelihood > 0.6:
            final_plan["priority"] = "high"
        else:
            final_plan["priority"] = "medium"
        
        state.simulation_results = self._render_scenarios(state)
        state.final_plan = final_plan
        state = log_reasoning(state, self.name, state.simulation_results, final_plan)
        state = record_decision(
            state,
            self.name,
            "Compiled final action plan",
            category="aggregation",
            scenarios=["delay_3hr", "crew_unavailable"],
            data={"priority": final_plan["priority"], "recommended_action": final_plan["recommended_action"]},
        )
        
        logger.info(
            f"✅ Final Plan: Priority={final_plan['priority']}, "
            f"Action={final_plan['recommended_action']}"
        )
        
        return state

    def _render_scenarios(self, state: DisruptionState) -> List[Dict[str, Any]]:
        templates = state.what_if_templates or self._default_templates(state)
        rendered = []
        for template in templates:
            scenario_key = template.get("scenario") or template.get("name") or "unknown"
            plan = template.get("plan", template.get("details", {}))
            relevant = [
                decision
                for decision in state.decision_log
                if "global" in decision.get("scenarios", [])
                or scenario_key in decision.get("scenarios", [])
            ]
            rendered.append(
                {
                    "scenario": scenario_key,
                    "plan": plan,
                    "summary": template.get("description") or plan.get("description"),
                    "agent_decisions": relevant,
                }
            )
        return rendered

    def _default_templates(self, state: DisruptionState) -> List[Dict[str, Any]]:
        return [
            {
                "scenario": "delay_3hr",
                "description": "Extended delay beyond three hours",
                "plan": {
                    "description": "Issue EU261/HKCAD support",
                    "actions": [
                        "Deploy hotel vouchers",
                        "Send proactive comms",
                        "Coordinate with finance for extra budget",
                    ],
                },
            },
            {
                "scenario": "crew_unavailable",
                "description": "Relief crew cannot report in time",
                "plan": {
                    "description": "Trigger crew contingency roster",
                    "actions": [
                        "Activate reserve crew",
                        "Re-sequence departures",
                        "Notify rostering control",
                    ],
                },
            },
        ]
