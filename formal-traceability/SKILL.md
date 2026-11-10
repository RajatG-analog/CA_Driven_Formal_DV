---
name: formal-traceability
description: Formal spec-to-proof traceability and sign-off — req_extraction.csv, property-to-requirement mapping, per-config proof results, signoff_matrix.csv, completeness audit, optional Jama/Confluence publish. Use when the user asks for formal traceability, sign-off matrix, unmapped requirements or orphan properties.
---

# Formal Traceability — Spec-to-Proof Requirement Tracking & Sign-Off

## When to Use
- Extract spec requirements from a PDF into a structured CSV
- Map every formal property (assert/assume/cover) back to a spec requirement
- Generate a sign-off matrix with per-config proof status
- Populate Jama items with formal verification proof status (via MCP)
- Update Confluence with traceability tables (via MCP)
- Audit traceability completeness — find unmapped requirements or orphan properties
- Produce coverage-to-requirement roll-up for sign-off reviews

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| Spec PDF | IP specification document | `control_port_spec.pdf` |
| Top module | DUT top-level module name | `sram_top_scan_wrapper` |
| Property files | All SVA files in `props/` or `sva/` | `props/sram_ahb_ctl_props.sv` |
| Assumption files | All assumption SVA files | `props/sram_assumptions.sv` |
| Bind files | All bind statements | `props/sram_abvip_bind.sv` |
| JG proof results | JasperGold HTML/RPT exports or CSV dumps | `results/summary_default.csv` |
| Output directory | Where traceability files go | `fpv_env/traceability/` |
| Jama project ID | (Optional) For MCP Jama updates | `42` |
| Confluence space | (Optional) For publishing results | `IPCOE` |

## Step-by-Step Procedure

### Step 1: Extract Spec Requirements → `req_extraction.csv`

- Read the spec PDF cover-to-cover.
- For every testable statement, behavioral rule, timing constraint, reset value, error condition, or protocol requirement, create a row with a unique `SPEC-ID`.

- **CRITICAL**:
  - Read each spec section with the View / queryFileWithEmbeddings tool BEFORE writing the corresponding rows.
  - Never invent requirements without reading the source text.

- **CSV format** — 6 columns, UTF-8, double-quote text fields containing commas:

```csv
SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes
SPEC-001,§2.1 Interfaces,PROTO,"AHB HREADY must be asserted within 16 cycles of HTRANS != IDLE",YES,Bounded liveness
SPEC-002,§2.1 Interfaces,PROTO,"APB PSLVERR asserted for unmapped address range",YES,Error path
SPEC-003,§3.1 Reset,RESET,"All outputs deassert within 1 cycle of reset assertion",YES,Async reset
SPEC-004,§4.2 DFT,DFT,"Scan mode forces all clock muxes to test clock",ASSUME,Assumption of Use
```

- **SPEC-ID naming**:
  - `SPEC-NNN` sequential, zero-padded to 3 digits.
  - Start at 001.

**Category taxonomy** — use exactly these values:

| Category | Meaning |
|----------|---------|
| `RESET` | Reset behavior, initial values, power-on state |
| `PROTO` | Protocol compliance (AHB, APB, SPI, I2C, etc.) |
| `FUNC` | Functional behavior (FSM, data path, control logic) |
| `ERROR` | Error detection, reporting, injection, recovery |
| `REG` | Register map, CSR fields, read/write behavior |
| `CLK` | Clock gating, clock muxing, frequency constraints |
| `DFT` | Design-for-test, scan, BIST, test mode |
| `TIMING` | Cycle-accurate timing, latency, throughput |
| `INTEG` | Integration-level, interrupt, trigger, DMA |
| `ECC` | Error correction/detection codes |
| `INIT` | Initialization sequences, boot, self-test |
| `SEC` | Security, lock, protection, access control |

**Formally_Verifiable values**:

| Value | Meaning |
|-------|---------|
| `YES` | Can be encoded as an SVA assertion |
| `ASSUME` | Becomes a formal assumption (spec Assumption of Use) |
| `COVER` | Verified via cover property (scenario existence) |
| `NO` | Not formally verifiable (analog, package-level, system) |
| `PARTIAL` | Partially verifiable — note which part in Notes column |
| `CSR` | Verified via Jasper CSR checker (register map) |
| `CONN` | Verified via Jasper connectivity checker |

**Quality rules for requirement extraction**:
- One requirement per row — do NOT combine multiple behaviors
- Quote the spec text faithfully — paraphrase only if the original is excessively long
- Include section number (§X.Y.Z) for every requirement
- Flag ambiguous spec language in Notes: "Spec unclear — assumed X"
- Count: a typical 50-page spec yields 80-150 requirements; 100+ pages yields 150-300+

### Step 2: Extract Property Labels from SVA Files

- For every SVA file, extract all property labels using this pattern:

```
assert property (@(posedge clk) ...) LABEL;
cover property (@(posedge clk) ...) LABEL;
assume property (@(posedge clk) ...) LABEL;
```

- Also capture labels from named properties:
```
property p_LABEL; ... endproperty
ast_LABEL: assert property (p_LABEL);
```

- Record for each property:
- `Property_Label` — the assertion/cover/assume label (e.g., `ast_D01_write_data`)
- `Property_Type` — `ASSERT`, `ASSUME`, or `COVER`
- `Property_File` — filename (e.g., `sram_ahb_ctl_props.sv`)
- `Bind_Target` — the module this is bound to (from bind statements)
- `Config` — which parameter configs this property is active for (`ALL`, or specific config names; check `generate if` guards)

- **CRITICAL**: Use grep to count properties per file and cross-check:
```
grep -c "assert property" props/*.sv
grep -c "cover property" props/*.sv
grep -c "assume property" props/*.sv
```

### Step 3: Map Properties to Requirements → `formal_traceability.csv`

- Create the mapping CSV linking every SPEC-ID to its formal property.

- **CSV format** — 7 columns:

```csv
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
SPEC-010,ASSERT,ast_D01_write_data,sram_ahb_ctl_props.sv,sram_ahb_ctl,ALL,MAPPED
SPEC-010,ASSERT,ast_D02_write_resp,sram_ahb_ctl_props.sv,sram_ahb_ctl,ALL,MAPPED
SPEC-042,ASSUME,asm_01_dft_inactive,sram_assumptions.sv,sram_top_scan_wrapper,ALL,MAPPED
INFRA-001,ASSERT,ast_xprop_hready,sram_misc_props.sv,sram_top_scan_wrapper,ALL,INFRA
INFRA-009,ASSERT,ast_SCB01_write_integrity,sram_scoreboard.sv,sram_ctl_top,ALL,INFRA
```

**Status values**:

| Status | Meaning |
|--------|---------|
| `MAPPED` | Spec requirement directly mapped to a formal property |
| `INFRA` | Infrastructure property not from spec (xprop, scoreboard, ABVIP) |
| `CSR` | Mapped via Jasper CSR checker |
| `CONN` | Mapped via Jasper connectivity checker |
| `UNMAPPED` | Spec requirement with NO corresponding property — **GAP** |
| `WAIVED` | Requirement waived with justification |
| `N/A` | Not applicable for formal (analog, package-level) |

**Mapping rules**:
- One SPEC-ID can map to MULTIPLE properties (1:N) — one row per property
- Every ASSERT and ASSUME must map to at least one SPEC-ID
- Infrastructure properties (xprop, scoreboard, ABVIP protocol) use `INFRA-NNN` IDs
- COVER properties are companions — they share the SPEC-ID of their parent ASSERT
- If a property has a `generate if (PARAM)` guard, set Config to the specific config name

**Gap analysis**: After mapping, scan for:
1. `UNMAPPED` SPEC-IDs → requirements with no formal coverage (must add properties or waive)
2. Orphan properties → assertions with no SPEC-ID (must trace back or mark INFRA)

### Step 4: Collect Proof Results per Configuration

- For each JasperGold run (one per parameter config), collect the proof status of every assertion.
- Sources (in priority order):

1. **JG HTML report** — parse `report_<config>.html` for proven/CEX/bounded/undetermined
2. **JG RPT file** — `jg_report.rpt` text export
3. **JG CSV export** — if available from `report -csv`
4. **Manual extraction** — read JG TCL log for `prove -all` results

- Record per-property, per-config status:

| Proof Status | Meaning |
|-------------|---------|
| `PROVEN` | Unbounded proof — property holds for all reachable states |
| `BOUNDED_N` | Proven up to N cycles — may need deeper engine or abstraction |
| `CEX` | Counter-example found — requires RCA classification |
| `UNDETERMINED` | Engine timeout — needs investigation |
| `INACTIVE` | Property disabled for this config (generate-if guard) |
| `WAIVED` | Waived with justification |

### Step 5: Generate Sign-Off Matrix → `signoff_matrix.csv`

- Aggregate per-config proof results into a sign-off matrix.

- **CSV format** — one row per config:

```csv
Config,Total_Assertions,Proven,Bounded,CEX,Undetermined,Waived,Inactive,Proof_Rate,Covers_Total,Covers_Hit,Cover_Rate,Assumptions,Assumption_Conflicts,Sign_Off
default,88,85,0,2,0,1,0,96.6%,93,89,95.7%,9,0,CONDITIONAL
ecc_disabled,72,72,0,0,0,0,16,100%,77,74,96.1%,9,0,PASS
rom_mode,65,65,0,0,0,0,23,100%,70,68,97.1%,9,0,PASS
```

**Sign_Off decision logic**:

| Condition | Sign_Off Value |
|-----------|---------------|
| Proof_Rate ≥ 95% AND CEX = 0 AND Assumption_Conflicts = 0 | `PASS` |
| Proof_Rate ≥ 95% AND CEX > 0, all classified as WAIVED/EXPECTED | `CONDITIONAL` |
| Proof_Rate < 95% OR unresolved CEX | `FAIL` |
| Any UNDETERMINED > 0 | `REVIEW` |

### Step 6: Traceability Completeness Audit

- Run a systematic audit and report gaps:

**6a. Forward trace** (Spec → Property):
```
For every SPEC-ID in req_extraction.csv where Formally_Verifiable = YES:
  → Must have at least one row in formal_traceability.csv with Status = MAPPED
  → Flag any SPEC-ID with Status = UNMAPPED
```

**6b. Reverse trace** (Property → Spec):
```
For every property label in SVA files:
  → Must appear in formal_traceability.csv
  → Flag orphan properties (in SVA but not in traceability CSV)
```

**6c. Config coverage**:
```
For every SPEC-ID mapped to a property with Config != ALL:
  → Verify property is active in at least one config
  → Flag SPEC-IDs only covered in disabled configs
```

**6d. Proof completeness**:
```
For every MAPPED property:
  → Must have a proof result in signoff_matrix or per-config results
  → Flag properties with no proof attempt
```

Generate audit summary:
```
Traceability Audit Summary
===========================
Total spec requirements:     158
  Formally verifiable (YES): 142
  Assumptions (ASSUME):        8
  Not verifiable (NO):         8

Forward trace:
  MAPPED:                    140 / 142 (98.6%)
  UNMAPPED (gaps):             2 — SPEC-087, SPEC-134

Reverse trace:
  Total properties:          181
  Traced to SPEC-ID:         173
  Infrastructure (INFRA):      8
  Orphan (no SPEC-ID):         0

Config coverage:
  Properties active in ALL:  165
  Config-specific:            16
  Config gaps:                 0

Proof completeness:
  All configs run:           YES
  Unproven properties:         0
```

### Step 7: Update Jama Items (Optional — via MCP)

If a Jama project is configured, update requirement items with formal proof status:

1. Search Jama for each SPEC-ID using `mcp-jama_search_items`
2. For matched items, update the verification status field using `mcp-jama_update_item`
3. Record the Jama Item ID in the traceability CSV (add `Jama_ID` column)

**Jama field mapping**:
```
Proof Status PROVEN     → Jama: "Formally Verified — Proven"
Proof Status BOUNDED    → Jama: "Formally Verified — Bounded (N cycles)"
Proof Status CEX+WAIVED → Jama: "Formally Verified — Waived (justification)"
Proof Status UNMAPPED   → Jama: "Formal — Not Yet Mapped"
```

### Step 7b: Generate AoU Traceability → `aou_traceability.csv`

Every Assumption of Use (AoU) from the spec must be tracked separately from
req_extraction.csv because AoU items require additional metadata: the Part F
category, the anti-vacuity cover, and a justification linking to the spec.

**CSV format** — 12 columns:

```csv
AOU_ID,Spec_Section,AoU_Text,Part_F_Category,Assumption_Label,Assumption_File,Assume_Expression,Anti_Vacuity_Cover,Config,Jama_Item_ID,Justification,Status
AOU-001,§5.2 Integration,Scan mode inactive during functional operation,Cat1_DFT,ASM_001_scan_mode_off,sram_assumptions.sv,scan_mode == 1'b0,cov_ASM_001,ALL,,Spec §5.2: All scan inputs tied to 0,MAPPED
AOU-002,§3.1 Reset,De-assertion of HRESETn synchronous to HCLK,Cat2_Reset,ASM_010_resetn_monotonic,sram_assumptions.sv,HRESETn |=> HRESETn,cov_ASM_010,ALL,,Spec §3.1: monotonic deassertion,MAPPED
AOU-003,,ATE_en is static during operation,Cat3_Static,ASM_030_ATE_en_stable,sram_assumptions.sv,$stable(ATE_en),cov_ASM_030,ALL,,Engineering: ATE configured before operation,ENGINEERING
AOU-004,,JG hready loopback for AHB-Lite,Cat4_Protocol,ASM_050_hready_loopback,sram_assumptions.sv,hready == hreadyout,cov_ASM_050,ALL,,Engineering: AHB-Lite single-slave topology,ENGINEERING
```

**AOU_ID naming**: `AOU-NNN` sequential, zero-padded to 3 digits. Start at 001.

**Part_F_Category values** — must match exactly:

| Value | Part F Category |
|-------|-----------------|
| `Cat1_DFT` | DFT / Scan mode constraints |
| `Cat2_Reset` | Reset stability / monotonic deassertion |
| `Cat3_Static` | Static configuration inputs |
| `Cat4_Protocol` | Bus protocol (APB/AHB/AXI) |
| `Cat5_Idle` | Idle protocol / mutual exclusion |
| `Cat6_ClkRatio` | Clock frequency ratio |
| `Cat7_ConstAssign` | Constant-assign model (JG engine workaround) |
| `Cat8_Feature` | Feature-specific (lock, protection, word-size) |
| `Cat9_CSR` | CSR-only additional |
| `Cat10_Scoreboard` | Scoreboard task isolation |

**Status values**:

| Status | Meaning |
|--------|---------|
| `MAPPED` | AoU item from spec has a corresponding formal assumption |
| `UNMAPPED` | AoU item identified in spec but no assumption written — **GAP** |
| `WAIVED` | AoU item waived (e.g., covered by ABVIP instead) |
| `ENGINEERING` | Assumption added beyond spec AoU (engineering rationale only) |

**Mandatory checks after populating**:
1. Every AoU from spec "Assumptions of Use" / "Integration Guidelines" → at least one MAPPED row
2. Every `assume property` in SVA files → appears in aou_traceability.csv (MAPPED or ENGINEERING)
3. Every MAPPED row has a non-empty Anti_Vacuity_Cover
4. Every ENGINEERING row has a clear rationale (not just "needed for proof")
5. `check_assumptions -conflict` returns EMPTY for all configs

**Expected counts by IP complexity**:

| IP Complexity | Spec AoU Items | Engineering | Total |
|---------------|---------------|-------------|-------|
| Simple (single-clock) | 5–10 | 3–5 | 8–15 |
| Medium (multi-protocol) | 15–25 | 8–15 | 23–40 |
| Complex (multi-clock) | 20–35 | 10–20 | 30–55 |

### Step 8: Publish to Confluence (Optional — via MCP)

Generate a Confluence page with:
- Traceability summary table (from audit in Step 6)
- Sign-off matrix table (from Step 5)
- Gap list with assigned owners
- Link to JasperGold project archive

Use `mcp-confluence_search_pages` to find existing page, then update or create.

## Traceability File Relationships

```
                    ┌─────────────────────┐
                    │   Spec PDF          │
                    │   (source of truth) │
                    └─────────┬───────────┘
                              │ Step 1
                              ▼
                    ┌─────────────────────┐
                    │ req_extraction.csv  │
                    │ SPEC-001..SPEC-NNN  │
                    └─────────┬───────────┘
                              │ Step 3
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ props/*.sv      │ │ assumptions.sv  │ │ scoreboard.sv   │
│ (ASSERT/COVER)  │ │ (ASSUME)        │ │ (INFRA ASSERT)  │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │ Step 3
                              ▼
                    ┌─────────────────────┐
                    │formal_traceability. │
                    │csv                  │
                    │ SPEC-ID → Property  │
                    └─────────┬───────────┘
                              │ Steps 4-5
                              ▼
                    ┌─────────────────────┐
                    │ signoff_matrix.csv  │
                    │ Per-config proof    │
                    │ status + sign-off   │
                    └─────────┬───────────┘
                              │ Steps 6-8
                    ┌─────────┼─────────┐
                    ▼         ▼         ▼
               ┌────────┐ ┌──────┐ ┌──────────┐
               │ Audit  │ │ Jama │ │Confluence│
               │ Report │ │ MCP  │ │ MCP      │
               └────────┘ └──────┘ └──────────┘
```

## Output Files

```
fpv_env/traceability/
├── req_extraction.csv           # SPEC-ID → requirement text (Step 1)
├── formal_traceability.csv      # SPEC-ID → property mapping (Step 3)
├── aou_traceability.csv         # AOU-ID → assumption mapping (Step 7b)
├── signoff_matrix.csv           # Per-config proof roll-up (Step 5)
└── traceability_audit.txt       # Completeness audit report (Step 6)
```

## Quality Checklist

### Requirement Extraction
- [ ] Every spec section visited — no sections skipped
- [ ] SPEC-IDs are sequential with no gaps
- [ ] Each requirement is atomic (one behavior per row)
- [ ] Category values match the taxonomy exactly
- [ ] Formally_Verifiable column is populated for every row
- [ ] Assumptions of Use explicitly tagged as `ASSUME`

### Property Mapping
- [ ] Every `YES` requirement has at least one MAPPED property
- [ ] Every assertion in SVA files appears in formal_traceability.csv
- [ ] INFRA properties use INFRA-NNN IDs (xprop, scoreboard, ABVIP)
- [ ] Config column is accurate — checked against generate-if guards
- [ ] No orphan properties (in SVA but not in CSV)
- [ ] No UNMAPPED gaps — or gaps are documented with justification

### Sign-Off Matrix
- [ ] All parameter configs have a row in signoff_matrix.csv
- [ ] Proof rates calculated correctly (Proven / (Total - Inactive - Waived))
- [ ] Cover hit rates calculated correctly
- [ ] Assumption conflict count is 0 for all configs
- [ ] Sign_Off decision follows the logic table exactly
- [ ] Waived items have justification documented

### Completeness
- [ ] Forward trace: ≥95% of YES requirements are MAPPED
- [ ] Reverse trace: 0 orphan properties
- [ ] All configs run to completion
- [ ] Audit report generated and reviewed