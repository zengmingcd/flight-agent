from ..models.flight_intent import FlightIntent
from pathlib import Path
from .llm_client import OpenAIClient
from .flight_parsing_error import FlightParsingError

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_PATH = PROJECT_ROOT / "prompts" / "flight_parser_v1.md"

class FlightParser:
    def __init__(self) -> None:
        self.client = OpenAIClient()
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def parse(self, user_query: str) -> FlightIntent:
        try:
            intent = self.client.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_query,
                response_model=FlightIntent
            )
        except Exception as exc:
            raise FlightParsingError(
                "Failed to parse flight query!"
            ) from exc

        intent.missing_fields = self.calculate_missing_fields(intent)

        return intent
    
    def calculate_missing_fields(self, intent: FlightIntent) -> list[str]:
        missing_fields = []
        
        if intent.origin is None:
            missing_fields.append("origin")

        if intent.destination is None:
            missing_fields.append("destination")

        if intent.departure_date is None:
            missing_fields.append("departure_date")

        if (intent.trip_type == "round_trip"
            and intent.return_date is None):
            missing_fields.append("return_date")

        return missing_fields
