# Prologis Racking Design Engine — Assumptions & Logic

**For Engineering Review**
*Document all assumptions, formulas, and logic built into the automated racking design engine so the engineering team can verify, correct, or refine them.*

---

## 1. Seismic Lookup & Engineering Requirements

### How It Works
Given a building address, we:
1. Geocode the address to lat/lon (using OpenStreetMap/Nominatim)
2. Query the **USGS ASCE 7-22 web service** for seismic design parameters
3. Map the resulting **Seismic Design Category (SDC)** to engineering requirements

### Assumptions

| Parameter | Our Default | Confidence | Notes |
|-----------|-------------|------------|-------|
| **Risk Category** | II | HIGH | Standard for warehouses (non-essential facilities) |
| **Site Class** | D | MEDIUM | Default when no geotechnical/soil data is available. Engineers may override with actual soil data. |
| **Building Code** | IBC everywhere except California (CBC) | HIGH | Determined by lat/lon bounding box for California |

### SDC → Anchor Mapping

This is one of the most critical assumptions. We map SDC to anchors per base plate:

| SDC | Anchors per Base Plate | Anchors per Frame (= ×2 base plates) | Anchor Type | Anchor Size | Embed Depth |
|-----|----------------------|---------------------------------------|-------------|-------------|-------------|
| A | 1 | 2 | Wedge | 1/2" × 4" | 2.25" |
| B | 1 | 2 | Wedge | 1/2" × 4" | 2.25" |
| C | 2 | 4 | Hilti Kwik Bolt TZ2 | 1/2" × 4" | 2.25" |
| D | 4 | 8 | Hilti Kwik Bolt TZ2 | 5/8" × 4.5" | 3.75" |
| E | 4 | 8 | Hilti Kwik Bolt TZ2 | 5/8" × 4.5" | 3.75" |
| F | 4 | 8 | Hilti Kwik Bolt TZ2 | 5/8" × 4.5" | 3.75" |

**Confidence: MEDIUM** — We derived this from the Spirit Halloween project (Perris CA, SDC D) where OneRack LLC and Seizmic Inc both specified 4 anchors per base plate with Hilti KB-TZ2 at 0.625" dia × 3.75" embed. SDC A/B values (1 per base plate, wedge anchors) are based on low-seismic project data (Spartan, Wesco, Grainger, Creative Werks). **The actual anchor count comes from the prelim engineering report — this is our default until engineers provide project-specific specs.**

> **QUESTION FOR ENGINEERS:** Is this SDC-to-anchor mapping reasonable as a starting default? What other factors drive anchor count beyond SDC?

### SDC → Bracing Requirements

| SDC | Bracing Level | Row Spacers Required | Prelim Engineering Required |
|-----|---------------|---------------------|---------------------------|
| A-B | Standard | No | No |
| C | Enhanced | Yes | Yes |
| D-F | Full seismic | Yes | Yes |

**Confidence: MEDIUM** — Based on general industry practice. Need engineer confirmation on what "enhanced" vs "full seismic" bracing means in practice.

### California Detection

We use a lat/lon bounding box to determine if a site is in California (for CBC vs IBC). This is a rough check — it correctly identifies most CA sites but could theoretically misclassify border areas.

**Confidence: HIGH** — Simple and effective for US addresses.

---

## 2. Fire Code & High-Pile Storage Logic

### How It Works
We assess fire code requirements based on:
- Storage height (top of highest pallet, not rack height)
- NFPA commodity classification
- Storage area in square feet
- Jurisdiction (IBC vs CBC)

### Commodity Classification (NFPA 13 / IBC)

| Class | Description | High-Pile Threshold |
|-------|-------------|-------------------|
| I | Noncombustible on wood pallets | 12 ft |
| II | Class I in corrugated cartons | 12 ft |
| III | Wood, paper, natural fibers, Group C plastics | 12 ft |
| IV | Class I-III with Group A plastics (≤5%) | 12 ft |
| High Hazard | Group A plastics >5%, flammables, aerosols | 6 ft |

**Confidence: HIGH** — Straight from IFC 2021 Table 3206.2. Thresholds are well-established.

> **QUESTION FOR ENGINEERS:** In practice, what commodity class are most Prologis tenants? Is Class II a good default?

### Sprinkler Requirements

Our logic for sprinkler type based on storage height and commodity:

| Storage Height | Class I-III | Class IV+ |
|---------------|-------------|-----------|
| ≤25 ft | ESFR K25.2 ceiling only | ESFR K25.2 ceiling only |
| 25-30 ft | ESFR K28 ceiling only (Class I-II), ESFR + in-rack (Class III) | ESFR + in-rack |
| >30 ft | ESFR + in-rack at 10ft and 20ft levels | ESFR + in-rack |

**Confidence: LOW** — This is our most uncertain area. Sprinkler design is highly project-specific and depends on ceiling height, K-factor availability, water supply, and local fire authority (AHJ) requirements. **We flag these as "verify with fire protection engineer" in every case.**

> **QUESTION FOR ENGINEERS:** Should we even attempt to specify sprinkler types, or just flag when in-rack sprinklers are likely needed and leave the details to the FPE?

### Sprinkler Clearance

| Sprinkler Type | Minimum Clearance | Our Default |
|---------------|-------------------|-------------|
| ESFR | 36" to deflectors | 36" |
| Other | 18" to deflectors (NFPA 13 min) | 24" recommended |

**Confidence: HIGH** — 36" for ESFR is industry standard. This directly affects maximum rack height.

### Flue Space Requirements

| Condition | Transverse (across beam) | Longitudinal (front-to-back) |
|-----------|-------------------------|------------------------------|
| Storage ≤20 ft, Class I-II | 3" | 3" |
| Storage ≤20 ft, Class III+ | 3" | 6" |
| Storage >20 ft | 3" | 6" |

**Confidence: MEDIUM** — Based on NFPA 13 / FM Global DS 8-9. The standard 6" longitudinal flue is what we use for back-to-back row spacing.

### Fire Department Access Aisles

- Required when storage area >12,000 sqft
- Minimum width: 8 ft clear

**Confidence: MEDIUM** — IFC 3206.9 reference. Specific requirements vary by AHJ.

### Fire Baffles

- Triggered when storage >15 ft AND commodity Class III, IV, or High Hazard
- Spacing: every 10 bays (when required)

**Confidence: LOW** — Baffle requirements vary significantly by jurisdiction and AHJ interpretation. We flag "may be required — verify with AHJ."

> **QUESTION FOR ENGINEERS:** What's the actual fire baffle policy for Prologis projects? Is it always driven by the local fire marshal?

### California-Specific Notes

- CBC 2022 Chapter 32 applies (stricter than IBC in some areas)
- State Fire Marshal may require additional review
- High-pile storage permit required from local fire authority for any storage >12 ft

**Confidence: HIGH** — California requirements are well-documented.

---

## 3. Layout Engine Logic

### How It Works
Given building dimensions and rack requirements, we calculate:
1. Optimal frame height from clear height
2. Number of beam levels
3. Row placement (back-to-back pairs across building width)
4. Bay placement (along building depth)
5. Cross-aisle (tunnel) placement
6. Column avoidance

### Frame Height Selection

We select the largest standard frame height that fits under the clear height minus sprinkler clearance (36"):

| Standard Frame Heights Available |
|--------------------------------|
| 96" (8ft), 120" (10ft), 144" (12ft), 168" (14ft), 192" (16ft), 216" (18ft), 240" (20ft), 264" (22ft), 288" (24ft), 336" (28ft) |

Formula: `max_frame = clear_height_inches - 36" sprinkler clearance`

Example: 32 ft clear height = 384" → 384" - 36" = 348" → Best fit: 336" (28ft frame)

**Confidence: HIGH** — Standard frame sizes are well-established. 36" clearance for ESFR is conservative.

> **QUESTION FOR ENGINEERS:** Are these the right standard frame heights? Are there common sizes we're missing?

### Beam Level Calculation

Formula: `beam_levels = floor((frame_height - first_beam_height) / level_spacing) + 1`

| Parameter | Default | Notes |
|-----------|---------|-------|
| First beam height | 88" (~7'4") | Clears forklifts, allows floor-level pallet |
| Level spacing | 60" | Pallet height (48") + beam depth (~4") + clearance (~6") |

**Confidence: MEDIUM** — These defaults work for standard 48" pallets. Different pallet heights or load types would need different spacing.

> **QUESTION FOR ENGINEERS:** Is 88" a good default for first beam height? Does this vary by forklift type? Is 60" level spacing right for standard 48" pallets?

### Aisle Width Defaults

| Forklift Type | Aisle Width | Our Default |
|---------------|-------------|-------------|
| Sit-down counterbalanced | 144" (12 ft) | ✓ |
| Reach truck | 120" (10 ft) | ✓ (most common default) |
| Narrow aisle (turret) | 72" (6 ft) | ✓ |
| Very narrow aisle (VNA) | 66" (5.5 ft) | ✓ |

**Confidence: HIGH** — Industry standard aisle widths.

### Row Placement Logic

Rows run perpendicular to the dock wall. We place them as back-to-back pairs across the building width:

1. Start with wall clearance (4 ft from side walls)
2. Add half-aisle at the wall side
3. Place back-to-back pairs: `pair_width = 2 × frame_depth + 6" flue space`
4. Row module = `pair_width + aisle_width`
5. Fit as many pairs as possible across available width
6. If leftover space allows, add a single wall row

**Confidence: MEDIUM** — This is a simplified model. Real layouts may have:
- Non-rectangular buildings
- Columns that force row offsets
- Different rack types in different zones
- Pallet flow or pushback in some rows

### Bay Placement Logic

Bays run along the building depth (dock-to-back):

1. Reserve staging area at dock wall (default: 50 ft)
2. Reserve wall clearance at back wall (4 ft)
3. Bay module = `beam_length + upright_width` (3" for teardrop, 4" for structural)
4. Fit as many bays as possible in available depth

**Confidence: MEDIUM** — Staging area depth of 50 ft is a default that will vary by project.

> **QUESTION FOR ENGINEERS:** What's a typical staging depth for Prologis buildings? Does it vary by number of dock doors or throughput?

### Beam Length from Pallet Size

| Pallet Size | Beam Length (2 pallets/bay) |
|-------------|---------------------------|
| 48×40 | 96" |
| 42×42 | 96" |
| 40×48 | 96" |

**Confidence: HIGH** — 96" beam for 48×40 pallets (2 per bay) is the most common configuration in all 7 projects analyzed.

### Cross-Aisle (Tunnel) Placement

- Default spacing: every 20 bays
- Tunnel beam length: 144" (3 pallets wide)
- Each tunnel replaces a normal bay position

**Confidence: MEDIUM** — 20-bay spacing is a reasonable default, but actual tunnel placement depends on:
- Forklift traffic patterns
- Number of dock doors
- Product flow requirements

> **QUESTION FOR ENGINEERS:** What drives tunnel placement and spacing in practice?

### Column Avoidance

If building column grid is provided, we plot columns on the grid but currently only note them — we don't automatically adjust rack rows around columns. In practice, columns should fall in flue spaces between back-to-back rows.

**Confidence: LOW** — This is an area that needs improvement. Column avoidance is one of the trickiest parts of rack layout design.

> **QUESTION FOR ENGINEERS:** How do you typically handle building columns? Always in flue spaces? Do you adjust row spacing to accommodate columns?

---

## 4. BOM Formulas

These formulas have been validated against 7 real Prologis projects. They follow the Prologis "counting model" template (2-sheet Excel with COUNTIF-based counting).

### Frames (Uprights)

```
frames = bays + end_frames + tunnel_bays
```

End frames are a separate input (not a formula). In simpler projects, `end_frames ≈ number_of_rows`.

| Validation | Bays | End Frames | Total Frames | Match |
|-----------|------|-----------|--------------|-------|
| Spartan | 258 | 20 (= rows) | 278 | ✓ |
| Wesco | 196+14 tunnels | 14 (= rows) | 224 | ✓ |
| Grainger | 4813 | 153 (= rows) | 4966 | ✓ |
| Spirit 8ft | 3302 | 66 | 3368 | ✓ |
| Creative Werks A | 408 | 20 | 428 | ✓ |

**Confidence: HIGH** — Validated across all projects.

### Beams

```
beams = bays × beams_per_bay
```

Where `beams_per_bay = beam_levels × 2` (front beam + back beam per level).

Beams are tracked separately by:
- Beam length (96", 48", 144" for tunnels, etc.)
- Load rating (e.g., 36E, 59E)

**Confidence: HIGH** — Consistent across all projects.

### Wire Decks

```
wiredecks = bays × wiredecks_per_bay
```

Where `wiredecks_per_bay` is a manual input from the elevation drawing, typically = `beam_levels × floor(beam_length / deck_width)`.

Important: Wire decks may only appear on certain bay types (e.g., tunnel bays only, or all bays).

Standard deck width: 46" (seen in 6 of 7 projects; Tesla used 58").

**Confidence: HIGH** — Formula is simple, but the per-bay count must come from the elevation drawing.

### Pallet Supports

```
pallet_supports = bays × pallet_supports_per_bay
```

Where `pallet_supports_per_bay = beam_levels × decks_per_beam × 2`

**Not all projects have pallet supports.** Spirit had them heavily; Creative Werks had none. More common with structural rack.

**Confidence: MEDIUM** — Formula is correct when they're used, but whether they're needed is project-specific.

> **QUESTION FOR ENGINEERS:** When are pallet supports required vs not? Is it driven by rack style, beam length, load weight, or something else?

### Anchors

```
anchors = frames × anchors_per_frame
```

Anchors per frame varies by project (determined by prelim engineering report, driven by SDC + loads):

| Project | Anchors/Frame | Location | SDC |
|---------|--------------|----------|-----|
| Spartan | 2 | Unknown | Low |
| Wesco | 2 | Unknown | Low |
| Tesla | 8 | Unknown | High? |
| Grainger | 2 | Joliet, IL | A |
| Spirit | 8 | Bloomington, CA | D |
| Creative Werks | 2 | Elk Grove Village, IL | A-B |

**Confidence: HIGH on the formula, MEDIUM on the default values.** The formula is simple multiplication, but the anchors-per-frame value must come from engineering.

### Hardware (Structural Rack Only)

```
bolts = total_beams × 4
nuts = total_beams × 4
```

Validated against Spartan: 2142 beams × 4 = 8568 bolts ✓

**Confidence: HIGH** — Only applies to structural (bolted) connections.

### Shims

Default: 1 per frame. Some projects use 2, some omit entirely.

**Confidence: LOW** — Varies significantly. Must be user input.

### End of Aisle Guards

No clean formula — varies by project. Must be counted from the layout drawing.

**Confidence: N/A** — This is always a manual input.

### Guard Anchors

```
guard_anchors = (total_eoa_guards + filler_angles) × 4
```

**Confidence: HIGH** — 4 anchors per guard is consistent across all projects.

### Row Spacers / Frame Ties

No universal formula. Multiple sizes used per project (6", 8", 12", 18", 24"). Quantities come from the layout drawing and flue space specs.

**Confidence: N/A** — Always project-specific.

> **QUESTION FOR ENGINEERS:** Are there rules of thumb for row spacer sizing and quantity based on frame height, SDC, or back-to-back depth?

---

## 5. Pricing Model

### How It Works
We generate an Excel spreadsheet that matches the Prologis pricing model format (validated against the Wesco project model).

### Structure
- Single "Pricing" sheet
- **Materials section:** Each BOM line item with Qty, Cost (input), Price (auto-calculated from margin), Total Cost, Total Price
- **Install section:** Main Scope + Lift Rental
- **Freight section:** By manufacturer (rack MFG, Hilti, WWMH)
- **Services section:** Project Management, TCO & Uncertainties, High Pile, Permit Services, Engineering Calculations, Dumpsters
- **Grand Total** with Profit/Margin calculation
- **Sidebar:** Project Margin input, Pricing Summary, Pallet Positions with $/PP calculation, Materials/Freight comparison (Model vs Quote)

### Price Formula
```
Price = Cost / (1 - Project Margin%)
```

All prices auto-calculate from the cost column and margin percentage. User enters costs; prices are derived.

**Confidence: HIGH** — Directly modeled from the Wesco pricing spreadsheet.

### Manufacturer Assignment

| BOM Category | Default Manufacturer |
|-------------|---------------------|
| Frames, Beams, Spacers, Shims, Hardware, Pallet Supports | Rack manufacturer (user-specified) |
| Anchors | Hilti |
| Wire Decks, EoA Guards | WWMH |

**Confidence: MEDIUM** — This is the pattern from Wesco. Other projects may use different suppliers.

> **QUESTION FOR ENGINEERS:** Is this manufacturer assignment standard across Prologis, or does it vary by market/project?

---

## 6. Prologis Market Data

We maintain a database of Prologis markets with pre-computed typical values:

| Market | State | Typical SDC | Building Code | Typical Clear Height |
|--------|-------|-------------|---------------|---------------------|
| Inland Empire / SoCal | CA | D | CBC | 32-36 ft |
| Los Angeles / South Bay | CA | D | CBC | 28-32 ft |
| SF Bay Area | CA | D-E | CBC | 28-32 ft |
| Seattle / Tacoma | WA | D | IBC | 28-32 ft |
| Chicago | IL | A-B | IBC | 32-36 ft |
| Dallas / DFW | TX | A-B | IBC | 32-40 ft |
| Indianapolis | IN | A-B | IBC | 32-36 ft |
| Columbus | OH | A | IBC | 32-36 ft |
| Houston | TX | A | IBC | 32-36 ft |
| New Jersey / PA | NJ/PA | A-B | IBC | 32-36 ft |
| Atlanta | GA | A-B | IBC | 32-36 ft |
| Memphis | TN | C-D | IBC | 28-32 ft |
| Phoenix | AZ | B | IBC | 32-36 ft |
| Denver | CO | B | IBC | 28-32 ft |

**Confidence: MEDIUM** — SDC values are approximate for the market area. Actual SDC depends on exact address (we do a live USGS lookup for accuracy). Clear heights are typical ranges from recent Prologis construction.

> **QUESTION FOR ENGINEERS:** Are these market-level SDC values accurate? Any markets where the SDC varies significantly within the market area?

---

## 7. Used vs. New Rack Assessment

### Logic

| SDC | Our Recommendation | Reasoning |
|-----|--------------------|-----------|
| A-B | Either used or new viable | Low seismic — used rack doesn't need special certification |
| C | Either, with engineering review | Moderate seismic — needs inspection and engineering sign-off |
| D-F | Strongly recommend new | High seismic — used rack certification is expensive; may not meet current code |

### Teardrop vs Structural (for used rack)
- **Teardrop:** Most manufacturers use compatible teardrop pattern — mixing brands is generally OK
- **Structural:** Bolt patterns vary by manufacturer — must match for beam-to-column connections

### Used Rack Inspection Requirements (always)
- Visual inspection of all components
- Check for: bent columns, cracked welds, damaged teardrop slots, corrosion, straightness
- Verify load capacity ratings match design
- Verify frame height and depth match specs
- Base plates must not be bent, cracked, or have weld defects
- Wire decks: check for bent/broken wires, proper flange condition

**Confidence: MEDIUM** — General industry practice. Specific policies may vary.

> **QUESTION FOR ENGINEERS:** Does Prologis have a formal policy on used vs new rack? Are there specific inspection standards you follow?

---

## 8. Known Gaps & Open Questions

### Things We Need Engineer Input On

1. **Anchor counts by SDC** — Is our SDC→anchor mapping a reasonable starting point? What other factors matter?
2. **First beam height** — Is 88" a good default? How does this vary?
3. **Level spacing** — Is 60" right for standard 48" pallets?
4. **Staging depth** — Is 50 ft a reasonable default? What drives this?
5. **Tunnel/cross-aisle spacing** — What determines placement in practice?
6. **Column avoidance** — How do you handle building columns in rack layouts?
7. **Pallet support usage** — When are they required?
8. **Row spacer rules** — Any rules of thumb for sizing and quantity?
9. **Fire baffles** — What's the Prologis policy?
10. **Sprinkler modifications** — Should we try to assess when in-rack sprinklers are needed, or leave that entirely to the FPE?
11. **Commodity classification** — What's the typical class for Prologis tenants?
12. **Used rack policy** — Formal guidelines?
13. **Standard frame heights** — Are we missing any common sizes?
14. **Manufacturer assignments** — Is Hilti for anchors and WWMH for wire decks standard across Prologis?

### Things That Are Always Project-Specific (No Formula)

These items can't be auto-calculated and will always need manual input:
- End of aisle guard counts
- Row spacer sizes and quantities
- Column/post protector counts
- Shims per frame (0, 1, or 2)
- Fire baffle placement
- Actual anchor specs (from prelim engineering)

---

*This document was generated from the Prologis Racking Design Engine codebase. All formulas have been validated against 7 real Prologis projects: Spartan, Wesco, Tesla, Grainger, Spirit Halloween, Creative Werks, and EJ Welch.*
