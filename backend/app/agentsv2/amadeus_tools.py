"""Amadeus API tools for ADK agents.

These tools enable agents to search flights, hotels, and create bookings
using real Amadeus data instead of synthetic data.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from ..services.amadeus_client import get_amadeus_client, AmadeusAPIError
from ..config import settings


logger = logging.getLogger(__name__)


async def search_alternative_flights_tool(
    origin: str,
    destination: str,
    departure_date: str,
    passenger_count: int = 1,
    max_results: int = 5
) -> Dict[str, Any]:
    """Search for alternative flight options using Amadeus API.
    
    This tool searches for real flight offers that can be used for
    passenger re-accommodation during disruptions.
    
    Args:
        origin: Origin airport code (e.g., 'HKG')
        destination: Destination airport code (e.g., 'LAX')
        departure_date: Departure date in YYYY-MM-DD format
        passenger_count: Number of passengers to accommodate
        max_results: Maximum number of alternative flights to return
        
    Returns:
        Dictionary containing:
            - alternatives: List of flight options with pricing
            - count: Number of options found
            - search_params: Parameters used for search
            - error: Error message if search fails
    """
    try:
        client = get_amadeus_client()
        
        logger.info(
            f"🔍 Searching alternative flights: {origin} → {destination} "
            f"on {departure_date} for {passenger_count} pax"
        )
        
        # Search for flight offers
        offers = await client.search_flight_offers(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            adults=min(passenger_count, 9),  # Amadeus API limit per search
            max_results=max_results,
            currency="USD",
            non_stop=False
        )
        
        if not offers:
            return {
                "alternatives": [],
                "count": 0,
                "search_params": {
                    "origin": origin,
                    "destination": destination,
                    "date": departure_date,
                    "passengers": passenger_count
                },
                "error": "No alternative flights found"
            }
        
        # Parse and simplify offers
        alternatives = []
        for offer in offers:
            parsed = client.parse_flight_offer(offer)
            if parsed:
                alternatives.append({
                    **parsed,
                    "raw_offer": offer  # Keep raw offer for booking
                })
        
        logger.info(f"✅ Found {len(alternatives)} alternative flights")
        
        return {
            "alternatives": alternatives,
            "count": len(alternatives),
            "search_params": {
                "origin": origin,
                "destination": destination,
                "date": departure_date,
                "passengers": passenger_count
            },
            "reasoning": (
                f"Located {len(alternatives)} alternative flight options "
                f"with prices ranging from ${min(a['price']['total'] for a in alternatives):.2f} "
                f"to ${max(a['price']['total'] for a in alternatives):.2f}"
            )
        }
        
    except AmadeusAPIError as e:
        logger.error(f"Amadeus API error: {e}")
        return {
            "alternatives": [],
            "count": 0,
            "search_params": {},
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error searching flights: {e}", exc_info=True)
        return {
            "alternatives": [],
            "count": 0,
            "search_params": {},
            "error": f"Unexpected error: {str(e)}"
        }


async def search_hotels_tool(
    city_code: str,
    check_in_date: str,
    check_out_date: str,
    room_count: int = 1,
    passenger_count: int = 1,
    max_results: int = 5
) -> Dict[str, Any]:
    """Search for hotel accommodations using Amadeus API.
    
    This tool searches for hotel options when passengers need overnight
    accommodation due to flight disruptions.
    
    Args:
        city_code: City or airport code (e.g., 'LAX', 'NYC')
        check_in_date: Check-in date in YYYY-MM-DD format
        check_out_date: Check-out date in YYYY-MM-DD format
        room_count: Number of rooms needed
        passenger_count: Number of passengers to accommodate
        max_results: Maximum number of hotels to return
        
    Returns:
        Dictionary containing:
            - hotels: List of hotel options with pricing
            - count: Number of hotels found
            - total_cost: Estimated total cost for all rooms
            - search_params: Parameters used for search
    """
    try:
        client = get_amadeus_client()
        
        logger.info(
            f"🏨 Searching hotels in {city_code}: "
            f"{check_in_date} to {check_out_date}, {room_count} rooms"
        )
        
        # Calculate adults per room
        adults_per_room = max(1, passenger_count // room_count)
        
        # Search for hotels
        hotels = await client.search_hotels(
            city_code=city_code,
            check_in_date=check_in_date,
            check_out_date=check_out_date,
            adults=adults_per_room,
            rooms=room_count,
            max_results=max_results
        )
        
        if not hotels:
            return {
                "hotels": [],
                "count": 0,
                "total_cost": 0,
                "search_params": {
                    "city": city_code,
                    "check_in": check_in_date,
                    "check_out": check_out_date,
                    "rooms": room_count
                },
                "error": "No hotels found"
            }
        
        # Parse hotel offers
        parsed_hotels = []
        total_cost = 0
        for hotel in hotels:
            parsed = client.parse_hotel_offer(hotel)
            if parsed:
                # Calculate cost for all rooms
                per_room_cost = parsed["price"]["total"]
                total_room_cost = per_room_cost * room_count
                total_cost += total_room_cost
                
                parsed["total_cost_all_rooms"] = total_room_cost
                parsed["rooms_booked"] = room_count
                parsed_hotels.append(parsed)
        
        logger.info(
            f"✅ Found {len(parsed_hotels)} hotels, "
            f"estimated cost: ${total_cost:.2f}"
        )
        
        return {
            "hotels": parsed_hotels,
            "count": len(parsed_hotels),
            "total_cost": total_cost,
            "search_params": {
                "city": city_code,
                "check_in": check_in_date,
                "check_out": check_out_date,
                "rooms": room_count,
                "passengers": passenger_count
            },
            "reasoning": (
                f"Located {len(parsed_hotels)} hotel options near {city_code}. "
                f"Estimated total cost for {room_count} rooms: ${total_cost:.2f}"
            )
        }
        
    except AmadeusAPIError as e:
        logger.error(f"Amadeus API error: {e}")
        return {
            "hotels": [],
            "count": 0,
            "total_cost": 0,
            "search_params": {},
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error searching hotels: {e}", exc_info=True)
        return {
            "hotels": [],
            "count": 0,
            "total_cost": 0,
            "search_params": {},
            "error": f"Unexpected error: {str(e)}"
        }


async def book_flight_tool(
    flight_offer: Dict[str, Any],
    passenger_count: int,
    passenger_details: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Book a flight using Amadeus API.
    
    This tool confirms pricing and creates a flight order for the selected
    alternative flight during re-accommodation.
    
    Args:
        flight_offer: Flight offer object (from search_alternative_flights_tool)
        passenger_count: Number of passengers to book
        passenger_details: Optional list of passenger information
        
    Returns:
        Dictionary containing:
            - success: Whether booking succeeded
            - pnr: Booking reference number
            - flight_number: Booked flight number
            - confirmation: Booking confirmation details
            - error: Error message if booking fails
    """
    try:
        client = get_amadeus_client()
        
        # Extract raw offer (needed for API calls)
        raw_offer = flight_offer.get("raw_offer", flight_offer)
        
        logger.info(
            f"📝 Attempting to book flight {flight_offer.get('flight_number', 'N/A')} "
            f"for {passenger_count} passengers"
        )
        
        # Step 1: Confirm pricing
        priced_offer = await client.price_flight_offer(raw_offer)
        
        if not priced_offer:
            return {
                "success": False,
                "error": "Failed to confirm flight pricing"
            }
        
        # Step 2: Prepare traveler data
        # In production, this would come from passenger manifest
        # For now, create mock travelers
        travelers = passenger_details or []
        if not travelers:
            for i in range(min(passenger_count, 9)):  # API limit
                travelers.append({
                    "id": str(i + 1),
                    "dateOfBirth": "1990-01-01",
                    "name": {
                        "firstName": f"PASSENGER{i+1}",
                        "lastName": "DOE"
                    },
                    "contact": {
                        "emailAddress": f"passenger{i+1}@cathay.com",
                        "phones": [{
                            "deviceType": "MOBILE",
                            "countryCallingCode": "852",
                            "number": "12345678"
                        }]
                    }
                })
        
        # Step 3: Create booking
        order = await client.create_flight_order(priced_offer, travelers)
        
        if not order:
            return {
                "success": False,
                "error": "Failed to create flight booking"
            }
        
        # Extract booking details
        pnr = order.get("associatedRecords", [{}])[0].get("reference", "N/A")
        flight_number = flight_offer.get("flight_number", "N/A")
        
        logger.info(f"✅ Flight booked successfully: PNR={pnr}")
        
        return {
            "success": True,
            "pnr": pnr,
            "flight_number": flight_number,
            "confirmation": {
                "order_id": order.get("id"),
                "booking_date": datetime.now().isoformat(),
                "passengers_booked": len(travelers),
                "total_price": priced_offer.get("price", {}).get("total"),
                "currency": priced_offer.get("price", {}).get("currency")
            },
            "reasoning": (
                f"Successfully booked flight {flight_number} for {len(travelers)} passengers. "
                f"PNR: {pnr}"
            )
        }
        
    except AmadeusAPIError as e:
        logger.error(f"Amadeus booking error: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    except Exception as e:
        logger.error(f"Unexpected error during booking: {e}", exc_info=True)
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}"
        }


async def comprehensive_reaccommodation_tool(
    origin: str,
    destination: str,
    original_departure_date: str,
    passenger_count: int,
    vip_count: int = 0,
    delay_minutes: int = 0
) -> Dict[str, Any]:
    """Comprehensive re-accommodation tool combining flights and hotels.
    
    This high-level tool orchestrates the complete re-accommodation process:
    1. Search for alternative flights
    2. If overnight stay needed, search for hotels
    3. Return complete re-accommodation plan
    
    Args:
        origin: Origin airport code
        destination: Destination airport code
        original_departure_date: Original departure date
        passenger_count: Number of passengers
        vip_count: Number of VIP passengers
        delay_minutes: Expected delay duration
        
    Returns:
        Dictionary containing:
            - flight_options: Alternative flight options
            - hotel_options: Hotel options (if needed)
            - recommended_plan: Recommended re-accommodation strategy
            - total_cost_estimate: Estimated total cost
    """
    try:
        logger.info(
            f"🎯 Comprehensive re-accommodation: {origin}→{destination}, "
            f"{passenger_count} pax, {delay_minutes}min delay"
        )
        
        # Determine new departure date based on delay
        original_date = datetime.strptime(original_departure_date, "%Y-%m-%d")
        
        if delay_minutes > 180:  # 3+ hours
            new_departure_date = (original_date + timedelta(days=1)).strftime("%Y-%m-%d")
            needs_hotel = True
        else:
            new_departure_date = original_departure_date
            needs_hotel = False
        
        # Step 1: Search alternative flights
        flight_results = await search_alternative_flights_tool(
            origin=origin,
            destination=destination,
            departure_date=new_departure_date,
            passenger_count=passenger_count,
            max_results=5
        )
        
        hotel_results = None
        total_cost = 0
        
        # Step 2: Search hotels if needed
        if needs_hotel and flight_results["count"] > 0:
            # Estimate room count (2 passengers per room)
            room_count = max(1, passenger_count // 2)
            
            # Get city code from destination
            city_code = destination[:3] if len(destination) > 3 else destination
            
            hotel_results = await search_hotels_tool(
                city_code=city_code,
                check_in_date=original_departure_date,
                check_out_date=new_departure_date,
                room_count=room_count,
                passenger_count=passenger_count,
                max_results=3
            )
            
            if hotel_results["count"] > 0:
                total_cost += hotel_results["total_cost"]
        
        # Step 3: Calculate total cost including flight
        if flight_results["count"] > 0:
            best_flight = flight_results["alternatives"][0]
            # Estimate total flight cost (price shown is per person in some APIs)
            flight_cost = best_flight["price"]["total"] * passenger_count
            total_cost += flight_cost
        
        # Step 4: Create recommended plan
        recommended_plan = {
            "strategy": "next_day_with_hotel" if needs_hotel else "same_day_alternate",
            "priority": "high" if vip_count > 0 else "medium",
            "actions": []
        }
        
        if flight_results["count"] > 0:
            recommended_plan["actions"].append({
                "type": "rebook_flight",
                "details": f"Rebook on {flight_results['alternatives'][0]['flight_number']}",
                "departure_time": flight_results['alternatives'][0]['departure']['time']
            })
        
        if needs_hotel and hotel_results and hotel_results["count"] > 0:
            recommended_plan["actions"].append({
                "type": "book_hotel",
                "details": f"Arrange overnight stay at {hotel_results['hotels'][0]['name']}",
                "cost": hotel_results['hotels'][0]['price']['total']
            })
        
        if vip_count > 0:
            recommended_plan["actions"].insert(0, {
                "type": "vip_priority",
                "details": f"Prioritize {vip_count} VIP passengers for immediate rebooking"
            })
        
        recommended_plan["actions"].append({
            "type": "notify_passengers",
            "details": "Send SMS/email notifications with new itinerary"
        })
        
        logger.info(
            f"✅ Re-accommodation plan complete. "
            f"Flights: {flight_results['count']}, "
            f"Hotels: {hotel_results['count'] if hotel_results else 0}, "
            f"Est. cost: ${total_cost:.2f}"
        )
        
        return {
            "flight_options": flight_results,
            "hotel_options": hotel_results,
            "recommended_plan": recommended_plan,
            "total_cost_estimate": total_cost,
            "needs_hotel": needs_hotel,
            "reasoning": (
                f"Delay of {delay_minutes} minutes requires "
                f"{'next-day rebooking with hotel accommodation' if needs_hotel else 'same-day alternative flight'}. "
                f"Found {flight_results['count']} flight options. "
                f"Estimated total cost: ${total_cost:,.2f}"
            )
        }
        
    except Exception as e:
        logger.error(f"Error in comprehensive re-accommodation: {e}", exc_info=True)
        return {
            "flight_options": {"alternatives": [], "count": 0},
            "hotel_options": None,
            "recommended_plan": {
                "strategy": "manual_intervention_required",
                "actions": []
            },
            "total_cost_estimate": 0,
            "error": str(e)
        }


# Tool registry for Amadeus tools
AMADEUS_TOOLS = {
    "search_alternative_flights": search_alternative_flights_tool,
    "search_hotels": search_hotels_tool,
    "book_flight": book_flight_tool,
    "comprehensive_reaccommodation": comprehensive_reaccommodation_tool,
}
