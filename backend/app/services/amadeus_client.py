"""Amadeus API client for flight and hotel operations.

This module provides a wrapper around the Amadeus Self-Service APIs for:
- Flight search and availability
- Flight pricing and booking
- Hotel search and booking
- Airport and city lookups

Uses the test environment by default with static data for development.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from ..config import settings


logger = logging.getLogger(__name__)


class AmadeusAPIError(Exception):
    """Custom exception for Amadeus API errors."""
    pass


class AmadeusClient:
    """Client for Amadeus Self-Service APIs.
    
    Handles authentication, request formatting, and response parsing
    for flight and hotel operations.
    
    Attributes:
        client_id: Amadeus API client ID
        client_secret: Amadeus API client secret
        environment: 'test' or 'production'
        base_url: API base URL based on environment
    """
    
    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        environment: str = "test"
    ):
        """Initialize Amadeus client.
        
        Args:
            client_id: API client ID (defaults to settings)
            client_secret: API client secret (defaults to settings)
            environment: 'test' or 'production' (default: 'test')
        """
        self.client_id = client_id or settings.amadeus_client_id
        self.client_secret = client_secret or settings.amadeus_client_secret
        self.environment = environment
        
        if environment == "production":
            self.base_url = "https://api.amadeus.com"
        else:
            self.base_url = "https://test.api.amadeus.com"
        
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        
        logger.info(f"🌍 Amadeus client initialized (env={environment})")
    
    async def _get_access_token(self) -> str:
        """Get or refresh OAuth2 access token.
        
        Returns:
            Valid access token
            
        Raises:
            AmadeusAPIError: If authentication fails
        """
        # Check if current token is still valid
        if self._access_token and self._token_expiry:
            if datetime.now() < self._token_expiry - timedelta(minutes=5):
                return self._access_token
        
        # Request new token
        auth_url = f"{self.base_url}/v1/security/oauth2/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    auth_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if response.status_code != 200:
                    raise AmadeusAPIError(
                        f"Authentication failed: {response.status_code} - {response.text}"
                    )
                
                token_data = response.json()
                self._access_token = token_data["access_token"]
                expires_in = token_data.get("expires_in", 1800)  # Default 30 min
                self._token_expiry = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("✅ Amadeus access token refreshed")
                return self._access_token
                
        except httpx.HTTPError as e:
            raise AmadeusAPIError(f"HTTP error during authentication: {e}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            params: Query parameters
            json_data: JSON body for POST requests
            
        Returns:
            Response JSON data
            
        Raises:
            AmadeusAPIError: If request fails
        """
        token = await self._get_access_token()
        url = f"{self.base_url}{endpoint}"
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.amadeus+json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=headers, json=json_data)
                else:
                    raise AmadeusAPIError(f"Unsupported HTTP method: {method}")
                
                # Handle errors
                if response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("errors", [{}])[0].get("detail", error_detail)
                    except:
                        pass
                    
                    raise AmadeusAPIError(
                        f"API request failed: {response.status_code} - {error_detail}"
                    )
                
                return response.json()
                
        except httpx.HTTPError as e:
            raise AmadeusAPIError(f"HTTP error during request: {e}")
    
    async def search_flight_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        adults: int = 1,
        max_results: int = 10,
        currency: str = "USD",
        non_stop: bool = False
    ) -> List[Dict[str, Any]]:
        """Search for flight offers.
        
        Args:
            origin: Origin airport code (e.g., 'HKG')
            destination: Destination airport code (e.g., 'LAX')
            departure_date: Departure date in YYYY-MM-DD format
            adults: Number of adult passengers
            max_results: Maximum number of offers to return
            currency: Currency code (default: USD)
            non_stop: Whether to search only non-stop flights
            
        Returns:
            List of flight offer objects
            
        Example:
            offers = await client.search_flight_offers(
                origin="HKG",
                destination="LAX",
                departure_date="2025-12-01",
                adults=150
            )
        """
        params = {
            "originLocationCode": origin,
            "destinationLocationCode": destination,
            "departureDate": departure_date,
            "adults": adults,
            "max": max_results,
            "currencyCode": currency,
        }
        
        if non_stop:
            params["nonStop"] = "true"
        
        try:
            response = await self._make_request("GET", "/v2/shopping/flight-offers", params=params)
            offers = response.get("data", [])
            
            logger.info(
                f"✈️  Found {len(offers)} flight offers: {origin} → {destination} on {departure_date}"
            )
            
            return offers
            
        except AmadeusAPIError as e:
            logger.error(f"Flight search failed: {e}")
            return []
    
    async def price_flight_offer(self, flight_offer: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Confirm pricing for a flight offer.
        
        Args:
            flight_offer: Flight offer object from search_flight_offers
            
        Returns:
            Priced flight offer or None if pricing fails
        """
        try:
            json_data = {
                "data": {
                    "type": "flight-offers-pricing",
                    "flightOffers": [flight_offer]
                }
            }
            
            response = await self._make_request(
                "POST",
                "/v1/shopping/flight-offers/pricing",
                json_data=json_data
            )
            
            priced_offers = response.get("data", {}).get("flightOffers", [])
            if priced_offers:
                logger.info("💰 Flight offer priced successfully")
                return priced_offers[0]
            
            return None
            
        except AmadeusAPIError as e:
            logger.error(f"Flight pricing failed: {e}")
            return None
    
    async def create_flight_order(
        self,
        priced_offer: Dict[str, Any],
        travelers: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Create a flight booking order.
        
        Args:
            priced_offer: Priced flight offer from price_flight_offer
            travelers: List of traveler information
            
        Returns:
            Flight order object or None if booking fails
            
        Example traveler format:
            {
                "id": "1",
                "dateOfBirth": "1990-01-01",
                "name": {
                    "firstName": "JOHN",
                    "lastName": "DOE"
                },
                "contact": {
                    "emailAddress": "john.doe@example.com",
                    "phones": [{
                        "deviceType": "MOBILE",
                        "countryCallingCode": "1",
                        "number": "1234567890"
                    }]
                }
            }
        """
        try:
            json_data = {
                "data": {
                    "type": "flight-order",
                    "flightOffers": [priced_offer],
                    "travelers": travelers
                }
            }
            
            response = await self._make_request(
                "POST",
                "/v1/booking/flight-orders",
                json_data=json_data
            )
            
            order = response.get("data")
            if order:
                pnr = order.get("associatedRecords", [{}])[0].get("reference", "N/A")
                logger.info(f"🎫 Flight order created: PNR={pnr}")
            
            return order
            
        except AmadeusAPIError as e:
            logger.error(f"Flight booking failed: {e}")
            return None
    
    async def search_hotels(
        self,
        city_code: str,
        check_in_date: str,
        check_out_date: str,
        adults: int = 1,
        rooms: int = 1,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for hotel offers.
        
        Args:
            city_code: City code (e.g., 'LAX', 'NYC')
            check_in_date: Check-in date in YYYY-MM-DD format
            check_out_date: Check-out date in YYYY-MM-DD format
            adults: Number of adults
            rooms: Number of rooms
            max_results: Maximum number of results
            
        Returns:
            List of hotel offer objects
        """
        params = {
            "cityCode": city_code,
            "checkInDate": check_in_date,
            "checkOutDate": check_out_date,
            "adults": adults,
            "roomQuantity": rooms,
            "radius": 50,
            "radiusUnit": "KM",
            "hotelSource": "ALL"
        }
        
        try:
            response = await self._make_request("GET", "/v3/shopping/hotel-offers", params=params)
            hotels = response.get("data", [])
            
            logger.info(
                f"🏨 Found {len(hotels)} hotels in {city_code} "
                f"({check_in_date} to {check_out_date})"
            )
            
            return hotels[:max_results]
            
        except AmadeusAPIError as e:
            logger.error(f"Hotel search failed: {e}")
            return []
    
    async def get_flight_status(self, flight_number: str, date: str) -> Optional[Dict[str, Any]]:
        """Get real-time flight status (requires production environment).
        
        Args:
            flight_number: Flight number (e.g., 'CX888')
            date: Flight date in YYYY-MM-DD format
            
        Returns:
            Flight status information or None
        """
        carrier_code = flight_number[:2]
        flight_num = flight_number[2:]
        
        params = {
            "carrierCode": carrier_code,
            "flightNumber": flight_num,
            "scheduledDepartureDate": date
        }
        
        try:
            response = await self._make_request(
                "GET",
                "/v2/schedule/flights",
                params=params
            )
            
            flights = response.get("data", [])
            if flights:
                logger.info(f"📡 Flight status retrieved: {flight_number}")
                return flights[0]
            
            return None
            
        except AmadeusAPIError as e:
            logger.error(f"Flight status lookup failed: {e}")
            return None
    
    def parse_flight_offer(self, offer: Dict[str, Any]) -> Dict[str, Any]:
        """Parse flight offer into simplified format.
        
        Args:
            offer: Raw flight offer from API
            
        Returns:
            Simplified flight offer with key details
        """
        try:
            itinerary = offer["itineraries"][0]
            segments = itinerary["segments"]
            first_segment = segments[0]
            last_segment = segments[-1]
            
            return {
                "id": offer["id"],
                "price": {
                    "total": float(offer["price"]["total"]),
                    "currency": offer["price"]["currency"]
                },
                "departure": {
                    "airport": first_segment["departure"]["iataCode"],
                    "time": first_segment["departure"]["at"],
                    "terminal": first_segment["departure"].get("terminal")
                },
                "arrival": {
                    "airport": last_segment["arrival"]["iataCode"],
                    "time": last_segment["arrival"]["at"],
                    "terminal": last_segment["arrival"].get("terminal")
                },
                "duration": itinerary["duration"],
                "stops": len(segments) - 1,
                "airline": first_segment["carrierCode"],
                "flight_number": f"{first_segment['carrierCode']}{first_segment['number']}",
                "segments": [
                    {
                        "departure": seg["departure"]["iataCode"],
                        "arrival": seg["arrival"]["iataCode"],
                        "airline": seg["carrierCode"],
                        "flight_number": f"{seg['carrierCode']}{seg['number']}"
                    }
                    for seg in segments
                ]
            }
        except (KeyError, IndexError) as e:
            logger.warning(f"Error parsing flight offer: {e}")
            return {}
    
    def parse_hotel_offer(self, hotel: Dict[str, Any]) -> Dict[str, Any]:
        """Parse hotel offer into simplified format.
        
        Args:
            hotel: Raw hotel offer from API
            
        Returns:
            Simplified hotel offer with key details
        """
        try:
            offer = hotel["offers"][0] if hotel.get("offers") else {}
            
            return {
                "id": hotel["hotel"]["hotelId"],
                "name": hotel["hotel"]["name"],
                "rating": hotel["hotel"].get("rating"),
                "price": {
                    "total": float(offer.get("price", {}).get("total", 0)),
                    "currency": offer.get("price", {}).get("currency", "USD")
                },
                "location": {
                    "latitude": hotel["hotel"].get("latitude"),
                    "longitude": hotel["hotel"].get("longitude")
                },
                "address": hotel["hotel"].get("address", {}),
                "checkIn": offer.get("checkInDate"),
                "checkOut": offer.get("checkOutDate"),
                "room": {
                    "type": offer.get("room", {}).get("typeEstimated", {}).get("category"),
                    "beds": offer.get("room", {}).get("typeEstimated", {}).get("beds")
                }
            }
        except (KeyError, IndexError) as e:
            logger.warning(f"Error parsing hotel offer: {e}")
            return {}


# Singleton instance
_amadeus_client: Optional[AmadeusClient] = None


def get_amadeus_client() -> AmadeusClient:
    """Get or create Amadeus client singleton.
    
    Returns:
        Configured AmadeusClient instance
    """
    global _amadeus_client
    
    if _amadeus_client is None:
        _amadeus_client = AmadeusClient()
    
    return _amadeus_client
