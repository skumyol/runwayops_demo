#!/usr/bin/env python3
"""Quick CLI for exercising the LangGraph agents without the API layer.

This script mirrors what the frontend does: pull a provider payload, optionally
inject a what-if scenario, run the DisruptionWorkflow, and pretty-print the
results (risk, finance, crew, rebooking, what-if sims, and audit log summaries).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.agents import DisruptionWorkflow  # type: ignore  # noqa: E402
from app.agentsv2 import APIV2Workflow  # type: ignore  # noqa: E402
from app.config import settings  # type: ignore  # noqa: E402
from app.providers import ProviderMode, resolve_provider  # type: ignore  # noqa: E402
from app.services.scenario_overrides import apply_debug_scenario  # type: ignore  # noqa: E402


def _currency(value: float) -> str:
    return f"${value:,.0f}"


def render_summary(result: Dict[str, Any]) -> None:
    plan = result.get("final_plan", {})
    finance = plan.get("finance_estimate", {})
    rebooking = plan.get("rebooking_plan", {})
    crew = plan.get("crew_rotation", {})
    risk = plan.get("risk_assessment", {})

    print("\n=== FINAL PLAN ===")
    print(f"Detected: {plan.get('disruption_detected')} | Priority: {plan.get('priority')} | Action: {plan.get('recommended_action')}")
    if plan.get("signal_breakdown"):
        print("Drivers:")
        for key, details in plan["signal_breakdown"].items():
            print(f"  - {key.title():<9}: {details.get('evidence')} ({details.get('score'):.2f})")

    print("\nRisk:")
    print(f"  Probability: {risk.get('risk_probability', 0) * 100:.0f}% | Reason: {risk.get('reasoning')}")

    print("\nFinance:")
    print(f"  Total: {_currency(finance.get('total_usd', 0))}")
    for line in finance.get("breakdown", [])[:5]:
        print(f"    • {line}")

    print("\nRebooking:")
    print(f"  Strategy: {rebooking.get('strategy')} | Pax: {rebooking.get('estimated_pax')} | Hotel: {rebooking.get('hotel_required')}")
    for action in rebooking.get("actions", [])[:5]:
        print(f"    • {action}")

    print("\nCrew:")
    print(f"  Changes needed: {crew.get('crew_changes_needed')} | Backup: {crew.get('backup_crew_required')} | Notes: {crew.get('reasoning')}")

    if plan.get("what_if_scenarios"):
        print("\nWhat-if scenarios:")
        for scenario in plan["what_if_scenarios"]:
            print(f"  [{scenario['scenario']}] {scenario['plan']['description']}")
            for action in scenario["plan"].get("actions", [])[:3]:
                print(f"     • {action}")


def render_audit_log(result: Dict[str, Any]) -> None:
    log = result.get("audit_log", [])
    if not log:
        print("No audit log entries available.")
        return
    print("\n=== AUDIT LOG ===")
    for entry in log:
        agent = entry.get("agent")
        reasoning = entry.get("output")
        summary = json.dumps(reasoning)[:160] if reasoning else ""
        print(f"[{entry.get('timestamp')}] {agent}: {summary}")


async def run_agents(args: argparse.Namespace) -> Dict[str, Any]:
    mode: ProviderMode = args.mode or settings.default_mode  # type: ignore[assignment]
    provider = resolve_provider(mode)
    payload = await provider.get_payload(args.airport.upper(), args.carrier.upper())

    if args.scenario:
        payload = apply_debug_scenario(payload, args.scenario)

    if args.engine == "apiv2":
        workflow = APIV2Workflow()
    else:
        workflow = DisruptionWorkflow()

    return await workflow.run(payload)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run LangGraph agents locally for debugging")
    parser.add_argument("--airport", default="HKG", help="Station IATA code (default: HKG)")
    parser.add_argument("--carrier", default="CX", help="Carrier code (default: CX)")
    parser.add_argument(
        "--mode",
        choices=["synthetic", "realtime", "mongo"],
        default=None,
        help="Flight monitor provider to use (defaults to FLIGHT_MONITOR_MODE)",
    )
    parser.add_argument(
        "--scenario",
        choices=["delay_3hr", "crew_out", "weather_groundstop"],
        help="Optional debug scenario to inject before running agents",
    )
    parser.add_argument("--audit", action="store_true", help="Print the audit log after the summary")
    parser.add_argument("--json", action="store_true", help="Dump the raw final plan as JSON")
    parser.add_argument(
        "--engine",
        choices=["langgraph", "apiv2"],
        default=settings.agentic_mode,
        help="Agentic engine to execute (default: value from AGENTIC_MODE)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if not settings.agentic_enabled:
        parser.error("AGENTIC_ENABLED is false. Update backend/.env before running this script.")
    if not settings.openai_api_key:
        parser.error("OPENAI_API_KEY missing; set it in backend/.env or environment.")

    result = asyncio.run(run_agents(args))
    render_summary(result)
    if args.audit:
        render_audit_log(result)
    if args.json:
        print("\n=== JSON DUMP ===")
        print(json.dumps(result["final_plan"], indent=2))


if __name__ == "__main__":
    main()
