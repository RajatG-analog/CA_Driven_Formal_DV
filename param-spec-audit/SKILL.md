---
name: param-spec-audit
description: Audit every RTL parameter and hardcoded literal of an IP at IP level and SoC context, compare against the spec, check which values DV (formal/sim) actually exercised, and generate one HTML compliance report. Use before IP handoff/release, when a SoC reports a parameter-dependent bug, or when the user asks to check params, hardcoded values, tie-offs, default values, or parameter coverage vs spec.
---

# Parameter & Hardcoded-Constant Spec Audit

- Catches bugs like the adip_pinmux `PERIPHERAL_OUT_DEFAULT` escape:
  - The parameter existed at top, but `demux_cell` tied the unselected leg to `'b0`, so a SoC default of 1 never reached the peripheral.
  - DV only ran default=0, so it passed.
- Shell is **tcsh**: no `2>&1`, no heredocs, no inline `-c` scripts.

## Inputs to collect (ask the user if missing)

1. IP name, top module, RTL file glob (e.g. `$ADIP_BLOCKS_ROOT/<ip>/digital/rtl/*.sv`)
2. Spec (PDF / Jama / md)
3. SoC context: SoC RTL files instantiating the top, **or** a CSV `name,value,soc_context`
   (one row per param per SoC, e.g. Olympus+). Never invent SoC values.
4. DV directories (formal + sim), e.g. `<ip>/dv/formal`, `<ip>/dv/sim`

## Workflow

### Step 1 — Build the spec param CSV
Read the spec parameter/configuration section and every requirement that mentions a
default, idle, reset, tie-off or "unselected" value. Fill
`resources/spec_params_template.csv` (copy to `.tmp/<ip>_spec_params_<ts>.csv`):

| column | content |
|---|---|
| name | RTL parameter name |
| spec_default | default stated in spec, blank if none stated |
| spec_allowed | `lo..hi`, `a\|b\|c`, or `any` |
| spec_ref | section / PM-REQ id |
| spec_behavior | where the value must appear (all modes, which outputs) |

- Only record what the spec states.
- Mark absent info as blank, and report it as a spec gap.

### Step 2 — Run the scanner
```tcsh
python3 <skill_dir>/scripts/param_audit.py --ip <ip> --top <top> \
  --rtl "<rtl_glob>" --spec <spec_csv> \
  --soc "<soc_rtl_glob>"   (or --soc-csv <soc_csv>) \
  --dv <dv_dir1> <dv_dir2> \
  --out <ip>_param_audit.html
```
The scanner extracts:
- all `parameter`/`localparam` per module, top-level defaults
- SoC overrides of top params (from `#( .P(v) )` or CSV)
- DV values from `-param N V`, `-gN=V`, `-defparam`, `#(.N(V))`, `` `define ``
- propagation of every child param (PASSED / NOT_PROPAGATED / CHILD_DEFAULT)
- hardcoded literals on instance ports, `assign x = <lit>`, literal mux/else/default legs;
  **SUSPECT** when a DEFAULT/RESET/INIT/IDLE-style param exists in the module or any ancestor

### Step 3 — Manual deep checks (mandatory, script is heuristic)
For every SUSPECT literal and every DEFAULT-style parameter:
1. Trace the param from top to every leaf output it should drive. Read the RTL.
2. Confirm every mode branch (GPIO/ESS/test/peripheral, reset, invalid select) uses the
   param rather than a literal. Check `case default`, the else branch, and demux unused legs.
3. Check DV: was a **non-default, non-uniform** value run (e.g. all-1s and alternating
   `0x55`)? Was the property checked in **every** mode where the spec requires it? Grep the
   connectivity CSVs and SVA for the output under each mode condition.
4. Check the waiver files (`dqa/cmd.usr/*.awl`, formal `waiver*.tcl`) for waivers that hide the literal.

For non-default params, check that each SoC value is inside spec range and in a DV config.

### Step 4 — Report
Add a "Findings" section at the top of the HTML (edit the file), one row per issue:
param, RTL location, spec ref, SoC impact, DV gap, and recommended fix. Fixes are
RTL (use param) or DV (add config/property) or spec (clarify). Classify each issue as:
- **RTL non-compliant**: literal bypasses the param, or RTL default differs from spec
- **DV gap**: SoC value or mode not verified, single-value DV, or default only
- **Spec gap**: param not in spec, or behaviour per mode not stated
- **Compliant**: spec, RTL, SoC and DV all agree

- Copy the report to the user's public_html report area if requested, and give the path.

## Status rules (script)
- FAIL: SPEC_DEFAULT_MISMATCH, RTL_DEFAULT_OUT_OF_RANGE, SOC_OUT_OF_RANGE, DV_GAP_SOC_VALUE, NOT_PROPAGATED, HARDCODED_LITERAL_BYPASS.
- WARN: NOT_IN_SPEC, DV_SINGLE_VALUE, DV_DEFAULT_ONLY, UNUSED.
- PASS: no issues.

## Known limits
- Regex parser: no `generate`-dependent widths or macros, and no `defparam` hierarchy.
- SUSPECT literals in `sel`/index expressions are usually benign padding, so review before reporting.
- Large integers are shown in hex.
