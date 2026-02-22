# BOM Formulas — Validated Against 6 Real Projects

Cross-referenced: Spartan (structural), Wesco (teardrop/Mecalux), Tesla (teardrop/Mecalux), Grainger (teardrop), Spirit Halloween (teardrop, multiple configs), Creative Werks (teardrop/Mecalux)

## Counting Model Architecture

The BOM creation process uses a standard **2-sheet Excel template** (confirmed from Spirit + Creative Werks counting models):

### Sheet 1: "Drawing" (named range "Canvas")
- Grid where each cell = an elevation type number (1, 2, 3...)
- Grid layout mirrors the physical warehouse layout
- Each cell represents one bay
- Back-to-back rows shown as adjacent row pairs
- Spacer counts may be calculated from the grid

### Sheet 2: "BOM"
- **Top section** (rows 5-15): Per-elevation inputs
  - Col A: Elevation # | Col B: Name | Col C: `=COUNTIF(Canvas, elevation#)`
  - Col E: EndFrame count (manual!) | Col F: `=EndFrames + BayCount`
  - Col G+: Beams per bay per size (manual per-bay counts)
  - Col M+: Wire deck count per bay | Col P: Pallet supports per bay
  - Col Q: Pallet positions per bay
- **Bottom section** (rows 19-29): Totals = `per_bay_value × $bay_count`
- **Totals row**: SUM

**The fundamental formula is just: `total = per_bay_count × number_of_bays`**

The "per bay count" values come from elevation drawings and are entered manually.

---

## Frames (Uprights)

```
frames = bays + end_frames
```

**End frames are a SEPARATE INPUT, not simply = rows.**

| Project | Bays | End Frames | Total Frames | End/Row Ratio |
|---------|------|-----------|--------------|---------------|
| Spartan | 258 | 20 (=rows) | 278 | 1.0 |
| Wesco | 196+14 | 14 (=rows) | 224 | 1.0 |
| Grainger | 4813 | 153 (=rows) | 4966 | 1.0 |
| Spirit 8ft | 3302 | 66 (~rows) | 3368 | ~1.0 |
| Spirit 8ft CM | 3062 | 67 (manual) | 3129 | — |
| Creative Werks A | 408 | 20 (manual) | 428 | — |
| Creative Werks B | 164 | 8 (manual) | 172 | — |

In simpler projects, end_frames ≈ rows. In counting models, it's explicitly entered from the layout.

**Validated:** All 6 projects ✓

## Beams

```
beams = bays × beams_per_bay
```

Where `beams_per_bay = beam_levels × 2` (front + back), entered per elevation type.

**Calculate per beam size AND load rating separately.** A project can have:
- Multiple beam lengths (Grainger: 96"+48", Spirit: 96"+48"+144")
- Multiple load ratings per bay type (Spirit: 36E+59E on 96" bays)
- Different levels for tunnels vs standard bays

In the counting model, `beams_per_bay` is a direct manual input per elevation type.

**Validated:** All 6 projects ✓

## Wire Decks

```
wiredecks = bays × wiredecks_per_bay
```

Where `wiredecks_per_bay = beam_levels × floor(beam_length / deck_width)` per elevation type.

In the counting model, this is a direct manual input column.

**Important:** Wire decks may ONLY appear on certain bay types:
- Creative Werks: wiredecks on ALL bays (3104 = beams)
- Spirit: wiredecks ONLY on tunnel bays (standard bays get pallet supports instead)
- Spartan: wiredecks on all bays (structural + flanged decks)

### Deck Width — User input

| Project | Depth | Width | Note |
|---------|-------|-------|------|
| Spartan | 44" | 46" | Flanged |
| Wesco | 42" | 46" | Step |
| Tesla | 48" | 58" | Outlier |
| Grainger | 48" | 46" | |
| Spirit | 42" | 46" | |
| Cr. Werks | 42" | 46" | |

Default 46". Tesla's 58" is the only exception seen.

## Pallet Supports

```
pallet_supports = bays × pallet_supports_per_bay
```

Where `pallet_supports_per_bay = beam_levels × decks_per_beam × 2`

| Project | Per Bay | Derivation |
|---------|---------|-----------|
| Spartan 92" | ~2 per wiredeck | structural, = wiredecks × 2 |
| Spirit 96" | 12 | = 3 levels × 2 decks × 2 |
| Spirit 48" | 6 | = 3 levels × 1 deck × 2 |
| Spirit 144" | 30 | = 5 levels × 3 decks × 2 |
| Creative Werks | 0 | None listed (teardrop, no pallet supports) |

In the counting model, this is a direct manual input column (Col P).

**Not all projects have pallet supports.** Spirit has them heavily; Creative Werks has none.

## Anchors (Frame Anchors)

```
anchors = frames × anchors_per_frame
```

| Project | Depth | Anch/Frame | Size | Location |
|---------|-------|-----------|------|----------|
| Spartan | 44" | 2 | 1/2"×4" | — |
| Wesco | 42" | 2 | 1/2"×4" | — |
| Tesla | 48" | 8 | 1/2"×4" | — |
| Grainger | 48" | 2 | 1/2"×4" | Joliet IL |
| Spirit | 42" | 8 | 5/8"×5" | Bloomington IL |
| Cr. Werks | 42" | 2 | 1/2"×4" | Elk Grove Village IL |

**NOT depth-driven, NOT rack-style-driven.** Spirit and Creative Werks are both 42" teardrop in Illinois but use 2 vs 8. Likely engineer/seismic spec. **Must be user input. Anchor size also varies.**

## Shims

| Project | Shims | Pattern |
|---------|-------|---------|
| Spartan | 556 | 2 per frame (= 1 per anchor) |
| Wesco | 224 | 1 per frame |
| Spirit | 3368 | 1 per frame |
| Cr. Werks | — | Not listed |

**Default: 1 per frame. Some projects omit entirely.**

## End of Aisle Guards

| Project | Per Side | Rows | Ratio |
|---------|----------|------|-------|
| Spartan | 20 | 20 | 1.0 |
| Wesco | 28 | 14 | 2.0 |
| Spirit 8ft | 186 | 66 | 2.82 |
| Spirit 12ft | 108 | 36 | 3.0 |
| Cr. Werks | 20 | 14 | 1.43 |

**No clean formula.** Must be user input or extracted from layout.

## Guard Anchors (3/4")

```
guard_anchors_3_4 = (total_eoa_guards × 4) + (filler_angles × 4)
```

| Project | 3/4" Anchors | Breakdown |
|---------|-------------|-----------|
| Spartan | 160 | 40 guards × 4 |
| Spirit 8ft | 1488 | 372 guards × 4 |
| Cr. Werks | 260 | 40 guards × 4 + 25 fillers × 4 |

**4 anchors per guard/filler is consistent across all projects.**

## Row Spacers / Frame Ties

**Layout-specific. Multiple sizes, no universal formula.**

| Project | 6" | 8" | 12" | 18" | 24" |
|---------|-----|-----|------|------|------|
| Spartan | — | 168 | — | 186 | — |
| Wesco | — | — | 276 | 60 | — |
| Tesla | — | — | 2344 | — | — |
| Grainger | — | — | 1305 | 222 | 5580 |
| Spirit 8ft | — | — | 5052* | — | — |
| Spirit 12ft | — | — | 3112 | — | — |
| Cr. Werks | 384 | 387 | 129 | 258 | — |

*Spirit 8ft calls them "Frame Ties" instead of "Row Spacers"

Sizes come from layout drawing flue space specs. Counts vary by project.

## Column/Post Protectors

Layout-specific. Counted from the floor plan.

| Project | V-Nose | Guard Posts | Rails | Filler Angles |
|---------|--------|------------|-------|---------------|
| Wesco | 168 | 17 | 26 | — |
| Cr. Werks | 386 | — | — | 25 |

## Hardware (Structural Only)

```
bolts = total_beams × 4
nuts = total_beams × 4
```

**Validated:** Spartan ✓ (8568 = 2142 × 4)

## Pallet Stops

Only seen on Spirit. Per-bay count from elevation.
- Selective: Double 12" pallet stops
- Pallet Flow: Single 3" offset pallet stops

## Fire Baffles

Only seen on Tesla P-type (1 per bay). Code/height-driven.

---

## Summary: Counting Model Inputs

The tool should collect these inputs per elevation type:

| Input | Source | Notes |
|-------|--------|-------|
| Bay count | Drawing grid / COUNTIF | Core input |
| End frame count | Manual from layout | ≈ rows, but varies |
| Beams per bay per size | Elevation drawing | Per beam length + load rating |
| Wire decks per bay | Elevation drawing | May be 0 for non-tunnel bays |
| Pallet supports per bay | Elevation drawing | May be 0 |
| Pallet positions per bay | Elevation drawing | For summary |
| Anchors per frame + size | Engineer spec | 2 or 8, varies |
| Shims per frame | Project spec | 0-2 |
| EoA guard count | Layout | No formula |
| Row spacer sizes + counts | Layout flue specs | No formula |
| Column protectors | Layout | No formula |
