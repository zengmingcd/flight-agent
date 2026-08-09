# This is test for Day 04

import json
from pathlib import Path
import pytest

from app.services.llm_client import OpenAIClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "app" / "prompts" / "flight_parser_v1.md"

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
                "I want to fly from Toronto to Chengdu around Christmas for three weeks."
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
def test_flight_prompt(
    user_prompt: str,
    expected_fields: dict,
) -> None:
    system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    client = OpenAIClient()

    response_text = client.generate_text(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )

    print(response_text)

    result = json.loads(response_text)

    for field, expected_value in expected_fields.items():
        assert result[field] == expected_value