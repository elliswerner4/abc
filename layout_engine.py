"""
Warehouse Racking Layout Design Engine
for Prologis Racking BOM Tool.

Takes warehouse building parameters and generates an optimal racking layout —
the same kind of layout a human rack engineer would design.

Output feeds directly into the BOM calculator and pricing model.
"""

import math
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ─── Constants ────────────────────────────────────────────

STANDARD_FRAME_HEIGHTS_IN = [96, 120, 144, 168, 192, 216, 240, 264, 288, 336]

AISLE_WIDTHS_IN = {
    "sitdown": 144,       # 12ft — sit-down counterbalanced
    "reach": 120,         # 10ft — reach truck (most common for selective)
    "narrow_aisle": 72,   # 6ft — turret/swing-reach
    "vna": 66,            # 5.5ft — very narrow aisle
}

FORKLIFT_NAMES = {
    "sitdown": "Sit-Down Counterbalanced",
    "reach": "Reach Truck",
    "narrow_aisle": "Narrow Aisle (Turret)",
    "vna": "Very Narrow Aisle",
}

# Frame width (depth of the upright column profile, not frame depth)
UPRIGHT_WIDTH_IN = {
    "teardrop": 3,
    "structural": 4,
}

# Standard first beam height (clears forklifts + allows floor-level pallet)
FIRST_BEAM_HEIGHT_IN = 88  # ~7'4"

# Standard level spacing for 48" tall pallets
# = pallet height (48") + beam depth (~4") + clearance (~6") ≈ 60"
LEVEL_SPACING_IN = 60

# Minimum clearance from back wall and side walls
WALL_CLEARANCE_FT = 4

# Minimum clearance from top of rack to sprinkler deflectors
SPRINKLER_CLEARANCE_IN = 36  # ESFR recommendation

# Flue space between back-to-back rows
FLUE_SPACE_IN = 6  # Standard 6"

# Cross-aisle default spacing (bays between tunnels)
DEFAULT_CROSS_AISLE_SPACING = 20


# ─── Data Classes ─────────────────────────────────────────

@dataclass
class BuildingSpec:
    length_ft: float           # Dock-to-back wall
    width_ft: float            # Side-to-side
    clear_height_ft: float     # To lowest obstruction
    dock_side: str = "south"   # Which wall has dock doors
    num_dock_doors: int = 10
    column_grid_x_ft: float = 0   # Column spacing along length (0 = no columns)
    column_grid_y_ft: float = 0   # Column spacing along width
    column_size_in: float = 24    # Column size (square)
    exclusions: list = field(default_factory=list)


@dataclass
class RackRequirements:
    target_pallet_positions: int = 0   # 0 = maximize
    pallet_size: str = "48x40"
    pallet_weight_lbs: int = 2500
    rack_type: str = "selective"
    rack_style: str = "teardrop"
    frame_depth_in: int = 42
    forklift_type: str = "reach"
    new_or_used: str = "new"
    min_staging_depth_ft: float = 50
    cross_aisle_spacing: int = 0       # 0 = auto
    max_beam_levels: int = 0           # 0 = auto


@dataclass
class RowSpec:
    row_id: int
    x_ft: float              # X position (distance from left wall)
    y_start_ft: float        # Y start (from dock wall)
    y_end_ft: float          # Y end
    bays: int
    direction: str = "north_south"
    is_back_to_back: bool = True
    pair_id: int = 0         # Which back-to-back pair
    side: str = "left"       # "left" or "right" of the pair


@dataclass
class CrossAisle:
    bay_position: int        # Which bay number the cross-aisle is at
    y_ft: float              # Y position
    width_ft: float = 12     # Cross-aisle width


@dataclass
class ColumnPosition:
    x_ft: float
    y_ft: float
    size_in: float
    conflicts_with_rack: bool = False
    protector_needed: bool = False


@dataclass
class BayTypeOutput:
    """Output format matching the BOM calculator input"""
    label: str
    bays: int
    end_frames: int
    tunnels: int
    beam_length: int
    beams_per_bay: int
    wiredecks_per_bay: int
    pallet_supports_per_bay: int
    tunnel_beam_length: int = 144
    tunnel_beams_per_bay: int = 4


@dataclass
class LayoutResult:
    # Summary
    total_pallet_positions: int = 0
    total_bays: int = 0
    total_rows: int = 0
    total_frames: int = 0
    utilization_pct: float = 0
    
    # Rack specs (calculated)
    frame_height_in: int = 0
    beam_levels: int = 0
    beam_length_in: int = 0
    aisle_width_in: int = 0
    pallets_per_bay: int = 2
    
    # Layout
    rows: list = field(default_factory=list)
    row_pairs: int = 0
    cross_aisles: list = field(default_factory=list)
    columns: list = field(default_factory=list)
    staging_area: dict = field(default_factory=dict)
    
    # For BOM generation
    bay_types: list = field(default_factory=list)
    end_frames: int = 0
    tunnel_bays: int = 0
    
    # Design notes
    notes: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


# ─── Helper Functions ─────────────────────────────────────

def best_frame_height(clear_height_in: float) -> int:
    """Find the largest standard frame height that fits under clear height with sprinkler clearance."""
    max_frame = clear_height_in - SPRINKLER_CLEARANCE_IN
    best = STANDARD_FRAME_HEIGHTS_IN[0]
    for h in STANDARD_FRAME_HEIGHTS_IN:
        if h <= max_frame:
            best = h
        else:
            break
    return best


def calc_beam_levels(frame_height_in: int, first_beam_in: int = FIRST_BEAM_HEIGHT_IN,
                     level_spacing_in: int = LEVEL_SPACING_IN) -> int:
    """Calculate maximum beam levels for a frame height."""
    if frame_height_in <= first_beam_in:
        return 1
    return int((frame_height_in - first_beam_in) / level_spacing_in) + 1


def beam_length_for_pallet(pallet_size: str, pallets_wide: int = 2) -> int:
    """
    Calculate beam length from pallet size.
    Standard: 2 pallets per bay, beam accommodates both + clearance.
    
    48x40 pallet → 2 × 48" + clearance = 96" beam (most common)
    48x48 pallet → 2 × 48" + clearance = 96" beam
    42x42 pallet → 2 × 42" + clearance = 96" beam (round up)
    """
    # Parse pallet size "WxD" — W is what faces the beam
    parts = pallet_size.lower().replace("x", " ").split()
    pallet_width = int(parts[0]) if parts else 48
    
    # 2 pallets + clearance → round to nearest standard beam
    # For 48x40 pallets: industry standard is 96" beam (fits 2 pallets with ~3" clearance each side)
    # The 48" is the pallet DEPTH, but pallets face the beam on their 40" side typically
    # Convention: beam_length = standardized for pallet configuration
    
    standard_beams = [48, 72, 84, 92, 96, 102, 108, 120, 144]
    
    # Standard mappings
    pallet_to_beam = {
        48: 96,    # 48x40: most common, 96" beam (industry standard)
        42: 96,    # 42x42: 96" beam
        40: 96,    # 40x48: 96" beam
    }
    
    if pallet_width in pallet_to_beam and pallets_wide == 2:
        return pallet_to_beam[pallet_width]
    
    # Fallback: calculate
    raw = pallet_width * pallets_wide + 6
    
    # Round up to standard beam lengths
    standard_beams = [48, 72, 84, 92, 96, 102, 108, 120, 144]
    for bl in standard_beams:
        if bl >= raw:
            return bl
    return 144


def tunnel_beam_length(standard_beam_in: int) -> int:
    """Tunnel beams are typically 1.5x standard (3 pallets wide) = 144"."""
    return 144  # Standard tunnel width


# ─── Main Design Function ─────────────────────────────────

def design_layout(building: dict, requirements: dict = None) -> dict:
    """
    Design a warehouse racking layout from building specs.
    
    Args:
        building: dict with keys from BuildingSpec
        requirements: dict with keys from RackRequirements
    
    Returns:
        dict matching LayoutResult structure, ready for BOM calculator
    """
    # Parse inputs
    b = BuildingSpec(**{k: v for k, v in building.items() if k in BuildingSpec.__dataclass_fields__})
    r = RackRequirements(**{k: v for k, v in (requirements or {}).items() if k in RackRequirements.__dataclass_fields__})
    
    result = LayoutResult()
    
    # ── Step 1: Calculate Rack Specs ──
    clear_height_in = b.clear_height_ft * 12
    result.frame_height_in = best_frame_height(clear_height_in)
    
    if r.max_beam_levels > 0:
        result.beam_levels = min(r.max_beam_levels, calc_beam_levels(result.frame_height_in))
    else:
        result.beam_levels = calc_beam_levels(result.frame_height_in)
    
    result.beam_length_in = beam_length_for_pallet(r.pallet_size)
    result.aisle_width_in = AISLE_WIDTHS_IN.get(r.forklift_type, 120)
    result.pallets_per_bay = 2  # Standard for selective
    
    upright_w = UPRIGHT_WIDTH_IN.get(r.rack_style, 3)
    
    result.notes.append(f"Frame height: {result.frame_height_in}\" ({result.frame_height_in/12:.0f}ft)")
    result.notes.append(f"Beam levels: {result.beam_levels}")
    result.notes.append(f"Beam length: {result.beam_length_in}\"")
    result.notes.append(f"Aisle width: {result.aisle_width_in}\" ({result.aisle_width_in/12:.1f}ft) — {FORKLIFT_NAMES.get(r.forklift_type, r.forklift_type)}")
    
    # ── Step 2: Calculate Row Module ──
    # Back-to-back pair width (inches):
    #   frame_depth + flue_space + frame_depth
    pair_width_in = r.frame_depth_in * 2 + FLUE_SPACE_IN
    
    # Row module = pair_width + aisle
    row_module_in = pair_width_in + result.aisle_width_in
    row_module_ft = row_module_in / 12
    
    result.notes.append(f"Row module: {row_module_in}\" ({row_module_ft:.1f}ft) = 2×{r.frame_depth_in}\" + {FLUE_SPACE_IN}\" flue + {result.aisle_width_in}\" aisle")
    
    # ── Step 3: Determine Layout Orientation ──
    # Rows run PERPENDICULAR to the dock wall
    # "length" = dock-to-back (rows run this direction)
    # "width" = side-to-side (rows are spaced across this)
    
    # Available depth for rack (dock-to-back minus staging)
    staging_depth_ft = r.min_staging_depth_ft
    available_depth_ft = b.length_ft - staging_depth_ft - WALL_CLEARANCE_FT
    
    # Available width for rows
    available_width_ft = b.width_ft - (WALL_CLEARANCE_FT * 2)
    available_width_in = available_width_ft * 12
    
    result.staging_area = {
        "depth_ft": staging_depth_ft,
        "width_ft": b.width_ft,
        "area_sqft": staging_depth_ft * b.width_ft,
    }
    
    # ── Step 4: Place Row Pairs ──
    # How many back-to-back pairs fit across the width?
    # First pair needs half-aisle on the left side
    # Each pair = pair_width + aisle (between pairs)
    # Last pair: consider a single row against back wall
    
    # Space for first aisle + N pairs
    first_aisle_in = result.aisle_width_in / 2  # Half aisle at the wall side
    
    # Number of row pairs
    remaining_in = available_width_in - first_aisle_in
    num_pairs = int(remaining_in / row_module_in)
    
    # Check if we can fit a single row after the last pair
    used_width_in = first_aisle_in + num_pairs * row_module_in
    leftover_in = available_width_in - used_width_in
    has_wall_row = leftover_in >= (r.frame_depth_in + result.aisle_width_in)
    
    result.row_pairs = num_pairs
    total_row_count = num_pairs * 2 + (1 if has_wall_row else 0)
    result.total_rows = total_row_count
    
    result.notes.append(f"Row pairs: {num_pairs} back-to-back" + (" + 1 wall row" if has_wall_row else ""))
    
    # ── Step 5: Place Bays Along Rows ──
    # Bays run along the depth (dock-to-back)
    bay_module_in = result.beam_length_in + upright_w  # One bay = beam + one upright
    bay_module_ft = bay_module_in / 12
    
    available_bay_length_ft = available_depth_ft
    available_bay_length_in = available_bay_length_ft * 12
    
    bays_per_row = int(available_bay_length_in / bay_module_in)
    
    result.notes.append(f"Bays per row: {bays_per_row} ({bay_module_in}\" module × {bays_per_row} = {bays_per_row * bay_module_in / 12:.0f}ft)")
    
    # ── Step 6: Place Cross-Aisles (Tunnels) ──
    cross_aisle_spacing = r.cross_aisle_spacing if r.cross_aisle_spacing > 0 else DEFAULT_CROSS_AISLE_SPACING
    
    num_cross_aisles = max(0, (bays_per_row - 1) // cross_aisle_spacing)
    tunnel_positions = []
    for i in range(1, num_cross_aisles + 1):
        pos = i * cross_aisle_spacing
        if pos < bays_per_row:
            tunnel_positions.append(pos)
    
    # Each tunnel bay replaces a normal bay with a wider beam
    result.tunnel_bays = len(tunnel_positions) * total_row_count
    
    cross_aisle_list = []
    for pos in tunnel_positions:
        y_ft = staging_depth_ft + (pos * bay_module_ft)
        cross_aisle_list.append({"bay_position": pos, "y_ft": round(y_ft, 1), "width_ft": 12})
    result.cross_aisles = cross_aisle_list
    
    if tunnel_positions:
        result.notes.append(f"Cross-aisles at bay positions: {tunnel_positions}")
    
    # ── Step 7: Building Columns ──
    column_list = []
    if b.column_grid_x_ft > 0 and b.column_grid_y_ft > 0:
        # Place columns on grid
        num_cols_x = int(b.width_ft / b.column_grid_x_ft)
        num_cols_y = int(b.length_ft / b.column_grid_y_ft)
        
        for ix in range(1, num_cols_x):
            for iy in range(1, num_cols_y):
                cx = ix * b.column_grid_x_ft
                cy = iy * b.column_grid_y_ft
                col = {"x_ft": cx, "y_ft": cy, "size_in": b.column_size_in, 
                       "conflicts_with_rack": False, "protector_needed": False}
                
                # Check if column conflicts with rack rows
                # (simplified — check if column X falls within a row pair)
                # In practice, columns are designed to fall in flue spaces
                column_list.append(col)
        
        result.notes.append(f"Building columns: {b.column_grid_x_ft}ft × {b.column_grid_y_ft}ft grid ({len(column_list)} columns)")
    result.columns = column_list
    
    # ── Step 8: Build Row List ──
    rows = []
    row_id = 0
    pair_id = 0
    
    current_x_in = WALL_CLEARANCE_FT * 12 + first_aisle_in
    
    for p in range(num_pairs):
        # Left row of pair
        row_x_ft = current_x_in / 12
        rows.append({
            "row_id": row_id,
            "x_ft": round(row_x_ft, 2),
            "y_start_ft": staging_depth_ft,
            "y_end_ft": staging_depth_ft + bays_per_row * bay_module_ft,
            "bays": bays_per_row,
            "direction": "north_south",
            "is_back_to_back": True,
            "pair_id": pair_id,
            "side": "left",
        })
        row_id += 1
        
        # Right row of pair (frame_depth + flue away)
        right_x_in = current_x_in + r.frame_depth_in + FLUE_SPACE_IN
        rows.append({
            "row_id": row_id,
            "x_ft": round(right_x_in / 12, 2),
            "y_start_ft": staging_depth_ft,
            "y_end_ft": staging_depth_ft + bays_per_row * bay_module_ft,
            "bays": bays_per_row,
            "direction": "north_south",
            "is_back_to_back": True,
            "pair_id": pair_id,
            "side": "right",
        })
        row_id += 1
        pair_id += 1
        
        # Advance by full module
        current_x_in += row_module_in
    
    # Wall row (single-deep against far wall)
    if has_wall_row:
        wall_x_in = current_x_in + result.aisle_width_in
        rows.append({
            "row_id": row_id,
            "x_ft": round(wall_x_in / 12, 2),
            "y_start_ft": staging_depth_ft,
            "y_end_ft": staging_depth_ft + bays_per_row * bay_module_ft,
            "bays": bays_per_row,
            "direction": "north_south",
            "is_back_to_back": False,
            "pair_id": -1,
            "side": "wall",
        })
        row_id += 1
    
    result.rows = rows
    
    # ── Step 9: Calculate Totals ──
    standard_bays = bays_per_row * total_row_count - result.tunnel_bays
    result.total_bays = standard_bays + result.tunnel_bays
    
    # Pallet positions
    pp_per_standard_bay = result.beam_levels * result.pallets_per_bay
    pp_per_tunnel_bay = result.beam_levels * 3  # Tunnel = 3 pallets wide
    
    pp_standard = standard_bays * pp_per_standard_bay
    pp_tunnel = result.tunnel_bays * pp_per_tunnel_bay
    result.total_pallet_positions = pp_standard + pp_tunnel
    
    # End frames: 2 per row (one at each end) — simplified
    # In practice, end frames = rows for single-row ends, varies for shared ends
    result.end_frames = total_row_count  # One end frame per row (opposite ends share with adjacent)
    
    # Total frames
    result.total_frames = result.total_bays + result.end_frames + result.tunnel_bays
    
    # Utilization
    total_building_sqft = b.length_ft * b.width_ft
    rack_footprint_sqft = result.total_bays * (result.beam_length_in * r.frame_depth_in) / 144
    result.utilization_pct = round(rack_footprint_sqft / total_building_sqft * 100, 1)
    
    # ── Step 10: Generate Bay Types for BOM ──
    beams_per_bay = result.beam_levels * 2  # Front + back beam per level
    wiredecks_per_bay = result.beam_levels * max(1, math.floor(result.beam_length_in / 46))
    pallet_supports_per_bay = wiredecks_per_bay * 2 if r.rack_style == "structural" else 0
    
    bay_types = [{
        "label": "A",
        "bays": standard_bays,
        "end_frames": result.end_frames,
        "tunnels": result.tunnel_bays,
        "beam_length": result.beam_length_in,
        "beams_per_bay": beams_per_bay,
        "wiredecks_per_bay": wiredecks_per_bay,
        "pallet_supports_per_bay": pallet_supports_per_bay,
        "tunnel_beam_length": 144,
        "tunnel_beams_per_bay": result.beam_levels * 2,
    }]
    result.bay_types = bay_types
    
    result.notes.append(f"Total: {result.total_pallet_positions:,} PP across {result.total_bays:,} bays in {total_row_count} rows")
    result.notes.append(f"Floor utilization: {result.utilization_pct}%")
    
    # Warnings
    if r.target_pallet_positions > 0 and result.total_pallet_positions < r.target_pallet_positions:
        deficit = r.target_pallet_positions - result.total_pallet_positions
        result.warnings.append(f"Target PP shortfall: need {r.target_pallet_positions:,} but only fit {result.total_pallet_positions:,} ({deficit:,} short)")
        result.warnings.append("Consider: taller frames, narrower aisles, double-deep rack, or reducing staging area")
    
    return asdict(result)


# ─── Text Visualization ───────────────────────────────────

def print_layout_ascii(layout: dict):
    """Print a simple text representation of the layout."""
    print("=" * 60)
    print("WAREHOUSE RACKING LAYOUT")
    print("=" * 60)
    
    rows = layout.get("rows", [])
    if not rows:
        print("No rows generated")
        return
    
    # Summary
    print(f"Pallet Positions: {layout['total_pallet_positions']:,}")
    print(f"Bays: {layout['total_bays']:,}  Rows: {layout['total_rows']}  Frames: {layout['total_frames']:,}")
    print(f"Frame: {layout['frame_height_in']}\" ({layout['frame_height_in']/12:.0f}ft)")
    print(f"Beam Levels: {layout['beam_levels']}  Beam Length: {layout['beam_length_in']}\"")
    print(f"Aisle Width: {layout['aisle_width_in']}\"")
    print(f"Utilization: {layout['utilization_pct']}%")
    
    print("\nNotes:")
    for note in layout.get("notes", []):
        print(f"  • {note}")
    
    if layout.get("warnings"):
        print("\n⚠️ Warnings:")
        for w in layout["warnings"]:
            print(f"  ⚠ {w}")
    
    # Simple row diagram
    print("\n--- Top View (simplified) ---")
    print(f"{'DOCK':^60}")
    print(f"{'[STAGING AREA]':^60}")
    print()
    
    # Group by pairs
    pairs = {}
    for row in rows:
        pid = row["pair_id"]
        if pid not in pairs:
            pairs[pid] = []
        pairs[pid].append(row)
    
    for pid in sorted(pairs.keys()):
        pair_rows = pairs[pid]
        if pid == -1:
            # Wall row
            bays = pair_rows[0]["bays"]
            print(f"  |{'█' * min(bays, 50)}|  (wall row, {bays} bays)")
        else:
            bays = pair_rows[0]["bays"]
            print(f"  |{'█' * min(bays, 50)}|")
            print(f"  |{'█' * min(bays, 50)}|  (pair {pid}, {bays} bays each)")
            print(f"  {'~' * min(bays + 2, 52)}  ← aisle")
    
    print(f"\n{'BACK WALL':^60}")
    
    # Bay types for BOM
    print("\n--- Bay Types (for BOM) ---")
    for bt in layout.get("bay_types", []):
        print(f"  Type {bt['label']}: {bt['bays']} bays, {bt['end_frames']} end frames, {bt['tunnels']} tunnels")
        print(f"    Beams/bay: {bt['beams_per_bay']}, WD/bay: {bt['wiredecks_per_bay']}, PS/bay: {bt['pallet_supports_per_bay']}")


# ─── Demo ─────────────────────────────────────────────────

if __name__ == "__main__":
    # Typical Prologis building
    building = {
        "length_ft": 600,
        "width_ft": 300,
        "clear_height_ft": 32,
        "dock_side": "south",
        "num_dock_doors": 15,
        "column_grid_x_ft": 50,
        "column_grid_y_ft": 50,
    }
    
    requirements = {
        "target_pallet_positions": 0,  # Maximize
        "pallet_size": "48x40",
        "rack_type": "selective",
        "rack_style": "teardrop",
        "frame_depth_in": 42,
        "forklift_type": "reach",
        "min_staging_depth_ft": 50,
    }
    
    layout = design_layout(building, requirements)
    print_layout_ascii(layout)
