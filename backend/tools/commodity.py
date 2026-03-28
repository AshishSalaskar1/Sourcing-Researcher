import json
from pathlib import Path

_PROFILES_DIR = Path(__file__).resolve().parent.parent / "data" / "commodities"
_PROFILES_CACHE: dict[str, dict] = {}


def _load_profiles() -> dict[str, dict]:
    """Load all commodity profiles from JSON files. Cached after first call."""
    if _PROFILES_CACHE:
        return _PROFILES_CACHE
    for path in _PROFILES_DIR.glob("*.json"):
        profile = json.loads(path.read_text())
        name = profile["commodity"].lower()
        _PROFILES_CACHE[name] = profile
        for alias in profile.get("aliases", []):
            _PROFILES_CACHE[alias.lower()] = profile
    return _PROFILES_CACHE


def lookup_commodity_profile(commodity: str) -> dict | None:
    """Look up a commodity profile by name or alias.

    Returns the full profile dict or None if not found.
    """
    profiles = _load_profiles()
    return profiles.get(commodity.lower())


def list_available_commodities() -> list[str]:
    """List all available commodity names."""
    profiles = _load_profiles()
    return sorted({p["commodity"] for p in profiles.values()})
