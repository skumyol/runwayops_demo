"""Background service for updating flight disruptions with predictive signals.

This module periodically computes predictive signals and updates disruptions
in the synthetic data provider. It enriches IROP data with AI-driven insights
that can be displayed to operators through the flight monitor interface.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, Dict, List, Optional

from .predictive_signals import compute_predictive_signals


class DisruptionUpdater:
    """Periodically updates flight disruptions with predictive signal data."""

    def __init__(self, update_interval_seconds: int = 30):
        """
        Initialize the disruption updater.

        Args:
            update_interval_seconds: How often to compute and update signals
        """
        self.update_interval = update_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._latest_signals: Dict[str, Any] = {}

    async def start(self):
        """Start the background update task."""
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._update_loop())

    async def stop(self):
        """Stop the background update task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _update_loop(self):
        """Main loop that periodically updates disruption signals."""
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                # The actual update will happen when get_payload is called
                # This just triggers periodic refresh timing
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in disruption update loop: {e}")
                await asyncio.sleep(5)  # Brief delay on error

    def compute_and_store_signals(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compute predictive signals from payload and store for later retrieval.

        Args:
            payload: Flight monitor payload with flights, alerts, stats

        Returns:
            Computed predictive signals
        """
        try:
            signals = compute_predictive_signals(payload)
            self._latest_signals = signals
            self._enhance_flights_with_signals(payload, signals)
            return signals
        except Exception as e:
            print(f"Error computing predictive signals: {e}")
            return {}

    def _enhance_flights_with_signals(
        self, payload: Dict[str, Any], signals: Dict[str, Any]
    ):
        """
        Enhance flight data in payload with predictive signal insights.

        This adds predictive alert information to flights that match signal drivers
        and updates disruption likelihood based on risk probability.
        """
        if not signals:
            return

        flights = payload.get("flights", [])
        drivers = signals.get("drivers", [])
        risk_prob = signals.get("risk_probability", 0)
        disruption_detected = signals.get("disruption_detected", False)
        reasoning = signals.get("reasoning")

        # Map drivers to flight enhancements
        for flight in flights:
            # Add predictive insights to all flights with disruption risk
            if flight.get("statusCategory") in ["warning", "critical"]:
                # Generate detailed alert for disrupted flights
                flight["predictiveAlert"] = self._generate_predictive_alert(
                    flight,
                    drivers,
                    risk_prob,
                    reasoning=reasoning,
                    disruption_detected=disruption_detected,
                )
                
                # Update disruption likelihood based on signals
                self._update_flight_disruption_likelihood(
                    flight, risk_prob, drivers, disruption_detected
                )
            elif disruption_detected and risk_prob > 0.6:
                # Even normal flights may need preventive alerts if risk is high
                flight["predictiveAlert"] = self._generate_predictive_alert(
                    flight,
                    drivers,
                    risk_prob,
                    reasoning=reasoning,
                    disruption_detected=disruption_detected,
                )
                
    def _update_flight_disruption_likelihood(
        self,
        flight: Dict[str, Any],
        risk_prob: float,
        drivers: List[Dict[str, Any]],
        disruption_detected: bool,
    ):
        """
        Update flight disruption likelihood based on predictive signals.
        
        This modifies the flight's status to reflect predicted risk levels.
        """
        # Add disruption likelihood field
        flight["disruptionLikelihood"] = {
            "probability": round(risk_prob, 2),
            "level": "high" if risk_prob >= 0.7 else "medium" if risk_prob >= 0.5 else "low",
            "detected": disruption_detected,
        }
        
        # Escalate status if needed based on high risk
        if risk_prob >= 0.8 and flight.get("statusCategory") == "warning":
            # Escalate warning to critical if risk is very high
            flight["predictiveEscalation"] = True
            flight["predictiveRisk"] = "CRITICAL"
        elif risk_prob >= 0.6 and flight.get("statusCategory") == "normal":
            # Flag normal flights with medium-high risk
            flight["predictiveRisk"] = "ELEVATED"
        
        # Add risk drivers summary to flight
        high_risk_drivers = [d for d in drivers if d.get("score", 0) > 0.5]
        if high_risk_drivers:
            flight["riskDrivers"] = [
                {
                    "category": d.get("category"),
                    "score": round(d.get("score", 0), 2),
                }
                for d in high_risk_drivers
            ]

    def _generate_predictive_alert(
        self,
        flight: Dict[str, Any],
        drivers: List[Dict[str, Any]],
        risk_prob: float,
        *,
        reasoning: Optional[str] = None,
        disruption_detected: bool = False,
    ) -> Dict[str, Any]:
        """
        Generate a predictive alert for a specific flight based on signal drivers.

        Args:
            flight: Flight data dictionary
            drivers: List of risk drivers from predictive signals
            risk_prob: Overall disruption risk probability

        Returns:
            Predictive alert dictionary with recommendations
        """
        # Find relevant drivers
        relevant_drivers = []

        for driver in drivers:
            category = driver.get("category", "").lower()
            impact = driver.get("impact_count", 0)

            # Check if driver affects this flight
            if category == "weather" and impact > 0:
                relevant_drivers.append(driver)
            elif category == "crew" and not flight.get("crewReady", True):
                relevant_drivers.append(driver)
            elif category == "aircraft" and not flight.get("aircraftReady", True):
                relevant_drivers.append(driver)

        if not relevant_drivers:
            # Generic alert for all disrupted flights
            relevant_drivers = drivers[:2]  # Top 2 drivers

        # Build recommendations based on drivers
        recommendations = []
        for driver in relevant_drivers[:3]:  # Top 3
            category = driver.get("category", "Unknown")
            evidence = driver.get("evidence", "")
            score = driver.get("score", 0)

            if category.lower() == "weather" and score > 0.5:
                recommendations.append(
                    f"Monitor weather conditions: {evidence}"
                )
                recommendations.append(
                    "Consider pre-emptive slot adjustments"
                )
            elif category.lower() == "crew" and score > 0.4:
                recommendations.append(
                    f"Crew constraint detected: {evidence}"
                )
                recommendations.append(
                    "Verify standby crew availability"
                )
            elif category.lower() == "aircraft" and score > 0.4:
                recommendations.append(
                    f"Aircraft status: {evidence}"
                )
                recommendations.append(
                    "Review MX clearance timeline"
                )

        if not recommendations:
            recommendations = [
                "Monitor operational metrics",
                "Keep communication channels open",
            ]

        prediction = self._summarize_prediction(risk_prob, disruption_detected)
        reasoning_text = self._compose_reasoning(relevant_drivers, reasoning)

        return {
            "riskProbability": round(risk_prob, 2),
            "severity": "high" if risk_prob >= 0.7 else "medium" if risk_prob >= 0.5 else "low",
            "prediction": prediction,
            "reasoning": reasoning_text,
            "drivers": [
                {
                    "category": d.get("category", "Unknown"),
                    "score": round(d.get("score", 0), 2),
                    "evidence": d.get("evidence", ""),
                }
                for d in relevant_drivers
            ],
            "recommendations": recommendations[:4],  # Max 4 recommendations
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

    def _summarize_prediction(self, risk_prob: float, detected: bool) -> str:
        """Return a human-readable summary of the predictive agent's view."""
        if risk_prob >= 0.85:
            return "Predictive agent flags severe disruption risk"
        if risk_prob >= 0.7 or detected:
            return "Predictive agent detects high disruption risk"
        if risk_prob >= 0.5:
            return "Predictive agent monitoring elevated risk"
        return "Predictive agent monitoring — low risk"

    def _compose_reasoning(
        self, drivers: List[Dict[str, Any]], global_reasoning: Optional[str]
    ) -> str:
        """Blend driver evidence with global reasoning for transparency."""
        driver_notes = [
            d.get("evidence")
            for d in drivers
            if d.get("evidence")
        ]
        notes = []
        if driver_notes:
            notes.append("Drivers: " + "; ".join(driver_notes))
        if global_reasoning:
            notes.append(global_reasoning)
        return " ".join(notes) if notes else "Predictive agent did not provide additional reasoning."

    def get_latest_signals(self) -> Dict[str, Any]:
        """Get the most recently computed predictive signals."""
        return self._latest_signals


# Global singleton instance
_updater_instance: Optional[DisruptionUpdater] = None


def get_disruption_updater() -> DisruptionUpdater:
    """Get or create the global disruption updater instance."""
    global _updater_instance
    if _updater_instance is None:
        _updater_instance = DisruptionUpdater(update_interval_seconds=30)
    return _updater_instance
