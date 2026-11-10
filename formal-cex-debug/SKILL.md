---
name: formal-cex-debug
description: Debug JasperGold counter-examples — load CEX waveform (FSDB/VCD/FST), backward-trace to primary inputs, correlate with assumptions and spec, classify root cause (RTL bug, property/CSV error, spec gap) and generate a debug report and JG debug TCL. Use when a formal assertion or connectivity check fails, or a cover is unreachable.
---

# Formal CEX Debug Skill — LLM-Assisted Counter-Example Analysis

## When to Use
- Activate when the user asks to:
- Debug a counter-example (CEX) from JasperGold
- Analyze a failing assertion waveform (FSDB/VCD/FST)
- Trace a CEX back to primary inputs
- Perform root cause analysis on formal verification failures
- Classify CEX as RTL bug, assumption gap, property error, etc.
- Debug undetermined or unreachable properties

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| **CEX waveform** | FSDB, VCD, or FST from JasperGold | `jgproject/cex/ast_D01_write_data.fsdb` |
| **Property name** | Failing assertion or cover label | `ast_D01_write_data` |
| **Property file** | SVA file containing the property | `props/sram_ahb_ctl_props.sv` |
| **RTL files** | RTL source for the bind target module | `rtl/sram_ahb_ctl.sv` |
| **Spec PDF** | IP specification (optional but recommended) | `ADIP_SRAM_Controller.pdf` |
| **Assumptions file** | Assumptions constraining the design | `props/sram_assumptions.sv` |
| **VERDI_HOME** | Path to Verdi installation (for FSDB) | `$VERDI_HOME` |

---

## Prerequisites — Verdi NPI (pynpi) Setup

- For FSDB waveform parsing, Verdi's NPI Python binding is required:

```
VERDI_HOME must be set (e.g., /cad/adi/apps/synopsys/verdi/<version>)
pynpi location: $VERDI_HOME/share/NPI/python/pynpi
LD_LIBRARY_PATH must include: $VERDI_HOME/share/NPI/lib/linux64
```

- For VCD/FST files, the built-in `queryWaveform` tool works directly without any additional setup.

---

## Step-by-Step Procedure

### Step 1: Load the CEX Waveform

**1a. Identify the waveform file:**
- JasperGold stores CEX waveforms in the jgproject directory.
- Common locations:
```
jgproject/cex/<property_name>.fsdb
jgproject/cex/<property_name>.vcd
jgproject/<session>/cex_traces/
```

- If the user provides a `.fsdb` file, use the pynpi parser resource script.
- If `.vcd` or `.fst`, use the `queryWaveform` tool directly.

**1b. Get basic waveform info:**
- Simulation time range (start → end)
- Timescale (1ns, 1ps, etc.)
- Total cycle count of the CEX trace
- Identify the clock signal and its period

**1c. Get the scope hierarchy:**
- List top-level scopes
- Find the DUT instance path
- Find the bind module instance path (where assertions live)

### Step 2: Extract the Failing Property's Signal Set

**2a. Read the SVA property from the property file:**
- Use `View` to read the property file and find the exact assertion:
```
ast_D01_write_data: assert property (
    is_full_word_write |-> hwdata == sram_wdata[31:0]
);
```

**2b. Parse the property into signal groups:**

| Group | Description | Example |
|-------|-------------|---------|
| **Antecedent signals** | Trigger/LHS of `\|->` or `\|=>` | `is_full_word_write` |
| **Consequent signals** | Check/RHS that failed | `hwdata`, `sram_wdata` |
| **Clock** | Clocking block reference | `clk` (from `default clocking`) |
| **Reset** | Disable iff expression | `rst_n` (from `default disable iff`) |
| **Delay signals** | Any `##N` or `$past()` references | Timing-dependent signals |

**2c. Expand derived signals:**
- If a signal is a wire/logic derived from other signals (e.g., `is_full_word_write = write_active && hsize == 3'b010`), read the RTL or property file to find the constituent signals.
- Add ALL leaf signals to the extraction list.

### Step 3: Extract Signal Values from Waveform

**3a. For each signal in the extraction list, query the waveform:**

- Using `queryWaveform`:
```
- Get all value changes for the signal over the CEX time range
- Get the signal value at the failure cycle
- Get the signal value 1-2 cycles before the failure
```

**3b. Build the cycle-by-cycle signal table:**

- Create a table with one row per clock cycle, columns for each signal:

```
Cycle | clk | rst_n | htrans | hsel | hwrite | hsize | hwdata    | sram_wdata | is_write | FAIL?
------+-----+-------+--------+------+--------+-------+-----------+------------+----------+------
   0  |  ↑  |   0   |  00    |  0   |   0    | 010   | 00000000  | 00000000   |    0     |
   1  |  ↑  |   1   |  10    |  1   |   1    | 010   | DEADBEEF  | 00000000   |    1     |
   2  |  ↑  |   1   |  00    |  0   |   0    | 010   | DEADBEEF  | CAFEBABE   |    0     | ← FAIL
```

**3c. Identify the failure point:**
- Which cycle does the assertion fail?
- What are the actual vs expected values at that cycle?
- Is the antecedent satisfied at the trigger cycle?

### Step 4: Backward Trace — From Failure to Primary Inputs

**4a. Trace the failing consequent signal backward:**

- Starting from the signal that has the wrong value at the failure cycle:
1. Read the RTL to find its driver (assign, always block, case/if-else)
2. Identify all signals in the driver expression
3. Query those signals' values at the relevant cycle(s)
4. For registered signals, look one cycle earlier (input to the flop)
5. Repeat until you reach primary inputs or assumptions

**4b. Build the signal dependency tree:**

```
sram_wdata[31:0] (WRONG at cycle 2)
  └── driven by: ram_write_data[31:0] (in sram_ahb_ctl.sv:142)
      └── driven by: mux(hwdata, rmw_merged_data) sel=is_partial
          ├── hwdata[31:0] = DEADBEEF (correct from AHB bus)
          ├── is_partial = 1 ← WHY? hsize should indicate word
          └── rmw_merged_data = CAFEBABE (stale from previous read)
              └── ROOT CAUSE: is_partial incorrectly asserted
```

**4c. Identify the root cause signal:**
- The root cause is the earliest signal in the dependency tree whose value deviates from the spec-expected behavior.

### Step 5: Correlate with RTL Source

**5a. Read the RTL driver code:**
- Use `View` to read the exact RTL lines that drive the root cause signal.
- Include the full always block or assign statement, plus 5 lines of context above and below.

**5b. Check for common RTL patterns that cause CEX:**

| Pattern | Symptom in CEX | Root Cause |
|---------|---------------|------------|
| Priority mux override | Correct input present but wrong output | Higher-priority condition active |
| Missing case default | Output = X or stale value | Unhandled state in case/if-else |
| Pipeline timing | Signal correct but 1 cycle late/early | Address vs data phase mismatch |
| Gated clock hold | Register doesn't update for N cycles | ICG clock gate disabled |
| RMW race | Stale data merged during partial write | Read-modify-write timing |
| Counter wrap | Unexpected state transition | Overflow at reduced bit width |
| Reset domain cross | Uninitialized value at cycle 1-2 | Secondary reset not modeled |

**5c. Read RTL comments:**
- RTL comments often explain intentional behavior that looks like a bug.
- ALWAYS read comments near the driver before classifying as RTL_BUG.

### Step 6: Correlate with Assumptions

**6a. Read the assumptions file and list all active assumptions:**
- For each assumption, check if it constrains any signal in the dependency tree.

**6b. Check for missing assumptions:**
- Is there an unconstrained input in the CEX that should be static?
- Is there a protocol rule not encoded as an assumption?
- Does the spec AoU list a constraint not present in assumptions?

**6c. Check for over-constraining assumptions:**
- Do the active assumptions make the antecedent unreachable?
- Is a forced value (e.g., `ecc_en == 1`) preventing exploration?
- Run mental `check_assumptions -conflict` — are any assumptions
  mutually exclusive?

**6d. Check ABVIP assumptions:**
- If ABVIP is integrated, verify that ABVIP's built-in assumptions are not conflicting with manual assumptions.
- Common issue: manual protocol assumption says X, ABVIP says Y.

### Step 7: Correlate with Spec (Spec-Anchored RCA)

**7a. Find the SPEC-ID:**
- Read the assertion's comment for the SPEC-ID reference:
```
// SPEC-038 | AHB write data forwarded to SRAM within 2 cycles
ast_D01_write_data: assert property (...)
```

**7b. Read the spec section:**
- Use `View` or `queryFileWithEmbeddings` to read the exact spec section referenced by the SPEC-ID.

**7c. Three-way comparison:**

```
SPEC says: "Write data from AHB shall be forwarded to SRAM
            within 2 clock cycles of the data phase"

SVA checks: hwdata == sram_wdata[31:0] on is_full_word_write

RTL does:   Muxes hwdata with rmw_merged_data based on is_partial,
            but is_partial is asserted even for word writes when
            byte_en != 4'b1111 due to hsize decoding bug
```

**7d. Classify:**

| Classification | Criteria |
|---|---|
| **RTL_BUG** | RTL does not implement what spec requires |
| **PROPERTY_ISSUE** | SVA over/under-specifies vs spec intent |
| **ASSUMPTION_ISSUE** | Missing or over-constraining assumption |
| **ENGINE_LIMIT** | Proof timeout, not a real failure |
| **TOOL_ARTIFACT** | JG modeling issue (reset domain, blackbox) |
| **SPEC_AMBIGUITY** | Spec is unclear, need clarification |
| **EXPECTED** | Cover unreachable by design (spec AoU) |

### Step 8: Generate Debug Report

- Create a structured report for each analyzed CEX:

```markdown
## CEX Analysis: <property_name>

### Property
- **File:** <property_file>:<line>
- **SVA:** <full assertion code>
- **SPEC-ID:** SPEC-NNN
- **Spec Section:** §X.Y <title>

### Waveform Summary
- **CEX Length:** N cycles
- **Failure Cycle:** M
- **Trigger Cycle:** M-1 (antecedent satisfied)

### Signal Trace at Failure
| Signal | Cycle M-1 | Cycle M | Expected | Actual |
|--------|-----------|---------|----------|--------|
| hwdata | DEADBEEF  | DEADBEEF| DEADBEEF | DEADBEEF | ✓
| sram_wdata | 00000000 | CAFEBABE | DEADBEEF | CAFEBABE | ✗

### Backward Trace
<signal dependency tree from Step 4b>

### Root Cause
<1-3 sentence root cause with RTL file:line reference>

### Classification: <RTL_BUG | PROPERTY_ISSUE | ...>

### Suggested Fix
<specific code change, assumption addition, or property edit>

### Spec Reference
> "<exact quoted text from specification>"
```

### Step 9: Generate JG Debug TCL

- For each analyzed CEX, generate a JG debug script that the engineer can source to visualize the critical signals:

```tcl
proc debug_<property_name> {} {
    puts "\n=== CEX Debug: <property_name> ==="
    puts "Classification: <classification>"
    puts "Root Cause: <1-line summary>"

    visualize -new_window
    visualize -violation \
        -property {<embedded>::<bind_path>.<property_name>} -bg

    # Add critical signals with color coding
    # RED = failing signal (wrong value)
    visualize -add_wave -hier {<dut>.<failing_signal>} \
        -color red -label "<signal> (FAILING)"

    # YELLOW = root cause signal
    visualize -add_wave -hier {<dut>.<root_cause_signal>} \
        -color yellow -label "<signal> (ROOT CAUSE)"

    # GREEN = reference/expected signals
    visualize -add_wave -hier {<dut>.<reference_signal>} \
        -color green -label "<signal> (expected)"

    # BLUE = antecedent/trigger signals
    visualize -add_wave -hier {<dut>.<trigger_signal>} \
        -color blue -label "<signal> (trigger)"

    puts "--- Spec §X.Y says: <requirement> ---"
    puts "--- Look for: <what to check in waveform> ---"
}
```

### Step 10: Batch Analysis Mode

- When multiple CEX exist (common after first prove -all), process them in batch:

**10a. Collect all failing properties:**
```
grep -E "CEX|cex|FAILED" results/report_fpv.txt | \
    awk '{print $1}' > rca/failing_props.txt
```

**10b. Triage by category (fast-path filtering):**

| Check | Fast Classification | Action |
|-------|-------------------|--------|
| CEX at cycle 1-2 | TOOL_ARTIFACT (reset domain) | Add `disable iff` |
| Same root signal in 5+ CEX | Single root cause | Fix once |
| Protocol signal in CEX | ASSUMPTION_GAP | Add protocol assumption |
| Unconstrained input toggling | ASSUMPTION_GAP | Add stability assumption |
| Antecedent never true | VACUOUS | Needs separate config run |

**10c. Group by root cause:**
- Multiple CEX often share the same root cause.
- After analyzing the first CEX in a group, mark the rest as "same root cause as F-001" and verify with a spot-check of one more from the group.

**10d. Priority order:**
1. RTL_BUG — report immediately, highest severity
2. ASSUMPTION_GAP — fix assumptions, re-run prove
3. PROPERTY_ISSUE — fix SVA, re-run prove
4. TOOL_ARTIFACT — fix disable iff, re-run prove
5. ENGINE_LIMIT — tune engines, increase time limit
6. VACUOUS — plan separate config run

---

## Verdi NPI (pynpi) Integration

### Architecture

```
JasperGold CEX (.fsdb)
    │
    ▼
pynpi Parser (resources/fsdb_cex_parser.py)
    │  - Reads signal hierarchy
    │  - Extracts value changes
    │  - Traces cone-of-influence
    │  - Outputs structured JSON
    │
    ▼
LLM Analysis (this skill)
    │  - Correlates with RTL source
    │  - Correlates with assumptions
    │  - Correlates with spec
    │  - Classifies root cause
    │
    ▼
Debug Report + JG TCL Script
```

### Using the pynpi Parser

- The `resources/fsdb_cex_parser.py` script provides these capabilities:

**1. Signal Discovery:**
```
python3 fsdb_cex_parser.py --fsdb <file> --list-signals [--scope <path>]
```
- Returns all signals under the given scope with their widths and types.

**2. Value Extraction:**
```
python3 fsdb_cex_parser.py --fsdb <file> --signals <sig1,sig2,...> \
    [--start <time>] [--end <time>]
```
- Returns cycle-by-cycle values for each signal as JSON.

**3. Cone-of-Influence Trace:**
```
python3 fsdb_cex_parser.py --fsdb <file> --trace <signal> \
    --rtl-dir <path> [--depth <N>]
```
- Backward-traces a signal through RTL to find its driver chain.

**4. Transition Summary:**
```
python3 fsdb_cex_parser.py --fsdb <file> --transitions <signal> \
    [--start <time>] [--end <time>]
```
- Returns all value transitions with timestamps.

### Fallback: queryWaveform Tool

- For VCD and FST files, or when pynpi is not available, use the built-in `queryWaveform` tool which supports:
- `get_signals()` — list signals with filtering
- `get_signal_value_at_time()` — point value query
- `get_signal_changes()` — transition list
- `get_scopes()` — hierarchy navigation

- The analysis methodology is identical — only the waveform access layer differs.

---

## Common CEX Patterns Reference

### Pattern 1: Reset Domain Crossing
```
Symptom:  CEX at cycle 1-2, signal = X or 0
Cause:    Secondary reset domain not initialized by JG
Fix:      disable iff (!rst_primary || !rst_secondary)
Detect:   CEX cycle ≤ 2 AND signal in non-primary reset domain
```

### Pattern 2: Priority Mux Override
```
Symptom:  Correct input present but output takes different value
Cause:    Higher-priority condition in RTL mux is active in CEX
Fix:      Add higher-priority guard to assertion antecedent
Detect:   Multiple inputs to a mux; CEX selects unexpected path
```

### Pattern 3: AHB Address/Data Phase Mismatch
```
Symptom:  Assertion uses haddr/hsize (address phase) but checks
          sram_wdata/sram_wen (data phase) — off by 1 cycle
Cause:    AHB pipeline: address phase is cycle N, data is N+1
Fix:      Use $past(haddr) or data-phase registered versions
Detect:   Signal timing diagram shows 1-cycle offset
```

### Pattern 4: Gated Clock Register Hold
```
Symptom:  Register doesn't update for many cycles in CEX
Cause:    ICG clock gate disabled, register holds stale value
Fix:      Increase bound (##[1:512]) or add ICG enable assumption
Detect:   Clock gate enable = 0 during CEX window
```

### Pattern 5: Partial Write RMW Corruption
```
Symptom:  sram_wdata != hwdata during write
Cause:    Partial write triggers read-modify-write; merged data
Fix:      Gate assertion with is_full_word_write
Detect:   hsize != WORD or byte_en != 4'b1111 in CEX
```

### Pattern 6: Unconstrained Static Input
```
Symptom:  Configuration input toggles mid-operation in CEX
Cause:    Input should be static but has no stability assumption
Fix:      Add $stable() assumption; file spec gap if not in AoU
Detect:   Input changes value in cycle > 0
```

### Pattern 7: ABVIP Superseded Assumption Conflict
```
Symptom:  Protocol assumption says X, ABVIP says Y
Cause:    Manual assumption not commented out after ABVIP integration
Fix:      Comment out manual assumption with ABVIP cross-reference
Detect:   check_assumptions -conflict returns non-empty
```

### Pattern 8: ECC Error During Write-Back
```
Symptom:  Write completion assertion fails, sram_wen = 0
Cause:    2-bit ECC error detected during RMW read-back, write blocked
Fix:      Add !ecc_err_2b to write completion antecedent
Detect:   ECC error flags active during write cycle in CEX
```

### Pattern 9: Free Variable Not Explored
```
Symptom:  Assertion proven but companion cover unreachable
Cause:    CSR free variable solver picks default path, skips exploration
Fix:      Force specific value or add reachability cover
Detect:   Cover antecedent depends on free variable; cover UNREACHABLE
```

### Pattern 10: Counter Overflow at Reduced Width
```
Symptom:  Unexpected FSM transition or counter wrap in CEX
Cause:    Timer/counter reduced from 24→8 bits, wraps in 256 cycles
Fix:      Assert on state signals not raw counter values
Detect:   Counter reaches max value and wraps in CEX
```

---

## Output Files

```
rca/
├── cex_analysis_<property>.md      — Per-CEX detailed analysis report
├── cex_signal_trace_<property>.json — Cycle-by-cycle signal values
├── debug_failures.tcl              — JG debug script (one proc per CEX)
├── formal_rca_report.md            — Aggregated RCA report (all CEX)
├── failing_props.txt               — List of all failing properties
└── rca_summary.csv                 — Classification summary table
```

### rca_summary.csv Format

```csv
Property,Status,CEX_Cycles,Classification,Root_Cause_Signal,RTL_File,RTL_Line,SPEC_ID,Fix_Type,Notes
ast_D01_write_data,CEX,12,RTL_BUG,is_partial,sram_ahb_ctl.sv,142,SPEC-038,RTL_FIX,hsize decode missing word case
ast_F08_liveness,UNDETERMINED,—,ENGINE_LIMIT,—,—,—,SPEC-072,ENGINE_TUNE,Increase time to 8h
cov_E03_2bit_err,UNREACHABLE,—,ASSUMPTION_ISSUE,ecc_en,—,—,SPEC-045,ADD_COVER,ecc_en forced to 1
```

---

## Quality Checklist

- [ ] Every CEX has a complete 5-step analysis (waveform → trace → RTL → assumptions → spec)
- [ ] Every classification has a spec reference (SPEC-ID or protocol ref)
- [ ] RTL_BUG entries include exact file:line and suggested fix
- [ ] ASSUMPTION_ISSUE entries cite spec AoU section
- [ ] PROPERTY_ISSUE entries include corrected SVA code
- [ ] Batch analysis groups CEX by root cause (no duplicate analysis)
- [ ] JG debug TCL generated for all non-trivial CEX
- [ ] Cycle-by-cycle signal table covers failure cycle ± 3 cycles minimum
- [ ] Backward trace reaches primary inputs or assumptions
- [ ] All findings documented in formal_rca_report.md
- [ ] No assumptions added without spec or engineering justification
- [ ] Report reviewed by engineer before any assumption/property changes
