# BOM Examples Analysis

## Example 1: Wesco
- **Single bay type** (A only)
- **196 bays** @ 96" + 14 tunnels @ 144"
- **2,044 pallet positions**, 14 rows
- **Rack type:** Teardrop (Mecalux)
- **Frame height:** 20'
- **Frame depth:** 42"

### BOM Components:
| Component | QTY | Notes |
|---|---|---|
| Teardrop Frames 20'x42" \|313 | 196 | Main frames |
| Teardrop Frames 20'x42" \|312 | 28 | Tunnel/end frames? |
| Teardrop Beams 96" \|40E | 1,568 | Standard beams |
| Teardrop Beams 144" \|65Q | 56 | Tunnel beams |
| Step Wiredecks 42"x46" | 1,652 | |
| Row Spacers 12" | 276 (336 col A?) | |
| Row Spacers 18" | 60 | |
| Anchors 1/2"x4" HUS-EZ | 448 | |
| Shims | 224 | |
| Column Protectors 24" | 168 | V-Nose |
| End of Aisle Guard Right 42" | 28 | |
| End of Aisle Guard Left 42" | 28 | |
| Anchors 3/4"x4.5" HUS-EZ | 460 | For guards/protectors |
| Guard Rail 42" Posts | 17 | |
| Guard Rail 10' Rails | 26 | |
| Building Column Protector 8"x8" | 1 | |

---

## Example 2: Tesla
- **4 bay types:** A, B, C, P
- **1,144 bays** @ 120" (no tunnels)
- **12,374 pallet positions**, 55 rows
- **Rack type:** Teardrop (Mecalux)
- **Frame height:** 28'
- **Frame depth:** 48"
- **Split across 2 suites** (Suite 100 + Suite 101)

### BOM Components (Total):
| Component | A | B | C | P | Total |
|---|---|---|---|---|---|
| Frames 28'x48" \|4B102 | 129 | 71 | 53 | 946 | 1,199 |
| Beams 120" \|40E | 1,230 | 660 | 530 | 7,216 | 9,636 |
| Beams 120" \|36E | - | 132 | 318 | - | 450 |
| Beams 120" \|27E | - | - | - | - | 0 (top-level) |
| Step Wiredecks 48"x58" | - | - | - | - | 10,086 |
| Rowspacers 12" | - | - | - | - | 2,344 |
| Anchors 1/2"x4" KwikBolt | 1,032 | 568 | 424 | 7,568 | 9,592 |
| Fire Baffles 48"x120" | - | - | - | 902 | 902 |
| Fire Baffles Tek Screws | - | - | - | - | 1 (box?) |

### Suite 100 vs Suite 101:
- Suite 100: 1,066 bays, 11,168 positions, 52 rows — uses different frame code for B/C
- Suite 101: 78 bays, 1,206 positions, 3 rows — uses B/C rack frame variant

### Key Observations:
- Tesla uses "B/C RACK" variant frames in sub-BOMs but not in top-level totals
- Different beam types (40E, 36E, 27E) map to different bay types
- Fire baffles only on P type (push-back? or other config)
- Wiredecks and rowspacers are totals only (not broken by bay type)

---

## Patterns Across All 3 Examples (Spartan + Wesco + Tesla)

### Common BOM Components:
1. **Frames** (uprights) — sized by height x depth, with MFG part numbers
2. **Beams** — sized by length, with load capacity codes
3. **Wiredecks** — sized by depth x width (step or flanged)
4. **Row Spacers** — various lengths (8", 12", 18")
5. **Anchors** — for frames (1/2") and for guards (3/4")
6. **Shims** — typically 1 per anchor point

### Variable Components:
- **End of Aisle Guards** (left/right)
- **Guard Rails** (posts + rails)
- **Column Protectors** (V-nose or building column)
- **Fire Baffles** (Tesla only — likely code-driven for taller/deeper configs)
- **Pallet Supports** (Spartan only — structural rack specific)

### Rack Types:
- **Spartan:** Structural rack (beams welded/bolted, different from teardrop)
- **Wesco:** Teardrop (Mecalux) — standard selective
- **Tesla:** Teardrop (Mecalux) — standard selective, multiple bay types

### Count Derivation Patterns:
- Frames = (bays + 1) per row (sharing uprights between bays), but varies
- Beams = bays × beam_levels_per_bay
- Wiredecks = typically matches beam pairs (1 deck per beam level per bay)
- Anchors = 2 per frame × number of frames (4 bolts per base plate)
- Shims = 1 per frame typically
