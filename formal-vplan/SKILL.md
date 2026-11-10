---
name: formal-vplan
description: Generate a spec-driven Cadence vManager .vplanx for formal verification from an IP spec. Use when the user asks to create a formal vplan/vplanx or a vManager verification plan for an IP.
---

# Formal Verification VPlan Creation Skill

## When to Use
Activate this skill when the user asks to:
- Create a vplan / vplanx for formal verification
- Generate a Cadence vManager verification plan from a spec / PDF
- Build a VPlan from IP specification documents
- Create a formal verification plan for an IP block

## Overview
- This skill generates a Cadence vManager-compatible `.vplanx` file (gzip-compressed XML) by extracting verification requirements directly from an IP specification document (PDF).
- The output is loadable in vManager Planner (toolVersion 23.09).
- The vplan is **spec-driven** — requirements come from the spec, NOT from existing assertions.
- This ensures the vplan captures what SHOULD be verified, not just what HAS been verified.

## Inputs Required
- Gather these from the user before generating:

| Input | Description | Example |
|-------|-------------|---------|
| **Spec PDF** | IP specification document (PDF) | `ADIP_SRAM_Controller.pdf` |
| **IP Name** | Design/IP name for the vplan | `ADIP_SRAM_Controller` |
| **Top Module** | Formal top module (FML_INSTTOP) | `sram_top_scan_wrapper` |
| **Owner** | Engineer name for vplan ownership | `rgulghan` |
| **vManager Settings** | Server, project, port | See template below |

## Step-by-Step Procedure

### Step 1: Read the Spec PDF
1. Use `View` or `queryFileWithEmbeddings` to find the table of contents
2. Identify all feature areas: interfaces, protocols, datapaths, FSMs, registers, error handling, modes, resets, clocking, interrupts, test/debug features
3. Read each section systematically — do NOT skip sections
4. For long PDFs, read in chunks of 500-2000 lines, extract requirements, then continue

### Step 2: Extract Requirements from Each Spec Section
For every spec statement that describes a behavior, timing, value, or constraint, create a verification item with:
- **Requirement ID**: `SPEC-NNN` sequential numbering
- **Category**: Which feature area it belongs to
- **Requirement Text**: The exact spec language or a precise paraphrase
- **Formally Verifiable**: YES / ASSUME / NO
  - YES = can be checked with an SVA assertion
  - ASSUME = integration constraint (assumption of use)
  - NO = cannot be formally verified (e.g., analog behavior, performance)
- **Verification Criteria**: What EXACTLY must be checked — specific signals, values, timing, conditions. NEVER be vague.

- **CRITICAL**: Be exhaustive.
  - Every behavioral statement in the spec is a potential vplan item.
  - Read EVERY section before generating items.
  - Do not summarize or skip "obvious" requirements.

### Step 3: Organize into Sections
Group requirements into logical feature sections based on the spec structure:

```
Formal Assertions/
├── Protocol (AHB/AXI/APB interface checks)
├── Datapath (encode, decode, data integrity)
├── Control (FSM, sequencing, initialization)
├── Interrupt & Status (error flags, counters, W1C)
├── Configuration (mode selection, protection keys)
├── X-Propagation (output X-free checks)
└── Scoreboard (end-to-end data integrity)
Assumptions and Constraints/
├── DFT and Reset Constraints
├── Protection Key Constraints
└── Protocol Constraints
CSR Verification/
└── Register Map (one entry per CSR register)
Coverage/
└── Formal Coverage (stimuli, COI, proof, bound)
```

### Step 4: Create metricsPort Items from Requirements
For each requirement extracted from the spec:

**For verifiable requirements (YES):**
- `metrics_port_kind` = `CHECK`
- `name` = Short descriptive name derived from the requirement (e.g., `ECC single-bit error correction`)
- `details` = Full requirement text from spec + specific verification criteria (signals, values, timing)
- `implementation_note` = Suggested SVA approach or pseudo-property
- `assumePlanned` = `false`

**For integration constraints (ASSUME):**
- `metrics_port_kind` = `CHECK`
- `name` = Constraint name (e.g., `Reset synchronous to clock`)
- `details` = Spec text describing the constraint
- `implementation_note` = Suggested assume property
- `assumePlanned` = `true`

**For CSR registers:**
- `metrics_port_kind` = `COVERAGE`
- `name` = Register name with offset (e.g., `SRAMECCCON (0x018)`)
- `details` = All fields, bit positions, access types, reset values from the spec register table
- `implementation_note` = CSR checker approach (backdoor/frontdoor)

- **CRITICAL for details field** — MUST be multi-sentence, spec-sourced, and specific:
1. Start with `"Spec X.Y.Z (Section Name):"` referencing the exact spec section
2. Quote or closely paraphrase the spec's behavioral description (2-3 sentences minimum)
3. Name the specific signals, register fields, and bit positions involved
4. State the exact expected values, timing relationships, or state transitions
5. Call out corner cases mentioned in the spec (e.g., "counter saturates at 7", "W1C clears only when no new error coincides")
6. For CSR entries: include offset, access type, reset value, ALL field names with bit positions

**BAD** (too vague):
- "Verify ECC error correction works correctly"
- "Check that initialization completes"
- "Validate register access"

**GOOD** (spec-driven, detailed):
- "Spec 1.3.6 (ECC Protection): Since the controller uses SEC-DED mechanism, it can CORRECT single-bit errors. The Hsiao algorithm identifies the erroneous bit position via syndrome bits and flips it back. On single-bit error (non-test mode), corrected data must differ from raw SRAM data (the corrupted bit was flipped back)."
- "Spec 1.3.6 (Memory Initialization): Initialization through MMR — SEN (Enable SRAM initialization) and INITEN (Start Memory initialization) need to be set in SRAMINITCON register. When both start_manual_init and init_en are set, init_in_progress must assert within 1024 cycles."
- "Spec 1.3.3.2.2.7: Read-write (gated by usr_prot). Reset: 0x000000C9. Fields: EN[0]=1 (ECC enable, default ON), BUSERRTYPE[4:3]=2'b01 (default: bus error on 2-bit only), INTERRTYPE[6:5]=2'b11 (default: interrupt on 1-bit and 2-bit), RECERRTYPE[8:7]=2'b01 (default: current error recording). Bits[2:1] RESERVED, Bits[31:9] RESERVED."

### Step 5: Generate the vplanx XML
Use the Python template in `resources/gen_vplanx_template.py`. The template provides:
- `metrics_port()` — creates a single vplan entry (CHECK or COVERAGE)
- `section_start()` / `section_end()` — creates section hierarchy
- UUID generation for all XML `id` attributes
- Gzip compression to produce `.vplanx`

### Step 6: Add vManager Settings
Add to the JasperGold TCL setup file:

```tcl
#vManager Settings
set ENABLE_VMGR                  1
set VMGR_SERVER                  "adblvmgrproxy.adbldesign.analog.com"
set VMGR_PORT                    8080
set VMGR_PROJECT                 "<project_name>"
set ENABLE_VPLAN                 1
set VPLAN_SOURCE                 "${FPV_ROOT}/<IP_NAME>_VPLAN.vplanx"
set FML_INSTTOP                  "<top_module>"
```

### Step 7: Generate Traceability CSV (Optional)
If assertion files already exist, create a mapping CSV:
```
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
SPEC-001,ASSERT,ast_xxx,props_file.sv,top_module,ALL,MAPPED
```
- This links spec requirements to implemented assertions and identifies gaps.

## Spec Reading Best Practices

### What to Extract
- **Behavioral statements**: "When X happens, Y must occur within N cycles"
- **Reset values**: "After reset, register R has value V"
- **Error conditions**: "If invalid access, error response generated"
- **FSM transitions**: "State moves from A to B when condition C"
- **Data transformations**: "Input data is encoded as output with parity"
- **Timing constraints**: "Signal must be stable for N cycles"
- **Mode-dependent behavior**: "When mode=M, feature F behaves as..."
- **Register fields**: Every bit field, access type, reset value, side effects
- **Integration constraints**: "Input X must be synchronous to clock Y"
- **Protection/security**: "Register writes gated by protection key"

### What NOT to Extract
- Marketing language / overview paragraphs
- Revision history
- Document formatting instructions
- References to other documents (unless they contain requirements)

### Section-by-Section Reading Order
1. **Table of Contents** — map all sections
2. **Feature Overview** — identify all feature areas
3. **Interface Description** — protocols, ports, signals
4. **Functional Description** — core behavior, datapaths, FSMs
5. **Register Map** — every register, field, access type, reset value
6. **Error Handling** — error conditions, responses, recovery
7. **Initialization/Reset** — boot sequence, reset behavior
8. **Test/Debug Modes** — DFT, test mode, diagnostics
9. **Interrupt** — sources, masking, clearing, priority
10. **Integration Guidelines** — constraints, assumptions of use
11. **Timing/Clocking** — clock domains, synchronization
12. **Parameter Configurations** — parameterized behavior differences

## vplanx XML Schema Reference

### Root Structure
```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<vplanx:plan xmlns:vplanx="http://www.cadence.com/vplanx">
    <metaData id="UUID">
        <name>IP_NAME</name>
        <planId>UUID</planId>
        <sourceTool>vManager Planner</sourceTool>
        <toolVersion>23.09</toolVersion>
        <schemaVersion>1.0</schemaVersion>
        <buildTime>YYYY-MM-DD HH:MM:SS</buildTime>
    </metaData>
    <rootElements>
        <section>...</section>
    </rootElements>
</vplanx:plan>
```

### Section Element
```xml
<section id="UUID">
    <name>Section Name</name>
    <attributes>
        <attribute><name>creator</name><value>owner</value></attribute>
    </attributes>
    <subElements>
        <!-- nested sections or metricsPort entries -->
    </subElements>
</section>
```

### metricsPort Element (Leaf Item)
```xml
<metricsPort id="UUID">
    <name>requirement_name</name>
    <attributes>
        <attribute><name>metrics_port_kind</name><value>CHECK|COVERAGE|TESTCASE</value></attribute>
        <attribute><name>creator</name><value>owner</value></attribute>
        <attribute><name>details</name><value>Spec requirement text + verification criteria</value></attribute>
        <attribute><name>implementation_note</name><value>Suggested SVA approach or pseudo-property</value></attribute>
        <attribute><name>owner</name><value>owner</value></attribute>
    </attributes>
    <assumePlanned>false</assumePlanned>
</metricsPort>
```

### mappingPattern — NOT needed for formal vplans
- Do NOT include `<mappingPatterns>` in formal vplan metricsPort entries.
- The vplanx schema only accepts `TEST` and `COVERAGE` as domain values — `FORMAL` is NOT a valid domain and will cause a parsing error.
- Formal properties are mapped to vManager via `FML_INSTTOP` and the adsim/JasperGold integration, not via mappingPatterns.

### metrics_port_kind Values
| Kind | Use For |
|------|---------|
| `CHECK` | Spec requirements verifiable by assertions or assumptions |
| `COVERAGE` | CSR register checks, formal coverage metrics, cover properties |
| `TESTCASE` | Simulation test cases (NOT used in FPV vplans) |

### assumePlanned
- `false` for assertions and covers (default)
- `true` for assumptions / integration constraints

## XML Special Characters
- Always escape in details/implementation_note:
| Character | Escape |
|-----------|--------|
| `&` | `&amp;` |
| `<` | `&lt;` |
| `>` | `&gt;` |
| `"` | `&quot;` |

## Output Files
- The skill produces:
1. `<IP_NAME>_VPLAN.xml` — human-readable XML (for inspection)
2. `<IP_NAME>_VPLAN.vplanx` — gzip-compressed XML (for vManager)
3. `req_extraction.csv` — all requirements extracted from spec (optional)

## Quality Checklist
- Before delivering the vplan:
- [ ] Every spec section has been read — no sections skipped
- [ ] Every behavioral statement in the spec has a corresponding vplan item
- [ ] Every register in the register map has its own CSR entry
- [ ] Every integration constraint is captured as an assumption (assumePlanned=true)
- [ ] Details field includes specific signals, values, and timing — NEVER vague
- [ ] Implementation_note suggests a concrete SVA approach
- [ ] All XML special characters are escaped
- [ ] The .vplanx file is valid gzip (test with `gunzip -t`)
- [ ] vManager TCL settings are added to the JG setup TCL
- [ ] Total vplan items ≥ number of spec requirements (1:1 minimum coverage)