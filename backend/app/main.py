import asyncio
from contextlib import asynccontextmanager
from datetime import date
from typing import Any
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from .agents import VibeSearch, plan_trip
from .config import get_settings
from .infra import Database, create_cache
from .providers import AmadeusProvider, MapboxProvider, ProviderError, TomorrowWeatherProvider
from .schemas import FlightSearch, HotelSearch, RouteRequest, TransactionCreate, TripPlanRequest, VibeSearch as VibeSearchRequest, WeatherRequest

settings = get_settings()
cache: Any = None
cache_mode = "memory"
database = Database(settings.database_url)
amadeus: AmadeusProvider
mapbox: MapboxProvider
tomorrow: TomorrowWeatherProvider
vibes: VibeSearch


@asynccontextmanager
async def lifespan(_app: FastAPI):
    global cache, cache_mode, amadeus, mapbox, tomorrow, vibes
    cache, cache_mode = await create_cache(settings.redis_url)
    await database.connect()
    amadeus = AmadeusProvider(settings, cache)
    mapbox = MapboxProvider(settings)
    tomorrow = TomorrowWeatherProvider(settings)
    vibes = VibeSearch(settings)
    yield
    await cache.close()
    await database.close()


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "service": settings.app_name, "cache": cache_mode, "database": database.mode, "providers": {"amadeus": amadeus.configured if 'amadeus' in globals() else False, "mapbox": bool(settings.mapbox_token), "tomorrow_io": bool(settings.tomorrow_api_key), "pinecone": bool(settings.pinecone_api_key)}}


@app.post("/api/flights")
async def flights(request: FlightSearch) -> dict[str, Any]:
    try:
        results = await amadeus.flights(request.origin.upper(), request.destination.upper(), request.departure_date, request.adults)
        return {"source": "amadeus", "results": results}
    except ProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/hotels")
async def hotels(request: HotelSearch) -> dict[str, Any]:
    if request.check_out_date <= request.check_in_date:
        raise HTTPException(status_code=422, detail="check_out_date must be after check_in_date")
    try:
        results = await amadeus.hotels(request.city_code.upper(), request.check_in_date, request.check_out_date, request.adults)
        return {"source": "amadeus", "results": results}
    except ProviderError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.post("/api/vibe-search")
async def vibe_search(request: VibeSearchRequest) -> dict[str, Any]:
    return {"source": "pinecone" if settings.pinecone_api_key else "local-fallback", "results": await vibes.search(request.query, request.city, request.limit)}


@app.post("/api/route")
async def route(request: RouteRequest) -> dict[str, Any]:
    try:
        return await mapbox.route(request.origin, request.destination, request.profile)
    except ProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/weather")
async def weather(request: WeatherRequest) -> dict[str, Any]:
    if request.end_date < request.start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    try:
        return await tomorrow.forecast(request.latitude, request.longitude, request.start_date, request.end_date)
    except ProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@app.post("/api/trips/plan")
async def trips_plan(request: TripPlanRequest) -> dict[str, Any]:
    if request.end_date < request.start_date:
        raise HTTPException(status_code=422, detail="end_date must be on or after start_date")
    result = await plan_trip(request.model_dump(), settings)
    await database.save_trip(result["trip_id"], request.destination, result)
    return result


@app.post("/api/transactions", status_code=201)
async def create_transaction(request: TransactionCreate) -> dict[str, Any]:
    from uuid import uuid4
    transaction = {"id": str(uuid4()), **request.model_dump()}
    await database.save_transaction(transaction["id"], transaction)
    return {"transaction": transaction, "split_amount_eur": round(request.amount_eur / max(len(request.participants), 1), 2)}


class ConnectionManager:
    def __init__(self) -> None:
        self.connections: dict[str, set[WebSocket]] = {}

    async def connect(self, trip_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.connections.setdefault(trip_id, set()).add(websocket)

    def disconnect(self, trip_id: str, websocket: WebSocket) -> None:
        self.connections.get(trip_id, set()).discard(websocket)

    async def broadcast(self, trip_id: str, message: dict[str, Any]) -> None:
        await asyncio.gather(*(connection.send_json(message) for connection in self.connections.get(trip_id, set())), return_exceptions=True)


manager = ConnectionManager()


@app.websocket("/ws/trips/{trip_id}")
async def trip_socket(websocket: WebSocket, trip_id: str) -> None:
    await manager.connect(trip_id, websocket)
    try:
        await websocket.send_json({"event": "connected", "trip_id": trip_id})
        while True:
            message = await websocket.receive_json()
            message["trip_id"] = trip_id
            await manager.broadcast(trip_id, {"event": "trip_update", "data": message})
    except WebSocketDisconnect:
        manager.disconnect(trip_id, websocket)
