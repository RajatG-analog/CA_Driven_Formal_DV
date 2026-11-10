---
name: formal-connectivity
description: Spec-only Jasper Connectivity App flow (JasperGold 2025.09) — generate check_conn CSVs (positive, default/isolation, priority and expected-CEX negative CONNECTION rows; no SVA), TCL setup or adsim sim.setup with run commands, waivers, traceability, CEX debug, optional vPlan and final param audit. Use when the user asks for connectivity CSVs, mux/pinmux/interconnect routing checks, check_conn setup, or connectivity sign-off.
---

# Formal Connectivity Skill — Jasper Connectivity App CSV Specs

**Resource loading (MANDATORY):**
- `resources/...` paths are relative to this skill's directory (the directory containing this SKILL.md).
- Resources are NOT preloaded. At each step that says "Read `resources/<file>`", open that file with View BEFORE writing any output for the step.
- Never generate a template, CSV, traceability CSV or HTML report from memory when a resource file exists for it.
- This flow uses NO SVA: every check (positive, default/isolation, priority, negative) is a `check_conn` CSV CONNECTION row.

| Step | Resource file (read when reaching the step) |
|------|---------------------------------------------|
| Step 4b — sim.setup | `resources/sim_setup_template.md` |
| Step 6b — default / isolation / negative CSV checks | `resources/negative_checks.md` |
| Traceability | `resources/traceability_format.md` |
| HTML report | `resources/html_report_spec.md` |
| Any step — concrete example | `resources/pinmux_worked_example.md` |

## When to Use
Activate when the user asks to:
- Create connectivity CSV specs for Jasper Connectivity App
- Verify signal routing (mux/demux, crossbar, pin-mux, interconnect)
- Check data path connectivity from source to destination
- Generate connectivity specs from a spreadsheet or spec document
- Debug connectivity failures (toggle, expression, branch waivers)
- Generate parameterized waiver TCL for large channel/IO count (`<N_CH>`) designs

## Upfront Questions (ASK ONCE, BEFORE ANY WORK — MANDATORY)

- Ask ALL of these in ONE question round (AskUserQuestions) before Step 1.
- Do not re-ask later; reuse the answers in every step. Record them in the final summary.
- If an answer is "not known yet", continue and mark the dependent output as TODO.

| # | Question | Options / format | Used in |
|---|----------|------------------|---------|
| Q1 | Spec source | PDF / Excel / Jama / md path | Step 1–3 |
| Q2 | RTL filelist (compile only) | path to `filelist.f` | Step 4 |
| Q3 | Top module | `<top_module>` | elaborate, `FML_INSTTOP` |
| Q4 | Output / formal directory | e.g. `$ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>` | all outputs |
| Q5 | Run flow | A. TCL / B. adsim sim.setup / C. both | Step 4 |
| Q6 | adsim block name (if B/C) | e.g. `adip_pinmux` | RUNCMD `-block` |
| Q7 | Config list + directory layout | e.g. `1_io/peri_8`, `8_io/peri_8` or cfg_min/cfg_default/cfg_max | `<cfg_dir>`, `-resdir`, `-force_setup` |
| Q8 | Parameter values per config | `<PARAM>=<VAL>` per config | elaborate `-param` |
| Q9 | Run mode | GUI (`-gui`, needed for `-jgcov` one-step) / batch | RUNCMD |
| Q10 | Configs that run negative tests | list of configs / none | `check_conn -enable` of `neg_*` |
| Q11 | ProofGrid | yes (bsub command) / no | proofgrid lines |
| Q12 | Prove / coverage time limit | e.g. 48h, per-property 1h | `set_prove_time_limit`, `check_cov -measure` |
| Q13 | Web report location | e.g. `${GPMS_NOBACKUP}/../public_html/$USER/jasper_reports` | HTML / check_cov reports |
| Q14 | vManager / vPlan | vPlan NOW / LATER / NOT NEEDED; vManager on/off | Optional vPlan step, `ENABLE_VMGR` |
| Q15 | SoC context for final param audit | SoC RTL glob / SoC CSV / not available | Final Step |
| Q16 | Traceability publish | none / Jama / Confluence | Sign-Off Traceability |

- Only spec-gap questions are asked later (missing path/name/width/default, unreferenced ports, spec-ambiguity CEX), since they are found during the flow.

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| **Spec / Excel** | Connectivity specification (PDF, Excel, or description) | `<ip>_spec.pdf` |
| **RTL files** | Filelist for JG compile ONLY (DUT under test — never a requirement source) | `filelist.f` |
| **Top module** | DUT top for formal | `<top_module>` |
| **Output dir** | Where to write connectivity collateral | `fpv_env/connectivity/` |

**SPEC-ONLY PRINCIPLE (MANDATORY):**
- The specification is the ONE AND ONLY primary source for every connection, condition, latency, index formula, default value and signal name.
- NEVER read RTL source to derive, complete, or correct connectivity checks
  - Deriving expectations from the design under test makes verification circular (bugs in RTL become "expected" behavior).
- RTL is only compiled by JG.
- If a spec item is missing or ambiguous, ASK the user / log a spec gap — do NOT fill it from RTL.

**TOOL DOCUMENTATION (MANDATORY):**
- For all Jasper command/CSV syntax, always refer to the installed Cadence docs at `/cad/adi/apps/cadence/jasper/2025.09-p002/doc`.
- Docs win over memory or examples in this skill.
- Consult:

| Topic | Document |
|-------|----------|
| Connectivity app, CSV format (TOGGLE_CHECKS/TOGGLE_CHECKS_END, COND_EXPR, CONDITION, LATENCIES, CLOCK, DISABLE), `check_conn` | `jasper_conn_userguide.pdf` |
| All TCL commands/options (`analyze`, `elaborate`, `clock`, `reset`, `prove`, `report`) | `jasper_command_reference.pdf` |
| Coverage, `check_cov` measure/report/waive | `jasper_cov_userguide.pdf` |
| Apps overview | `jasper_apps_userguide.pdf` |
| ProofGrid settings | `jasper_proofgrid_manager.pdf` |
| Engine selection | `jasper_engine_selection.pdf` |
| SV construct support | `AN_SystemVerilog12_construct_support.pdf` |
| TCL utilities / scripting | `jasper_tcl_library.pdf`, `AN_scripting.pdf` |
| Example app setups | `example_jasper_apps/` |
| Browsable HTML docs | `HTML/` |

**KEY PRINCIPLE:** (per `jasper_conn_userguide.pdf`)
- Do NOT define global clocks/resets — use `clock -none` / `reset -none`.
- Clock and reset nets are then checked like any other signal.
- Defining a global clock/reset can over-constrain and give false results.
- All inputs are free variables by default.
- Combinational paths: plain CONNECTION rows (+ COND_EXPR if conditional).
- Sequential paths (through registers):
  - `CLOCK` / `DEFAULT_CLOCK` rows — clock for the connection
  - `LATENCIES` / `DEFAULT_LATENCIES` rows — cycle delay (fixed or `[min:max]`)
  - `DISABLE` / `DEFAULT_DISABLE` rows — disable check during reset
- Assumptions / constant conditions (Appendix A, assumes & stopats):
  - Only when the spec defines a fixed operating condition
    (e.g. static config registers → `assume -constant`)
  - Never to hide a failing connection

---

## Step-by-Step Procedure

### Step 1: Identify Connectivity Type

| Type | When | Approach |
|------|------|----------|
| **Pin Mux** | Channel/IO multiplexing (source → destination) | One CSV per channel group |
| **Data Path** | Functional data routing (encoder → memory → decoder) | One CSV per data flow |
| **Interconnect** | Bus fabric (masters → targets) | Per-master isolation tasks |
| **Control Path** | Config register → functional block enables | One CSV per subsystem |
| **Feedback** | Status/interrupt signals back to controller | One CSV |

### Step 2: Read the Spec (ONLY)
1. Read the spec to identify ALL source → destination signal mappings
2. Take signal/port names, widths and hierarchy from the spec (port tables,
   interface lists, block diagrams). Do NOT open RTL to look them up.
3. Note conditional connections (mux select, enable gating) from the spec
4. Note latency (pipeline stages between source and destination) from the spec
5. **CRITICAL:** If the spec does not document an interface, path, signal name
   or width, record it as a SPEC GAP and ask the user. Do NOT read RTL to
   discover it. Name mismatches are found by `check_conn -validate`, which
   reports them back for the spec owner to resolve.

### Step 2b: Common Library Dependency Audit
For combinational designs using gate-level primitives (e.g., `adip_mux_cell`
from `adip_boxes.v`):
- Include the common library file EXPLICITLY in the analyze command
- Add `+incdir` for the common library headers
- Use `-disable_auto_bbox` in elaborate to prevent unwanted blackboxing
- Do NOT include vendor cell libraries that pull in undefined dependencies

### Step 3: Create Connectivity CSV

- **TOGGLE_CHECKS / TOGGLE_CHECKS_END block is MANDATORY.**
- Every CSV spec file MUST start with `TOGGLE_CHECKS` and end with `TOGGLE_CHECKS_END` (conn user guide: toggle covers are generated for all connections between the two tags).
- Without it, JG generates connectivity assertions but NOT toggle covers, reducing coverage completeness (see Pitfall 3).

**CSV Format:**
```
TOGGLE_CHECKS
CONNECTION,<name>,,<source_signal>,,<destination_signal>
TOGGLE_CHECKS_END
```

**With conditions (mux select):**
```
TOGGLE_CHECKS
CONNECTION,<name>,,<source_signal>,,<destination_signal>
,COND_EXPR,"<condition_expression>"
TOGGLE_CHECKS_END
```

**COND_EXPR double-quotes — project rule (ALWAYS quote):**
- The conn user guide example is unquoted (`,COND_EXPR,rd_ready==1'b1`); quoting is not a tool requirement for simple expressions.
- Quotes ARE required when the expression contains a comma (e.g. concatenation `{a,b}`, `inside {..,..}`) — otherwise the CSV splits it into cells.
- ADI rule: always quote, so generated CSVs are safe for every expression.
```
RIGHT: ,COND_EXPR,"<sel_A>[0]"
WRONG: ,COND_EXPR,<sel_A>[0]
```

**CONDITION / DEFAULT_CONDITION / CONDITION(STABLE) (jasper_conn_userguide.pdf, Table Format):**
- `CONDITION,<blk>,<sig>,<val1>,<val2>,...` — condition on a control signal for the last preceding CONNECTION.
  - Multiple values on one row are OR-ed; multiple CONDITION rows are AND-ed position-wise.
  - Use for static control-register selects (value lists from the spec register/select table).
- `DEFAULT_CONDITION` — same format; applies to all subsequent CONNECTION rows (added to their own CONDITION rows).
  - `CLEAR_DEFAULT_CONDITION` — stops applying it to later rows.
- `CONDITION(STABLE)` — same format, but the proof assumes the signal is constant (`assume -constant`).
  - Applies to ALL connections in the task — cannot be per connection.
  - Use ONLY when the spec states the signal is static (configured once, never changes during operation).
  - It constrains every check in the task: put STABLE-condition CSVs in their own task/config if other checks need the signal free.
- Precedence: if a CONNECTION has DEFAULT_CONDITION, CONDITION or CONDITION(STABLE), the tool IGNORES its COND_EXPR.
  - Never mix COND_EXPR and CONDITION on the same CONNECTION.
- Choose: COND_EXPR for arbitrary Boolean/temporal expressions; CONDITION for value lists on control signals; CONDITION(STABLE) for spec-static configuration.
- CSV quoting: no space between the comma and the opening double quote (`,COND_EXPR,"..."` — NOT `, "..."`), otherwise parse error.
```
TOGGLE_CHECKS
DEFAULT_CONDITION,<ctrl_blk>,<mode_reg>[1:0],2'd1
CONNECTION,c_cp_<name>_ch0,,<src_bus>[0],,<dst_bus>[0]
CONDITION,<ctrl_blk>,<src_sel>[2:0],3'd0,3'd4
CLEAR_DEFAULT_CONDITION
CONNECTION,c_cp_<name>_ch1,,<src_bus>[1],,<dst_bus>[1]
CONDITION(STABLE),<ctrl_blk>,<cfg_reg>[3:0],4'd2
TOGGLE_CHECKS_END
```

**With latency (pipeline delays):**
```
TOGGLE_CHECKS
CONNECTION,<name>,,<source_signal>,,<destination_signal>
,LATENCIES,<min_cycles>,<max_cycles>
TOGGLE_CHECKS_END
```

**Full example (mux):**
```
TOGGLE_CHECKS
CONNECTION,c_od_src1_ch3,,u_<blk>.<src_1>,,<dst_bus>[3]
,COND_EXPR,"<src_sel>[3] == <enc_1>"

CONNECTION,c_od_src2_ch5,,u_<blk>.<src_2>,,<dst_bus>[5]
,COND_EXPR,"<src_sel>[5] == <enc_2>"

CONNECTION,c_od_src0_ch0,,u_<blk>.<src_0>[0],,<dst_bus>[0]
,COND_EXPR,"<src_sel>[0] == <enc_0>"
TOGGLE_CHECKS_END
```

**Signal path rules:**
- Use FULL hierarchical path from DUT top as given in the spec: `u_sub.u_inner.signal_name`
- Bit widths come from the spec; width mismatches are reported by `check_conn -validate`
- For bus signals, specify bit ranges: `u_sub.data[7:0]`
- Use instance names documented in the spec; if the spec gives none, use top-level ports only

**Naming convention for CONNECTION names:**
- `c_id_<name>` — input data path connections
- `c_od_<name>` — output data path connections
- `c_cp_<name>` — control path connections
- `c_df_<name>` — default / isolation / select-exclusivity / leakage (constant source = spec default)
- `c_pri_<hi>_over_<lo>_ch<i>`, `c_pri_release_<hi>_to_<lo>_ch<i>` — priority winner / release
- `neg_<name>` — negative: intentionally WRONG row, must give a CEX (Step 6b)

### Step 4: Choose Run Flow (ASK THE USER — MANDATORY)

- Use the Upfront Questions answer Q5 (ask now only if it was not answered):

| Option | Output | Run command |
|--------|--------|-------------|
| **A. Standalone TCL** | `jg_conn_setup.tcl` + `RUNCMD_tcl` (Step 4a) | see Step 4a run command |
| **B. Adsim `sim.setup`** | `<cfg_dir>/sim.setup` + `<cfg_dir>/RUNCMD` (Step 4b) | see Step 4b run command |
| **C. Both** | Both files, kept consistent | — |

- Do NOT pick a default silently.
- Config layout, parameter values, run mode, negative configs, vManager/vPlan, report location: from Q6–Q14.

### Step 4b: Adsim `sim.setup` Format (if user selects B or C)

- Follow the reference format of `/proj/adip_digital/rgulghan/adip/adip_digital/adip_pinmux/dv/formal/formal_pinmux/1_io/peri_8/sim.setup`.
- Full generalized template (replace every `<...>`; one file per config dir):
  - Contains the header block, results/compile/incdir settings, `FML_TCL_COMMANDS` (elaborate, `clock -none`/`reset -none`, `check_conn -load`, ProofGrid, `check_cov`), `PRE_SIM_COMMANDS`, vManager/vPlan and `FML_INSTTOP` lines.
  - Read `resources/sim_setup_template.md` when doing this step.

**sim.setup rules:**
- Keep the header block; fill Configuration Parameters from the spec.
- Use `$ADIP_BLOCKS_ROOT`-relative paths, never absolute workarea paths.
- No `check_cov -init` (conflicts with adsim `-jgcov` cov_init, ECOV081).
- Database/UCD export belongs in `pre_exit.tcl`, staged via `PRE_SIM_COMMANDS`.
- `FML_INSTTOP` must equal the elaborate `-top`.
- Comment each CSV load with its spec category.

**sim.setup run command (MANDATORY — generate per config):**
- Write it to `<cfg_dir>/RUNCMD` and print it to the user.
- Generic form:
```
adsim -clean -block <ip_block> -gui -jgcov -jasper -formal \
      -resdir <abs_cfg_dir>/Result_ \
      -force_setup <abs_cfg_dir>/sim.setup
```
- Reference (adip_pinmux, 1_io/peri_8):
```
adsim -clean -block adip_pinmux -gui -jgcov -jasper -formal -resdir /proj/adip_digital/rgulghan/adip/adip_digital/adip_pinmux/dv/formal/formal_pinmux/1_io/peri_8/Result_ -force_setup /proj/adip_digital/rgulghan/adip/adip_digital/adip_pinmux/dv/formal/formal_pinmux/1_io/peri_8/sim.setup
```
- `<ip_block>` = adsim block name (e.g. `adip_pinmux`); `<abs_cfg_dir>` = absolute config directory.
- `-jgcov` requires one-step mode; `-gui` provides it. Use Q9 for GUI vs batch.
- One RUNCMD per config directory; `-resdir` and `-force_setup` must point to the same config dir.

### Step 4a: Create Connectivity TCL Setup (if user selects A or C)

- **CRITICAL:** Use `clock -none` and `reset -none`
  - conn user guide: defining global clock/reset can give false results and hides clock/reset connectivity
- For sequential paths add CLOCK / LATENCIES / DISABLE rows in the CSV instead.
- Inputs are free.
- Add assumes/stopats (user guide Appendix A) only for spec-defined operating conditions.

```tcl
clear -all
set FPV_ROOT <absolute_path>

check_cov -init -type all

analyze -sv09 +libext+.sv+.v +libunboundsearch \
    +incdir+<common_lib_paths> \
    -f ${FPV_ROOT}/rtl_list/filelist.f

elaborate -top <top_module> -disable_auto_bbox \
    -parameter <PARAM1> <val1> \
    -create_related_covers {witness} -extract_covergroups

clock -none
reset -none

# Load connectivity specs (one per category)
check_conn -load ${FPV_ROOT}/connectivity/<ip>_input_data_path.csv
check_conn -load ${FPV_ROOT}/connectivity/<ip>_output_data_path.csv
check_conn -load ${FPV_ROOT}/connectivity/<ip>_control_path.csv
check_conn -load ${FPV_ROOT}/connectivity/<cfg_dir>/spec_default_connections.csv
check_conn -load ${FPV_ROOT}/connectivity/<cfg_dir>/spec_mode_priority.csv

# Negative tests: ALL rows intentionally WRONG, each must give a CEX.
# Always loaded; disabled by default, enabled only in configs the user selects.
check_conn -load ${FPV_ROOT}/connectivity/<cfg_dir>/spec_negative_tests.csv
set RUN_NEGATIVES 0
set conn_list [check_conn -list connection]
if {!$RUN_NEGATIVES} {
    check_conn -disable [lsearch -inline -all $conn_list {neg_*}]
}

# Generate toggle checks — REQUIRED before validate
check_conn -generate_toggle_checks {}

# ALWAYS validate before prove — include condition/disable/clock signals in COI check
check_conn -validate -include all

# Prove all connectivity properties
prove -all

# Re-prove only selected connections after a CSV fix (instead of prove -all):
# check_conn -prove -connection {<conn_name1> <conn_name2>}

# Sign-off reports (see "Connectivity Sign-off Reports")
check_conn -report -file ${FPV_ROOT}/results/conn_report.csv -csv -full_name -show_rtl_info -sort_by classification -force
check_conn -signoff -port -file ${FPV_ROOT}/results/conn_signoff_port.csv -csv -full_name -force

# Coverage waivers: ADD WAIVERS HERE (source waiver TCL files once available)

# Coverage measurement — ALL types under -task {Connectivity}
check_cov -measure -task {Connectivity} \
    -type {statement toggle branch expression stimuli proof} \
    -time_limit 48h -per_property_time_limit 1h -verbose -skip_deadcode

# Reports
file mkdir ${FPV_ROOT}/results
report -force -file ${FPV_ROOT}/results/report_conn.txt -results -summary

# Per-type HTML coverage reports
check_cov -report -task {Connectivity} -type {toggle} -html \
    -report_file ${FPV_ROOT}/results/report_toggle.html \
    -exclude {unreachable waived deadcode} -force
check_cov -report -task {Connectivity} -type {expression} -html \
    -report_file ${FPV_ROOT}/results/report_expression.html \
    -exclude {unreachable waived deadcode} -force
check_cov -report -task {Connectivity} -type {branch} -html \
    -report_file ${FPV_ROOT}/results/report_branch.html \
    -exclude {unreachable waived deadcode} -force
check_cov -report -task {Connectivity} -type {statement} -html \
    -report_file ${FPV_ROOT}/results/report_statement.html \
    -exclude {unreachable waived deadcode} -force

# Combined coverage report
check_cov -report -task {Connectivity} -html \
    -report_file ${FPV_ROOT}/results/report_conn_cov.html \
    -exclude {unreachable waived deadcode} -force
```

**TCL run command (MANDATORY — generate per config):**
- Write it to `<cfg_dir>/RUNCMD_tcl` and print it to the user.
- Generic form (run from `<abs_cfg_dir>`):
```
jg <abs_cfg_dir>/jg_conn_setup.tcl
```
- Batch mode (if user requests): `jg -batch <abs_cfg_dir>/jg_conn_setup.tcl`
- Keep it independent of adsim: no `-jgcov`/`-force_setup`; TCL itself does `check_cov -init`.

- **CRITICAL — Use ABSOLUTE PATHS for all file references in TCL.**
- Define `FPV_ROOT` at top and prefix all paths with `${FPV_ROOT}`.
- JG working directory is `jgproject/`, NOT `fpv_env/`.
- Relative paths will fail with ESW046.

### Step 5: Handle Parameterized / Large Specs
For IPs with many channels/IOs (large `<N_CH>` × `<N_SRC>`), use Python to generate CSVs:

Create `scripts/gen_conn_csv.py`:
- Read IO configuration from Excel or parameter file
- Generate one CSV per channel group or per mux select value
- Parameterize signal paths using channel index
- Output to `connectivity/` directory

**CRITICAL — Signal index math is the #1 source of connectivity failures in parameterized designs (see Pitfall 1):**
```
WRONG: <ctrl_bus>[i*<N_SRC>+P+w]
RIGHT: <ctrl_bus>[(i*<N_SRC>+P)*<CTRL_W>+w]

WRONG: <src_sel>[i*3+:3]
RIGHT: <src_sel>[i*<SEL_W>+:<SEL_W>]  (spec select-group width <SEL_W>, not the minimum ceil(log2(<N_SRC>)) bits)
```
- Always verify computed indices against the spec port widths and index formulas.

### Step 6: Reachability / Anti-Vacuity and Priority (CSV only)

**Reachability / anti-vacuity:**
- Covers come from TOGGLE_CHECKS … TOGGLE_CHECKS_END: JG generates a toggle cover per source bit of every wrapped CONNECTION.
- Expected-CEX `neg_` rows (Step 6b) prove the checker is not vacuous.
- Each scenario below MUST be exercised by the COND_EXPR of at least one CONNECTION row:
  - all modes off (default state)
  - each mode alone
  - each mux select value
  - all modes on (only the top-priority source wins)
  - each (hi, lo) overlap
- Before relying on any witness / precondition cover for COND_EXPR, check `jasper_conn_userguide.pdf` for such an option; do not invent one.

**Priority Masking — lower-priority modes while a higher-priority mode is active (MANDATORY):**
- Priority order comes from the spec ONLY (example: `<mode_A>` > `<mode_B>` > `<mode_C>` > `<mode_D>`; pair notation `<mode_hi>` > `<mode_lo>`).
- For every pair (high, low) with high > low, generate in `<cfg_dir>/spec_mode_priority.csv`:
  - **Winner (positive):** `c_pri_<hi>_over_<lo>_ch<i>` — high source → destination; COND_EXPR: high AND low enabled.
  - **Release (positive):** `c_pri_release_<hi>_to_<lo>_ch<i>` — low source → destination; COND_EXPR: high (and every other mode above low) deasserted, low enabled.
  - **Low-mode outputs (positive):** `c_df_` rows — outputs owned by the low mode at their spec default (or spec-defined pass-through) while high is active.
  - **Masked (negative, in `spec_negative_tests.csv`):** `neg_pri_<lo>_over_<hi>_ch<i>` — low source → destination while high active; must give a CEX.
- Cover all overlap combinations, not only pairs:
  - each high mode with every subset of lower modes enabled (e.g. `<mode_A>`+`<mode_B>`+`<mode_C>`+`<mode_D>`)
  - all modes enabled simultaneously → winner row from the top-priority source
- Traceability category: `PRIORITY`; every row cites the spec priority section.
- CSV form:
```
TOGGLE_CHECKS
CONNECTION,c_pri_<hi>_over_<lo>_ch0,,<src_hi>[0],,<dst_bus>[0]
,COND_EXPR,"<sel_hi>[0] && <sel_lo>[0]"
CONNECTION,c_pri_release_<hi>_to_<lo>_ch0,,<src_lo>[0],,<dst_bus>[0]
,COND_EXPR,"!(<sel_hi>[0]) && <sel_lo>[0]"
CONNECTION,c_df_<lo>_during_<hi>_ch0,,<DEFAULT_PARAM>,,<lo_out_bus>[0]
,COND_EXPR,"<sel_hi>[0] && <sel_lo>[0]"
TOGGLE_CHECKS_END
```
- Negative (masked) row, in `spec_negative_tests.csv`:
```
TOGGLE_CHECKS
CONNECTION,neg_pri_<lo>_over_<hi>_ch0,,<src_lo>[0],,<dst_bus>[0]
,COND_EXPR,"<sel_hi>[0] && <sel_lo>[0]"
TOGGLE_CHECKS_END
```
- Signal names above are illustrative; take real names and default values from the spec (adip_pinmux instance: `resources/pinmux_worked_example.md`).
- Combinational design: these are 0-cycle checks; no clock needed (see KEY PRINCIPLE).

### Step 6b: Negative Scenario Checking (MANDATORY)

- Positive connectivity checks (Steps 3–5) verify that the RIGHT source reaches the RIGHT destination under the RIGHT condition.
- Default / isolation checks verify that outputs are at the spec default when they must be, so WRONG sources cannot leak.
- Negative (expected-CEX) tests verify that the checker itself detects WRONG connections.
- All three are CSV CONNECTION rows (no SVA); all are required for complete verification.

**Default / isolation / select-exclusivity / leakage = POSITIVE constant-source rows (`c_df_`):**
- SOURCE = the spec default constant (e.g. `1'b0`, `1'b1`, or the spec default parameter value); DESTINATION = the output; COND_EXPR = the condition where the spec says the output must be at default.
- The conn user guide allows constant values as sources.
- If the output equals the constant under that condition, no other source can leak onto it.
```
TOGGLE_CHECKS
CONNECTION,c_df_<mode>_ch0,,1'b0,,<dst_bus>[0]
,COND_EXPR,"!(<sel_mode>[0])"
TOGGLE_CHECKS_END
```
- File: `<cfg_dir>/spec_default_connections.csv`.

**Default / Isolated Values — SPEC ONLY (MANDATORY for every `c_df_` and negative-default row):**
- The constant source MUST come from the spec — never from RTL, never assumed `0`.
- Before writing any `c_df_` row, extract per output (record in `req_extraction.csv`, Category `DEFAULT`):
  - **Default value:** exact value per bit (e.g. `1'b0`, `1'b1`, `<DEFAULT_PARAM>[q]`) + spec section.
  - **Level:** IP-level (fixed in the IP) or SoC-context (set by parameter / tie-off / integration).
    - IP-level → hard-code the spec value as the CONNECTION source.
    - SoC-context → use the spec default parameter value of each config; run per config with the spec/integration values.
  - **Allowed alternatives:** does the spec permit other values?
    - Single value only → one `c_df_` row with that constant.
    - Set of values (e.g. param-programmable, either 0 or 1) → separate configs, one per allowed value (param value per config), each with its own `c_df_` row for that value.
    - "Don't care" / undefined → no `c_df_` row; rely on the expected-CEX `neg_` rows.
- If the spec does not state the default, its level, or whether other values are allowed:
  - log a SPEC GAP and ASK the user; do NOT generate that row.
- Every `c_df_` / negative-default row in `formal_traceability.csv` must reference the `DEFAULT` SPEC_ID it relies on.

**Why negative tests matter:**
- A mux that always outputs `1'b1` can pass positive checks whose conditions are never met (vacuous) or a checker can be mis-configured.
- Expected-CEX rows prove the tool distinguishes right from wrong connections.

**NOTE — no `ILLEGAL` keyword:** the 2025.09 conn user guide has no `ILLEGAL`/negative-connection keyword.
- Negatives are intentionally WRONG CONNECTION rows that must each give a CEX.

**Negative tests (`<cfg_dir>/spec_negative_tests.csv`, prefix `neg_`):**
- Header comment in the CSV: `ALL rows INTENTIONALLY WRONG — each must give a CEX`.
- Categories:
  - wrong channel mapping (ch i source → ch j destination; representative pairs: adjacent, first/last, mid-range)
  - wrong source under a select value
  - wrong mode source
  - reversed priority (`neg_pri_<lo>_over_<hi>_ch<i>`)
  - non-default value on an isolated output (e.g. `1'b1` when spec default is `1'b0`)
- A `neg_` row that PROVES is a finding (checker vacuous or spec/RTL issue) → `formal-cex-debug` flow.
- Loading: a CEX can mark a regression config FAIL (adsim error pattern).
  - Load the negative CSV in a SEPARATE `check_conn` task/config, or keep it out of regression configs.
  - Configs that run negatives come from Q10; the templates load the CSV and `check_conn -disable` the `neg_*` rows elsewhere.

**Category details (constant-source templates, negative rows, `gen_conn_csv.py` generator, expected row counts):**
- Read `resources/negative_checks.md` when doing this step.
- adip_pinmux instance with reference CSVs: `resources/pinmux_worked_example.md`.

**File Organization:**

| Check | File | Row type |
|-------|------|----------|
| Mode isolation, select exclusivity, default values, leakage | `<cfg_dir>/spec_default_connections.csv` | positive `c_df_` CONNECTION (constant source) |
| Priority winner / release / low-mode outputs | `<cfg_dir>/spec_mode_priority.csv` | positive `c_pri_` / `c_df_` CONNECTION |
| Negative (expected-CEX) | `<cfg_dir>/spec_negative_tests.csv` | intentionally wrong `neg_` CONNECTION |

### Step 7: Debug and Waiver

**First-level check_conn debug (run BEFORE formal-cex-debug):**
- Connection reported "Outside COI" by `-validate`:
  - `check_conn -connection <name> -debug validate` → returns the signals not found in the destination COI.
  - Cause is usually a wrong path/index/name in the CSV vs the spec → fix CSV; if the spec path is correct, RTL finding.
  - Requires `check_conn -validate` to have run first.
- Failing connection whose trace goes through a black box or register:
  - `check_conn -connection <name> -debug bbox_out` → black-box outputs in the failing trace (missing RTL / auto-bbox).
  - `check_conn -connection <name> -debug register` → register ports in the trace (path has latency → add LATENCIES/CLOCK).
- After fixing a CSV row: re-prove only those connections with `check_conn -prove -connection {<names>}`.
- Negative tests per config: `check_conn -enable|-disable [lsearch -inline -all [check_conn -list connection] {neg_*}]`.
  - Disabled connections are excluded from `-report`, `-signoff` and `-save_as`.

**CEX Debug — use the `formal-cex-debug` skill (MANDATORY on any failing property):**
- Load skill `formal-cex-debug` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-cex-debug/SKILL.md`)
- Trigger: any positive CONNECTION row (incl. `c_df_`, `c_pri_`) that fails, any toggle cover that is unreachable, and any intentional negative (`neg_`) row that does NOT give a CEX.
- Load it and follow its steps (waveform load → backward trace → spec correlation → report → JG debug TCL; batch mode for many fails).
- Connectivity-specific rules:
  - Spec is the reference: classify against the spec section of the SPEC_ID, never "fix" the check to match RTL.
  - Check CSV causes first: index math (Pitfall 1), COND_EXPR quoting (Pitfall 2), missing condition, wrong default value (Step 6b).
  - Classification → action:
    - RTL bug → design finding, keep the check failing
    - CSV error vs spec → fix the CSV, re-run
    - Spec gap / ambiguity → log in `req_extraction.csv`, ask the user
    - Negative test with no CEX → negative row is wrong or the checker is vacuous; fix it or report the spec/RTL issue
- Output: `fpv_env/rca/cex_<property>.md` per failure (+ batch summary); link from `index.html`.

**Waiver categories for combinational connectivity:**

| Waiver Type | When | Detail |
|-------------|------|--------|
| **Toggle** | Unused signal bits that can never toggle | Unused select bits (e.g., bit[3] of 4-bit group when only 3 used), constant-tied mux inputs (`demux_cell` with one input = 0), write-once registers after first write |
| **Expression** | Dead sub-expressions in gate-level cells | `(S0 & B)` when B is constant 0 in mux primitive, `(~S0 & A)` when A is constant 0 |
| **Branch** | Unreachable case statement branches | Case values that cannot occur with given parameterization, default branches when all valid values are covered |
| **Proof** | Properties that are architecturally unreachable | COV_BUS_WRITE on RO registers, CONNECTION rows vacuous due to configuration constraints |

**Common connectivity failures:**
1. Signal typo in CSV → `check_conn -validate` catches this
2. Bit-width mismatch → check widths in spec; report spec/RTL disagreement as a finding
3. Missing condition → connection only valid under certain mux select
4. Latency mismatch → add LATENCIES row with correct pipeline depth
5. Inverted polarity → source is active-high, dest is active-low (add NOT)
6. Signal index miscalculation → verify computed indices against spec formulas (Pitfall 1)
7. Unquoted COND_EXPR containing a comma → CSV cell split / parse error (Pitfall 2)
8. Missing TOGGLE_CHECKS / TOGGLE_CHECKS_END → toggle covers not generated (Pitfall 3)
9. Spec-RTL mismatch → log as a finding/spec gap; never change the check to match RTL (Pitfall 5)

**Waiver TCL — syntax is `check_cov -waivers -add` (jasper_command_reference.pdf, check_cov), NOT `check_conn`:**
- `check_cov -waive -toggle/-expr/-branch` does NOT exist in 2025.09; verify options in the command reference before use.
```tcl
# Toggle waiver — unused select bit
check_cov -waivers -add -comment "Tied to 0, unused in this config" \
    -instance <hierarchy_path> -expression {<signal>[<bit>]} -type toggle

# Expression waiver — dead sub-expression in mux primitive (by source location)
check_cov -waivers -add -comment "Constant-0 mux input — dead branch" \
    -source_file <file> -start_line <line> -end_line <line> -type expression

# Branch waiver — unreachable case branch
check_cov -waivers -add -comment "Default case unreachable for this config" \
    -source_file <file> -start_line <line> -end_line <line> -type branch

# Export / re-import waivers
check_cov -waivers -export -file_name <waiver_file>
check_cov -waivers -import -file_name <waiver_file>
```
- Confirm `-type` values for your coverage model in jasper_cov_userguide.pdf.

**Waiver scaling for parameterized designs:**
- Waivers scale dramatically with `<N_CH>` × `<N_SRC>` (cfg_min → cfg_max grows by orders of magnitude, mostly expression waivers in mux primitives; measured adip_pinmux counts in `resources/pinmux_worked_example.md`).
- Use Python scripts to generate waiver TCL programmatically.

- Target: **100% formal coverage AFTER waivers** across all configurations.

Create `scripts/gen_waiver_tcl.py`:
- Read parameter configuration
- Generate toggle waivers for unused select bits per channel
- Generate expression waivers for dead mux primitive branches
- Output to `connectivity/waiver_conn_<cfg>.tcl`

**Waiver Policy:**

Legitimate waivers:
- Architecturally unreachable coverage points (structural analysis)
- Features disabled by parameter in a given config
- Unused signal bits (documented architectural choice)
- Constant-tied inputs in mux/demux primitives

NOT legitimate:
- "Couldn't figure out why coverage is low" — investigate further
- "Connection check too complex for engine" — simplify or decompose
- Waivers on reachable paths to hide low coverage

---

## Connectivity Pitfalls Reference

**PITFALL 1 — CSV SIGNAL INDEX MISCALCULATION:**
- Most common error in connectivity CSV generation for parameterized designs.
- Always verify computed indices against the spec port widths.
```
WRONG: <ctrl_bus>[i*<N_SRC>+P+w]
RIGHT: <ctrl_bus>[(i*<N_SRC>+P)*<CTRL_W>+w]

WRONG: <src_sel>[i*3+:3]
RIGHT: <src_sel>[i*<SEL_W>+:<SEL_W>]  (spec select-group width <SEL_W>, not the minimum ceil(log2(<N_SRC>)) bits)
```
- adip_pinmux instance: `resources/pinmux_worked_example.md`.

**PITFALL 2 — CSV COND_EXPR QUOTING:**
- Mandatory when the expression contains a comma; ADI rule: always quote:
```
RIGHT: ,COND_EXPR,"<sel_A>[0]"
WRONG: ,COND_EXPR,<sel_A>[0]
```

**PITFALL 3 — TOGGLE_CHECKS / TOGGLE_CHECKS_END MISSING:**
- Every CSV spec file MUST wrap its connections in `TOGGLE_CHECKS` … `TOGGLE_CHECKS_END`.
- Without it, JG generates connectivity assertions but NOT toggle covers, reducing coverage completeness.

**PITFALL 4 — CHECK_CONN -VALIDATE BEFORE PROVE:**
- Always run `check_conn -validate` after loading all CSVs.
- Catches: signal name typos, width mismatches, overlapping conditions.
- Without `-validate`, errors only appear during prove.

**PITFALL 5 — SPEC-RTL MISMATCH (UNDOCUMENTED INTERFACES):**
- Spec may NOT document all interfaces (e.g., a whole mode/interface missing from the spec).
- Do NOT read RTL to fill the gap.
- Record each missing item as a SPEC GAP (Formally_Verifiable=NO, Notes="Spec gap — awaiting spec update") and ask the user / spec owner.
- Checks are written only after the spec documents the behavior.

**PITFALL 6 — GLOBAL CLOCK/RESET IN CONNECTIVITY:**
```
WRONG: clock PCLK / reset -expression {!PRESETn}
RIGHT: clock -none / reset -none
       + per-connection CLOCK / LATENCIES / DISABLE rows for sequential paths
```
- Global clock/reset over-constrains the checks and stops clock/reset nets from being verified as connections (jasper_conn_userguide.pdf).

**PITFALL 7 — COMMON LIBRARY DEPENDENCY:**
- Some IPs depend on common library primitives (e.g., `adip_mux_cell` from `adip_boxes.v`).
- These MUST be explicitly included + `+incdir` for headers.
- Do NOT include vendor cell libraries that pull in undefined dependencies.

**PITFALL 8 — AUTO BLACKBOX IN COMBINATIONAL DESIGNS:**
- Use `-disable_auto_bbox` in elaborate to prevent JG from blackboxing gate-level cells that ARE needed for connectivity checking.

---

## CSV Organization Strategy

| IP Type | CSV Organization |
|---------|-----------------|
| Pin Mux (`<N_CH>` channels) | One CSV per channel or per channel group |
| Data Path | One CSV per functional flow (TX path, RX path) |
| Interconnect | One CSV per master, with COND_EXPR for address decode |
| Control Path | One CSV per subsystem (enables, selects) |
| Register Routing | One CSV per register bank |
| Feedback | One CSV for status/interrupt paths back to controller |

## Configuration Matrix for Connectivity

- For parameterized designs, create multiple configurations to cover:

| Config | Parameters | Purpose |
|--------|-----------|---------|
| cfg_min | `<N_CH>`=1 (or minimum) | Fast iteration, debug CSV correctness |
| cfg_default | `<N_CH>`=default | Baseline regression |
| cfg_max | `<N_CH>`=max | Full parameterization proof |
| cfg_feature_X | Feature toggle | Per-feature coverage |

- Each config needs its own:
- Generated CSV specs (from `gen_conn_csv.py`)
- Generated waiver TCL (from `gen_waiver_tcl.py`)
- JG run producing per-config coverage report

## Connectivity Sign-off Reports (MANDATORY)

- Generate after `prove` completes (TCL: after `prove -all`; sim.setup: in `pre_exit.tcl`, since FML_TCL_COMMANDS run before prove).
- **1. Connection report** — combined proof status per connection:
  - `check_conn -report -file <results>/conn_report.csv -csv -full_name -show_rtl_info -sort_by classification -force`
  - Contains name, source/destination, proof status, toggle status, COI status, classification, RTL info.
  - Feeds `formal_traceability.csv` Status, `signoff_matrix.csv` and the HTML report.
  - Every enabled positive row must be proven; every enabled `neg_` row must be CEX.
- **2. Port sign-off report** — spec completeness:
  - `check_conn -signoff -port -file <results>/conn_signoff_port.csv -csv -full_name -force` (optional `-instance <inst>`).
  - Lists every instance port with #connections as source and as destination.
  - Any port with 0 source AND 0 destination connections = not covered by the spec CSVs:
    - Do NOT add a check from RTL.
    - Log it as a SPEC GAP in `req_extraction.csv` (Formally_Verifiable=NO, Notes="unreferenced port — signoff report") and ask the user.
    - Close only when the spec documents the port (then add the CONNECTION) or the user marks it N/A with reason.
- **3. Classification review** (classification column of the connection report / Connectivity Viewer):
  - `tie 0` / `tie 1` / `tie const` — destination tied to a constant:
    - Expected only for `c_df_` rows whose spec default equals that constant.
    - On any data/control row → finding: path is hardcoded (cross-check with the final param-spec-audit).
  - `no_connection` (with auto-blackbox) → source not reaching destination through a black box → check `-disable_auto_bbox` and filelist.
  - `partial equal name` / `none` — informational; review that the spec mapping is intended.
- Link both report files from `index.html`.

## Traceability (MANDATORY)

- Formal connectivity verification requires full spec-to-property traceability.
- Generate TWO CSV files in `fpv_env/traceability/`:

### File 1: `req_extraction.csv` — Spec Requirement Extraction

- Extract every connectivity-relevant requirement from the spec ONLY.
- Each row is one atomic requirement.

**Columns:**
```
SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes
```

**Column definitions, Category values (`MUX_DATA`, `DEMUX_DATA`, `CTRL`, `FEEDBACK`, `ISOLATION`, `DEFAULT`, `PRIORITY`, `PARAM`, `INTEG`), Formally_Verifiable values (`YES` / `ASSUME` / `NO`) and example rows:**
- Read `resources/traceability_format.md` when doing this step.

- **CRITICAL:** Every row MUST cite a spec section.
- `PDF_Section=RTL` is NOT allowed.
- Undocumented behavior is listed as a spec gap, not a requirement.

### File 2: `formal_traceability.csv` — Requirement-to-Property Mapping

- Map each SPEC_ID from `req_extraction.csv` to the specific CONNECTION rows (positive, `c_df_`, `c_pri_`, `neg_`) that verify it.
- Each row is one property mapping.

**Columns:**
```
SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status
```

**Column definitions, Property_Type values (`CONNECTION` / `NEG` / `TOGGLE` / `ASSUME`), Status values (`MAPPED` / `UNMAPPED` / `WAIVED` / `INFRA`) and example rows:**
- Read `resources/traceability_format.md` when doing this step.
- One SPEC_ID may map to MANY properties (e.g. one CONNECTION row per channel); each mapping gets its own row.

### Traceability Completeness Check

- After generating both CSVs, verify:
1. Every `SPEC_ID` with `Formally_Verifiable=YES` in `req_extraction.csv` has at
   least one `MAPPED` row in `formal_traceability.csv`
2. No `UNMAPPED` entries remain (unless explicitly justified)
3. Every CONNECTION name in the connectivity CSVs appears in `formal_traceability.csv`
4. Every `neg_` CONNECTION name in `spec_negative_tests.csv` appears in `formal_traceability.csv` (Property_Type `NEG`)

- **Gap report:**
  - Any SPEC_ID with `Formally_Verifiable=YES` but no corresponding `MAPPED` entry in `formal_traceability.csv` is a **verification gap**
  - It must be closed before signoff.

### Sign-Off Traceability — use the `formal-traceability` skill (MANDATORY after proofs)
- Load skill `formal-traceability` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-traceability/SKILL.md`)
- Run after all configs are proven and CEXs are resolved; before vPlan creation and the Final Audit.
- Reuse (do not regenerate) `req_extraction.csv` and `formal_traceability.csv` from this section as its Step 1/3 inputs.
- Execute from it:
  - Step 2: extract labels from the CSVs (CONNECTION names: `c_*`, `c_df_*`, `c_pri_*`, `neg_*`)
  - Step 4: collect proof results per config (1_io, 8_io, 32_io, ...)
  - Step 5: `signoff_matrix.csv`
  - Step 6: completeness audit (unmapped requirements, orphan properties)
  - Step 7 / 8 (Jama / Confluence publish): ONLY per Q16
- Spec-only rule: every row cites a spec section; no `PDF_Section=RTL`.
- Output: `fpv_env/traceability/signoff_matrix.csv` (+ audit report); link from `index.html`.

## Output Files

```
fpv_env/connectivity/
├── <ip>_input_data_path.csv    Input data path connectivity spec
├── <ip>_output_data_path.csv   Output data path connectivity spec
├── <ip>_control_path.csv       Control path connectivity spec
├── <ip>_feedback.csv           Feedback/status path spec
├── <cfg_dir>/spec_default_connections.csv  Default / isolation c_df_ rows (constant source)
├── <cfg_dir>/spec_mode_priority.csv        Priority c_pri_ winner / release rows
├── <cfg_dir>/spec_negative_tests.csv       Expected-CEX neg_ rows (ALL intentionally wrong)
├── jg_conn_setup.tcl           JG connectivity TCL (flow A/C)
├── <cfg_dir>/sim.setup         Adsim setup per config (flow B/C)
├── <cfg_dir>/RUNCMD            adsim run command for sim.setup (flow B/C)
├── <cfg_dir>/RUNCMD_tcl        jg run command for TCL setup (flow A/C)
├── <cfg_dir>/pre_exit.tcl      Post-prove hook (UCD export, flow B/C)
├── waiver_*.tcl                Coverage waivers (added later — see "ADD WAIVERS HERE")
└── waiver_conn_<cfg>.tcl       Per-config waivers (if parameterized)

fpv_env/scripts/
├── gen_conn_csv.py             Parameterized CSV generator (positive, c_df_, c_pri_, neg_)
└── gen_waiver_tcl.py           Parameterized waiver generator

fpv_env/traceability/
├── req_extraction.csv          Spec requirement extraction (SPEC_ID → requirement)
├── formal_traceability.csv     Requirement-to-property mapping (SPEC_ID → property)
└── signoff_matrix.csv          Per-config sign-off (formal-traceability)

fpv_env/rca/
└── cex_<property>.md           CEX root-cause reports (formal-cex-debug)

fpv_env/results/
├── report_conn.txt             JG results summary
├── conn_report.csv             check_conn -report (status, classification, RTL info)
├── conn_signoff_port.csv       check_conn -signoff -port (unreferenced ports = spec gaps)
└── report_conn_cov.html        Coverage report (HTML)

fpv_env/reports/                HTML report suite (see resources/html_report_spec.md)
```

## HTML Report Generation (MANDATORY)

- After connectivity verification completes, generate the publishable HTML report suite with `scripts/gen_conn_report.py` (output `fpv_env/reports/`).
- 4 page types: `index.html` (landing page), `csv_generation_methodology.html`, `mapping_verification_methodology.html`, `mapping_verification_report_<cfg>.html` (per-config detail).
- Full page contents, styling, generator script usage, output files and publishing steps:
  - Read `resources/html_report_spec.md` when doing this step.

## Optional Step: vPlan Creation (USER DECIDES — now or later)

- Use the `formal-vplan` skill:
  - Load skill `formal-vplan` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-vplan/SKILL.md`)
- Use the Upfront Questions answer Q14 (ask now only if not answered; do NOT decide silently):
  - **NOW** → run it after `req_extraction.csv` / `formal_traceability.csv` are complete, before the Final Audit.
  - **LATER** → skip; keep `ENABLE_VPLAN` / `VPLAN_SOURCE` commented in sim.setup; list it as a pending item in the final summary.
  - **NOT NEEDED** → skip; remove the vManager vPlan lines from sim.setup.
- If NOW:
  - Load the `formal-vplan` skill and follow its steps in full.
  - Requirements come from the spec only (same SPEC_IDs as `req_extraction.csv`, category `CONN`/`PRIORITY`/`DEFAULT`/...).
  - Section the plan by connectivity category (Input/Output data path, Control, Feedback, Defaults, Priority, Negative).
  - Map properties by CONNECTION name patterns (`c_id_*`, `c_cp_*`, `c_df_*`, `c_pri_*`, `neg_*`) so the plan works for all configs.
  - Output: `<IP>_Formal_VPlan_Connectivity.vplanx`; set `VPLAN_SOURCE` to it and enable `ENABLE_VPLAN : 1`.
  - Re-run the sim.setup RUNCMD so vManager grades the plan.
- The user can request the vPlan at any later time; the skill then starts from this step using the existing CSVs and traceability files.

## Final Step: Parameter & Default-Value Audit (MANDATORY — run LAST)

- After connectivity proofs, waivers, traceability and HTML reports are complete, run the `param-spec-audit` skill.
  - Load skill `param-spec-audit` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/param-spec-audit/SKILL.md`)
  - Load it and follow its Steps 1–4 in full.
- Why: connectivity checks prove routing for the configs that were run; the audit catches defaults/params that
  are hardcoded in RTL or never exercised (e.g. the adip_pinmux `PERIPHERAL_OUT_DEFAULT` escape).
- Inputs reused from this flow (do not re-ask the user if already known):
  - IP name, top module, RTL filelist (compile list from Step 4)
  - Spec + the `DEFAULT` rows of `req_extraction.csv` (Step 6b) → seed the audit spec CSV
  - DV dir = this connectivity directory (sim.setup `-param`, TCL `elaborate -param`, CSVs, waivers)
  - SoC context: from Q15 (SoC RTL glob or SoC CSV); never invent SoC values
- Spec-only rule still applies:
  - Expected values come from the spec only.
  - RTL is read here only as the item UNDER AUDIT (to find literals that bypass a param), never to define expected values.
- Feed results back:
  - **DV gap** → add the missing config / CONNECTION / negative check, re-run, then re-run the audit.
  - **Spec gap** → log in `req_extraction.csv` and ask the user.
  - **RTL non-compliant** → report as a design finding; do NOT change checks to match RTL.
- Output: `fpv_env/reports/<ip>_param_audit.html`; link it from `index.html`.

## Reference
**Authoritative Jasper documentation (ALWAYS consult first):**
`/cad/adi/apps/cadence/jasper/2025.09-p002/doc`

- See the TOOL DOCUMENTATION table at the top of this skill for which document to use.

**Skill resources (`resources/`, read when doing the referenced step):**
- `resources/sim_setup_template.md` — Step 4b full adsim `sim.setup` template
- `resources/negative_checks.md` — Step 6b default/isolation (`c_df_`) and negative (`neg_`) CSV templates, generator, expected counts
- `resources/traceability_format.md` — `req_extraction.csv` / `formal_traceability.csv` column definitions and example rows
- `resources/html_report_spec.md` — HTML report suite (4 pages, styling, generator, publishing)
- `resources/pinmux_worked_example.md` — Worked example (adip_pinmux) mapping all generic placeholders
- The `jasper-conn` skill at `/cad/adi/apps/chipagents/config/main/skills/jasper-conn/` contains additional connectivity methodology details, example CSV formats (`interrupt_connectivity.csv`), and alias tables (`FV_global_aliases.csv`).

## Quality Checklist

### Positive Connectivity
- [ ] Every spec-documented signal path has a CONNECTION row
- [ ] No check derived from RTL; spec gaps logged and raised to user (Pitfall 5)
- [ ] All hierarchical paths taken from spec; `check_conn -validate` clean
- [ ] Bit widths match spec for source and destination
- [ ] Signal indices verified against spec port widths/formulas (Pitfall 1)
- [ ] Conditional connections have COND_EXPR with double-quoted values (Pitfall 2)
- [ ] Every CSV file wrapped in TOGGLE_CHECKS … TOGGLE_CHECKS_END (Pitfall 3)
- [ ] No `ILLEGAL` rows in CSVs; negatives are expected-CEX `neg_` CONNECTION rows; no SVA anywhere
- [ ] Pipeline connections have LATENCIES with correct depth

### Negative Connectivity (Step 6b)
- [ ] Mode isolation: `c_df_` row (constant source = spec default) for every output owned by an inactive mode
- [ ] Select decode exclusivity: `c_df_` row for every unselected demux/mux output
- [ ] Default output values / default routing: rows for all outputs when no mode active
- [ ] Every `c_df_` constant taken from spec, with level (IP / SoC-context) and allowed-value set recorded (one config per allowed value); gaps asked to user
- [ ] Priority: `c_pri_` winner + `c_pri_release_` rows per (hi, lo) pair in `spec_mode_priority.csv`
- [ ] Negatives in `spec_negative_tests.csv` (header: ALL rows INTENTIONALLY WRONG): wrong channel (representative pairs), wrong source under select, wrong mode source, reversed priority, non-default value
- [ ] Upfront Questions Q1–Q16 asked once and answers recorded; negative-test configs per Q10
- [ ] Reachability scenarios (all modes off, each mode alone, each select value, all modes on, each hi+lo overlap) exercised by at least one COND_EXPR
- [ ] Naming convention followed (`c_df_`, `c_pri_`, `neg_`)
- [ ] Default / priority / negative rows generated for all parameter configs

### CEX Debug
- [ ] Every failing / unreachable property analysed with `formal-cex-debug`; RCA file per failure
- [ ] Every intentional negative test gave a CEX
- [ ] No check changed to match RTL; RTL bugs reported as findings

### Sign-Off Traceability
- [ ] `formal-traceability` run; `signoff_matrix.csv` generated per config
- [ ] Completeness audit clean (no unmapped YES requirements, no orphan properties)

### vPlan (optional)
- [ ] User asked NOW / LATER / NOT NEEDED; choice recorded in final summary
- [ ] If NOW: vplanx generated via `formal-vplan`, `VPLAN_SOURCE` set, RUNCMD re-run

### Final Audit
- [ ] `param-spec-audit` run after connectivity; report `<ip>_param_audit.html` generated and linked
- [ ] All audit FAILs closed (DV gaps fixed, spec gaps raised, RTL findings reported)

### Traceability
- [ ] `req_extraction.csv` generated from spec only; every row cites a spec section
- [ ] Spec gaps listed separately (no `PDF_Section=RTL` rows)
- [ ] `formal_traceability.csv` generated mapping every SPEC_ID to properties
- [ ] Every `Formally_Verifiable=YES` requirement has at least one `MAPPED` entry
- [ ] No `UNMAPPED` entries remain (gaps closed or justified)
- [ ] Every CONNECTION name in CSVs appears in `formal_traceability.csv`
- [ ] Every `neg_` name in `spec_negative_tests.csv` appears in `formal_traceability.csv`

### Infrastructure
- [ ] `check_conn -generate_toggle_checks {}` run before validate
- [ ] `check_conn -validate -include all` passes with 0 errors before prove
- [ ] COND_EXPR and CONDITION never mixed on one CONNECTION; CONDITION(STABLE) only for spec-static signals, in its own task if needed
- [ ] Negative rows loaded and disabled/enabled per config via `check_conn -disable/-enable`
- [ ] Outside-COI connections debugged with `check_conn -connection <c> -debug validate`
- [ ] `check_conn -report` CSV generated; all enabled positives proven, all enabled `neg_` rows CEX
- [ ] `check_conn -signoff -port` CSV generated; every unreferenced port logged as spec gap / closed by user
- [ ] Classification reviewed: no unexpected `tie 0/1/const` or `no_connection`
- [ ] `clock -none` / `reset -none` used; sequential paths use CLOCK/LATENCIES/DISABLE rows (Pitfall 6)
- [ ] `-disable_auto_bbox` in elaborate (Pitfall 8)
- [ ] Common library files explicitly included with `+incdir` (Pitfall 7)
- [ ] Coverage measured with `-task {Connectivity}` after prove
- [ ] Waivers use `check_cov -waivers -add` (NOT `check_conn`, NOT `check_cov -waive`)
- [ ] Waivers documented with engineering justification
- [ ] Waiver policy followed (no waivers on reachable paths)
- [ ] 100% formal coverage target AFTER waivers
- [ ] Parameterized generation scripts tested for all configs
- [ ] Per-config coverage reports generated (HTML)
