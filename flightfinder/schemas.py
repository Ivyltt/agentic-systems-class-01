"""Structured data contracts for the agentic workflow.

Schemas make the handoff between agents and deterministic code explicit. ParsedQuery captures the user's request in typed fields, while FlightSearchReport defines the final output that another application could consume."""

from typing import List, Optional

from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    departure_iata: str = Field(description="Origin airport IATA code, for example SFO")
    destination_iata: str = Field(description="Destination airport IATA code, for example JFK")
    date: str = Field(description="Departure date in YYYY-MM-DD format")
    date_window_start: Optional[str] = Field(
        default=None,
        description="Earliest acceptable departure date in YYYY-MM-DD format; null when the date is exact",
    )
    date_window_end: Optional[str] = Field(
        default=None,
        description="Latest acceptable departure date in YYYY-MM-DD format; null when the date is exact",
    )
    return_date: Optional[str] = Field(default=None, description="Return date in YYYY-MM-DD format; null for one-way trips")
    budget_usd: Optional[float] = Field(default=None, description="Maximum budget in USD; null if not mentioned")
    cabin: Optional[str] = Field(default=None, description="Cabin preference, for example economy or business; null if not mentioned")
    other_preferences: Optional[str] = Field(default=None, description="Other preferences, such as whether connections are acceptable")




    date_is_flexible: bool = Field(
        description=(
            "Judge from the user's wording whether the travel date is flexible. Vague wording such as "
            "'around', 'approximately', or 'early November' means true, unless the user emphasizes an exact required date. "
            "Explicit wording such as 'must', 'only', or 'cannot change' means false. Default to true when there is no clue, "
            "because a small, bounded date search is cheaper than missing a better option."
        )
    )


class FlightOption(BaseModel):
    airline: str = Field(description="Airline name")
    departure_date: Optional[str] = Field(
        default=None,
        description="Departure date in YYYY-MM-DD format, copied from the search strategy that produced this option",
    )
    departure_time: str = Field(description="Departure time")
    arrival_time: str = Field(description="Arrival time")
    duration: str = Field(description="Flight duration")
    price_usd: float = Field(description="Price in USD")
    stops: str = Field(description="Nonstop / 1 stop / 2 or more stops")
    source_strategy: str = Field(description="Which parallel date search produced this option, including the searched departure date")
    booking_url: Optional[str] = Field(default=None, description="Booking URL if present in the raw data")


class FlightSearchReport(BaseModel):
    origin: str
    destination: str
    date: str
    within_budget: bool = Field(description="Whether at least one recommended option satisfies the user's budget/preferences")
    options: List[FlightOption] = Field(description="Recommended flight options sorted by value, maximum 5")
    notes: str = Field(description="Additional user-facing notes, especially if the budget could not be fully satisfied")
