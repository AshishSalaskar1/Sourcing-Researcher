import httpx


async def fetch_world_bank_indicator(
    client: httpx.AsyncClient,
    country_code: str,
    indicator: str,
    years: str = "2019:2024",
) -> dict:
    """Fetch economic indicator from World Bank Open Data API.

    No API key needed. Returns latest available data points.

    Args:
        client: httpx async client.
        country_code: ISO 3-letter country code (e.g., 'MDG').
        indicator: World Bank indicator code (e.g., 'NY.GDP.MKTP.CD').
        years: Date range string (e.g., '2019:2024').

    Returns:
        Dict with indicator, country, and list of year/value entries.
    """
    url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}"
    resp = await client.get(
        url,
        params={"format": "json", "per_page": 10, "date": years},
    )
    resp.raise_for_status()
    data = resp.json()
    if len(data) < 2 or data[1] is None:
        return {"indicator": indicator, "country": country_code, "data": []}
    entries = [
        {"year": item["date"], "value": item["value"]}
        for item in data[1]
        if item["value"] is not None
    ]
    return {"indicator": indicator, "country": country_code, "data": entries}
