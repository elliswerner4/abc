"""Prologis Racking BOM Tool — FastAPI Server (v2)

Rebuilt with validated formulas from 7 real projects.
"""

import os
import json
import math
import traceback
from pathlib import Path
from typing import List, Dict

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse, FileResponse
from io import BytesIO

from dotenv import load_dotenv
env_path = Path(__file__).parent / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

from pdf_extractor import extract_from_pdf
from xlsx_generator import generate_pricing_xlsx

app = FastAPI(title="Prologis Racking BOM Tool")

# Register new engine modules
try:
    from seismic import register_routes as register_seismic
    register_seismic(app)
except ImportError:
    pass

try:
    from fire_code import register_routes as register_fire
    register_fire(app)
except ImportError:
    pass

try:
    from layout_viz import register_routes as register_viz
    register_viz(app)
except ImportError:
    pass

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

assets_dir = Path(__file__).parent / "assets"
assets_dir.mkdir(exist_ok=True)
app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")


@app.get("/")
async def index():
    return FileResponse(str(static_dir / "index.html"))


# ── BOM Calculation Engine ────────────────────────────────

def compute_bom(data: dict) -> dict:
    """
    Counting-model-based BOM calculator.
    
    Input: {
        project_name, client, rack_style, manufacturer,
        frame_height, frame_depth, deck_width,
        anchors_per_frame, shims_per_frame,
        bay_types: [{
            label, bays, end_frames, tunnels,
            beam_length, beams_per_bay,
            wiredecks_per_bay, pallet_supports_per_bay,
            tunnel_beam_length, tunnel_beams_per_bay,
        }],
        # User-input items (no formula):
        eoa_guards_left, eoa_guards_right,
        spacers: [{ size, qty }],
        pallet_positions,
    }
    """
    bay_types = data.get("bay_types", [])
    frame_depth = data.get("frame_depth", 42)
    frame_height = data.get("frame_height", 264)
    rack_style = data.get("rack_style", "teardrop").lower()
    deck_width = data.get("deck_width", 46)
    anchors_per_frame = data.get("anchors_per_frame", 2)
    shims_per_frame = data.get("shims_per_frame", 1)
    manufacturer = data.get("manufacturer", "")

    bay_type_details = []
    total_frames = 0
    total_beams = 0
    total_wiredecks = 0
    total_pallet_supports = 0
    total_bays = 0
    total_tunnels = 0
    bom_items = []

    # Track beams by size for separate BOM lines
    beams_by_desc = {}
    wiredecks_by_desc = {}

    for bt in bay_types:
        label = bt.get("label", "?")
        bays = bt.get("bays", 0)
        end_frames = bt.get("end_frames", 0)
        tunnels = bt.get("tunnels", 0)
        beam_length = bt.get("beam_length", 96)
        beams_per_bay = bt.get("beams_per_bay", 8)  # total beams per bay (levels × 2)
        wiredecks_per_bay = bt.get("wiredecks_per_bay", 0)
        pallet_supports_per_bay = bt.get("pallet_supports_per_bay", 0)
        tunnel_beam_length = bt.get("tunnel_beam_length", 144)
        tunnel_beams_per_bay = bt.get("tunnel_beams_per_bay", 4)

        # Frames = bays + end_frames + tunnels
        frames = bays + end_frames + tunnels

        # Beams = bays × beams_per_bay (already includes ×2 for front+back)
        beams = bays * beams_per_bay
        tunnel_beams = tunnels * tunnel_beams_per_bay
        total_beams_this_type = beams + tunnel_beams

        # Wire decks = bays × wiredecks_per_bay
        wiredecks = bays * wiredecks_per_bay
        # Tunnel wiredecks: calculate from tunnel beams
        tunnel_wd_per_bay = 0
        if tunnels > 0 and tunnel_beams_per_bay > 0:
            tunnel_levels = tunnel_beams_per_bay // 2
            tunnel_wd_per_bay = tunnel_levels * max(1, math.floor(tunnel_beam_length / deck_width))
        tunnel_wiredecks = tunnels * tunnel_wd_per_bay
        wiredecks += tunnel_wiredecks

        # Pallet supports = bays × pallet_supports_per_bay
        pallet_supports = bays * pallet_supports_per_bay

        total_frames += frames
        total_beams += total_beams_this_type
        total_wiredecks += wiredecks
        total_pallet_supports += pallet_supports
        total_bays += bays
        total_tunnels += tunnels

        bay_type_details.append({
            "label": label,
            "bays": bays,
            "end_frames": end_frames,
            "tunnels": tunnels,
            "beam_length": beam_length,
            "beams_per_bay": beams_per_bay,
            "wiredecks_per_bay": wiredecks_per_bay,
            "pallet_supports_per_bay": pallet_supports_per_bay,
            "frames": frames,
            "beams": total_beams_this_type,
            "wiredecks": wiredecks,
            "pallet_supports": pallet_supports,
        })

        # Accumulate beams by description
        style_label = rack_style.title()
        beam_desc = f'{style_label} | Beams | {beam_length}"'
        beams_by_desc[beam_desc] = beams_by_desc.get(beam_desc, 0) + beams
        if tunnel_beams > 0:
            tunnel_desc = f'{style_label} | Beams | {tunnel_beam_length}" | Tunnel'
            beams_by_desc[tunnel_desc] = beams_by_desc.get(tunnel_desc, 0) + tunnel_beams

        # Accumulate wiredecks
        if wiredecks_per_bay > 0:
            deck_type = "Step" if rack_style == "teardrop" else "Flanged"
            wd_desc = f'{deck_type} | Wiredecks | {frame_depth}" x {deck_width}"'
            wiredecks_by_desc[wd_desc] = wiredecks_by_desc.get(wd_desc, 0) + (bays * wiredecks_per_bay)
        if tunnel_wiredecks > 0:
            deck_type = "Step" if rack_style == "teardrop" else "Flanged"
            wd_desc = f'{deck_type} | Wiredecks | {frame_depth}" x {deck_width}"'
            wiredecks_by_desc[wd_desc] = wiredecks_by_desc.get(wd_desc, 0) + tunnel_wiredecks

    # === Build BOM Items ===
    style_label = rack_style.title()

    # Frames (single line — all types combined, or per type if multiple depths)
    bom_items.append({
        "item": f'{style_label} | Frames | {frame_height/12:.0f}\' x {frame_depth}"',
        "qty": total_frames,
        "category": "Frames",
    })

    # Beams (per beam size)
    for desc, qty in beams_by_desc.items():
        bom_items.append({"item": desc, "qty": qty, "category": "Beams"})

    # Wire decks (combined by description)
    for desc, qty in wiredecks_by_desc.items():
        bom_items.append({"item": desc, "qty": qty, "category": "Wire Decks"})

    # Pallet supports
    if total_pallet_supports > 0:
        bom_items.append({
            "item": f'Pallet Supports | {frame_depth}"',
            "qty": total_pallet_supports,
            "category": "Pallet Supports",
        })

    # Row spacers (user input)
    spacers = data.get("spacers", [])
    for sp in spacers:
        size = sp.get("size", "12")
        qty = sp.get("qty", 0)
        if qty > 0:
            bom_items.append({
                "item": f'Row Spacers | {size}"',
                "qty": qty,
                "category": "Row Spacers",
            })

    # Anchors (frame anchors)
    total_anchors = total_frames * anchors_per_frame
    anchor_size = data.get("anchor_size", '1/2" x 4"')
    bom_items.append({
        "item": f'Anchors | {anchor_size}',
        "qty": total_anchors,
        "category": "Anchors",
    })

    # Shims
    total_shims = total_frames * shims_per_frame
    if total_shims > 0:
        bom_items.append({
            "item": "Shims",
            "qty": total_shims,
            "category": "Shims",
        })

    # End of aisle guards (user input)
    eoa_left = data.get("eoa_guards_left", 0)
    eoa_right = data.get("eoa_guards_right", 0)
    if eoa_left > 0:
        bom_items.append({
            "item": f'End of Aisle Guard | {frame_depth}" | Left',
            "qty": eoa_left,
            "category": "EoA Guards",
        })
    if eoa_right > 0:
        bom_items.append({
            "item": f'End of Aisle Guard | {frame_depth}" | Right',
            "qty": eoa_right,
            "category": "EoA Guards",
        })

    # Guard anchors 3/4" (4 per guard)
    total_eoa = eoa_left + eoa_right
    guard_anchors_per = data.get("guard_anchors_per", 4)
    if total_eoa > 0:
        guard_anchors = total_eoa * guard_anchors_per
        bom_items.append({
            "item": 'Anchors | 3/4" x 4"',
            "qty": guard_anchors,
            "category": "Anchors",
        })

    # Hardware (structural only)
    if rack_style == "structural":
        bolt_count = total_beams * 4
        bom_items.append({
            "item": 'Hardware | 1/2" x 2" Bolts',
            "qty": bolt_count,
            "category": "Hardware",
        })
        bom_items.append({
            "item": 'Hardware | 1/2" Hex Nut',
            "qty": bolt_count,
            "category": "Hardware",
        })

    summary = {
        "total_bays": total_bays,
        "total_tunnels": total_tunnels,
        "total_frames": total_frames,
        "total_beams": total_beams,
        "total_wiredecks": total_wiredecks,
        "total_pallet_supports": total_pallet_supports,
        "total_anchors": total_anchors,
        "total_eoa_guards": total_eoa,
        "total_pallet_positions": data.get("pallet_positions", 0),
    }

    return {
        "project_name": data.get("project_name", ""),
        "client": data.get("client", data.get("client_name", "")),
        "rack_style": rack_style,
        "manufacturer": manufacturer,
        "frame_height": frame_height,
        "frame_depth": frame_depth,
        "deck_width": deck_width,
        "anchors_per_frame": anchors_per_frame,
        "shims_per_frame": shims_per_frame,
        "bay_type_details": bay_type_details,
        "bom_items": bom_items,
        "summary": summary,
    }


# ── API Endpoints ─────────────────────────────────────────

@app.post("/api/analyze")
async def analyze_pdf(file: UploadFile = File(...)):
    if not OPENAI_API_KEY:
        raise HTTPException(500, "OPENAI_API_KEY not configured")
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Please upload a PDF file")

    try:
        pdf_bytes = await file.read()
        if len(pdf_bytes) < 100:
            raise HTTPException(400, "PDF file appears empty or corrupt")

        extracted = await extract_from_pdf(pdf_bytes, OPENAI_API_KEY)
        
        normalized = {
            "project_name": extracted.get("project_name", ""),
            "client": extracted.get("client", ""),
            "rack_style": extracted.get("rack_style", "teardrop"),
            "frame_height": extracted.get("frame_height", 264),
            "frame_depth": extracted.get("frame_depth", 42),
            "deck_width": extracted.get("deck_width", 46),
            "anchors_per_frame": extracted.get("anchors_per_frame", 2),
            "shims_per_frame": extracted.get("shims_per_frame", 1),
            "bay_types": extracted.get("bay_types", []),
        }

        result = compute_bom(normalized)
        result["extracted_raw"] = extracted
        return JSONResponse(content=result)

    except json.JSONDecodeError as e:
        raise HTTPException(422, f"GPT-4o returned invalid JSON. Try manual entry. Detail: {e}")
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.post("/api/calculate")
async def calculate_from_manual(request: Request):
    try:
        data = await request.json()
        result = compute_bom(data)
        return JSONResponse(content=result)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Calculation failed: {str(e)}")


@app.post("/api/generate-xlsx")
async def generate_xlsx(request: Request):
    try:
        bom_data = await request.json()

        project = {
            "name": bom_data.get("project_name", ""),
            "client": bom_data.get("client", ""),
            "rack_style": bom_data.get("rack_style", ""),
            "manufacturer": bom_data.get("manufacturer", ""),
            "frame_height_ft": bom_data.get("frame_height", 264) / 12,
            "frame_depth": bom_data.get("frame_depth", 42),
            "total_pallet_positions": bom_data.get("summary", {}).get("total_pallet_positions", 0),
        }

        bay_types = [
            {"name": bt["label"], "bays": bt["bays"], "end_frames": bt.get("end_frames", 0),
             "beams_per_bay": bt.get("beams_per_bay", 0)}
            for bt in bom_data.get("bay_type_details", [])
        ]

        rack_mfg = bom_data.get("manufacturer", "")
        def _assign_mfg(cat):
            cat_lower = cat.lower()
            if any(k in cat_lower for k in ["frame", "beam", "spacer", "shim", "hardware", "pallet support"]):
                return rack_mfg
            elif "anchor" in cat_lower:
                return "Hilti"
            elif any(k in cat_lower for k in ["wire", "deck", "eoa", "guard"]):
                return "WWMH"
            return ""

        bom = [
            {
                "category": item["category"],
                "description": item["item"],
                "total_qty": item["qty"],
                "mfg": _assign_mfg(item["category"]),
                "notes": "",
            }
            for item in bom_data.get("bom_items", [])
        ]

        xlsx_bytes = generate_pricing_xlsx(project=project, bay_types=bay_types, bom=bom)

        project_name = bom_data.get("project_name", "BOM") or "BOM"
        safe_name = "".join(c for c in project_name if c.isalnum() or c in " _-")[:40]
        filename = f"{safe_name}_Pricing_Model.xlsx"

        return StreamingResponse(
            BytesIO(xlsx_bytes),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(xlsx_bytes)),
            },
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"XLSX generation failed: {str(e)}")


# ── Markets & Design Endpoints ────────────────────────────

@app.get("/api/markets")
async def list_markets():
    """List all Prologis markets with typical specs"""
    try:
        from prologis_markets import list_all_markets, PROLOGIS_MARKETS
        return {"markets": list_all_markets(), "detail": PROLOGIS_MARKETS}
    except ImportError:
        raise HTTPException(500, "Markets module not available")


@app.post("/api/design")
async def design_layout(request: Request):
    """
    Full pipeline: building spec + requirements → layout → BOM → pricing-ready data.
    
    Input: {
        address: str (optional — triggers seismic lookup),
        building: { length_ft, width_ft, clear_height_ft, dock_side, num_dock_doors, ... },
        requirements: { target_pallet_positions, pallet_size, rack_type, frame_depth_in, forklift_type, ... },
        project_name: str,
        client: str,
    }
    """
    try:
        data = await request.json()
        result = {"status": "design_engine_coming_soon"}
        
        # Step 1: Seismic lookup if address provided
        address = data.get("address", "")
        if address:
            try:
                from seismic import lookup_site
                seismic = lookup_site(address)
                result["seismic"] = seismic
            except Exception as e:
                result["seismic_error"] = str(e)
        
        # Step 2: Layout design (coming soon)
        try:
            from layout_engine import design_layout as _design
            building = data.get("building", {})
            requirements = data.get("requirements", {})
            if building:
                layout = _design(building, requirements)
                result["layout"] = layout
        except ImportError:
            result["layout"] = {"status": "layout_engine_not_yet_available"}
        
        # Step 3: Fire assessment
        if address:
            try:
                from fire_code import full_site_assessment, CommodityClass
                seismic_data = result.get("seismic", {})
                sdc = seismic_data.get("seismic", {}).get("sdc", "B")
                state = address.split(",")[-1].strip().split()[0] if "," in address else "IL"
                building_spec = data.get("building", {})
                clear_ht = building_spec.get("clear_height_ft", 32)
                assessment = full_site_assessment(
                    sdc=sdc, state=state,
                    storage_height_ft=clear_ht - 3,  # rough storage height
                    storage_area_sqft=building_spec.get("length_ft", 300) * building_spec.get("width_ft", 300),
                )
                result["fire_assessment"] = assessment
            except Exception as e:
                result["fire_assessment_error"] = str(e)
        
        return JSONResponse(content=result)
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f"Design failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
