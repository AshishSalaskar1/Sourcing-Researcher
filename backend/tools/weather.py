import httpx


async def fetch_weather_forecast(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    forecast_days: int = 7,
) -> dict:
    """Fetch weather forecast from Open-Meteo API.

    No API key needed. Returns daily temperature, precipitation, and weather codes.

    Args:
        client: httpx async client.
        latitude: Location latitude.
        longitude: Location longitude.
        forecast_days: Number of forecast days (1-16).

    Returns:
        Open-Meteo JSON response with daily forecast data.
    """
    resp = await client.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "auto",
            "forecast_days": forecast_days,
        },
    )
    resp.raise_for_status()
    return resp.json()


async def fetch_historical_weather(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> dict:
    """Fetch historical weather from Open-Meteo Archive API.

    Useful for detecting anomalies vs historical norms.

    Args:
        client: httpx async client.
        latitude: Location latitude.
        longitude: Location longitude.
        start_date: Start date (YYYY-MM-DD).
        end_date: End date (YYYY-MM-DD).

    Returns:
        Open-Meteo JSON response with historical daily data.
    """
    resp = await client.get(
        "https://archive-api.open-meteo.com/v1/archive",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max,precipitation_sum",
            "timezone": "auto",
        },
    )
    resp.raise_for_status()
    return resp.json()
