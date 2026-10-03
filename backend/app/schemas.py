from datetime import date
from typing import Literal
from pydantic import BaseModel, Field


class FlightSearch(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_date: date
    adults: int = Field(default=1, ge=1, le=9)


class HotelSearch(BaseModel):
    city_code: str = Field(min_length=3, max_length=3)
    check_in_date: date
    check_out_date: date
    adults: int = Field(default=1, ge=1, le=9)


class VibeSearch(BaseModel):
    query: str = Field(min_length=2, max_length=300)
    city: str = Field(default="Lisbon", max_length=80)
    limit: int = Field(default=8, ge=1, le=20)


class TripPlanRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=100)
    start_date: date
    end_date: date
    travelers: int = Field(default=1, ge=1, le=20)
    budget_eur: float = Field(default=1000, gt=0)
    preferences: list[str] = Field(default_factory=list)
    energy_level: Literal["low", "medium", "high"] = "medium"


class RouteRequest(BaseModel):
    origin: tuple[float, float]
    destination: tuple[float, float]
    profile: Literal["driving", "walking", "cycling", "driving-traffic"] = "walking"


class WeatherRequest(BaseModel):
    latitude: float
    longitude: float
    start_date: date
    end_date: date


class TransactionCreate(BaseModel):
    trip_id: str
    description: str = Field(min_length=1, max_length=200)
    amount_eur: float = Field(gt=0)
    participants: list[str] = Field(default_factory=list)
