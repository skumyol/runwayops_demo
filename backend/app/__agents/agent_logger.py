"""Enhanced logging for agent communication and workflow visibility."""

import logging
import json
from typing import Any

logger = logging.getLogger(__name__)


def log_agent_start(agent_name: str, input_summary: str = ""):
    """Log the start of an agent's execution."""
    logger.info("=" * 80)
    logger.info(f"🤖 {agent_name.upper()} AGENT: Starting execution...")
    if input_summary:
        logger.info(f"📥 Input: {input_summary}")
    logger.info("=" * 80)


def log_agent_thinking(agent_name: str, thought: str):
    """Log an agent's reasoning process."""
    logger.info(f"💭 {agent_name}: {thought}")


def log_agent_llm_call(agent_name: str, prompt_summary: str, model: str):
    """Log when an agent makes an LLM call."""
    logger.info(f"🔮 {agent_name}: Calling LLM ({model})...")
    logger.info(f"   Prompt: {prompt_summary[:200]}...")


def log_agent_llm_response(agent_name: str, response_summary: str):
    """Log LLM response."""
    logger.info(f"✨ {agent_name}: LLM Response received")
    logger.info(f"   {response_summary[:300]}...")


def log_agent_decision(agent_name: str, decision: str, rationale: str = ""):
    """Log an agent's decision."""
    logger.info(f"✅ {agent_name}: Decision: {decision}")
    if rationale:
        logger.info(f"   Rationale: {rationale}")


def log_agent_output(agent_name: str, output_summary: str):
    """Log an agent's output."""
    logger.info(f"📤 {agent_name}: Output generated")
    logger.info(f"   {output_summary}")


def log_agent_complete(agent_name: str, status: str = "SUCCESS"):
    """Log completion of agent execution."""
    icon = "✅" if status == "SUCCESS" else "❌"
    logger.info(f"{icon} {agent_name} AGENT: Execution {status}")
    logger.info("=" * 80)


def log_agent_communication(from_agent: str, to_agent: str, message: str):
    """Log communication between agents."""
    logger.info(f"💬 {from_agent} → {to_agent}: {message}")


def log_agent_data(agent_name: str, data: Any, label: str = "Data"):
    """Log structured data from an agent."""
    if isinstance(data, (dict, list)):
        logger.info(f"📊 {agent_name}: {label}:")
        logger.info(f"   {json.dumps(data, indent=2)[:500]}")
    else:
        logger.info(f"📊 {agent_name}: {label}: {data}")
