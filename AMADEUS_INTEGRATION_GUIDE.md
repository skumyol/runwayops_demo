# Amadeus API Integration Guide

This guide explains how to use the Amadeus Self-Service API integration for real flight and hotel re-accommodation in the agent system.

## Overview

The agents now support **real flight and hotel data** from Amadeus API instead of synthetic data. When configured, the system will:

1. **Search alternative flights** using real availability and pricing
2. **Search hotels** for overnight accommodation during disruptions
3. **Book flights** through Amadeus (test environment)
4. **Calculate real costs** for re-accommodation

The integration gracefully falls back to synthetic data if Amadeus credentials are not configured.

## Setup Instructions

### 1. Get Amadeus API Credentials

1. Register for a free account at [developers.amadeus.com](https://developers.amadeus.com/register)
2. Create a new application in the Amadeus dashboard
3. Copy your **Client ID** and **Client Secret**

### 2. Configure Environment Variables

Update your `backend/.env` file (or create from `.env.example`):

```bash
# Amadeus Self-Service API Configuration
AMADEUS_CLIENT_ID=your-actual-client-id
AMADEUS_CLIENT_SECRET=your-actual-client-secret
AMADEUS_ENVIRONMENT=test  # Use 'test' for development
```

**Important**: 
- Use `test` environment for development (free, static test data)
- Use `production` environment for live data (requires payment)

### 3. Install Dependencies

Dependencies are already included in `requirements.txt`:

```bash
cd backend
pip install -r requirements.txt
# or with uv:
uv pip install -r requirements.txt
```

## How It Works

### Agent Workflow with Amadeus

When a disruption is detected, the **RebookingAgent** now:

1. **Extracts flight details** from the disruption:
   - Origin airport code
   - Destination airport code
   - Departure date
   - Passenger count

2. **Calls Amadeus API** to:
   - Search alternative flights with real pricing
   - Search hotels if overnight stay is needed
   - Calculate total re-accommodation cost

3. **Returns enriched data**:
   ```json
   {
     "strategy": "next_day_with_hotel",
     "data_source": "amadeus",
     "flight_options": {
       "alternatives": [...],
       "count": 5
     },
     "hotel_options": {
       "hotels": [...],
       "total_cost": 15000
     },
     "total_cost_estimate": 250000
   }
   ```

### Fallback Behavior

If Amadeus credentials are not configured or API calls fail:
- System automatically falls back to synthetic data
- Logs indicate data source: `"data_source": "synthetic"`
- No errors or service interruptions

## Available Tools

### 1. `search_alternative_flights_tool`

Searches for real flight alternatives using Amadeus Flight Offers Search API.

```python
result = await search_alternative_flights_tool(
    origin="HKG",
    destination="LAX",
    departure_date="2025-12-01",
    passenger_count=150,
    max_results=5
)
```

**Returns:**
```json
{
  "alternatives": [
    {
      "id": "offer-1",
      "price": {"total": 450.00, "currency": "USD"},
      "departure": {"airport": "HKG", "time": "2025-12-01T14:30:00"},
      "arrival": {"airport": "LAX", "time": "2025-12-01T10:15:00"},
      "flight_number": "CX888",
      "stops": 0,
      "duration": "PT11H45M"
    }
  ],
  "count": 5
}
```

### 2. `search_hotels_tool`

Searches for hotel accommodations near the airport/city.

```python
result = await search_hotels_tool(
    city_code="LAX",
    check_in_date="2025-12-01",
    check_out_date="2025-12-02",
    room_count=75,
    passenger_count=150,
    max_results=5
)
```

**Returns:**
```json
{
  "hotels": [
    {
      "id": "HILAX123",
      "name": "Airport Hotel LAX",
      "rating": "4",
      "price": {"total": 150.00, "currency": "USD"},
      "total_cost_all_rooms": 11250.00
    }
  ],
  "total_cost": 11250.00
}
```

### 3. `book_flight_tool`

Creates a flight booking (test environment only).

```python
result = await book_flight_tool(
    flight_offer=selected_offer,
    passenger_count=150,
    passenger_details=travelers
)
```

**Returns:**
```json
{
  "success": true,
  "pnr": "ABC123",
  "flight_number": "CX888",
  "confirmation": {
    "order_id": "order_xyz",
    "total_price": "67500.00"
  }
}
```

### 4. `comprehensive_reaccommodation_tool` (Recommended)

High-level tool that orchestrates the complete re-accommodation process.

```python
result = await comprehensive_reaccommodation_tool(
    origin="HKG",
    destination="LAX",
    original_departure_date="2025-12-01",
    passenger_count=150,
    vip_count=15,
    delay_minutes=240
)
```

**Returns:** Complete re-accommodation plan with flights, hotels, and actions.

## Test Data

Amadeus test environment provides static data for common routes:

### Sample Flight Routes
- **HKG → LAX** (Hong Kong to Los Angeles)
- **MAD → BCN** (Madrid to Barcelona)
- **NYC → LON** (New York to London)
- **SYD → SIN** (Sydney to Singapore)

### Sample City Codes for Hotels
- **LAX** (Los Angeles)
- **LON** (London)
- **NYC** (New York)
- **PAR** (Paris)

See [Amadeus Test Data Guide](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/test-data/#flights) for full list.

## Usage Examples

### Example 1: Agent Workflow with Amadeus

When you trigger the disruption workflow with agentic system enabled:

```bash
# Start the backend with agentic system
cd backend
AGENTIC_ENABLED=true AMADEUS_CLIENT_ID=your-id AMADEUS_CLIENT_SECRET=your-secret uvicorn app.main:app --reload
```

The RebookingAgent will automatically:
1. Detect disruptions
2. Extract flight details
3. Call Amadeus API for alternatives
4. Return real pricing and availability

### Example 2: Direct API Testing

Test Amadeus integration directly:

```python
from app.services.amadeus_client import get_amadeus_client

client = get_amadeus_client()

# Search flights
offers = await client.search_flight_offers(
    origin="HKG",
    destination="LAX",
    departure_date="2025-12-01",
    adults=1,
    max_results=5
)

print(f"Found {len(offers)} flight offers")
for offer in offers:
    parsed = client.parse_flight_offer(offer)
    print(f"Flight: {parsed['flight_number']}, Price: ${parsed['price']['total']}")
```

### Example 3: Dashboard Integration

The dashboard will automatically display Amadeus data when available:

```javascript
// Frontend detects data source
if (rebookingPlan.data_source === 'amadeus') {
  // Show real flight alternatives with pricing
  rebookingPlan.flight_options.alternatives.forEach(flight => {
    console.log(`${flight.flight_number}: $${flight.price.total}`);
  });
  
  // Show real hotel options
  if (rebookingPlan.hotel_options) {
    console.log(`Hotels: ${rebookingPlan.hotel_options.count} options`);
  }
}
```

## Configuration Options

### Config Settings (`backend/app/config.py`)

```python
@dataclass
class Settings:
    # Amadeus API settings
    amadeus_client_id: str | None = None
    amadeus_client_secret: str | None = None
    amadeus_environment: str = "test"  # test or production
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AMADEUS_CLIENT_ID` | Yes | None | Your Amadeus API client ID |
| `AMADEUS_CLIENT_SECRET` | Yes | None | Your Amadeus API client secret |
| `AMADEUS_ENVIRONMENT` | No | `test` | API environment (`test` or `production`) |

## API Limits

### Test Environment
- **Rate Limits**: 1 transaction per second
- **Monthly Quota**: 2,000 transactions (free)
- **Data**: Static cached data, refreshed daily
- **Booking**: Test bookings only (not real reservations)

### Production Environment
- **Rate Limits**: Higher (varies by plan)
- **Cost**: Pay-per-transaction
- **Data**: Real-time live data
- **Booking**: Real flight reservations

## Troubleshooting

### Error: "Authentication failed"

**Cause**: Invalid or missing credentials

**Solution**: 
1. Verify `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` are correct
2. Check credentials in [Amadeus dashboard](https://developers.amadeus.com/my-apps)

### Error: "No alternative flights found"

**Cause**: Invalid route or date in test environment

**Solution**: 
- Use [known test routes](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/test-data/#flights)
- Ensure date format is `YYYY-MM-DD`
- Try common routes like `HKG → LAX`

### Warning: "Amadeus tools not available - falling back to synthetic data"

**Cause**: Credentials not configured

**Solution**: This is expected behavior. Add credentials to `.env` to enable Amadeus.

### Error: "API request failed: 429 - Too Many Requests"

**Cause**: Rate limit exceeded

**Solution**: 
- Wait 1 second between requests in test environment
- Upgrade to production for higher limits

## Monitoring and Logging

The system logs all Amadeus interactions:

```
🌍 Amadeus client initialized (env=test)
✅ Amadeus access token refreshed
🔍 Searching alternative flights: HKG → LAX on 2025-12-01 for 150 pax
✈️  Found 5 flight offers: HKG → LAX on 2025-12-01
🏨 Found 3 hotels in LAX (2025-12-01 to 2025-12-02)
✅ Re-accommodation plan complete. Flights: 5, Hotels: 3, Est. cost: $250,000.00
```

Look for:
- `data_source: "amadeus"` in agent outputs
- `🌍` emoji for Amadeus API calls
- Cost estimates in USD

## Next Steps

1. **Get Credentials**: [Register at Amadeus](https://developers.amadeus.com/register)
2. **Configure**: Add credentials to `backend/.env`
3. **Test**: Run workflow and check logs for `data_source: "amadeus"`
4. **Integrate**: Update dashboard to display Amadeus data
5. **Production**: Switch to production environment when ready

## Resources

- [Amadeus Self-Service APIs Documentation](https://developers.amadeus.com/self-service)
- [Flight Offers Search API](https://developers.amadeus.com/self-service/category/air/api-doc/flight-offers-search)
- [Hotel Search API](https://developers.amadeus.com/self-service/category/hotel/api-doc/hotel-search)
- [Test Data Guide](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/test-data)
- [API Reference](https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides/test-data/#flights)

## Support

For Amadeus API issues, contact [Amadeus Support](https://developers.amadeus.com/support)

For integration issues with this codebase, check:
- `backend/app/services/amadeus_client.py` - API client
- `backend/app/agentsv2/amadeus_tools.py` - Agent tools
- `backend/app/agentsv2/tools.py` - Tool integration
- `backend/app/agentsv2/agents.py` - RebookingAgent implementation
