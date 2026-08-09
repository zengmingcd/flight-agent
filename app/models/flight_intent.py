from typing import Literal

from pydantic import BaseModel, Field


TripType = Literal["one_way", "round_trip", "unknown"]

CabinClass = Literal[
    "economy",
    "premium_economy",
    "business",
    "first",
    "unknown",
]

Currency = Literal[
    "CAD",
    "USD",
    "CNY",
    "unknown",
]

class FlightIntent(BaseModel):
    """Structured representation of a user's flight search request."""
    origin: str | None = None
    destination: str | None = None
    departure_date: str | None = None
    return_date: str | None = None

    trip_type: TripType = "unknown"
    passengers: int = Field(default=1, ge=1, le=20)
    cabin_class: CabinClass = "unknown"

    max_price: float | None = Field(default=None, gt=0)
    currency: Currency = "unknown"

    flexible_dates: bool = False
    raw_user_query: str = Field(min_length=1)

    missing_fields: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)

