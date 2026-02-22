"""
Fire Code, High-Pile Storage, and Permitting Requirements Engine
for Prologis Racking BOM Tool.

Determines permit requirements, fire protection specs, and code compliance
based on building location, rack configuration, and commodity type.

References:
- IBC 2021 Chapter 32 (High-Piled Combustible Storage)
- NFPA 13 (Sprinkler Systems)
- IFC 2021 Chapter 32
- 2022 California Fire Code
- FM Global Data Sheet 8-9 (Storage of Class I-IV Commodities)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─── Commodity Classifications (IBC/NFPA) ─────────────────────────

class CommodityClass(str, Enum):
    """
    NFPA 13 / IBC Commodity Classification
    Determines sprinkler requirements and storage height limits.
    """
    CLASS_I = "I"      # Noncombustible on wood pallets (metals, glass)
    CLASS_II = "II"    # Class I in corrugated cartons (canned goods)
    CLASS_III = "III"  # Wood, paper, natural fibers, Group C plastics
    CLASS_IV = "IV"    # Class I-III with Group A plastics (≤5%)
    HIGH_HAZARD = "HH" # Group A plastics >5%, flammable liquids, aerosols
    
    @property
    def description(self):
        return {
            "I": "Noncombustible products on wood pallets",
            "II": "Class I products in corrugated cartons",
            "III": "Wood, paper, natural fibers, Group C plastics",
            "IV": "Class I-III with Group A plastics (≤5% by weight)",
            "HH": "Group A expanded plastics, flammable liquids, aerosols",
        }[self.value]

    @property
    def high_pile_threshold_ft(self):
        """Height above which high-pile permit is required"""
        # IFC 2021 Table 3206.2 — thresholds trigger high-pile storage requirements
        # For most commodities, 12ft triggers high-pile designation
        # This is STORAGE height (top of highest pallet), not rack height
        return {
            "I": 12,
            "II": 12,
            "III": 12,
            "IV": 12,
            "HH": 6,  # High-hazard: much lower threshold
        }[self.value]


# ─── Sprinkler Systems ─────────────────────────────────────────────

class SprinklerType(str, Enum):
    """Types of sprinkler systems for high-pile storage"""
    ESFR = "ESFR"              # Early Suppression Fast Response — ceiling only
    CMSA = "CMSA"              # Control Mode Specific Application
    IN_RACK = "in_rack"        # In-rack sprinklers (within rack structure)
    ESFR_PLUS_INRACK = "ESFR+IR"  # Both ceiling ESFR + in-rack


@dataclass
class SprinklerSpec:
    """Sprinkler system specification"""
    system_type: SprinklerType
    ceiling_k_factor: float = 0      # K-factor for ceiling sprinklers
    ceiling_temp_rating: int = 0     # Temperature rating (°F)
    ceiling_pressure_psi: float = 0  # Required pressure
    in_rack_levels: list = field(default_factory=list)  # Heights for in-rack heads
    in_rack_k_factor: float = 0
    notes: str = ""


# ─── High-Pile Storage Requirements ───────────────────────────────

@dataclass
class HighPileRequirements:
    """Requirements that trigger when storage exceeds high-pile threshold"""
    is_high_pile: bool
    storage_height_ft: float
    commodity_class: CommodityClass
    threshold_ft: float
    
    # Permit requirements
    operational_permit_required: bool = False
    fire_protection_plan_required: bool = False
    high_pile_permit_required: bool = False
    
    # Fire protection
    sprinkler_spec: Optional[SprinklerSpec] = None
    fire_department_access_aisle_required: bool = False
    fire_department_access_aisle_width_ft: float = 0
    max_pile_volume_cuft: int = 0
    
    # Flue spaces (NFPA 13)
    transverse_flue_in: float = 3    # Between pallets across beam (side-to-side)
    longitudinal_flue_in: float = 6   # Between rows (front-to-back through rack)
    
    # Aisles
    min_aisle_width_ft: float = 0
    max_storage_area_sqft: int = 0
    
    # Baffles
    fire_baffles_required: bool = False
    baffle_spacing_bays: int = 0
    
    notes: list = field(default_factory=list)


def assess_high_pile(
    storage_height_ft: float,
    commodity_class: CommodityClass,
    storage_area_sqft: float,
    building_sprinklered: bool = True,
    jurisdiction: str = "IBC"  # "IBC" or "CBC"
) -> HighPileRequirements:
    """
    Assess high-pile combustible storage requirements.
    
    Args:
        storage_height_ft: Height of storage (top of highest pallet, NOT rack height)
        commodity_class: NFPA commodity classification
        storage_area_sqft: Total high-pile storage area in square feet
        building_sprinklered: Whether building has sprinklers
        jurisdiction: "IBC" for International Building Code, "CBC" for California
    
    Returns:
        HighPileRequirements with all applicable requirements
    """
    threshold = commodity_class.high_pile_threshold_ft
    is_high_pile = storage_height_ft > threshold
    
    req = HighPileRequirements(
        is_high_pile=is_high_pile,
        storage_height_ft=storage_height_ft,
        commodity_class=commodity_class,
        threshold_ft=threshold,
    )
    
    if not is_high_pile:
        req.notes.append(f"Storage height {storage_height_ft}ft below {threshold}ft threshold — not high-pile")
        return req
    
    # ── High-pile storage IS triggered ──
    req.high_pile_permit_required = True
    req.operational_permit_required = True
    req.fire_protection_plan_required = True
    
    # IFC 2021 / CBC Table 3206.2 — area thresholds for permits
    # High-pile permit always required when exceeding height threshold
    # Operational permit thresholds vary by commodity
    permit_area_thresholds = {
        CommodityClass.CLASS_I: 500,    # sqft
        CommodityClass.CLASS_II: 500,
        CommodityClass.CLASS_III: 500,
        CommodityClass.CLASS_IV: 500,
        CommodityClass.HIGH_HAZARD: 200,  # Lower for high-hazard
    }
    
    if storage_area_sqft > permit_area_thresholds.get(commodity_class, 500):
        req.notes.append("Exceeds area threshold — full high-pile storage plan required")
    
    # ── Flue space requirements (NFPA 13 / FM Global) ──
    if storage_height_ft <= 20:
        req.transverse_flue_in = 3
        req.longitudinal_flue_in = 3 if commodity_class in [CommodityClass.CLASS_I, CommodityClass.CLASS_II] else 6
    else:
        req.transverse_flue_in = 3
        req.longitudinal_flue_in = 6  # 6" always for >20ft storage
    
    # ── Sprinkler requirements ──
    if building_sprinklered:
        if storage_height_ft <= 25 and commodity_class in [CommodityClass.CLASS_I, CommodityClass.CLASS_II, CommodityClass.CLASS_III]:
            # ESFR can handle up to ~25ft for Class I-III
            req.sprinkler_spec = SprinklerSpec(
                system_type=SprinklerType.ESFR,
                ceiling_k_factor=25.2,
                ceiling_temp_rating=165,
                ceiling_pressure_psi=25,
                notes="ESFR ceiling-only, K25.2 — verify with fire protection engineer"
            )
        elif storage_height_ft <= 30:
            # 25-30ft: may need ESFR K28+ or CMSA + in-rack
            if commodity_class in [CommodityClass.CLASS_I, CommodityClass.CLASS_II]:
                req.sprinkler_spec = SprinklerSpec(
                    system_type=SprinklerType.ESFR,
                    ceiling_k_factor=28.0,
                    ceiling_temp_rating=165,
                    ceiling_pressure_psi=40,
                    notes="ESFR K28 ceiling-only — verify with FPE"
                )
            else:
                req.sprinkler_spec = SprinklerSpec(
                    system_type=SprinklerType.ESFR_PLUS_INRACK,
                    ceiling_k_factor=25.2,
                    ceiling_temp_rating=165,
                    ceiling_pressure_psi=25,
                    in_rack_levels=[10],  # In-rack at ~10ft
                    in_rack_k_factor=8.0,
                    notes="ESFR + in-rack required for Class III/IV at this height"
                )
        else:
            # >30ft: almost always needs in-rack sprinklers
            req.sprinkler_spec = SprinklerSpec(
                system_type=SprinklerType.ESFR_PLUS_INRACK,
                ceiling_k_factor=25.2,
                ceiling_temp_rating=165,
                ceiling_pressure_psi=25,
                in_rack_levels=[10, 20],
                in_rack_k_factor=8.0,
                notes="In-rack sprinklers required — consult fire protection engineer"
            )
    
    # ── Fire department access ──
    # IFC 3206.9 — requires access aisles for fire department
    if storage_area_sqft > 12000:
        req.fire_department_access_aisle_required = True
        req.fire_department_access_aisle_width_ft = 8  # Minimum 8ft clear
        req.notes.append("Fire department access aisles required (>12,000 sqft)")
    
    # ── Maximum pile/area limits ──
    if commodity_class == CommodityClass.HIGH_HAZARD:
        req.max_storage_area_sqft = 2500 if building_sprinklered else 500
    else:
        req.max_storage_area_sqft = 0  # No limit with sprinklers for Class I-IV
    
    # ── Minimum aisle widths (fire code) ──
    req.min_aisle_width_ft = 8 if storage_height_ft > 20 else 4
    
    # ── Fire baffles ──
    # Required in some jurisdictions for rack >15ft with certain commodities
    if storage_height_ft > 15 and commodity_class in [CommodityClass.CLASS_III, CommodityClass.CLASS_IV, CommodityClass.HIGH_HAZARD]:
        req.fire_baffles_required = True
        req.baffle_spacing_bays = 10
        req.notes.append("Fire baffles may be required — verify with AHJ")
    
    # ── California-specific ──
    if jurisdiction == "CBC":
        req.notes.append("California: CBC 2022 Chapter 32 applies — stricter than IBC in some areas")
        req.notes.append("California: State Fire Marshal may require additional review")
        if storage_height_ft > 12:
            req.notes.append("California: High-pile storage permit required from local fire authority")
    
    return req


# ─── Permitting Requirements ──────────────────────────────────────

@dataclass
class PermitRequirements:
    """All permits/approvals needed for a racking installation"""
    # Building permits
    building_permit_required: bool = True  # Almost always yes
    structural_engineering_required: bool = False
    building_department_plans: bool = True
    
    # Fire permits
    fire_permit_required: bool = False
    high_pile_storage_permit: bool = False
    fire_protection_plan: bool = False
    sprinkler_modification_permit: bool = False
    
    # Engineering
    prelim_engineering_required: bool = False
    seismic_analysis_required: bool = False
    slab_analysis_required: bool = False
    
    # Inspections
    anchor_inspection_required: bool = False
    final_inspection_required: bool = True
    
    # Estimated timeline
    typical_permit_weeks: int = 2
    
    notes: list = field(default_factory=list)


def assess_permits(
    sdc: str,
    storage_height_ft: float,
    commodity_class: CommodityClass,
    storage_area_sqft: float,
    rack_style: str = "teardrop",
    jurisdiction: str = "IBC",
    sprinkler_modification: bool = False,
) -> PermitRequirements:
    """
    Determine all permits and approvals required.
    
    Args:
        sdc: Seismic Design Category (A through F)
        storage_height_ft: Height of stored goods
        commodity_class: NFPA commodity class
        storage_area_sqft: Storage footprint
        rack_style: "teardrop" or "structural"
        jurisdiction: "IBC" or "CBC"
        sprinkler_modification: Whether sprinklers need modification
    """
    p = PermitRequirements()
    
    # Building permits — almost always required for rack installation
    p.building_permit_required = True
    p.building_department_plans = True
    p.notes.append("Rack layout drawings required for building department")
    
    # Seismic engineering
    if sdc in ("C", "D", "E", "F"):
        p.structural_engineering_required = True
        p.prelim_engineering_required = True
        p.seismic_analysis_required = True
        p.anchor_inspection_required = True
        p.notes.append(f"SDC {sdc}: Structural/seismic engineering required per IBC 2209")
        p.notes.append("Prelim engineering from rack manufacturer or 3rd party (OneRack, Seizmic Inc)")
        if sdc in ("D", "E", "F"):
            p.notes.append("Special inspection of anchors required")
            p.typical_permit_weeks = 4  # Longer for high-seismic
    elif sdc in ("A", "B"):
        p.notes.append(f"SDC {sdc}: Standard installation, no special seismic analysis needed")
        p.typical_permit_weeks = 2
    
    # High-pile storage
    hp = assess_high_pile(storage_height_ft, commodity_class, storage_area_sqft, 
                          jurisdiction=jurisdiction)
    if hp.is_high_pile:
        p.fire_permit_required = True
        p.high_pile_storage_permit = True
        p.fire_protection_plan = True
        p.notes.append("High-pile storage permit required from fire authority")
        p.notes.append("Commodity classification and storage arrangement must be documented")
    
    # Sprinkler modifications
    if sprinkler_modification:
        p.sprinkler_modification_permit = True
        p.notes.append("Sprinkler modification permit required — fire protection engineer review")
        p.typical_permit_weeks = max(p.typical_permit_weeks, 4)
    
    # Slab analysis
    # Rule of thumb: racks >20ft or heavy loads need slab verification
    if storage_height_ft > 20 or sdc in ("D", "E", "F"):
        p.slab_analysis_required = True
        p.notes.append("Slab/floor analysis recommended — verify load capacity for anchors")
    
    # California-specific
    if jurisdiction == "CBC":
        p.typical_permit_weeks = max(p.typical_permit_weeks, 4)
        p.notes.append("California: Plan check typically 2-4 weeks")
        p.notes.append("California: State Fire Marshal review may be required for large installations")
        if storage_area_sqft > 50000:
            p.notes.append("California: Large installation — expect 4-6 week permit process")
            p.typical_permit_weeks = 6
    
    return p


# ─── Clearance Requirements ───────────────────────────────────────

def sprinkler_clearance_requirements(
    sprinkler_type: str = "ESFR",
    storage_height_ft: float = 25,
) -> dict:
    """
    Returns required clearance between top of storage and sprinkler deflectors.
    
    NFPA 13 requirements:
    - Minimum 18" clearance from top of storage to sprinkler deflectors
    - ESFR: 36" recommended for optimal spray pattern
    - In-rack: varies by design
    
    This determines usable rack height from clear height.
    """
    if sprinkler_type == "ESFR":
        # ESFR requires more clearance for spray pattern
        min_clearance_in = 36  # 3 feet
        recommended_clearance_in = 36
    else:
        min_clearance_in = 18  # NFPA 13 minimum
        recommended_clearance_in = 24  # Recommended
    
    # Top of load clearance from ceiling/roof deck
    # Clear height is to sprinkler deflectors or lowest obstruction
    return {
        "min_clearance_in": min_clearance_in,
        "recommended_clearance_in": recommended_clearance_in,
        "max_storage_height_in": int(storage_height_ft * 12) - recommended_clearance_in,
        "notes": [
            f"Minimum {min_clearance_in}\" clearance to sprinkler deflectors (NFPA 13)",
            f"Recommended {recommended_clearance_in}\" for optimal spray pattern",
            "Top of load (including pallet overhang) must not exceed max storage height",
        ]
    }


# ─── Used vs New Rack ─────────────────────────────────────────────

@dataclass
class UsedRackAssessment:
    """Assessment of used vs new rack considerations"""
    recommended: str  # "new" or "used" or "either"
    cost_savings_pct: float  # Estimated savings for used
    lead_time_weeks_new: int
    lead_time_weeks_used: int
    
    # Risks/limitations of used
    risks: list = field(default_factory=list)
    requirements: list = field(default_factory=list)
    
    notes: list = field(default_factory=list)


def assess_used_vs_new(
    sdc: str,
    frame_height_ft: float,
    total_frames: int,
    rack_style: str = "teardrop",
    commodity_class: CommodityClass = CommodityClass.CLASS_II,
) -> UsedRackAssessment:
    """
    Assess whether used or new rack is appropriate.
    
    Key factors:
    - Seismic zone: Used rack in SDC D+ is risky (may not meet current code)
    - Availability: Used rack is commodity-dependent on market conditions
    - Structural: Must be inspected for damage, corrosion, weld integrity
    - Teardrop: More interchangeable between manufacturers than structural
    """
    
    assessment = UsedRackAssessment(
        recommended="either",
        cost_savings_pct=30,  # Typical 25-40% savings
        lead_time_weeks_new=8,  # 6-10 weeks for new
        lead_time_weeks_used=2,  # 1-3 weeks for used
    )
    
    # Seismic considerations
    if sdc in ("D", "E", "F"):
        assessment.recommended = "new"
        assessment.cost_savings_pct = 0  # Not recommended
        assessment.risks.append("Used rack may not meet current seismic code requirements")
        assessment.risks.append("Engineering certification for used rack in high-seismic zones is costly")
        assessment.risks.append("Base plates and anchors must be verified for current SDC requirements")
        assessment.requirements.append("If using used rack in SDC D+: PE certification required")
        assessment.requirements.append("All frames must be inspected for damage before installation")
        assessment.notes.append(f"SDC {sdc}: Strongly recommend new rack — used rack certification is expensive")
    elif sdc == "C":
        assessment.recommended = "either"
        assessment.risks.append("Used rack in SDC C: engineering review required")
        assessment.requirements.append("Inspect all frames for teardrop slot damage, bent columns, weld cracks")
        assessment.notes.append("SDC C: Used rack viable but needs engineering review")
    else:
        assessment.recommended = "either"
        assessment.notes.append(f"SDC {sdc}: Used rack is a viable, cost-effective option")
    
    # Rack style considerations
    if rack_style == "structural":
        assessment.cost_savings_pct *= 0.8  # Less savings for structural (more variable)
        assessment.risks.append("Structural rack: bolt patterns vary by manufacturer — mixing is difficult")
        assessment.requirements.append("Structural: Must match manufacturer for beam-to-column connections")
    else:
        assessment.notes.append("Teardrop rack: Most manufacturers use compatible teardrop pattern")
        assessment.notes.append("Teardrop: Mixing brands is generally OK for frames + beams")
    
    # Size/scale
    if total_frames > 500:
        assessment.risks.append(f"Large order ({total_frames} frames): may be hard to source matching used inventory")
        assessment.notes.append("Large projects: consider mix of new + used to balance cost and availability")
    
    # Used rack requirements (always)
    assessment.requirements.extend([
        "Visual inspection of all components before acceptance",
        "Check for: bent columns, cracked welds, damaged teardrop slots, corrosion, straightness",
        "Verify load capacity ratings match design requirements",
        "Verify frame height and depth match specifications",
        "Base plates must not be bent, cracked, or have weld defects",
        "Wire decks: check for bent/broken wires, proper flange condition",
    ])
    
    # Cost estimate refinement
    if frame_height_ft > 20:
        assessment.lead_time_weeks_used = 3  # Tall frames harder to source used
        assessment.notes.append("Tall frames (>20ft): less common in used market, longer lead time")
    
    return assessment


# ─── Code Jurisdiction Lookup ─────────────────────────────────────

def determine_jurisdiction(state: str, county: str = "") -> dict:
    """
    Determine which building code applies.
    
    Most US jurisdictions use IBC (International Building Code).
    California uses CBC (California Building Code) which is IBC + amendments.
    
    Returns: {code, edition, fire_code, notes}
    """
    state = state.upper().strip()
    
    if state in ("CA", "CALIFORNIA"):
        return {
            "building_code": "CBC",
            "edition": "2022",
            "fire_code": "CFC 2022",
            "seismic_reference": "2022 CBC Section 2209",
            "notes": [
                "California Building Code (CBC) 2022 applies",
                "Based on 2021 IBC with California amendments",
                "California Fire Code (CFC) 2022 for fire protection",
                "State Fire Marshal jurisdiction for some occupancies",
                "All rack installations require building permit",
            ]
        }
    else:
        return {
            "building_code": "IBC",
            "edition": "2021",
            "fire_code": "IFC 2021",
            "seismic_reference": "2021 IBC Section 2209 / ASCE 7-22",
            "notes": [
                f"International Building Code (IBC) 2021 applies in {state}",
                "Local amendments may apply — check with building department",
                "International Fire Code (IFC) 2021 for fire protection",
                "Verify local adoption year — some jurisdictions lag by 1-2 code cycles",
            ]
        }


# ─── Complete Site Assessment ─────────────────────────────────────

def full_site_assessment(
    sdc: str,
    state: str,
    storage_height_ft: float,
    storage_area_sqft: float,
    commodity_class: CommodityClass = CommodityClass.CLASS_II,
    rack_style: str = "teardrop",
    total_frames: int = 100,
    sprinkler_type: str = "ESFR",
) -> dict:
    """
    Complete site assessment combining all checks.
    
    Returns everything needed for the project: permits, fire code, used/new, clearances.
    """
    import dataclasses
    
    def _to_dict(obj):
        """Recursively convert dataclasses to dicts"""
        if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
            return {k: _to_dict(v) for k, v in dataclasses.asdict(obj).items()}
        elif isinstance(obj, list):
            return [_to_dict(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: _to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, Enum):
            return obj.value
        return obj
    
    jurisdiction_code = "CBC" if state.upper() in ("CA", "CALIFORNIA") else "IBC"
    
    return {
        "jurisdiction": determine_jurisdiction(state),
        "high_pile": _to_dict(assess_high_pile(
            storage_height_ft, commodity_class, storage_area_sqft,
            jurisdiction=jurisdiction_code
        )),
        "permits": _to_dict(assess_permits(
            sdc, storage_height_ft, commodity_class, storage_area_sqft,
            rack_style, jurisdiction_code
        )),
        "used_vs_new": _to_dict(assess_used_vs_new(
            sdc, storage_height_ft / 12 * 12,  # rough frame height
            total_frames, rack_style, commodity_class
        )),
        "clearances": sprinkler_clearance_requirements(sprinkler_type, storage_height_ft),
    }


# ─── FastAPI Route Integration ────────────────────────────────────

def register_routes(app):
    """Register fire code / permitting routes with FastAPI app"""
    from fastapi import Query
    
    @app.get("/api/fire-assessment")
    async def fire_assessment(
        storage_height_ft: float = Query(..., description="Height of stored goods in feet"),
        commodity_class: str = Query("II", description="NFPA commodity class: I, II, III, IV, HH"),
        storage_area_sqft: float = Query(10000, description="Storage area in sqft"),
        sdc: str = Query("B", description="Seismic Design Category"),
        state: str = Query("IL", description="State code"),
        rack_style: str = Query("teardrop"),
        total_frames: int = Query(100),
    ):
        cc = CommodityClass(commodity_class)
        return full_site_assessment(
            sdc=sdc,
            state=state,
            storage_height_ft=storage_height_ft,
            storage_area_sqft=storage_area_sqft,
            commodity_class=cc,
            rack_style=rack_style,
            total_frames=total_frames,
        )


# ─── Demo ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    
    print("=" * 60)
    print("FIRE CODE & PERMITTING ASSESSMENT")
    print("=" * 60)
    
    # Scenario 1: Spirit Halloween — Perris, CA (SDC D)
    print("\n--- Spirit Halloween (Perris, CA — SDC D) ---")
    result = full_site_assessment(
        sdc="D",
        state="CA",
        storage_height_ft=28,
        storage_area_sqft=200000,
        commodity_class=CommodityClass.CLASS_III,
        rack_style="teardrop",
        total_frames=400,
    )
    print(json.dumps(result, indent=2, default=str))
    
    # Scenario 2: Chicago warehouse (SDC A)
    print("\n--- Chicago Warehouse (SDC A) ---")
    result = full_site_assessment(
        sdc="A",
        state="IL",
        storage_height_ft=25,
        storage_area_sqft=150000,
        commodity_class=CommodityClass.CLASS_II,
        rack_style="teardrop",
        total_frames=600,
    )
    print(json.dumps(result, indent=2, default=str))
