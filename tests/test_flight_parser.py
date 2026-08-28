# this is test for day 5

import pytest
from app.services.flight_parser import FlightParser
from app.models.flight_intent import FlightIntent

@pytest.mark.parametrize(
    ("user_prompt", "expected_fields"),
    [
        (
            "I want to fly from Toronto to Calgary.",
            {
                "origin": "Toronto",
                "destination": "Calgary",
                "departure_date": None,
                "trip_type": "unknown",
                "passengers": 1,
            },
        ),
        (
            (
                "I need a one-way business-class ticket "
                "from Toronto to New York on September 15, 2026"
            ),
            {
                "origin": "Toronto",
                "destination": "New York",
                "departure_date": "2026-09-15",
                "trip_type": "one_way",
                "cabin_class": "business",
            },
        ),
        (
            (
                "Find a round trip from Toronto to Vancouver from August 10, 2026 "
                "to August 17, 2026 for 2 passengers in economy under 1200 CAD."
            ),
            {
                "origin": "Toronto",
                "destination": "Vancouver",
                "departure_date": "2026-08-10",
                "return_date": "2026-08-17",
                "trip_type": "round_trip",
                "passengers": 2,
                "cabin_class": "economy",
                "max_price": 1200,
                "currency": "CAD",
                "flexible_dates": False,
                "missing_fields": []
            }
        ),
        (
            (
                "I want to fly from Toronto to Chengdu around Christmas for three weeks. "
                "Two adults and one child, under 5000 CAD."
            ),
            {
                "origin": "Toronto",
                "destination": "Chengdu",
                "trip_type": "unknown",
                "passengers": 3,
                "max_price": 5000,
                "currency": "CAD",
                "flexible_dates": True,
                "departure_date": None,
                "return_date": None,
                "missing_fields": [
                    "departure_date"
                ]
            }
        ),
        (
            "I want to travel next month",
            {
                "origin": None,
                "destination": None,
                "departure_date": None,
                "trip_type": "unknown",
                "flexible_dates":  True,
                "missing_fields": [
                    "origin",
                    "destination",
                    "departure_date"
                    ]
            }
        )
    ],
)
def test_flight_parser(
    user_prompt: str,
    expected_fields: dict,
) -> None:
    
    flight_parser = FlightParser()

    intent = flight_parser.parse(
        user_query=user_prompt,
    )

    assert isinstance(intent, FlightIntent)

    for field, expected_value in expected_fields.items():
        assert getattr(intent, field) == expected_value