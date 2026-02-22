"""
Warehouse Racking Layout SVG Visualizer
for Prologis Racking BOM Tool.

Renders layout results as professional SVG floor plans
matching the Prologis CAD drawing style.
"""

from typing import Optional

# ─── Color Scheme (Prologis-inspired) ─────────────────────

COLORS = {
    "building_outline": "#333333",
    "building_fill": "#FAFAFA",
    "rack_bay": "#4A90D9",
    "rack_bay_tunnel": "#F5A623",
    "rack_bay_alt": "#7ED321",
    "aisle": "#FFFFFF",
    "staging": "#FFF8E1",
    "staging_border": "#FFD54F",
    "column": "#888888",
    "column_protector": "#D32F2F",
    "text": "#333333",
    "text_light": "#888888",
    "dimension": "#4A90D9",
    "grid": "#EEEEEE",
    "title_bg": "#00544E",
    "title_text": "#FFFFFF",
    "dock_door": "#FF8A65",
}

SCALE = 1.8  # pixels per foot (default)


def render_layout_svg(layout: dict, project_name: str = "", 
                       building: dict = None, scale: float = SCALE) -> str:
    """
    Render a warehouse layout as an SVG string.
    
    Args:
        layout: LayoutResult dict from layout_engine.design_layout()
        project_name: For the title block
        building: BuildingSpec dict (for dimensions, dock info)
        scale: pixels per foot
    
    Returns:
        Complete SVG string
    """
    if building is None:
        building = {}
    
    bldg_w = building.get("width_ft", 300)
    bldg_l = building.get("length_ft", 600)
    dock_side = building.get("dock_side", "south")
    num_docks = building.get("num_dock_doors", 10)
    
    # SVG dimensions (building + margins for labels/title block)
    margin = 80
    title_height = 80
    svg_w = bldg_w * scale + margin * 2
    svg_h = bldg_l * scale + margin * 2 + title_height
    
    parts = []
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w:.0f} {svg_h:.0f}" '
                 f'width="{svg_w:.0f}" height="{svg_h:.0f}" '
                 f'style="font-family:Arial,Helvetica,sans-serif;">')
    
    # Background
    parts.append(f'<rect width="{svg_w}" height="{svg_h}" fill="white"/>')
    
    # Coordinate transform: origin at top-left of building
    ox = margin  # X offset
    oy = margin  # Y offset (dock at bottom if south)
    
    def bx(ft): return ox + ft * scale
    def by(ft): return oy + ft * scale  # Y: 0 = back wall (top), length = dock wall (bottom)
    
    # ── Building Outline ──
    parts.append(f'<rect x="{ox}" y="{oy}" width="{bldg_w * scale:.1f}" height="{bldg_l * scale:.1f}" '
                 f'fill="{COLORS["building_fill"]}" stroke="{COLORS["building_outline"]}" stroke-width="3"/>')
    
    # ── Grid lines (light) ──
    for x in range(0, int(bldg_w) + 1, 50):
        parts.append(f'<line x1="{bx(x):.1f}" y1="{oy}" x2="{bx(x):.1f}" y2="{by(bldg_l):.1f}" '
                     f'stroke="{COLORS["grid"]}" stroke-width="0.5"/>')
    for y in range(0, int(bldg_l) + 1, 50):
        parts.append(f'<line x1="{ox}" y1="{by(y):.1f}" x2="{bx(bldg_w):.1f}" y2="{by(y):.1f}" '
                     f'stroke="{COLORS["grid"]}" stroke-width="0.5"/>')
    
    # ── Staging Area ──
    staging = layout.get("staging_area", {})
    staging_depth = staging.get("depth_ft", 50)
    # Staging is at the dock end (bottom of drawing = high Y)
    staging_y = bldg_l - staging_depth
    parts.append(f'<rect x="{ox}" y="{by(staging_y):.1f}" '
                 f'width="{bldg_w * scale:.1f}" height="{staging_depth * scale:.1f}" '
                 f'fill="{COLORS["staging"]}" stroke="{COLORS["staging_border"]}" stroke-width="1" stroke-dasharray="8,4"/>')
    parts.append(f'<text x="{bx(bldg_w/2):.1f}" y="{by(staging_y + staging_depth/2):.1f}" '
                 f'text-anchor="middle" dominant-baseline="middle" '
                 f'font-size="14" fill="{COLORS["text_light"]}" font-style="italic">STAGING AREA ({staging_depth:.0f}ft)</text>')
    
    # ── Dock Doors ──
    if num_docks > 0:
        dock_y = by(bldg_l)
        door_width = min(12, bldg_w / (num_docks + 1)) * scale
        spacing = bldg_w * scale / (num_docks + 1)
        for i in range(num_docks):
            dx = ox + spacing * (i + 1) - door_width / 2
            parts.append(f'<rect x="{dx:.1f}" y="{dock_y - 4:.1f}" '
                         f'width="{door_width:.1f}" height="8" '
                         f'fill="{COLORS["dock_door"]}" rx="2"/>')
    
    # ── Rack Rows ──
    rows = layout.get("rows", [])
    frame_depth_ft = 42 / 12  # default, could be parameterized
    beam_length_ft = layout.get("beam_length_in", 96) / 12
    
    for row in rows:
        row_x = row.get("x_ft", 0)
        y_start = row.get("y_start_ft", 0)
        y_end = row.get("y_end_ft", 0)
        bays = row.get("bays", 0)
        is_btb = row.get("is_back_to_back", True)
        
        # Row rectangle: x position, spanning from y_start to y_end
        # In our coordinate system: y increases downward (toward dock)
        # But layout y_start is from dock, so we need to flip
        # Actually layout y_start = staging_depth (near dock), y_end = further from dock
        # In SVG: dock is at bottom (high Y), so rack rows go from top toward bottom
        
        # Flip: SVG y = bldg_l - layout_y (so dock=bottom, back wall=top)
        svg_row_x = bx(row_x)
        svg_row_y_start = by(bldg_l - y_end)   # far from dock = top
        svg_row_y_end = by(bldg_l - y_start)    # near dock = bottom
        row_height = svg_row_y_end - svg_row_y_start
        
        color = COLORS["rack_bay"]
        opacity = 0.85 if is_btb else 0.65
        
        parts.append(f'<rect x="{svg_row_x:.1f}" y="{svg_row_y_start:.1f}" '
                     f'width="{frame_depth_ft * scale:.1f}" height="{row_height:.1f}" '
                     f'fill="{color}" fill-opacity="{opacity}" stroke="{color}" stroke-width="0.5" rx="1"/>')
        
        # Row label
        label_x = svg_row_x + frame_depth_ft * scale / 2
        label_y = svg_row_y_start - 4
        if row.get("pair_id", -1) >= 0 and row.get("side") == "left":
            parts.append(f'<text x="{label_x:.1f}" y="{label_y:.1f}" '
                         f'text-anchor="middle" font-size="7" fill="{COLORS["text_light"]}">'
                         f'P{row["pair_id"]}</text>')
    
    # ── Cross-Aisles ──
    for ca in layout.get("cross_aisles", []):
        ca_y = ca.get("y_ft", 0)
        ca_width_ft = ca.get("width_ft", 12)
        svg_ca_y = by(bldg_l - ca_y - ca_width_ft)
        parts.append(f'<rect x="{ox}" y="{svg_ca_y:.1f}" '
                     f'width="{bldg_w * scale:.1f}" height="{ca_width_ft * scale:.1f}" '
                     f'fill="{COLORS["rack_bay_tunnel"]}" fill-opacity="0.15" '
                     f'stroke="{COLORS["rack_bay_tunnel"]}" stroke-width="0.5" stroke-dasharray="4,4"/>')
    
    # ── Building Columns ──
    for col in layout.get("columns", []):
        cx = bx(col.get("x_ft", 0))
        cy = by(bldg_l - col.get("y_ft", 0))  # flip Y
        size = col.get("size_in", 24) / 12 * scale
        parts.append(f'<rect x="{cx - size/2:.1f}" y="{cy - size/2:.1f}" '
                     f'width="{size:.1f}" height="{size:.1f}" '
                     f'fill="{COLORS["column"]}" stroke="#555" stroke-width="0.5"/>')
    
    # ── Dimension Labels ──
    # Building width (top)
    parts.append(f'<line x1="{ox}" y1="{oy - 25}" x2="{bx(bldg_w):.1f}" y2="{oy - 25}" '
                 f'stroke="{COLORS["dimension"]}" stroke-width="1" marker-start="url(#arrow)" marker-end="url(#arrow)"/>')
    parts.append(f'<text x="{bx(bldg_w/2):.1f}" y="{oy - 30}" text-anchor="middle" '
                 f'font-size="12" fill="{COLORS["dimension"]}" font-weight="bold">{bldg_w:.0f}ft</text>')
    
    # Building length (right)
    right_x = bx(bldg_w) + 25
    parts.append(f'<line x1="{right_x}" y1="{oy}" x2="{right_x}" y2="{by(bldg_l):.1f}" '
                 f'stroke="{COLORS["dimension"]}" stroke-width="1"/>')
    parts.append(f'<text x="{right_x + 5}" y="{by(bldg_l/2):.1f}" '
                 f'font-size="12" fill="{COLORS["dimension"]}" font-weight="bold" '
                 f'transform="rotate(90,{right_x + 5},{by(bldg_l/2):.1f})">{bldg_l:.0f}ft</text>')
    
    # ── Title Block ──
    tb_y = svg_h - title_height
    parts.append(f'<rect x="0" y="{tb_y}" width="{svg_w}" height="{title_height}" fill="{COLORS["title_bg"]}"/>')
    
    pp = layout.get("total_pallet_positions", 0)
    bays_total = layout.get("total_bays", 0)
    rows_total = layout.get("total_rows", 0)
    frame_ht = layout.get("frame_height_in", 0)
    levels = layout.get("beam_levels", 0)
    beam_len = layout.get("beam_length_in", 0)
    aisle_w = layout.get("aisle_width_in", 0)
    
    title = project_name or "Warehouse Layout"
    parts.append(f'<text x="20" y="{tb_y + 25}" font-size="18" font-weight="bold" '
                 f'fill="{COLORS["title_text"]}">{_escape(title)}</text>')
    
    specs_line = (f'{pp:,} Pallet Positions  |  {bays_total:,} Bays  |  {rows_total} Rows  |  '
                  f'{frame_ht/12:.0f}ft Frames  |  {levels} Levels  |  {beam_len}" Beams  |  '
                  f'{aisle_w/12:.0f}ft Aisles')
    parts.append(f'<text x="20" y="{tb_y + 48}" font-size="11" fill="{COLORS["title_text"]}" '
                 f'fill-opacity="0.8">{_escape(specs_line)}</text>')
    
    parts.append(f'<text x="20" y="{tb_y + 65}" font-size="10" fill="{COLORS["title_text"]}" '
                 f'fill-opacity="0.6">SELECTIVE RACK  |  PROLOGIS ESSENTIALS  |  PRELIMINARY DESIGN</text>')
    
    # Prologis logo text (right side)
    parts.append(f'<text x="{svg_w - 20}" y="{tb_y + 35}" text-anchor="end" '
                 f'font-size="22" font-weight="bold" fill="{COLORS["title_text"]}" '
                 f'fill-opacity="0.9">PROLOGIS</text>')
    parts.append(f'<text x="{svg_w - 20}" y="{tb_y + 52}" text-anchor="end" '
                 f'font-size="11" fill="{COLORS["title_text"]}" fill-opacity="0.6">ESSENTIALS</text>')
    
    # ── Scale Bar ──
    scale_bar_ft = 50
    sb_w = scale_bar_ft * scale
    sb_x = svg_w - margin - sb_w
    sb_y = oy - 15
    parts.append(f'<line x1="{sb_x}" y1="{sb_y}" x2="{sb_x + sb_w}" y2="{sb_y}" '
                 f'stroke="{COLORS["text"]}" stroke-width="2"/>')
    parts.append(f'<line x1="{sb_x}" y1="{sb_y - 4}" x2="{sb_x}" y2="{sb_y + 4}" '
                 f'stroke="{COLORS["text"]}" stroke-width="1"/>')
    parts.append(f'<line x1="{sb_x + sb_w}" y1="{sb_y - 4}" x2="{sb_x + sb_w}" y2="{sb_y + 4}" '
                 f'stroke="{COLORS["text"]}" stroke-width="1"/>')
    parts.append(f'<text x="{sb_x + sb_w/2}" y="{sb_y - 6}" text-anchor="middle" '
                 f'font-size="9" fill="{COLORS["text"]}">{scale_bar_ft}ft</text>')
    
    # ── Dock Label ──
    parts.append(f'<text x="{bx(bldg_w/2):.1f}" y="{by(bldg_l) + 20:.1f}" '
                 f'text-anchor="middle" font-size="12" font-weight="bold" '
                 f'fill="{COLORS["dock_door"]}">▼ DOCK DOORS ▼</text>')
    
    parts.append('</svg>')
    return '\n'.join(parts)


def _escape(text: str) -> str:
    """Escape text for SVG XML"""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def save_svg(svg_str: str, filepath: str):
    """Save SVG to file"""
    with open(filepath, 'w') as f:
        f.write(svg_str)


# ─── FastAPI Integration ──────────────────────────────────

def register_routes(app):
    """Register visualization routes with FastAPI"""
    from fastapi import Request
    from fastapi.responses import Response, JSONResponse
    
    @app.post("/api/layout-svg")
    async def generate_layout_svg(request: Request):
        """Generate layout + render as SVG"""
        try:
            data = await request.json()
            
            # Design the layout first
            from layout_engine import design_layout
            building = data.get("building", {})
            requirements = data.get("requirements", {})
            layout = design_layout(building, requirements)
            
            # Render SVG
            svg = render_layout_svg(
                layout=layout,
                project_name=data.get("project_name", ""),
                building=building,
            )
            
            return Response(content=svg, media_type="image/svg+xml")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JSONResponse(status_code=500, content={"error": str(e)})


# ─── Demo ─────────────────────────────────────────────────

if __name__ == "__main__":
    from layout_engine import design_layout
    
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
        "pallet_size": "48x40",
        "rack_type": "selective",
        "rack_style": "teardrop",
        "frame_depth_in": 42,
        "forklift_type": "reach",
        "min_staging_depth_ft": 50,
    }
    
    layout = design_layout(building, requirements)
    svg = render_layout_svg(layout, project_name="Sample Warehouse — 600x300, 32ft Clear", building=building)
    save_svg(svg, "/tmp/sample_layout.svg")
    print(f"SVG saved to /tmp/sample_layout.svg ({len(svg)} bytes)")
    print(f"Layout: {layout['total_pallet_positions']:,} PP, {layout['total_bays']:,} bays, {layout['total_rows']} rows")
