from datetime import date
from typing import Any
import httpx
from .config import Settings
from .infra import cached


class ProviderError(RuntimeError):
    pass


class AmadeusProvider:
    def __init__(self, settings: Settings, cache: Any) -> None:
        self.settings = settings
        self.cache = cache
        self.token: str | None = None
        self.token_expires_at = 0.0

    @property
    def configured(self) -> bool:
        return bool(self.settings.amadeus_client_id and self.settings.amadeus_client_secret)

    async def _token(self) -> str:
        import time
        if self.token and time.time() < self.token_expires_at:
            return self.token
        if not self.configured:
            raise ProviderError("Amadeus credentials are not configured")
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{self.settings.amadeus_host}/v1/security/oauth2/token", data={
                "grant_type": "client_credentials", "client_id": self.settings.amadeus_client_id,
                "client_secret": self.settings.amadeus_client_secret,
            })
        if response.is_error:
            raise ProviderError("Amadeus authentication failed")
        payload = response.json()
        self.token = payload["access_token"]
        self.token_expires_at = time.time() + payload.get("expires_in", 1800) - 60
        return self.token

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        token = await self._token()
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(f"{self.settings.amadeus_host}{path}", params=params, headers={"Authorization": f"Bearer {token}"})
        if response.is_error:
            raise ProviderError(response.json().get("errors", [{}])[0].get("detail", "Amadeus request failed"))
        return response.json()

    async def flights(self, origin: str, destination: str, departure_date: date, adults: int) -> list[dict[str, Any]]:
        key = f"flights:{origin}:{destination}:{departure_date}:{adults}"
        async def load() -> list[dict[str, Any]]:
            payload = await self._get("/v2/shopping/flight-offers", {"originLocationCode": origin, "destinationLocationCode": destination, "departureDate": departure_date.isoformat(), "adults": adults, "currencyCode": "EUR", "max": 8})
            return [{"id": offer.get("id"), "price": offer.get("price", {}).get("grandTotal"), "currency": offer.get("price", {}).get("currency", "EUR"), "airline": (offer.get("validatingAirlineCodes") or [None])[0], "duration": offer.get("itineraries", [{}])[0].get("duration"), "stops": max(len(offer.get("itineraries", [{}])[0].get("segments", [])) - 1, 0)} for offer in payload.get("data", [])]
        return await cached(self.cache, key, load, 120)

    async def hotels(self, city_code: str, check_in_date: date, check_out_date: date, adults: int) -> list[dict[str, Any]]:
        key = f"hotels:{city_code}:{check_in_date}:{check_out_date}:{adults}"
        async def load() -> list[dict[str, Any]]:
            payload = await self._get("/v2/shopping/hotel-offers", {"cityCode": city_code, "checkInDate": check_in_date.isoformat(), "checkOutDate": check_out_date.isoformat(), "adults": adults, "roomQuantity": 1, "currency": "EUR", "radius": 20, "radiusUnit": "KM", "hotelSource": "ALL"})
            return [{"hotel_id": item.get("hotel", {}).get("hotelId"), "name": item.get("hotel", {}).get("name"), "rating": item.get("hotel", {}).get("rating"), "price": (item.get("offers") or [{}])[0].get("price", {}).get("total"), "currency": (item.get("offers") or [{}])[0].get("price", {}).get("currency", "EUR")} for item in payload.get("data", [])]
        return await cached(self.cache, key, load, 120)


class MapboxProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def route(self, origin: tuple[float, float], destination: tuple[float, float], profile: str) -> dict[str, Any]:
        if not self.settings.mapbox_token:
            return {"source": "fallback", "distance_m": 0, "duration_s": 0, "geometry": None, "message": "Mapbox token is not configured"}
        coordinates = f"{origin[0]},{origin[1]};{destination[0]},{destination[1]}"
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(f"https://api.mapbox.com/directions/v5/mapbox/{profile}/{coordinates}", params={"access_token": self.settings.mapbox_token, "geometries": "geojson", "overview": "full"})
        if response.is_error:
            raise ProviderError("Mapbox routing failed")
        route = response.json().get("routes", [{}])[0]
        return {"source": "mapbox", "distance_m": route.get("distance"), "duration_s": route.get("duration"), "geometry": route.get("geometry")}


class TomorrowWeatherProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def forecast(self, latitude: float, longitude: float, start_date: date, end_date: date) -> dict[str, Any]:
        if not self.settings.tomorrow_api_key:
            return {"source": "fallback", "location": {"latitude": latitude, "longitude": longitude}, "timeline": [], "message": "Tomorrow.io key is not configured"}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get("https://api.tomorrow.io/v4/weather/forecast", params={"location": f"{latitude},{longitude}", "timesteps": "1d", "apikey": self.settings.tomorrow_api_key, "startTime": start_date.isoformat(), "endTime": end_date.isoformat()})
        if response.is_error:
            raise ProviderError("Tomorrow.io forecast failed")
        return {"source": "tomorrow.io", "location": {"latitude": latitude, "longitude": longitude}, "timeline": response.json().get("timelines", {}).get("daily", [])}
