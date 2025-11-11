from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

ALLOWED_MODES = {"synthetic", "realtime", "mongo"}


@dataclass(slots=True)
class Settings:
    default_mode: str = "synthetic"
    aviationstack_api_key: str | None = None
    aviationstack_base_url: str = "https://api.aviationstack.com/v1"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "runwayops"
    mongo_flight_collection: str = "flight_manifests"
    mongo_passenger_collection: str = "passengers"
    mongo_crew_collection: str = "crew"
    mongo_disruption_collection: str = "disruptions"
    mongo_aircraft_collection: str = "aircraft"
    mongo_flight_instance_collection: str = "flight_instances"
    mongo_agent_audit_collection: str = "agent_audit_logs"
    mongo_simulation_collection: str = "agent_simulations"
    # Agentic system settings
    agentic_enabled: bool = False
    llm_provider: str = "openai"  # openai, openrouter, deepseek, gemini
    llm_model: str = "gpt-4o"
    llm_temperature: float = 0.2
    # Provider-specific API keys
    openai_api_key: str | None = None
    openrouter_api_key: str | None = None
    deepseek_api_key: str | None = None
    gemini_api_key: str | None = None
    # Provider-specific endpoints (for custom deployments)
    openai_base_url: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    deepseek_base_url: str = "https://api.deepseek.com"

    def __post_init__(self) -> None:
        mode = os.getenv("FLIGHT_MONITOR_MODE", "synthetic").lower()
        if mode not in ALLOWED_MODES:
            mode = "synthetic"
        self.default_mode = mode
        self.aviationstack_api_key = os.getenv("AVIATIONSTACK_API_KEY")
        self.aviationstack_base_url = os.getenv(
            "AVIATIONSTACK_BASE_URL", self.aviationstack_base_url
        ).rstrip("/")
        self.mongo_uri = os.getenv("MONGO_URI", self.mongo_uri)
        self.mongo_db_name = os.getenv("MONGO_DB_NAME", self.mongo_db_name)
        self.mongo_flight_collection = os.getenv(
            "MONGO_FLIGHT_COLLECTION", self.mongo_flight_collection
        )
        self.mongo_passenger_collection = os.getenv(
            "MONGO_PASSENGER_COLLECTION", self.mongo_passenger_collection
        )
        self.mongo_crew_collection = os.getenv(
            "MONGO_CREW_COLLECTION", self.mongo_crew_collection
        )
        self.mongo_disruption_collection = os.getenv(
            "MONGO_DISRUPTION_COLLECTION", self.mongo_disruption_collection
        )
        self.mongo_aircraft_collection = os.getenv(
            "MONGO_AIRCRAFT_COLLECTION", self.mongo_aircraft_collection
        )
        self.mongo_flight_instance_collection = os.getenv(
            "MONGO_FLIGHT_INSTANCE_COLLECTION",
            self.mongo_flight_instance_collection,
        )
        self.mongo_agent_audit_collection = os.getenv(
            "MONGO_AGENT_AUDIT_COLLECTION", self.mongo_agent_audit_collection
        )
        self.mongo_simulation_collection = os.getenv(
            "MONGO_SIMULATION_COLLECTION", self.mongo_simulation_collection
        )
        # Agentic system settings
        self.agentic_enabled = os.getenv("AGENTIC_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        self.llm_provider = os.getenv("LLM_PROVIDER", self.llm_provider).lower()
        self.llm_model = os.getenv("LLM_MODEL", self.llm_model)
        self.llm_temperature = float(
            os.getenv("LLM_TEMPERATURE", str(self.llm_temperature))
        )
        # Provider API keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        # Provider endpoints
        self.openai_base_url = os.getenv("OPENAI_BASE_URL")
        self.openrouter_base_url = os.getenv(
            "OPENROUTER_BASE_URL", self.openrouter_base_url
        )
        self.deepseek_base_url = os.getenv(
            "DEEPSEEK_BASE_URL", self.deepseek_base_url
        )


settings = Settings()
