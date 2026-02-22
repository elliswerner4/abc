"""BOM Calculator — validated formulas from Spartan, Wesco, Tesla examples."""

import math
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class BayType:
    name: str
    bay_count: int
    row_count: int
    beam_levels: int
    beam_type: str = ""


@dataclass
class ProjectConfig:
    project_name: str = ""
    client_name: str = ""
    rack_style: str = "teardrop"
    manufacturer: str = "Mecalux"
    beam_length: float = 96.0
    frame_height_ft: float = 20.0
    frame_depth: float = 42.0
    pallet_size: str = '40"x48"'
    pallet_weight: int = 3000
    clear_height_ft: float = 24.0
    aisle_width: str = ""
    total_pallet_positions: int = 0
    tunnel_count: int = 0
    tunnel_beam_length: float = 144.0
    tunnel_beam_levels: int = 2
    bay_types: List[BayType] = field(default_factory=list)
    deck_width: float = 0
    anchors_per_frame: int = 0


@dataclass
class BOMLine:
    category: str
    description: str
    qty_by_type: Dict[str, int] = field(default_factory=dict)
    total_qty: int = 0
    notes: str = ""


def auto_deck_width(frame_depth: float) -> float:
    if frame_depth <= 44:
        return 46.0
    else:
        return 58.0


def auto_anchors_per_frame(frame_depth: float) -> int:
    if frame_depth <= 44:
        return 2
    else:
        return 8


def calculate_bom(config: ProjectConfig) -> List[BOMLine]:
    if config.deck_width == 0:
        config.deck_width = auto_deck_width(config.frame_depth)
    if config.anchors_per_frame == 0:
        config.anchors_per_frame = auto_anchors_per_frame(config.frame_depth)

    bom: List[BOMLine] = []

    # --- FRAMES ---
    frame_qty_by_type = {}
    total_frames = 0
    for bt in config.bay_types:
        frames = bt.bay_count + bt.row_count
        frame_qty_by_type[bt.name] = frames
        total_frames += frames
    total_frames += config.tunnel_count

    frame_height_str = f"{config.frame_height_ft:.0f}'" if config.frame_height_ft == int(config.frame_height_ft) else f"{config.frame_height_ft}'"
    frame_desc = f'{config.rack_style.title()} | Frames | {frame_height_str} x {config.frame_depth:.0f}"'

    bom.append(BOMLine(
        category="Frames",
        description=frame_desc,
        qty_by_type=frame_qty_by_type,
        total_qty=total_frames,
        notes=f"+{config.tunnel_count} tunnel frames" if config.tunnel_count else ""
    ))

    # --- BEAMS ---
    total_beams = 0
    beam_groups: Dict[str, int] = {}
    for bt in config.bay_types:
        beams = bt.bay_count * bt.beam_levels * 2
        key = f'{config.rack_style.title()} | Beams | {config.beam_length:.0f}" | {bt.beam_type}' if bt.beam_type else f'{config.rack_style.title()} | Beams | {config.beam_length:.0f}"'
        beam_groups[key] = beam_groups.get(key, 0) + beams
        total_beams += beams

    tunnel_beams = 0
    if config.tunnel_count > 0:
        tunnel_beams = config.tunnel_count * config.tunnel_beam_levels * 2
        key = f'{config.rack_style.title()} | Beams | {config.tunnel_beam_length:.0f}"'
        beam_groups[key] = beam_groups.get(key, 0) + tunnel_beams
        total_beams += tunnel_beams

    for desc, qty in beam_groups.items():
        bom.append(BOMLine(category="Beams", description=desc, total_qty=qty))

    # --- WIRE DECKS ---
    std_beam_pairs = (total_beams - tunnel_beams) // 2
    std_decks_per_pair = math.floor(config.beam_length / config.deck_width)
    std_wiredecks = std_beam_pairs * std_decks_per_pair

    tunnel_wiredecks = 0
    if tunnel_beams > 0:
        tunnel_beam_pairs = tunnel_beams // 2
        tunnel_decks_per_pair = math.floor(config.tunnel_beam_length / config.deck_width)
        tunnel_wiredecks = tunnel_beam_pairs * tunnel_decks_per_pair

    total_wiredecks = std_wiredecks + tunnel_wiredecks
    deck_type = "Step" if config.rack_style == "teardrop" else "Flanged"
    bom.append(BOMLine(
        category="Wire Decks",
        description=f'{deck_type} | Wiredecks | {config.frame_depth:.0f}" x {config.deck_width:.0f}"',
        total_qty=total_wiredecks
    ))

    # --- PALLET SUPPORTS (structural only) ---
    if config.rack_style == "structural":
        bom.append(BOMLine(
            category="Pallet Supports",
            description=f'Structural | Pallet Supports | {config.frame_depth:.0f}"',
            total_qty=total_wiredecks * 2
        ))

    # --- ROW SPACERS ---
    total_rows = sum(bt.row_count for bt in config.bay_types)
    spacer_estimate = round(total_frames * 1.5)
    bom.append(BOMLine(
        category="Row Spacers",
        description='Row Spacers | 12"',
        total_qty=spacer_estimate,
        notes="Estimate — verify with layout"
    ))

    # --- ANCHORS ---
    total_anchors = total_frames * config.anchors_per_frame
    bom.append(BOMLine(
        category="Anchors",
        description='Anchors | 1/2" x 4"',
        total_qty=total_anchors
    ))

    # --- SHIMS ---
    bom.append(BOMLine(
        category="Shims",
        description="Shims",
        total_qty=total_frames,
        notes="1 per frame"
    ))

    # --- END OF AISLE GUARDS ---
    bom.append(BOMLine(
        category="End of Aisle Guards",
        description=f'End of Aisle Guard | {config.frame_depth:.0f}" | Right',
        total_qty=total_rows * 2
    ))
    bom.append(BOMLine(
        category="End of Aisle Guards",
        description=f'End of Aisle Guard | {config.frame_depth:.0f}" | Left',
        total_qty=total_rows * 2
    ))

    # --- HARDWARE (structural only) ---
    if config.rack_style == "structural":
        bolt_count = total_beams * 4
        bom.append(BOMLine(
            category="Hardware",
            description='Hardware | 1/2" x 2" Bolts',
            total_qty=bolt_count
        ))
        bom.append(BOMLine(
            category="Hardware",
            description='Hardware | 1/2" Hex Nut',
            total_qty=bolt_count
        ))

    return bom


def bom_to_summary(config: ProjectConfig, bom: List[BOMLine]) -> dict:
    total_bays = sum(bt.bay_count for bt in config.bay_types) + config.tunnel_count
    total_rows = sum(bt.row_count for bt in config.bay_types)

    return {
        "project": {
            "name": config.project_name,
            "client": config.client_name,
            "rack_style": config.rack_style,
            "manufacturer": config.manufacturer,
            "beam_length": config.beam_length,
            "frame_height_ft": config.frame_height_ft,
            "frame_depth": config.frame_depth,
            "total_bays": total_bays,
            "total_rows": total_rows,
            "total_tunnels": config.tunnel_count,
            "total_pallet_positions": config.total_pallet_positions,
        },
        "bay_types": [
            {
                "name": bt.name,
                "bays": bt.bay_count,
                "rows": bt.row_count,
                "beam_levels": bt.beam_levels,
            }
            for bt in config.bay_types
        ],
        "bom": [
            {
                "category": line.category,
                "description": line.description,
                "total_qty": line.total_qty,
                "qty_by_type": line.qty_by_type,
                "notes": line.notes,
            }
            for line in bom
        ],
    }
