"""
Prologis Market Database

Pre-computed data for major Prologis logistics markets in the US.
Includes typical building specs, seismic zones, code jurisdictions,
and common rack configurations.

Source: Prologis portfolio data, USGS seismic maps, local building codes.
"""

# Each market has multiple sub-markets with representative addresses
# SDC values are TYPICAL — actual values depend on exact address

PROLOGIS_MARKETS = {
    # ─── WEST COAST (HIGH SEISMIC) ──────────────────────────────
    "inland_empire": {
        "name": "Inland Empire / SoCal",
        "state": "CA",
        "building_code": "CBC",
        "fire_code": "CFC 2022",
        "typical_sdc": "D",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Highest seismic risk in Prologis portfolio",
            "8 anchors/frame standard (4 per base plate)",
            "Hilti Kwik Bolt TZ2 or equivalent required",
            "Prelim engineering always required",
            "CBC 2022 Section 2209 governs rack design",
            "High-pile storage permits required from local fire authority",
            "Largest US logistics market by square footage",
        ],
        "sub_markets": {
            "ontario": {"lat": 34.0633, "lon": -117.6509, "typical_clear_ft": 36},
            "rancho_cucamonga": {"lat": 34.1064, "lon": -117.5931, "typical_clear_ft": 32},
            "perris": {"lat": 33.7825, "lon": -117.2286, "typical_clear_ft": 36},
            "moreno_valley": {"lat": 33.9425, "lon": -117.2297, "typical_clear_ft": 36},
            "redlands": {"lat": 34.0556, "lon": -117.1825, "typical_clear_ft": 32},
            "fontana": {"lat": 34.0922, "lon": -117.4350, "typical_clear_ft": 36},
            "bloomington": {"lat": 34.0697, "lon": -117.3953, "typical_clear_ft": 32},
            "riverside": {"lat": 33.9533, "lon": -117.3962, "typical_clear_ft": 32},
        },
    },
    
    "los_angeles": {
        "name": "Los Angeles / South Bay",
        "state": "CA",
        "building_code": "CBC",
        "fire_code": "CFC 2022",
        "typical_sdc": "D",
        "typical_clear_height_ft": [28, 32],
        "common_rack_configs": ["teardrop_42"],
        "notes": [
            "Older building stock, lower clear heights than IE",
            "Seismic requirements same as Inland Empire",
            "Port-proximate logistics (LA/Long Beach ports)",
            "Land-constrained — density premium",
        ],
        "sub_markets": {
            "compton": {"lat": 33.8959, "lon": -118.2201, "typical_clear_ft": 28},
            "carson": {"lat": 33.8317, "lon": -118.2612, "typical_clear_ft": 30},
            "city_of_industry": {"lat": 34.0195, "lon": -117.9587, "typical_clear_ft": 32},
        },
    },
    
    "seattle_tacoma": {
        "name": "Seattle / Tacoma",
        "state": "WA",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "D",
        "typical_clear_height_ft": [28, 32],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "High seismic — similar requirements to California",
            "Washington State Building Code (based on IBC)",
            "Cascadia subduction zone risk",
            "Port of Seattle/Tacoma logistics hub",
        ],
        "sub_markets": {
            "kent": {"lat": 47.3809, "lon": -122.2348, "typical_clear_ft": 32},
            "sumner": {"lat": 47.2037, "lon": -122.2401, "typical_clear_ft": 32},
            "tacoma": {"lat": 47.2529, "lon": -122.4443, "typical_clear_ft": 30},
            "auburn": {"lat": 47.3073, "lon": -122.2285, "typical_clear_ft": 32},
        },
    },
    
    "bay_area": {
        "name": "San Francisco Bay Area",
        "state": "CA",
        "building_code": "CBC",
        "fire_code": "CFC 2022",
        "typical_sdc": "D-E",
        "typical_clear_height_ft": [28, 32],
        "common_rack_configs": ["teardrop_42"],
        "notes": [
            "Very high seismic (San Andreas fault proximity)",
            "Some locations SDC E near fault traces",
            "Land-constrained, expensive",
            "Smaller buildings than IE",
        ],
        "sub_markets": {
            "tracy": {"lat": 37.7397, "lon": -121.4252, "typical_clear_ft": 32},
            "stockton": {"lat": 37.9577, "lon": -121.2908, "typical_clear_ft": 32},
            "fremont": {"lat": 37.5485, "lon": -121.9886, "typical_clear_ft": 28},
        },
    },
    
    # ─── CENTRAL US (LOW SEISMIC) ───────────────────────────────
    "chicago": {
        "name": "Chicago / Chicagoland",
        "state": "IL",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "A-B",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Low seismic — standard anchors (2/frame)",
            "Massive logistics hub — I-80/I-55/I-94 corridor",
            "Very large buildings (500K-1M+ sqft common)",
            "Cold climate — insulated buildings",
            "2/frame anchors, no special seismic engineering needed",
        ],
        "sub_markets": {
            "joliet": {"lat": 41.5250, "lon": -88.0817, "typical_clear_ft": 36},
            "romeoville": {"lat": 41.6475, "lon": -88.0898, "typical_clear_ft": 36},
            "elwood": {"lat": 41.4042, "lon": -88.1112, "typical_clear_ft": 36},
            "plainfield": {"lat": 41.6270, "lon": -88.2037, "typical_clear_ft": 36},
            "bolingbrook": {"lat": 41.6986, "lon": -88.0684, "typical_clear_ft": 32},
            "aurora": {"lat": 41.7606, "lon": -88.3201, "typical_clear_ft": 32},
        },
    },
    
    "dallas_dfw": {
        "name": "Dallas / Fort Worth",
        "state": "TX",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "A-B",
        "typical_clear_height_ft": [32, 36, 40],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Low seismic — standard anchors",
            "Very tall clear heights (36-40ft in new construction)",
            "Alliance area is major e-commerce hub",
            "Fast permitting compared to CA",
            "No state income tax — tenant-friendly",
        ],
        "sub_markets": {
            "alliance": {"lat": 32.9872, "lon": -97.3161, "typical_clear_ft": 40},
            "lancaster": {"lat": 32.5921, "lon": -96.7561, "typical_clear_ft": 36},
            "desoto": {"lat": 32.5899, "lon": -96.8570, "typical_clear_ft": 36},
            "wilmer": {"lat": 32.5891, "lon": -96.6853, "typical_clear_ft": 36},
            "forney": {"lat": 32.7482, "lon": -96.4719, "typical_clear_ft": 36},
        },
    },
    
    "indianapolis": {
        "name": "Indianapolis",
        "state": "IN",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "A-B",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Low seismic — crossroads of America (I-70/I-65)",
            "Major e-commerce distribution hub",
            "Fast permitting",
        ],
        "sub_markets": {
            "plainfield_in": {"lat": 39.7042, "lon": -86.3994, "typical_clear_ft": 36},
            "whitestown": {"lat": 39.9981, "lon": -86.3458, "typical_clear_ft": 36},
            "greenwood": {"lat": 39.6136, "lon": -86.1067, "typical_clear_ft": 32},
        },
    },
    
    "columbus_oh": {
        "name": "Columbus, OH",
        "state": "OH",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "A",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Very low seismic",
            "Central Ohio logistics corridor",
            "Growing e-commerce hub",
        ],
        "sub_markets": {
            "west_jefferson": {"lat": 39.9445, "lon": -83.2686, "typical_clear_ft": 36},
            "etna": {"lat": 39.9578, "lon": -82.6816, "typical_clear_ft": 36},
        },
    },
    
    "houston": {
        "name": "Houston",
        "state": "TX",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "A",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Lowest seismic risk in US",
            "Port of Houston logistics",
            "Flood zone considerations (not seismic)",
            "Hurricane risk — wind loads more relevant than seismic",
            "No state income tax",
        ],
        "sub_markets": {
            "baytown": {"lat": 29.7355, "lon": -94.9774, "typical_clear_ft": 36},
            "katy": {"lat": 29.7858, "lon": -95.8244, "typical_clear_ft": 36},
            "missouri_city": {"lat": 29.6186, "lon": -95.5377, "typical_clear_ft": 32},
        },
    },
    
    # ─── EAST COAST ─────────────────────────────────────────────
    "new_jersey_pa": {
        "name": "New Jersey / Pennsylvania",
        "state": "NJ/PA",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "A-B",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Low seismic, standard anchors",
            "Port Newark/Elizabeth logistics (East Coast gateway)",
            "NJ Turnpike/I-95 corridor",
            "Higher construction costs than Midwest",
            "Some NJ-specific fire code requirements",
            "PA (Lehigh Valley, Carlisle): fast-growing submarket",
        ],
        "sub_markets": {
            "edison_nj": {"lat": 40.5187, "lon": -74.4121, "typical_clear_ft": 36},
            "cranbury_nj": {"lat": 40.3162, "lon": -74.5135, "typical_clear_ft": 36},
            "carteret_nj": {"lat": 40.5773, "lon": -74.2318, "typical_clear_ft": 32},
            "carlisle_pa": {"lat": 40.2015, "lon": -77.1891, "typical_clear_ft": 36},
            "lehigh_valley_pa": {"lat": 40.6023, "lon": -75.4714, "typical_clear_ft": 36},
        },
    },
    
    "atlanta": {
        "name": "Atlanta",
        "state": "GA",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "A-B",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Low seismic — standard installation",
            "Major Southeast distribution hub",
            "I-85/I-75/I-20 interchange",
            "Fast permitting (Georgia)",
        ],
        "sub_markets": {
            "mcdonough": {"lat": 33.4473, "lon": -84.1469, "typical_clear_ft": 36},
            "jackson": {"lat": 33.2946, "lon": -83.9660, "typical_clear_ft": 36},
            "forest_park": {"lat": 33.6221, "lon": -84.3688, "typical_clear_ft": 32},
        },
    },
    
    # ─── MODERATE SEISMIC ───────────────────────────────────────
    "memphis": {
        "name": "Memphis, TN",
        "state": "TN",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "C-D",
        "typical_clear_height_ft": [28, 32],
        "common_rack_configs": ["teardrop_42"],
        "notes": [
            "MODERATE seismic — New Madrid fault zone",
            "SDC varies C to D depending on exact location",
            "May require seismic engineering (SDC C+ needs review)",
            "FedEx hub — major logistics market",
            "Anchors: 4/frame typical (2 per base plate)",
        ],
        "sub_markets": {
            "memphis": {"lat": 35.1495, "lon": -90.0490, "typical_clear_ft": 32},
            "olive_branch_ms": {"lat": 34.9618, "lon": -89.8295, "typical_clear_ft": 32},
        },
    },
    
    "phoenix": {
        "name": "Phoenix, AZ",
        "state": "AZ",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "B",
        "typical_clear_height_ft": [32, 36],
        "common_rack_configs": ["teardrop_42", "teardrop_48"],
        "notes": [
            "Low seismic — standard installation",
            "Growing logistics market (nearshoring from Mexico)",
            "Hot climate — HVAC considerations",
            "Fast permitting (Arizona)",
        ],
        "sub_markets": {
            "goodyear": {"lat": 33.4353, "lon": -112.3958, "typical_clear_ft": 36},
            "glendale": {"lat": 33.5387, "lon": -112.1860, "typical_clear_ft": 36},
            "surprise": {"lat": 33.6292, "lon": -112.3680, "typical_clear_ft": 36},
        },
    },
    
    "denver": {
        "name": "Denver / Front Range",
        "state": "CO",
        "building_code": "IBC",
        "fire_code": "IFC 2021",
        "typical_sdc": "B",
        "typical_clear_height_ft": [28, 32],
        "common_rack_configs": ["teardrop_42"],
        "notes": [
            "Low seismic — standard installation",
            "Growing market, I-25/I-70 corridor",
            "Altitude considerations (minimal for racking)",
            "Ellis's home market",
        ],
        "sub_markets": {
            "aurora": {"lat": 39.7294, "lon": -104.8319, "typical_clear_ft": 32},
            "henderson": {"lat": 39.9272, "lon": -104.8658, "typical_clear_ft": 32},
            "commerce_city": {"lat": 39.8083, "lon": -104.9339, "typical_clear_ft": 32},
        },
    },
}


def get_market_by_state(state: str) -> list:
    """Get all markets in a given state"""
    state = state.upper().strip()
    results = []
    for key, market in PROLOGIS_MARKETS.items():
        if state in market["state"].upper():
            results.append(market)
    return results


def get_nearest_market(lat: float, lon: float) -> dict:
    """Find the nearest Prologis market to given coordinates"""
    import math
    
    best_dist = float('inf')
    best_market = None
    best_submarket = None
    
    for key, market in PROLOGIS_MARKETS.items():
        for sm_key, sm in market.get("sub_markets", {}).items():
            dist = math.sqrt((lat - sm["lat"])**2 + (lon - sm["lon"])**2)
            if dist < best_dist:
                best_dist = dist
                best_market = market
                best_submarket = sm_key
    
    return {
        "market": best_market,
        "sub_market": best_submarket,
        "distance_deg": best_dist,
    }


def list_all_markets() -> list:
    """Return summary of all markets"""
    return [
        {
            "key": key,
            "name": m["name"],
            "state": m["state"],
            "typical_sdc": m["typical_sdc"],
            "typical_clear_height_ft": m["typical_clear_height_ft"],
            "building_code": m["building_code"],
        }
        for key, m in PROLOGIS_MARKETS.items()
    ]


if __name__ == "__main__":
    import json
    print("Prologis Markets:")
    for m in list_all_markets():
        print(f"  {m['name']:30s}  SDC: {m['typical_sdc']:5s}  Clear: {m['typical_clear_height_ft']}ft  Code: {m['building_code']}")
