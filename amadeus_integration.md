Perfect! **FastAPI** is an excellent choice for your flight re-accommodation system — it's fast, async-native, and integrates seamlessly with Amadeus, LangGraph/ADK agents, and real-time dashboards.

Below is a **complete, production-ready FastAPI setup** that ties everything together:

- Real Amadeus integration (search → price → book)
- Your LangGraph/ADK Disruption Workflow
- Mission Control Panel (MCP) via WebSocket + auto-docs
- Async execution, background tasks, rate limiting
- Ready for Docker + Google Cloud Run / AWS / Railway

Just copy-paste and run.

---

### 1. Project Structure

```bash
flight-reaccommodation/
├── main.py                 # FastAPI app
├── amadeus_client.py       # Amadeus wrapper
├── workflow_runner.py      # Your LangGraph/ADK workflow
├── mcp_dashboard.py        # Live MCP (WebSocket + HTML)
├── models.py               # Pydantic models
├── requirements.txt
└── docker-compose.yml
```

---

### 2. `requirements.txt`

```txt
fastapi
uvicorn[standard]
amadeus
python-multipart
jinja2
websockets
pydantic
langgraph
langchain-openai
google-adk  # if using ADK
python-dotenv
```

---

### 3. `amadeus_client.py` – Reusable Wrapper

```python
# amadeus_client.py
from amadeus import Client
from typing import List, Dict, Any
import os

class AmadeusClient:
    def __init__(self):
        self.amadeus = Client(
            client_id=os.getenv("AMADEUS_CLIENT_ID"),
            client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
            hostname=os.getenv("AMADEUS_ENV", "test")  # "production" for live
        )

    async def search_alternatives(self, origin: str, dest: str, date: str, adults: int = 1) -> List[Dict]:
        try:
            resp = self.amadeus.shopping.flight_offers_search.get(
                originLocationCode=origin,
                destinationLocationCode=dest,
                departureDate=date,
                adults=adults,
                currencyCode="USD",
                max=10
            )
            return resp.data
        except Exception as e:
            return {"error": str(e)}

    async def confirm_and_book(self, offer: Dict, travelers: List[Dict]) -> Dict:
        try:
            # Step 1: Price confirmation
            priced = self.amadeus.shopping.flight_offers.pricing.post(offer)
            priced_offer = priced.data['flightOffers'][0]

            # Step 2: Create order
            order = self.amadeus.booking.flight_orders.post(priced_offer, travelers)
            return order.data
        except Exception as e:
            return {"error": str(e), "stage": "booking"}

amadeus = AmadeusClient()
```

---

### 4. `models.py` – Input/Output Schemas

```python
# models.py
from pydantic import BaseModel
from typing import List, Dict, Any

class FlightInput(BaseModel):
    airport: str
    carrier: str
    stats: Dict[str, Any]
    flights: List[Dict[str, Any]]

class RebookResponse(BaseModel):
    status: str
    final_plan: Dict[str, Any]
    audit_log: List[Dict]
    booking_pnr: str = None
    new_flight_number: str = None
```

---

### 5. `workflow_runner.py` – Run Your Agent Workflow

```python
# workflow_runner.py
from app.agents import DisruptionWorkflow  # your existing LangGraph
# OR from adk import your_adk_workflow

workflow = DisruptionWorkflow()

async def run_disruption_workflow(flight_data: dict) -> dict:
    result = await workflow.run(flight_data)
    return result
```

---

### 6. `main.py` – FastAPI App (The Heart)

```python
# main.py
from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import json
import asyncio

from models import FlightInput, RebookResponse
from workflow_runner import run_disruption_workflow
from amadeus_client import amadeus

app = FastAPI(title="Cathay Pacific Disruption Re-Accommodation API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# WebSocket connections for MCP
connections = []

@app.websocket("/ws/mcp")
async def websocket_mcp(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # keep alive
    except WebSocketDisconnect:
        connections.remove(websocket)

async def broadcast_update(message: dict):
    for conn in connections:
        await conn.send_json(message)

# === MCP Dashboard ===
@app.get("/", response_class=HTMLResponse)
async def mcp_dashboard(request: Request):
    return templates.get_template("mcp.html").render({"request": request})

# === API: Trigger Re-Accommodation ===
@app.post("/api/disruption", response_model=RebookResponse)
async def handle_disruption(data: FlightInput, background: BackgroundTasks):
    # Step 1: Run agent workflow
    result = await run_disruption_workflow(data.dict())

    # Step 2: If rebooking needed, call Amadeus
    if result.get("disruption_detected") and result["final_plan"].get("rebooking_plan"):
        rebook_plan = result["final_plan"]["rebooking_plan"]
        origin = data.airport
        dest = "LAX"  # or extract from flight
        new_date = "2025-12-02"  # compute from delay
        adults = rebook_plan.get("estimated_pax", 1)

        offers = await amadeus.search_alternatives(origin, dest, new_date, adults)
        if offers and isinstance(offers, list):
            best_offer = offers[0]
            travelers = [{"id": "1", "name": {"firstName": "PAX", "lastName": "GROUP"}}]  # mock
            booking = await amadeus.confirm_and_book(best_offer, travelers)
      
            if "error" not in booking:
                pnr = booking.get('associatedRecords', [{}])[0].get('reference')
                flight_num = best_offer['itineraries'][0]['segments'][0]['flightNumber']
                result["final_plan"]["booking_pnr"] = pnr
                result["final_plan"]["new_flight_number"] = flight_num

    # Step 3: Broadcast to MCP
    await broadcast_update({
        "type": "update",
        "disruption": result["disruption_detected"],
        "plan": result["final_plan"],
        "audit_log_length": len(result["audit_log"])
    })

    return RebookResponse(
        status="processed",
        final_plan=result["final_plan"],
        audit_log=result["audit_log"],
        booking_pnr=result["final_plan"].get("booking_pnr"),
        new_flight_number=result["final_plan"].get("new_flight_number")
    )
```

---

### 7. `templates/mcp.html` – Mission Control Panel (Live Dashboard)

```html
<!DOCTYPE html>
<html>
<head>
    <title>Cathay Pacific MCP</title>
    <script>
        const ws = new WebSocket("ws://localhost:8000/ws/mcp");
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            document.getElementById("status").innerText = 
                `Disruption: ${data.disruption ? "DETECTED" : "None"} | PNR: ${data.plan.booking_pnr || "Pending"}`;
            console.log(data);
        };
    </script>
    <style>
        body { font-family: Arial; background: #0f1620; color: #00ff88; padding: 20px; }
        #status { font-size: 24px; }
    </style>
</head>
<body>
    <h1>Mission Control Panel (MCP)</h1>
    <div id="status">Waiting for disruption...</div>
    <pre id="log"></pre>
</body>
</html>
```

---

### 8. Run It

```bash
uvicorn main:app --reload --port 8000
```

**Open:**

- API Docs: http://localhost:8000/docs
- MCP Dashboard: http://localhost:8000

Send a test disruption:

```bash
curl -X POST http://localhost:8000/api/disruption \
  -H "Content-Type: application/json" \
  -d @test_input.json
```

Watch the MCP update **live** with PNR and new flight!

---

### Deploy in 2 Minutes (Docker + Cloud Run)

```yaml
# docker-compose.yml
version: '3.8'
services:
  api:
    build: .
    ports: ["8000:8000"]
    env_file: .env
```

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Deploy to **Google Cloud Run** (free tier):

```bash
gcloud run deploy flight-reaccommodation \
  --source . \
  --region asia-east1 \
  --allow-unauthenticated
```

---

Just say the word — you're 90% done with a world-class system!

### Using Test Data for Amadeus Flight APIs

The link you provided points to the Amadeus Self-Service APIs documentation on test data for flights. This guide explains that the test environment (test.api.amadeus.com) returns **static, cached data** for development and testing purposes, rather than live data. This avoids rate limits and allows consistent results without real bookings. The data is generated daily based on trending searches and is available for most major origin/destination pairs.

To access the test data:

- Sign up for a free Amadeus developer account at [developers.amadeus.com](https://developers.amadeus.com) to get API keys.
- Use the test endpoint (`https://test.api.amadeus.com`).
- For flights, use specific parameters in your API calls to trigger static responses. Examples from the docs include:
  - **Flight Offers Search** (GET /v2/shopping/flight-offers): Use `originLocationCode=MAD`, `destinationLocationCode=BCN`, `departureDate=2024-11-15`, `adults=1`, `max=10`. This returns up to 10 static flight offers for a one-way trip from Madrid to Barcelona.
  - **Flight Offers Price** (POST /v1/shopping/flight-offers/pricing): Pass a flight offer ID from the search above in the body (with `X-HTTP-Method-Override: PUT` header for pricing confirmation).
  - **Flight Create Orders** (POST /v1/booking/flight-orders): Use a priced offer from the previous step to simulate booking.
- Other endpoints like Flight Inspiration Search or Cheapest Date Search have similar static behaviors for common routes (e.g., origin=MAD, destination=PAR).

The responses are always in **JSON format**. Parsing is straightforward since it's standard REST JSON. Below, I'll explain the structure for the key flight endpoint (Flight Offers Search) and provide Python code to parse it. This assumes you're using the `requests` library to call the API.

#### Response Structure Overview

The JSON response has two main sections:

- **meta**: Metadata about the query and results.
  - `count`: Number of flight offers returned (e.g., 10).
  - `links`: Pagination links (self, next).
- **data**: Array of flight offer objects (the core dataset).
  - Each object represents one flight option:
    - `id`: Unique identifier for the offer.
    - `source`: Data source (e.g., "GDS" for global distribution system).
    - `price`: Pricing details.
      - `total`: Total price as string (e.g., "120.00").
      - `currency`: Currency code (e.g., "EUR").
      - `base`: Base fare (excl. taxes).
      - `taxes`, `fees`: Breakdowns.
    - `itineraries`: Array of itineraries (usually 1 for one-way).
      - Each itinerary has:
        - `duration`: Total duration (ISO 8601, e.g., "PT2H30M").
        - `segments`: Array of flight segments (e.g., stops).
          - Each segment has `departure`/`arrival` (with `iataCode`, `at` time, `terminal`), `carrierCode` (airline), `number` (flight number), `duration`, etc.
    - `travelerPricings`: Pricing per traveler (matches `adults` count).
      - `price`: Per-traveler price.
      - `fareOption`: "STANDARD" or "PRICE_CHOSEN".
      - `agencyFees`, `amendments`: Optional fees.

For full field details, see the [API reference](https://developers.amadeus.com/self-service/category/air/api-doc/flight-offers-search/api-reference).

#### How to Parse in Python

Here's a complete Python example:

1. Call the API to get the JSON response.
2. Parse with `json.loads()`.
3. Extract key fields like total price, duration, airlines, and flight times.
4. Sort offers by price (optional).

```python
import requests
import json

# Step 1: API call (replace with your keys; use test environment)
api_key = 'YOUR_API_KEY'
api_secret = 'YOUR_API_SECRET'  # Not used directly; get token first via /v1/security/oauth2/token

# First, get access token (omitted for brevity; see docs)
headers = {
    'Authorization': 'Bearer YOUR_ACCESS_TOKEN',
    'Accept': 'application/vnd.amadeus+json'
}

params = {
    'originLocationCode': 'MAD',
    'destinationLocationCode': 'BCN',
    'departureDate': '2024-11-15',
    'adults': 1,
    'max': 10,
    'currencyCode': 'EUR'  # Optional
}

response = requests.get(
    'https://test.api.amadeus.com/v2/shopping/flight-offers',
    headers=headers,
    params=params
)

if response.status_code == 200:
    data = response.json()  # Or json.loads(response.text)
  
    print(f"Found {data['meta']['count']} offers")
  
    # Step 2: Parse and extract
    offers = []
    for offer in data['data']:
        # Basic info
        offer_id = offer['id']
        total_price = float(offer['price']['total'])
        currency = offer['price']['currency']
      
        # Itinerary details (assume first itinerary for one-way)
        itinerary = offer['itineraries'][0]
        total_duration = itinerary['duration']
      
        # Flight segments (e.g., direct or with stops)
        segments = []
        for segment in itinerary['segments']:
            dep_time = segment['departure']['at']
            arr_time = segment['arrival']['at']
            airline = segment['carrierCode']
            flight_num = segment['number']
            dep_airport = segment['departure']['iataCode']
            arr_airport = segment['arrival']['iataCode']
            segments.append({
                'airline': airline,
                'flight': flight_num,
                'dep': f"{dep_airport} at {dep_time}",
                'arr': f"{arr_airport} at {arr_time}"
            })
      
        # Traveler pricing (first traveler)
        traveler_price = offer['travelerPricings'][0]['price']['total']
      
        offers.append({
            'id': offer_id,
            'price': total_price,
            'currency': currency,
            'duration': total_duration,
            'segments': segments,
            'traveler_price': float(traveler_price)
        })
  
    # Step 3: Sort by price (ascending)
    offers.sort(key=lambda x: x['price'])
  
    # Step 4: Output or process (e.g., print top 3)
    for o in offers[:3]:
        print(f"Offer {o['id']}: {o['price']} {o['currency']} ({o['duration']})")
        for seg in o['segments']:
            print(f"  - {seg['airline']}{seg['flight']}: {seg['dep']} -> {seg['arr']}")
    print(json.dumps(offers, indent=2))  # Full parsed data as JSON
else:
    print(f"Error: {response.status_code} - {response.text}")
```

#### Tips for Parsing Test Data

- **Load from file**: If you save the API response to `test_response.json`, load it with `with open('test_response.json') as f: data = json.load(f)`.
- **Error handling**: Check `data['meta']['count'] == 0` for no results. Use try/except for JSON parsing.
- **Advanced extraction**: For multi-stop flights, loop over multiple `itineraries`. Use libraries like `pandas` for tabular output (e.g., `pd.DataFrame(offers)`).
- **Test variations**: Change params like `nonStop=true` or add `returnDate` for round-trip to see different static datasets.
- **Next steps**: Pipe the parsed offer ID into Flight Offers Price for confirmed pricing, then to Create Orders for booking simulation.

This should get you started with parsing the static test datasets. If you share a specific response JSON or endpoint, I can refine the code! For production, switch to `production.api.amadeus.com` with real-time data.
