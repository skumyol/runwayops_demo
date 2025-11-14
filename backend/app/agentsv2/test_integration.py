"""Integration test for ADK-based disruption workflow.

This script tests the complete workflow with mock flight data.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


# Mock flight data for testing
MOCK_FLIGHT_DATA = {
    "airport": "HKG",
    "carrier": "CX",
    "timestamp": "2024-11-14T10:00:00Z",
    "stats": {
        "totalFlights": 45,
        "delayedFlights": 12,
        "paxImpacted": 350,
        "avgDelay": 125,
        "weatherScore": 0.75,  # High weather risk
        "aircraftScore": 0.65,  # Moderate aircraft issues
        "crewScore": 0.55,      # Crew availability concerns
    },
    "flights": [
        {
            "id": "CX888",
            "number": "CX888",
            "origin": "HKG",
            "destination": "JFK",
            "scheduledDeparture": "2024-11-14T14:00:00Z",
            "estimatedDeparture": "2024-11-14T16:30:00Z",
            "status": "delayed",
            "statusCategory": "critical",
            "delayMinutes": 150,
            "passengers": 250,
        },
        {
            "id": "CX889",
            "number": "CX889",
            "origin": "HKG",
            "destination": "LAX",
            "scheduledDeparture": "2024-11-14T15:00:00Z",
            "estimatedDeparture": "2024-11-14T16:00:00Z",
            "status": "delayed",
            "statusCategory": "warning",
            "delayMinutes": 60,
            "passengers": 200,
        }
    ],
    "alerts": [
        {
            "type": "weather",
            "severity": "high",
            "message": "Severe thunderstorms in area",
            "affectedFlights": ["CX888", "CX889"]
        }
    ]
}


async def test_workflow():
    """Test the ADK workflow with mock data."""
    logger.info("=" * 80)
    logger.info("🧪 Starting ADK Workflow Integration Test")
    logger.info("=" * 80)
    
    try:
        # Import workflow
        from .workflow import DisruptionWorkflowADK
        
        # Initialize workflow
        workflow = DisruptionWorkflowADK()
        logger.info("✅ Workflow initialized")
        
        # Execute workflow
        logger.info("\n📊 Test Data:")
        logger.info(json.dumps(MOCK_FLIGHT_DATA, indent=2))
        
        result = await workflow.run(MOCK_FLIGHT_DATA)
        
        # Display results
        logger.info("\n" + "=" * 80)
        logger.info("📋 WORKFLOW RESULTS")
        logger.info("=" * 80)
        
        logger.info(f"\n🎯 Disruption Detected: {result['disruption_detected']}")
        
        if result['disruption_detected']:
            final_plan = result['final_plan']
            logger.info(f"⚠️  Priority: {final_plan.get('priority', 'N/A')}")
            logger.info(f"🎬 Action: {final_plan.get('recommended_action', 'N/A')}")
            
            # Risk Assessment
            risk = result.get('risk_assessment', {})
            logger.info(f"\n📊 Risk Assessment:")
            logger.info(f"  - Likelihood: {risk.get('likelihood', 0):.2%}")
            logger.info(f"  - Duration: {risk.get('duration_minutes', 0)} minutes")
            logger.info(f"  - Impact: {risk.get('pax_impact', 'N/A')}")
            
            # Rebooking
            rebooking = result.get('rebooking_plan', {})
            logger.info(f"\n✈️  Rebooking Plan:")
            logger.info(f"  - Strategy: {rebooking.get('strategy', 'N/A')}")
            logger.info(f"  - Hotel Required: {rebooking.get('hotel_required', False)}")
            logger.info(f"  - Affected Passengers: {rebooking.get('estimated_pax', 0)}")
            
            # Finance
            finance = result.get('finance_estimate', {})
            logger.info(f"\n💰 Financial Impact:")
            logger.info(f"  - Total Cost: ${finance.get('total_usd', 0):,}")
            logger.info(f"  - Compensation: ${finance.get('compensation_usd', 0):,}")
            logger.info(f"  - Hotel/Meals: ${finance.get('hotel_meals_usd', 0):,}")
            
            # Crew
            crew = result.get('crew_rotation', {})
            logger.info(f"\n👥 Crew Management:")
            logger.info(f"  - Changes Needed: {crew.get('crew_changes_needed', False)}")
            logger.info(f"  - Backup Crew: {crew.get('backup_crew_required', 0)}")
            
            # What-if scenarios
            scenarios = result.get('simulation_results', [])
            if scenarios:
                logger.info(f"\n🔮 What-If Scenarios: {len(scenarios)}")
                for i, scenario in enumerate(scenarios, 1):
                    logger.info(f"  {i}. {scenario.get('scenario', 'N/A')}")
        
        # Audit Log Summary
        audit_log = result.get('audit_log', [])
        logger.info(f"\n📝 Audit Log: {len(audit_log)} entries")
        for entry in audit_log:
            logger.info(f"  - {entry.get('agent')}: {entry.get('timestamp')}")
        
        logger.info("\n" + "=" * 80)
        logger.info("✅ Integration Test Complete")
        logger.info("=" * 80)
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}", exc_info=True)
        return None


def main():
    """Main entry point."""
    # Run async test
    result = asyncio.run(test_workflow())
    
    if result:
        # Save result to file
        output_file = Path(__file__).parent / "test_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"\n💾 Results saved to: {output_file}")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())
