from pydantic import ValidationError
import pytest

from app.models.flight_intent import FlightIntent

def test_complete_flight_intent_is_valid() -> None:
    intent = FlightIntent(
        origin="Toronto",
        destination="Vancouver",
        departure_date="2026-12-23",
        return_date="2027-01-05",
        trip_type="round_trip",
        passengers=3,
        cabin_class="economy",
        max_price=500,
        currency="CAD",
        flexible_date=False,
        raw_user_query="Toronto to Vancouver Round Trip, 2 Passenger economy",
        missing_fields=[],
        confidence=0.95,
    )

    assert intent.origin == "Toronto"
    assert intent.destination == "Vancouver"
    assert intent.passengers == 3

def test_missing_departure_date_is_allowed() -> None:
    intent = FlightIntent(
        origin="Toronto",
        destination="Calgary",
        raw_user_query="Fly from Toronto to Calgary",
        missing_fields=["departure_date"],
        confidence=0.8
    )

    assert intent.departure_date is None
    assert "departure_date" in intent.missing_fields

def test_invalid_cabin_class_is_rejected() -> None:
    with pytest.raises(ValidationError):
        FlightIntent(
            origin="Toronto",
            destination="Vancouver",
            cabin_class="luxury",
            raw_user_query="Luxury flight to Vancouver",
            confidence=0.7
        )