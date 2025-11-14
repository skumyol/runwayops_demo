"""Periodic predictive monitoring service.

This service runs the predictive agent periodically to update flight disruption
predictions. It stops predicting for flights that already have confirmed disruptions.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..agentsv2 import APIV2Workflow
from ..config import settings

logger = logging.getLogger(__name__)


class PredictiveMonitor:
    """Monitors flights and updates disruption predictions periodically."""

    def __init__(self, update_interval_seconds: int = 60):
        """
        Initialize the predictive monitor.

        Args:
            update_interval_seconds: How often to run predictions (default: 60s)
        """
        self.update_interval = update_interval_seconds
        self._task: Optional[asyncio.Task] = None
        self._running = False
        self._predictions: Dict[str, Dict[str, Any]] = {}
        self._workflow = APIV2Workflow()

    async def start(self):
        """Start the background monitoring task."""
        if self._running:
            logger.warning("Predictive monitor already running")
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("🔮 Predictive monitor started (interval: %ds)", self.update_interval)

    async def stop(self):
        """Stop the background monitoring task."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("🛑 Predictive monitor stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(self.update_interval)
                # Note: In production, this would fetch active flights from a database
                # For now, predictions are computed on-demand
                logger.debug("🔮 Predictive monitor tick")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in predictive monitor loop: {e}")
                await asyncio.sleep(5)

    async def predict_disruption(
        self,
        flight_data: Dict[str, Any],
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Run predictive analysis on flight data.

        Args:
            flight_data: Flight monitor payload
            force: If True, run prediction even if disruption exists

        Returns:
            Prediction results with risk assessment
        """
        flight_number = flight_data.get("flight_number", "UNKNOWN")
        
        # Check if disruption already exists
        disruption = flight_data.get("disruption")
        if disruption and not force:
            status = disruption.get("status", "").lower()
            if status in ["confirmed", "active", "resolved"]:
                logger.info(
                    f"⏭️  {flight_number}: Disruption already {status}, skipping prediction"
                )
                return {
                    "flight_number": flight_number,
                    "prediction_skipped": True,
                    "reason": f"Disruption status: {status}",
                    "existing_disruption": disruption,
                }

        logger.info(f"🔮 {flight_number}: Running predictive analysis...")
        
        try:
            # Run the ADK workflow
            result = await self._workflow.run(flight_data)
            
            # Store prediction
            self._predictions[flight_number] = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "disruption_detected": result.get("disruption_detected", False),
                "risk_assessment": result.get("risk_assessment", {}),
                "signal_breakdown": result.get("signal_breakdown", {}),
            }
            
            logger.info(
                f"✅ {flight_number}: Prediction complete - "
                f"Disruption: {result.get('disruption_detected', False)}"
            )
            
            return {
                "flight_number": flight_number,
                "prediction": self._predictions[flight_number],
                "full_analysis": result,
            }
            
        except Exception as e:
            logger.error(f"❌ {flight_number}: Prediction failed - {e}")
            return {
                "flight_number": flight_number,
                "error": str(e),
            }

    def get_prediction(self, flight_number: str) -> Optional[Dict[str, Any]]:
        """Get the latest prediction for a flight."""
        return self._predictions.get(flight_number)

    def get_all_predictions(self) -> Dict[str, Dict[str, Any]]:
        """Get all stored predictions."""
        return self._predictions.copy()


# Global singleton instance
_monitor_instance: Optional[PredictiveMonitor] = None


def get_predictive_monitor() -> PredictiveMonitor:
    """Get or create the global predictive monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = PredictiveMonitor(update_interval_seconds=60)
    return _monitor_instance
