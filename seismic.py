"""
Prologis Racking BOM Tool — Seismic Lookup & Engineering Requirements Module

Provides:
  - Address geocoding via Nominatim/OSM
  - USGS ASCE 7-22 seismic design parameter lookups
  - SDC-based engineering requirement mapping for racking systems
  - Combined site lookup pipeline
  - Prologis market presets with pre-computed data
  - FastAPI route registration helper
"""

from __future__ import annotations

import json
import time
import urllib.parse
from functools import lru_cache
from typing import Any

import requests

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REQUEST_TIMEOUT = 15  # seconds
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USGS_URL = "https://earthquake.usgs.gov/ws/designmaps/asce7-22.json"
USER_AGENT = "PrologisRackingBOMTool/1.0 (seismic-lookup; contact@prologis-bom.internal)"

# Simple in-memory cache with TTL (seconds)
_CACHE: dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 3600  # 1 hour


def _cache_get(key: str) -> Any | None:
    entry = _CACHE.get(key)
    if entry and (time.time() - entry[0]) < _CACHE_TTL:
        return entry[1]
    if entry:
        del _CACHE[key]
    return None


def _cache_set(key: str, value: Any) -> None:
    _CACHE[key] = (time.time(), value)


# ---------------------------------------------------------------------------
# 1. Address Geocoding
# ---------------------------------------------------------------------------

def geocode(address: str) -> tuple[float, float]:
    """
    Geocode an address string to (latitude, longitude) via Nominatim/OSM.

    Raises ValueError if the address cannot be resolved.
    Raises requests.RequestException on network errors.
    """
    cache_key = f"geo:{address.strip().lower()}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    params = {"q": address, "format": "json", "limit": 1}
    headers = {"User-Agent": USER_AGENT}

    resp = requests.get(NOMINATIM_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    results = resp.json()
    if not results:
        raise ValueError(f"Geocoding failed: no results for '{address}'")

    lat = float(results[0]["lat"])
    lon = float(results[0]["lon"])
    result = (lat, lon)
    _cache_set(cache_key, result)
    return result


# ---------------------------------------------------------------------------
# 2. USGS Seismic Design Lookup
# ---------------------------------------------------------------------------

def get_seismic_data(
    lat: float,
    lon: float,
    risk_category: str = "II",
    site_class: str = "D",
) -> dict:
    """
    Query the USGS ASCE 7-22 web service for seismic design parameters.

    Returns dict with keys:
        ss, s1, sds, sd1, sdc, sms, sm1, pgam

    Risk Category II = standard for warehouses (non-essential facilities).
    Site Class D = default when no geotechnical/soil data is available.
    """
    cache_key = f"usgs:{lat:.4f},{lon:.4f},{risk_category},{site_class}"
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    params = {
        "latitude": round(lat, 4),
        "longitude": round(lon, 4),
        "riskCategory": risk_category,
        "siteClass": site_class,
        "title": "PrologisBOM",
    }

    resp = requests.get(USGS_URL, params=params, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()

    payload = resp.json()

    # Check for API-level errors
    req_info = payload.get("request", {})
    if req_info.get("status") != "success":
        error_msg = payload.get("response", "Unknown USGS API error")
        raise RuntimeError(f"USGS API error: {error_msg}")

    data = payload["response"]["data"]

    result = {
        "ss": data.get("ss"),
        "s1": data.get("s1"),
        "sds": data.get("sds"),
        "sd1": data.get("sd1"),
        "sdc": data.get("sdc"),
        "sms": data.get("sms"),
        "sm1": data.get("sm1"),
        "pgam": data.get("pgam"),
    }
    _cache_set(cache_key, result)
    return result


# ---------------------------------------------------------------------------
# 3. SDC → Engineering Requirements
# ---------------------------------------------------------------------------

# California FIPS state code check (simple heuristic via lat/lon bounding box)
_CA_LAT_RANGE = (32.5, 42.0)
_CA_LON_RANGE = (-124.5, -114.1)


def _is_california(lat: float | None = None, lon: float | None = None) -> bool:
    """Rough bounding-box check for California."""
    if lat is None or lon is None:
        return False
    return (_CA_LAT_RANGE[0] <= lat <= _CA_LAT_RANGE[1] and
            _CA_LON_RANGE[0] <= lon <= _CA_LON_RANGE[1])


def sdc_requirements(
    sdc: str,
    frame_height_in: float = 240.0,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    """
    Map a Seismic Design Category (A–F) to recommended racking engineering
    parameters.

    Parameters
    ----------
    sdc : str
        Seismic Design Category letter (A through F).
    frame_height_in : float
        Upright frame height in inches (default 240 = 20 ft).
    lat, lon : float, optional
        Coordinates used to determine building code jurisdiction (IBC vs CBC).

    Returns
    -------
    dict with engineering requirement fields.
    """
    sdc = sdc.upper().strip()
    if sdc not in {"A", "B", "C", "D", "E", "F"}:
        raise ValueError(f"Invalid SDC: '{sdc}'. Must be A–F.")

    # ---- Anchors per base plate ----
    if sdc in ("A", "B"):
        anchors_per_bp = 1
    elif sdc == "C":
        anchors_per_bp = 2
    else:  # D, E, F
        anchors_per_bp = 4

    # Two base plates per upright frame (left foot + right foot)
    anchors_per_frame = anchors_per_bp * 2

    # ---- Anchor type ----
    if sdc in ("A", "B"):
        anchor_type = "wedge"
    else:
        anchor_type = "Hilti Kwik Bolt TZ2"

    # ---- Anchor size ----
    if sdc in ("A", "B", "C"):
        anchor_size = '1/2" x 4"'
        anchor_embed = '2.25"'
    else:  # D, E, F
        anchor_size = '5/8" x 4.5"'
        anchor_embed = '3.75"'

    # ---- Bracing ----
    if sdc in ("A", "B"):
        bracing = "standard"
    elif sdc == "C":
        bracing = "enhanced"
    else:
        bracing = "full seismic"

    # ---- Row spacers & engineering ----
    row_spacers_required = sdc not in ("A", "B")
    prelim_engineering_required = sdc not in ("A", "B")

    # ---- Building code jurisdiction ----
    building_code = "CBC" if _is_california(lat, lon) else "IBC"

    return {
        "sdc": sdc,
        "frame_height_in": frame_height_in,
        "anchors_per_base_plate": anchors_per_bp,
        "anchors_per_frame": anchors_per_frame,
        "anchor_type": anchor_type,
        "anchor_size": anchor_size,
        "anchor_embed_depth": anchor_embed,
        "base_plate_bolts": anchors_per_bp,
        "bracing_required": bracing,
        "row_spacers_required": row_spacers_required,
        "prelim_engineering_required": prelim_engineering_required,
        "building_code": building_code,
    }


# ---------------------------------------------------------------------------
# 4. Combined Site Lookup
# ---------------------------------------------------------------------------

def lookup_site(
    address: str,
    risk_category: str = "II",
    site_class: str = "D",
    frame_height_in: float = 240.0,
) -> dict:
    """
    Full pipeline: address → geocode → USGS seismic data → engineering reqs.

    Returns a single dict with all fields the design engine needs.
    """
    lat, lon = geocode(address)

    seismic = get_seismic_data(lat, lon, risk_category=risk_category, site_class=site_class)

    sdc_letter = seismic.get("sdc", "D")
    reqs = sdc_requirements(sdc_letter, frame_height_in=frame_height_in, lat=lat, lon=lon)

    return {
        "address": address,
        "latitude": lat,
        "longitude": lon,
        "risk_category": risk_category,
        "site_class": site_class,
        "seismic": seismic,
        "requirements": reqs,
    }


# ---------------------------------------------------------------------------
# 5. Prologis Market Presets
# ---------------------------------------------------------------------------

PROLOGIS_MARKETS: dict[str, dict] = {
    # ── Inland Empire / SoCal ──────────────────────────────────────────
    "Perris, CA": {
        "lat": 33.7825, "lon": -117.2281,
        "typical_sdc": "D", "building_code": "CBC",
        "typical_clear_height_ft": 36,
        "market": "Inland Empire",
    },
    "Ontario, CA": {
        "lat": 34.0633, "lon": -117.6509,
        "typical_sdc": "D", "building_code": "CBC",
        "typical_clear_height_ft": 36,
        "market": "Inland Empire",
    },
    "Rancho Cucamonga, CA": {
        "lat": 34.1064, "lon": -117.5931,
        "typical_sdc": "D", "building_code": "CBC",
        "typical_clear_height_ft": 36,
        "market": "Inland Empire",
    },
    # ── Chicago ────────────────────────────────────────────────────────
    "Joliet, IL": {
        "lat": 41.5250, "lon": -88.0817,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Chicago",
    },
    "Romeoville, IL": {
        "lat": 41.6475, "lon": -88.0895,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Chicago",
    },
    "Elwood, IL": {
        "lat": 41.4039, "lon": -88.1115,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Chicago",
    },
    # ── Dallas / DFW ───────────────────────────────────────────────────
    "Dallas, TX": {
        "lat": 32.7767, "lon": -96.7970,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "DFW",
    },
    "Fort Worth, TX": {
        "lat": 32.7555, "lon": -97.3308,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "DFW",
    },
    "Alliance, TX": {
        "lat": 32.9690, "lon": -97.3197,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 40,
        "market": "DFW",
    },
    # ── New Jersey / PA ────────────────────────────────────────────────
    "Edison, NJ": {
        "lat": 40.5187, "lon": -74.4121,
        "typical_sdc": "B", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "NJ/PA",
    },
    "Cranbury, NJ": {
        "lat": 40.3165, "lon": -74.5135,
        "typical_sdc": "B", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "NJ/PA",
    },
    "Carlisle, PA": {
        "lat": 40.2015, "lon": -77.1886,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "NJ/PA",
    },
    # ── Atlanta ────────────────────────────────────────────────────────
    "McDonough, GA": {
        "lat": 33.4473, "lon": -84.1469,
        "typical_sdc": "B", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Atlanta",
    },
    "Jackson, GA": {
        "lat": 33.2946, "lon": -83.9660,
        "typical_sdc": "B", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Atlanta",
    },
    # ── Memphis ────────────────────────────────────────────────────────
    "Memphis, TN": {
        "lat": 35.1495, "lon": -90.0490,
        "typical_sdc": "D", "building_code": "IBC",
        "typical_clear_height_ft": 32,
        "market": "Memphis",
    },
    # ── Indianapolis ───────────────────────────────────────────────────
    "Indianapolis, IN": {
        "lat": 39.7684, "lon": -86.1581,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Indianapolis",
    },
    # ── Columbus ───────────────────────────────────────────────────────
    "Columbus, OH": {
        "lat": 39.9612, "lon": -82.9988,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Columbus",
    },
    # ── Houston ────────────────────────────────────────────────────────
    "Houston, TX": {
        "lat": 29.7604, "lon": -95.3698,
        "typical_sdc": "A", "building_code": "IBC",
        "typical_clear_height_ft": 32,
        "market": "Houston",
    },
    # ── Seattle / Tacoma ───────────────────────────────────────────────
    "Seattle, WA": {
        "lat": 47.6062, "lon": -122.3321,
        "typical_sdc": "D", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Seattle/Tacoma",
    },
    "Tacoma, WA": {
        "lat": 47.2529, "lon": -122.4443,
        "typical_sdc": "D", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Seattle/Tacoma",
    },
    # ── Phoenix ────────────────────────────────────────────────────────
    "Phoenix, AZ": {
        "lat": 33.4484, "lon": -112.0740,
        "typical_sdc": "B", "building_code": "IBC",
        "typical_clear_height_ft": 36,
        "market": "Phoenix",
    },
    # ── Denver ─────────────────────────────────────────────────────────
    "Denver, CO": {
        "lat": 39.7392, "lon": -104.9903,
        "typical_sdc": "B", "building_code": "IBC",
        "typical_clear_height_ft": 32,
        "market": "Denver",
    },
}


def get_market_preset(location: str) -> dict | None:
    """
    Look up a Prologis market preset by city name (case-insensitive partial match).

    Returns the preset dict or None if not found.
    """
    loc_lower = location.strip().lower()
    for key, data in PROLOGIS_MARKETS.items():
        if loc_lower in key.lower() or loc_lower == data.get("market", "").lower():
            return {"location": key, **data}
    return None


def lookup_market(location: str, frame_height_in: float | None = None) -> dict:
    """
    Convenience: use a market preset with sdc_requirements applied.
    Falls back to a live lookup_site if no preset matches.
    """
    preset = get_market_preset(location)
    if preset is None:
        # Not a known preset — do a live lookup
        return lookup_site(location, frame_height_in=frame_height_in or 240.0)

    height = frame_height_in or (preset["typical_clear_height_ft"] * 12)
    reqs = sdc_requirements(
        preset["typical_sdc"],
        frame_height_in=height,
        lat=preset["lat"],
        lon=preset["lon"],
    )
    return {
        "address": preset["location"],
        "latitude": preset["lat"],
        "longitude": preset["lon"],
        "market": preset.get("market"),
        "typical_clear_height_ft": preset.get("typical_clear_height_ft"),
        "risk_category": "II",
        "site_class": "D",
        "seismic": {
            "sdc": preset["typical_sdc"],
            "note": "preset value — call lookup_site() for live USGS data",
        },
        "requirements": reqs,
    }


# ---------------------------------------------------------------------------
# 6. FastAPI Route Registration Helper
# ---------------------------------------------------------------------------

def register_routes(app) -> None:
    """
    Register seismic API routes on a FastAPI (or compatible) app instance.

    Usage in server.py:
        from seismic import register_routes
        register_routes(app)
    """
    from fastapi import Query, HTTPException

    @app.get("/api/seismic")
    async def seismic_lookup(
        address: str = Query(..., description="Full street address or city/state"),
        risk_category: str = Query("II", description="ASCE 7 risk category (I–IV)"),
        site_class: str = Query("D", description="Site class (A–F)"),
        frame_height_in: float = Query(240.0, description="Frame height in inches"),
    ):
        """Look up seismic design parameters and racking engineering requirements for an address."""
        try:
            result = lookup_site(
                address,
                risk_category=risk_category,
                site_class=site_class,
                frame_height_in=frame_height_in,
            )
            return {"status": "ok", "data": result}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except requests.RequestException as exc:
            raise HTTPException(status_code=502, detail=f"Upstream API error: {exc}")
        except RuntimeError as exc:
            raise HTTPException(status_code=502, detail=str(exc))
        except Exception as exc:
            raise HTTPException(status_code=500, detail=f"Internal error: {exc}")

    @app.get("/api/seismic/markets")
    async def list_markets():
        """List all Prologis market presets."""
        return {"status": "ok", "markets": PROLOGIS_MARKETS}

    @app.get("/api/seismic/market")
    async def market_lookup(
        location: str = Query(..., description="City name or Prologis market name"),
        frame_height_in: float | None = Query(None, description="Override frame height"),
    ):
        """Look up seismic requirements using a Prologis market preset."""
        try:
            result = lookup_market(location, frame_height_in=frame_height_in)
            return {"status": "ok", "data": result}
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))

    @app.get("/api/seismic/sdc-requirements")
    async def sdc_req_endpoint(
        sdc: str = Query(..., description="Seismic Design Category (A–F)"),
        frame_height_in: float = Query(240.0, description="Frame height in inches"),
    ):
        """Get engineering requirements for a given SDC without an address lookup."""
        try:
            result = sdc_requirements(sdc, frame_height_in=frame_height_in)
            return {"status": "ok", "data": result}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    addr = sys.argv[1] if len(sys.argv) > 1 else "4323 Indian Ave, Perris, CA 92571"
    print(f"Looking up: {addr}\n")

    try:
        result = lookup_site(addr)
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)

        # Fallback: show market preset for Perris
        print("\nFalling back to market preset for Perris, CA:")
        fallback = lookup_market("Perris")
        print(json.dumps(fallback, indent=2))
