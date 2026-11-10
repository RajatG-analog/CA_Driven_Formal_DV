- ARCHIVED — superseded by ../SKILL.md; do not load (contains RTL-derived rules and invalid TCL).
# Formal FPV Skill — SVA Assertions, Models, Assumptions, Scoreboard

## When to Use
Activate when the user asks to:
- Create FPV assertions / SVA properties for an IP
- Write formal assumptions for an IP
- Create behavioral models for black-boxed cells
- Build a scoreboard for end-to-end data integrity
- Create a JasperGold FPV TCL setup
- Create a bind file for formal verification
- Write a complete FPV environment from a spec
- Debug CEX (counter-examples) from JasperGold runs

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| **Spec PDF** | IP specification document | `ADIP_SRAM_Controller.pdf` |
| **RTL files** | RTL source files or filelist.f | `filelist.f` |
| **Top module** | DUT top for formal | `sram_top_scan_wrapper` |
| **verification_plan.md** | Formal verification plan (from Step 1b) | `fpv_env/verification_plan.md` |
| **Output dir** | Where to write FPV collateral | `fpv_env/` |

---

## Step-by-Step Procedure

### Step 1: Read the Verification Plan
- Read `verification_plan.md` to understand:
- Feature areas and their verification approach
- Bind targets per feature
- Key signals per feature
- Expected assertion counts
- Assumption strategy
- Black-box strategy
- Parameter configurations

### Step 2: Read the Spec (Per Feature)
For EACH feature area listed in the verification plan:
1. Read the relevant spec section using `View` or `queryFileWithEmbeddings`
2. Extract EXACT behavioral requirements: signals, values, timing, conditions
3. Do NOT write assertions from memory — always verify against the spec first

### Step 3: Read the RTL (Per Bind Target)
For each bind target module:
1. Read the module header (parameters, ports)
2. Identify internal signals needed for assertions (wires, regs inside the module)
3. Apply Rule 14 (Signal Scope Analysis) — determine what is accessible
4. Note any generate blocks that affect signal accessibility

### Step 3b: Filelist Dependency Audit (MANDATORY)
- After reading RTL, verify the filelist covers ALL dependencies:

**Dependency Audit Procedure:**
1. Grep ALL RTL files for instantiated modules, interfaces, and packages
   that are NOT defined within the IP's own RTL directory
2. For EACH instantiated module name, classify it:
   - **DEFINED IN FILELIST**: module .sv/.v file is in filelist.f → OK
   - **SV INTERFACE** (ahb5_if, apb4_if, etc.): MUST be compiled
     → Add source file to filelist BEFORE first user
   - **TECH CELL** (adip_ICGCell, adip_clk_and, adip_sync_2ff, etc.):
     vendor cell without available RTL source
     → Add to -bbox_m list in elaborate command
   - **SRAM MACRO** (sram_8192x39, etc.): memory macro model
     → Add to -bbox_m list OR provide behavioral model
   - **COMMON UTILITY** (adip_gen_sync, etc.): from adip_common
     → Find source in common library, add to filelist
   - **UNKNOWN**: cannot find definition anywhere
     → STOP. Ask the user for the source file or confirm blackboxing
3. Build the -bbox_m list for the elaborate command
4. Verify: count of (filelist modules + bbox modules) must equal count of
   all instantiated modules. Any mismatch = elaborate WILL fail.

- **WHY THIS IS MANDATORY:**
  - Every JasperGold elaborate failure due to a missing module wastes a full analyze+elaborate cycle.
  - The errors appear one at a time — if 5 modules are missing, you get 5 separate runs each failing on the next missing module.
  - This one-time upfront check prevents ALL of those failures.

- **CRITICAL — SV INTERFACES CANNOT BE BLACKBOXED:**
  - ADIP IPs commonly use shared SV interfaces from adip_common (ahb5_if, apb4_if) that bundle bus signals.
  - The IP's simulation filelist often pulls these in via +incdir or library mappings that don't exist in the JasperGold formal context.
  - If missing, JG reports "instantiating unknown empty module" errors that look like tech cell issues but are actually missing source files.
  - SV interfaces CANNOT be blackboxed — they must be compiled.

### Step 4: Create Behavioral Models
- Create models in `models/` for black-boxed cells:

**RAM Model** (`<ip>_fpv_ram_model.sv`):
```systemverilog
module <ip>_fpv_ram_model #(
  parameter ADDR_WIDTH = 13,
  parameter DATA_WIDTH = 39
) (
  input  logic                  clk,
  input  logic [ADDR_WIDTH-1:0] addr,
  input  logic [DATA_WIDTH-1:0] d,
  input  logic [DATA_WIDTH-1:0] wem,
  input  logic                  we,
  input  logic                  me,
  output logic [DATA_WIDTH-1:0] q
);
  reg [DATA_WIDTH-1:0] mem [0:2**ADDR_WIDTH-1];
  integer idx;
  always @(posedge clk) begin
    if (me && we) begin
      for (idx = 0; idx < DATA_WIDTH; idx = idx + 1)
        if (wem[idx]) mem[addr][idx] <= d[idx];
    end
    if (me && !we) q <= mem[addr];
  end
endmodule
```

**ROM Model** (`<ip>_fpv_rom_model.sv`):
```systemverilog
module <ip>_fpv_rom_model #(
  parameter ADDR_WIDTH = 13,
  parameter DATA_WIDTH = 39
) (
  input  logic                  clk,
  input  logic [ADDR_WIDTH-1:0] addr,
  input  logic                  me,
  output logic [DATA_WIDTH-1:0] q
);
  reg [DATA_WIDTH-1:0] mem [0:2**ADDR_WIDTH-1];
  always @(posedge clk) if (me) q <= mem[addr];
endmodule
```

**ECC Reference Model** (if applicable):
- Pure combinational — encode and decode functions matching spec algorithm
- Used by scoreboard to independently predict parity / corrected data

**Error Injection Mechanism** (if ECC/error detection exists):
- Declare `error_inject_mask` as free variable (e.g., 39-bit for ECC)
- XOR onto memory read data: `sram_rdata = clean_data ^ error_inject_mask`
- Constrain: `$countones(error_inject_mask) <= <max_errors>`
- Constrain: `error_inject_mask == 0` during writes (protect data integrity)
- WARNING: If error_inject_mask is non-zero during write-back (RMW), memory
  model receives corrupted data, breaking scoreboard (see Pitfall 26)

**CSR Free Variable Strategy** (if wrapper methodology):
- CUT key CSR signals from the register block (MMR)
- Declare as free variables with `(* keep = "true" *)`
- Add STABILITY assumptions: CSR must not change during active transactions
- FORCE specific values for primary verification targets (e.g., ecc_en=1)
- Add COVER PROPERTIES to verify reachability of free variable values
- WARNING: Free variables may not be explored if solver finds easy paths
  with defaults — force critical values or add covers (see Pitfall 25)

### Step 5: Create Assumptions File
- Create `props/<ip>_assumptions.sv`:

```systemverilog
module <ip>_fpv_assumptions (
  input logic clk, rst_n,
  // all constrained input signals
);
  default clocking @(posedge clk); endclocking
  default disable iff (!rst_n);

  // ===== DFT Constraints (EVERY ADIP IP) =====
  ASM_001_scan_mode_off:   assume property (scan_mode == 1'b0);
  ASM_002_scan_enable_off: assume property (SE == 1'b0);
  ASM_003_scan_in_off:     assume property (scan_in == 1'b0);

  // ===== Reset Constraints =====
  ASM_010_resetn_monotonic: assume property (rst_n |=> rst_n);

  // ===== Protocol Constraints =====
  // From spec AoU section — cite spec section in comment

  // ===== Static Configuration Inputs =====
  // Constrain inputs configured once and never changed.
  // Source: Spec "Assumptions of Use" (AoU) section.
  // WARNING: Audit ALL inputs — specs often MISS static inputs that RTL
  // depends on. If formal finds CEX caused by toggling a "static" input,
  // add an assumption AND file a spec gap.
  // PATTERN: CSR stability during active transactions:
  //   (htrans != 2'b00) |-> $stable(csr_signal)

  // ===== Protection Keys (if applicable) =====
  // Enable all keys so register writes are not silently dropped
  ASM_020_usr_prot: assume property (sram_usr_prot == 1'b1);

  // ===== ICG / Init FSM Constraints (if applicable, Rule 13) =====
  ASM_030_ate_stable: assume property ($stable(ATE_en));
  // ASM_031_abort_pulse: assume property (abort_init |=> !abort_init);
  // ASM_032_no_abort_start: assume property (
  //   !(abort_init && start_manual_init)
  // );

  // ===== Anti-Vacuity Covers (1:1 with assumptions) =====
  cov_ASM_001: cover property (scan_mode == 1'b0 && SE == 1'b0);
  cov_ASM_010: cover property (rst_n == 1'b1);
endmodule

bind <top_module> <ip>_fpv_assumptions u_fpv_assumptions (
  .clk(HCLK), .rst_n(HRESETn), ...
);
```

**MANDATORY — Assumption Validation (before every proof run):**
```tcl
check_assumptions -conflict   # Must return EMPTY (no conflicts)
check_assumptions -dead_end   # Must return EMPTY (no dead ends)
```
- If either returns hits → FIX BEFORE PROCEEDING.
- Conflicting assumptions make ALL properties vacuously proven (SILENT FAILURE).

### Step 6: Create Property Files (One Per Feature)
- For EACH feature area, create `props/<ip>_<feature>_props.sv`:

**Mandatory structure:**
```systemverilog
module <ip>_<feature>_props #(
  parameter PARAM1 = <default>
) (
  input logic clk, rst_n,
  // all signals from bind target needed for this feature
);
  default clocking @(posedge clk); endclocking
  default disable iff (!rst_n);

  // SPEC-NNN | <requirement text>
  ast_<CAT><nn>_<name>: assert property (<antecedent> |-> <consequent>);
  cov_<CAT><nn>_<name>: cover property (<trigger_condition>);
endmodule

bind <target_module> <ip>_<feature>_props #(.PARAM1(PARAM1))
u_<feature>_props (.clk(clk), .rst_n(rst_n), ...);
```

**Naming convention:**
- Assertion: `ast_<CAT><nn>_<short_name>`
- Cover: `cov_<CAT><nn>_<short_name>`
- Categories: D=Data, E=Error, B=Byte-enable, S=SRAM interface, R=Response,
  F=FSM, M=Master, T=Timing, K=Boundary, W=Write, G=ClockGating, P=Perf

**Assertion Writing Rules:**
1. ALWAYS include `tmr_active_nxt` or equivalent in antecedent when asserting
   about next-state values — RTL priority muxes can override expected behavior
2. For pipelined datapaths, verify INDIVIDUAL STAGES, not end-to-end timing
   (end-to-end as covers only)
3. For W1C/W1S/HW-updated registers, verify the SET condition and CLEAR
   condition separately
4. For lock-protected registers, verify both the "write suppressed" and
   "error generated" behaviors
5. For assertions on signals in a different reset domain than the JG reset,
   use: `disable iff (!<primary_reset> || !<secondary_reset>)`
6. Wrap assertions in `generate if (<PARAM>)` for optional features
7. For generated/arrayed structures, write assertions on instance [0] and
   document that structural symmetry covers all instances
8. For AHB pipeline timing: address phase signals (hsize, haddr) are ONE CYCLE
   AHEAD of data phase signals (write_trans_en, ram_write_active). Use
   registered versions or data-phase signals for data-phase assertions.
9. For scoreboard compatibility: only gate scoreboard valid for FULL-WORD
   writes — partial writes do RMW so hwdata != sram_wdata.

**FSM Property Auto-Generation:**
For each FSM found in RTL, auto-generate these properties:
```systemverilog
// Legal states (safety)
ast_Fnn_legal: assert property (state inside {S0, S1, ..., Sn});
// Key transitions (safety)
ast_Fnn_trans: assert property (state == Si ##1 state == Sj |-> <condition>);
// Liveness (return to idle)
ast_Fnn_liveness: assert property (state != IDLE |-> ##[1:BOUND] state == IDLE);
// Transition covers (reachability)
cov_Fnn_Si_Sj: cover property (state == Si ##1 state == Sj);
```

### Step 7: Apply Mandatory Rules

- **Rule 1 — Companion Covers**:
  - Every assertion MUST have ≥1 companion cover.
  - The cover exercises the trigger to prove assumptions don't make it unreachable.
  - If the cover is unreachable, the assertion is vacuously true and provides no verification value.

- **Rule 2 — Assumption Traceability**:
  - Every assumption cites a spec section:
```
// A02: HSIZE always 32-bit — Spec §4.1 "Integration Guidelines"
asm_02_hsize_word: assume property (hsize == 3'd2);
```

- **Rule 3 — Bounded Liveness**:
  - NEVER use `s_eventually`.
  - Always bounded:
```
// GOOD: bounded liveness
ast_F08_liveness: assert property (state != IDLE |-> ##[1:256] state == IDLE);
// BAD: unbounded — will not converge
ast_bad: assert property (state != IDLE |-> s_eventually state == IDLE);
```

- **Rule 4 — Default Disable Iff**:
  - Use `default disable iff (!rst_n)` on all properties.

- **Rule 5 — Parameterized Bounds**:
  - Use IP parameters for bounds:
```
localparam PIPE_STAGES = BUFFER_CAPACITY / (4 * NUM_COMPARATORS);
localparam CHECK_BOUND = PIPE_STAGES + 4;
```

- **Rule 9 — Bind to Sub-Module**:
  - Each property file binds to the module it directly verifies.
  - Only cross-cutting props bind to top.

- **Rule 10 — X-Propagation on ALL Primary Outputs**:
  - Generate an xprop property file checking all output ports are not X/Z after reset:
```systemverilog
ast_xprop_<output>: assert property (rst_n |-> !$isunknown(<output>));
```

- **Rule 11 — SPEC-ID in Comments**:
```
// SPEC-NNN | JAMA: ADTL-SPEC2-NNNN | <requirement text>
```

- **Rule 12 — Gated-Clock Assertions**:
  - When register is on gated clock but assertion uses ungated clock, the register may hold its value for many ungated clock cycles.
  - Apply these patterns:

| Pattern | Problem | Fix |
|---------|---------|-----|
| `\|-> ##[1:N] eventuality` | ICG may not toggle for many cycles | Use large N (512–1024); accept bounded |
| `\|=> signal == $past(value)` | Register holds when gated clock off | Add `\|\| (signal == $past(signal))` to allow hold |
| `$fell(register)` | Fall delayed by gated clock/reset | Add `$past(hresetn) && hresetn` guard |
| Combinational self-clearing reg | HIGH for 1 hclk; gated clock offset | Add `\|\| $past(start_signal)` as trigger |
| Counter monotonic | Counter may be loaded on retrigger | Add `!start_trigger` guard |

- **Rule 13 — ICG Assumptions**:
  - For ICG-gated FSMs with abort/trigger:
```
assume -name M_ATE_STABLE {$stable(ATE_en)}
assume -name M_ABORT_PULSE {abort_init |=> !abort_init}
assume -name M_NO_ABORT_DURING_START {!(abort_init && start_manual_init)}
```
- Each assumption MUST cite the design intent it encodes and the formal exploit it prevents.

- **Rule 14 — Signal Scope Before Bind**:
  - Check signal accessibility:

| Scope | Accessible? | Example |
|-------|-------------|---------|
| Module-level wire/logic | YES | `wire ram_ecc_err;` |
| Signal declared INSIDE generate block | NO | `wire ecc_out;` inside `if(ECC)` |
| Signal inside instantiated sub-module | NO | `u_sub.internal_sig` |
| SV interface signals (bus.signal) | YES | `AHB5_BUS.haddr` |

- If a needed signal is inaccessible:

| Strategy | When to Use |
|----------|-------------|
| Retarget bind | Signal is port/wire of a specific sub-module |
| Add input ports to props | Signal accessible at bind target |
| Use module-level equivalent | Generate-scoped has module-level wire copy |
| Split property file | Assertions need signals from different levels |

- JG 2021.12 limitation:
  - Hierarchical references into generate blocks (e.g., `BLK.u_dec.*`) cause WNL021 warnings and resolve to X.
  - Always use bind ports instead.

### Step 8: Create Scoreboard (if data path exists)
- Create `props/<ip>_scoreboard.sv` using `jasper_scoreboard_3`:

```systemverilog
module <ip>_scoreboard_wrapper #(parameter ...) (
  input clk, rst_n,
  // write-side signals, read-side signals, error flags
);
  default clocking @(posedge clk); endclocking
  default disable iff (!rst_n);

  logic is_valid_write, is_valid_read;
  // Define write/read qualification logic

  jasper_scoreboard_3 #(
    .CHUNK_WIDTH(32), .IN_CHUNKS(1), .OUT_CHUNKS(1),
    .SINGLE_CLOCK(1), .MAX_PENDING(4), .LITE_CHECKS(1)
  ) u_scb (
    .clk(clk), .rstN(rst_n),
    .incoming_vld(is_valid_write), .incoming_data(wdata),
    .outgoing_vld(is_valid_read),  .outgoing_data(rdata)
  );

  // MANDATORY — explicit SVA assertions around scoreboard
  // Do NOT rely only on scoreboard IP internal checks (LITE_CHECKS).
  // The scoreboard IP only catches basic ordering violations.
  // You MUST add these explicit assertions:

  // Write data integrity — data arriving at SRAM matches AHB
  ast_SCB01_write_data: assert property (
    is_full_word_write |-> hwdata == sram_wdata[31:0]
  );

  // Read data integrity — data returned to AHB matches SRAM output
  ast_SCB02_read_data: assert property (
    is_valid_read |-> final_rd_data == hrdata
  );

  // No spurious writes — SRAM write enable only when expected
  ast_SCB03_no_spurious_write: assert property (
    sram_wen != '0 |-> ram_write_active
  );

  // Write address consistency — write targets correct SRAM addr
  ast_SCB04_write_addr: assert property (
    is_full_word_write |-> sram_addr == expected_addr
  );

  // Read liveness — read request eventually completes
  ast_SCB05_read_liveness: assert property (
    read_addr_phase |-> ##[1:8] is_valid_read
  );

  // Write data propagation — data reaches SRAM within N cycles
  ast_SCB06_write_prop: assert property (
    is_full_word_write |-> ##[1:4] sram_write_complete
  );

  // Write no overflow — pending count does not exceed capacity
  ast_SCB07_no_overflow: assert property (
    pending_count <= MAX_PENDING
  );

  // Companion covers (anti-vacuity)
  cov_SCB01: cover property (is_valid_write);
  cov_SCB02: cover property (is_valid_read);
  cov_SCB03: cover property (is_valid_write ##[1:4] is_valid_read);
endmodule
```

- **CRITICAL — Scoreboard Partial Write Handling:**
  - Jasper Scoreboard compares hwdata to sram_wdata, but partial writes do RMW.
  - sram_wdata contains merged data, not just hwdata.
  - Gate scoreboard valid with `is_full_word_write`.
  - Keep word-size-only assumption active for scoreboard.
  - Verify partials in separate run.

### Step 9: Create ABVIP Bind File
- Create `props/<ip>_abvip_bind.sv` for protocol compliance:

```systemverilog
module <ip>_abvip_bind;
bind <top_module> cdn_abvip_ahb5_lite_wrapper #(
  .VERIFY_BLK(32'd2),     // 2 = slave/responder
  .ABUS_WIDTH(32),
  .BURST_TYPES(1),
  .COVERAGE_ON(1'b1),
  .RST_CHECKS_ON(1'b1)
) u_abvip_ahb5 (
  .hclk(HCLK), .hresetn(HRESETn),
  .haddr(haddr), .htrans(htrans), .hsize(hsize),
  .hburst(3'b000), .hwdata(hwdata), .hwrite(hwrite),
  .hrdata(hrdata), .hready(hreadyout), .hready_global(hready),
  .hresp(hresp), .hsel(hsel), .hmastlock(1'b0),
  .hprot(hprot), .hnonsec(hnonsec), .hexcl(hexcl),
  .hmaster(hmaster), .hexokay(hexokay)
);
endmodule
```

**ABVIP Key Parameters Reference:**

| Parameter | Description | Guidance |
|-----------|-------------|----------|
| VERIFY_BLK | 0=Master, 1=Arbiter, 2=Slave, 3=Monitor | Set to IP's role |
| ABUS_WIDTH | Address bus width | Match design parameters |
| DBUS_WIDTH | Data bus width | Match design parameters |
| BURST_TYPES | 8-bit mask (bit 0=SINGLE, 3=INCR4, etc.) | Enable only supported bursts |
| MAX_WAIT_CYCLES_READY | Max stall cycles before protocol timeout | Design's max stall + margin |
| COVERAGE_ON | Enable formal cover properties | 1 for coverage collection |
| RST_CHECKS_ON | Enable reset behavior checks | 1 for most designs |

- **When ABVIP is integrated:**
  - Comment out ALL manual AHB/APB protocol assumptions in both the assumptions file and the JG TCL with a cross-reference.
  - Retain ONLY non-protocol assumptions (scan_mode, SE, protection keys, ICG).

### Step 9b: Tech Cell Handling

- When the RTL instantiates technology cells (clock gates, muxes, etc.), follow this decision tree:

1. Does the assertion verify combinatorial `_nxt` signals only?
   → YES: Blackbox the tech cell (`-bbox_m <cell>`)
   → NO (assertions on registered outputs, e.g., CSR checker):
2. Is a behavioral model available (RTL stub)?
   → YES: Include stub BEFORE filelist in analyze order
   → NO:
3. Can you write a simple behavioral stub?
   → YES: Write one. Pattern for clock gate:
```systemverilog
module <tech_cell> (CLK, CLKEN, SE, CLKOUT);
  input CLK, CLKEN, SE; output CLKOUT;
  reg en_latch;
  always @(CLK or CLKEN or SE)
    if (!CLK) en_latch = CLKEN | SE;
  assign CLKOUT = CLK & en_latch;
endmodule
```
   → NO: Use `-bbox_m` and accept limitations

- **Why this matters:**
  - Blackboxing a clock gate means CLKOUT is an unconstrained free variable — clocks may never toggle, registers may never update.
  - Fine for assertions on `_nxt` signals, but BREAKS anything depending on registered outputs (like CSR verification).
  - In production, we had to write a 6-line behavioral ICG stub to fix CSR failures after blackboxing stopped all register updates.

### Step 10: Create JG FPV Setup TCL
- Create `tcl/jg_fpv_setup.tcl`:

- **CRITICAL:**
  - Use ABSOLUTE PATHS for all file references in TCL.
  - Define FPV_ROOT at top and prefix all paths with `${FPV_ROOT}`.
  - JG working directory is `jgproject/`, NOT `fpv_env/`.
  - Relative paths will fail with ESW046.

```tcl
clear -all
set FPV_ROOT <absolute_path>

jasper_scoreboard_3 -init
check_cov -init -type {stimuli coi proof bound}

set ABVIP_INST_DIR /cad/adi/apps/cadence/vip/latest/vips/abvip
abvip -set_location $ABVIP_INST_DIR

analyze -sv -f ${FPV_ROOT}/rtl_list/filelist.f
analyze -sv ${FPV_ROOT}/models/*.sv
analyze -sv ${FPV_ROOT}/props/<ip>_assumptions.sv
analyze -sv ${FPV_ROOT}/props/<ip>_*_props.sv
analyze -sv09 ${FPV_ROOT}/props/<ip>_abvip_bind.sv

elaborate -top <top_module> \
    -parameter <PARAM1> <val1> \
    -bbox_m <tech_cell_1> \
    -bbox_m <tech_cell_2>

clock <CLK>
reset -expression {!<RSTn>}

# For dual-clock designs, declare ALL clocks:
# clock <CLK2>
# reset -expression {!<RST2>}

assume -name M_NO_SCAN {scan_mode == 1'b0}
assume -name M_NO_SE {SE == 1'b0}

# MANDATORY — validate assumptions before proof
check_assumptions -conflict
check_assumptions -dead_end

set_engine_mode {Hp Ht Hps}
set_prove_time_limit 4h
set_prove_per_property_time_limit 30m
set_max_trace_length 600

prove -all

# Check for VACUOUS assertions — verify anti-vacuity covers
# If a cover is UNREACHABLE, the corresponding assertion is vacuously true

check_cov -measure -source
check_cov -measure -type {stimuli coi proof bound}

file mkdir ${FPV_ROOT}/results
report -force -file ${FPV_ROOT}/results/report_fpv.txt -results -summary
report -force -file ${FPV_ROOT}/results/report_coverage.txt -type {stimuli coi proof bound}
```

- **Note on analyze -sv/-sv09 conflict:**
  - If a filelist.f contains internal `-sv` flags, using `-sv09` on the same analyze command causes ESW212.
  - Split into separate analyze commands.

### Step 11: Create Param Configs and jg_run_all.tcl
- Create `param_configs/cfg_<name>.tcl` for each configuration:
```tcl
set CFG_NAME "CFG_<NAME>"
set CFG_<PARAM1> <value1>
set CFG_<PARAM2> <value2>
```

- Create `tcl/jg_run_all.tcl` with a `proc run_config` that sources each config and runs analyze/elaborate/prove in a loop.

- **Configuration Selection Rationale — configs are chosen to cover:**
1. BOUNDARY VALUES: Min and max parameter values
2. FEATURE TOGGLES: Each optional feature on/off (e.g., ECC on/off, ROM mode)
3. PROTOCOL MODES: Each operating mode
4. PARAMETER INTERACTIONS: Combinations where parameters affect each other
5. SCALE: Minimum config (fast iteration) + maximum config (parameterization
   proof) + default config (regression baseline)

### Step 12: Phase 4b Collateral Audit
- Before finishing, verify ALL 10 checks pass:
1. ECC/error detection → ref model + error injection exist?
2. ROM/read-only mode → ROM model + ROM assertions exist?
3. All clocks declared in TCL?
4. APB register interface → APB constraint module exists?
5. Partial writes → byte-lane assertions + shadow memory exist?
6. Every assertion has a companion cover?
7. X-propagation checks on ALL primary outputs exist?
8. All tech cells in -bbox_m list?
9. CSR → CSV + bind + TCL exist? (defer to formal-csr skill)
10. Parameter sweep → jg_run_all.tcl with ≥3 configs?

- **Self-Audit Procedure (execute before proceeding):**
1. List every file you created in this session
2. For each row in the mandatory collateral table above, check:
   a) Does the IP have this feature? (grep RTL/spec if unsure)
   b) If YES — does the corresponding file exist?
   c) If file is MISSING — create it NOW
3. Verify EVERY assertion has a companion cover (`grep -c 'assert\|cover'`)
4. Verify ALL clocks from RTL are declared in TCL
   (`grep 'posedge\|negedge' <rtl_top>.sv` → list all clocks → compare to TCL)
5. Verify ALL tech cells are in -bbox_m list (Step 3b)
6. Count: assertions, covers, assumptions — log totals

---

## CEX Debug Methodology — Decision Tree

- When a CEX appears, follow this triage in order:

- **STEP 1 — CHECK CYCLE NUMBER:**
  - Cycle 1-2 CEX? → Likely UNINITIALIZED FLOPS in secondary reset domain.
  - FIX: Add `disable iff (!<reset1> || !<reset2>)` to the assertion, or add `&& <secondary_reset>` to antecedent.
  - PATTERN: If JG reset is reset_A but assertion touches reset_B domain.

- **STEP 2 — CHECK FOR VACUOUS ASSERTION:**
  - Is the assertion passing because the antecedent is NEVER TRUE?
  - Check: Is a forced constraint (e.g., word-size-only, ecc_en=1) making the antecedent unreachable?
  - FIX: Disable the assertion when the conflicting constraint is active.
  - Document which assertions are vacuous and need a SEPARATE RUN without the constraint.
  - Add ANTI-VACUITY COVERS for all forced assumptions.

- **STEP 3 — CHECK FOR UNCONSTRAINED INPUTS:**
  - Does CEX show an input toggling that should be static?
  - FIX: Add stability assumption.
  - FILE SPEC GAP if input is not listed in AoU but RTL depends on it.

- **STEP 4 — CHECK FOR PROTOCOL VIOLATION IN CEX:**
  - Does CEX show bus protocol violation (e.g., pready never asserts)?
  - FIX: Add/strengthen bus protocol assumptions.

- **STEP 5 — CHECK FOR IDLE PROTOCOL INTERFERENCE:**
  - Does CEX show inactive interface inputs toggling?
  - FIX: Add idle protocol assumptions.

- **STEP 6 — CHECK FOR UNREALISTIC RESET SEQUENCE:**
  - Does CEX show reset bouncing multiple times?
  - FIX: Add reset stability assumptions.

- **STEP 7 — CHECK FOR ADDRESS PHASE vs DATA PHASE TIMING MISMATCH:**
  - Does CEX show data-phase assertion firing on address-phase signal values?
  - FIX: Use data-phase (registered) versions of signals, or use `$past()` to align timing.
  - Remember: AHB address phase is ONE CYCLE AHEAD of data phase.

- **STEP 8 — READ THE RTL (CRITICAL):**
  - If none of the above:
    - → Export CEX waveform (VCD)
    - → Trace signal values cycle by cycle in the RTL
    - → READ RTL COMMENTS — the behavior may be correct by design
    - → Check for priority muxes, pipeline hazards, corner cases
    - → NEVER claim a bug without reading the relevant RTL lines

- **STEP 9 — CLASSIFY THE CEX:**
  - After investigation, classify as one of:
a) **TOOL ARTIFACT** → Fix with disable iff or assumption
b) **ASSUMPTION GAP** → Add missing assumption, trace to spec AoU
c) **ASSERTION BUG** → Fix the SVA expression
d) **REAL RTL BUG** → Document, file bug, keep assertion as-is
e) **SPEC AMBIGUITY** → Document, recommend spec clarification
f) **WAIVE** → Convert to cover property, document rationale
g) **VACUOUS** → Disable, document, plan separate run

- NEVER add an assumption just to make a CEX go away without understanding the root cause.
- Every assumption must be justified.

---

## FPV Pitfalls Reference

### Reset and Clock Pitfalls

- **PITFALL 1 — DUAL/MULTI-RESET DOMAIN (MOST COMMON):**
  - JasperGold can only use ONE reset expression.
  - Flops in other reset domains start as X at formal time 0.
  - This causes false-positive CEX at cycles 1-2 for any assertion touching the uninitialized domain.
  - FIX: `disable iff (!reset_primary || !reset_secondary)` on affected assertions.

- **PITFALL 2 — RESET TIMING MISMATCH:**
  - If two resets deassert at different times, transactions may initialize incorrectly.
  - FIX: Ensure both resets asserted/deasserted simultaneously in JG.

- **PITFALL 3 — MULTI-CLOCK DECLARATION:**
  - For dual-clock sequential designs (e.g., hclk + pclk), declare BOTH clocks in JG.
  - Serial interface clocks that are INPUTS (not driving DUT flops) are NOT declared — they are regular inputs with half-period assumptions.

### RTL Behavior Pitfalls

- **PITFALL 4 — RTL PRIORITY MUX OVERRIDE:**
  - RTL often has priority-encoded next-state muxes where a higher-priority condition overrides expected behavior.
  - Assertions MUST include the higher-priority condition in the antecedent.
  - FIX: Always check RTL for priority conditions before writing assertions.

- **PITFALL 5 — COUNTER/TIMER OVERFLOW AT REDUCED BIT WIDTH:**
  - For formal convergence, timer/counter widths are often reduced (24→8 bit).
  - Counters wrap much sooner, creating unexpected states.
  - FIX: Assert on active/state signals, not raw counter values.

- **PITFALL 6 — DOUBLE-BUFFERED REGISTERS:**
  - Registers that only update on trigger events can differ from programmed values mid-operation.
  - FIX: Assert STABILITY of buffered values (not equality) except at update events.

- **PITFALL 7 — ADDRESS PHASE vs DATA PHASE TIMING:**
  - hsize, haddr are address phase (cycle N).
  - write_trans_en, ram_write_active are data phase (cycle N+1).
  - Mixing these causes timing mismatches.
  - FIX: Use data-phase signals for data-phase assertions.

- **PITFALL 8 — DELAYED DISABLE / GRACEFUL SHUTDOWN:**
  - Some RTL has multi-cycle disable sequences.
  - Cannot assert immediate effect.
  - FIX: Convert to cover or add cycle tolerance.

- **PITFALL 9 — STOPREQ / GRACEFUL STOP LOGIC:**
  - Stop requests may only trigger actions when module is active.
  - If idle, stopreq_accept=1 but disable=0.
  - Include active state in antecedent.

### Tech Cell and Compile Pitfalls

- **PITFALL 10 — CLOCK GATE BLACKBOX vs STUB:**
  - Blackbox tech cell → clock gate output is unconstrained → registers don't update.
  - OK for assertions on combinatorial `_nxt` signals.
  - BREAKS CSR verification (needs working registered outputs).
  - FIX: Use behavioral stub for CSR runs (see Step 9b).

- **PITFALL 11 — VENDOR DEPENDENCY CHAIN:**
  - Never include vendor cell libraries that pull in unavailable dependencies.
  - Use blackbox or behavioral stubs instead.

- **PITFALL 12 — ANALYZE -sv/-sv09 CONFLICT:**
  - If filelist.f contains internal `-sv` flags, using `-sv09` on the same analyze command causes ESW212.
  - FIX: Split into separate analyze commands.

- **PITFALL 13 — SV INTERFACE DEPENDENCY (CANNOT BLACKBOX):**
  - ADIP IPs commonly instantiate shared SV interfaces (ahb5_if, apb4_if) from adip_common.
  - JG reports "instantiating unknown empty module" which looks like a tech cell issue, but SV interfaces CANNOT be blackboxed.
  - FIX: Add missing common library files to filelist BEFORE the first IP RTL file that uses them.
  - Compile order matters.
  - DETECTION: If module name ends in `_if` or `_connect`, it is almost certainly a missing SV interface — NOT a tech cell to blackbox.

- **PITFALL 14 — ELABORATE PARAMETER ORDER:**
  - JG applies `-param` in order.
  - If parameters have dependencies, specify independent parameters first.

### Engine and Tool Pitfalls

- **PITFALL 15 — JG Ht ENGINE ABSTRACT PORT BUG:**
  - Ht abstract engine can treat `output logic` top-level ports as free variables, assigning arbitrary values.
  - FIX: Add constant-assign assumptions for known-constant outputs.

- **PITFALL 16 — GENERATE BLOCKS FOR OPTIONAL FEATURES:**
  - When a parameter disables a feature, submodule is removed from elaboration.
  - All signal aliases and assertions referencing it MUST be inside `generate if (<PARAM>)` blocks.

### Scoreboard and Data Path Pitfalls

- **PITFALL 17 — SCOREBOARD FAILS WITH PARTIAL WRITES:**
  - Jasper Scoreboard compares hwdata to sram_wdata, but partial writes do RMW.
  - sram_wdata contains merged data, not just hwdata.
  - FIX: Gate scoreboard valid with `is_full_word_write`.
  - Keep word-size-only assumption active for scoreboard.
  - Verify partials in separate run.

- **PITFALL 18 — FREE VARIABLES NOT EXPLORED:**
  - CSR free variables may not be explored if solver finds easy paths with default values.
  - Symptom: assertions pass vacuously.
  - FIX: Force specific values or add cover properties for reachability.

- **PITFALL 19 — ERROR INJECTION DURING WRITE:**
  - If error_inject_mask is non-zero during write-back (RMW), memory model receives corrupted data, breaking scoreboard.
  - FIX: Constrain `error_inject_mask=0` when `ram_write_active` is high.

- **PITFALL 20 — 2-BIT ECC ERROR SUPPRESSES WRITE-BACK:**
  - During RMW, if 2-bit error detected on read-back, sram_wen forced to 0.
  - Assertions expecting write completion will CEX.
  - FIX: Include `!ecc_err_2b` in write completion antecedent.

- **PITFALL 21 — SCOREBOARD WITH ONLY COVERS AND NO ASSERTIONS:**
  - Instantiating jasper_scoreboard_3 with LITE_CHECKS and adding only cover properties is NOT sufficient.
  - The scoreboard IP's internal checks only catch basic ordering violations.
  - You MUST add explicit SVA assertions for write data integrity, read data integrity, no spurious writes, write address consistency, read liveness, and write data propagation (see Step 8).

### Pipeline and Timing Pitfalls

- **PITFALL 22 — PIPELINE LATENCY ASSERTIONS:**
  - Multi-stage pipelines add latency that makes end-to-end assertions complex and hard to prove.
  - Verify individual stages instead.
  - Use end-to-end scenarios as cover properties only.

### Bind and Signal Scope Pitfalls

- **PITFALL 23 — BIND CANNOT ACCESS INTERNAL WIRES VIA HIERARCHICAL REF:**
  - When binding to DUT top, you CANNOT reference internal wires declared inside a submodule.
  - JG only resolves ports and module-scope signals through hierarchy.
  - SYMPTOM: `"'I_wr_addr' is not declared under prefix 'ram_mmr_inst'"`
  - FIX: Reconstruct the equivalent logic using signals that ARE accessible at the bind target scope.
  - For APB-based MMRs:
```systemverilog
// WRONG — internal wires not accessible
.wr    (ram_mmr_inst.I_wr_stb),

// CORRECT — reconstruct from APB interface signals
.wr    (APB_SRAM_BUS.pwrite & APB_SRAM_BUS.penable & APB_SRAM_BUS.psel),
```

- **PITFALL 24 — TCL RELATIVE PATHS FAIL IN JASPERGOLD:**
  - JG working directory is `jgproject/`, NOT where the TCL script lives.
  - Relative paths like `rtl_list/filelist.f` will fail with ESW046.
  - FIX: Define `FPV_ROOT` at the top and prefix ALL file references with `${FPV_ROOT}` (see Step 10).

---

## Ideal Assertion Checklist — Complete IP Coverage

- This checklist defines the IDEAL set of assertions for a bus-connected IP with ECC, initialization, interrupts, test mode, and registers.
- Target: ~120 assertions.
- Skip categories that don't apply to the IP, but for categories that DO apply, every checkbox is MANDATORY.

### Category 1: ECC Encode / Parity
- [ ] Parity match: ref model output == DUT encoder parity
- [ ] Per-bit parity: generate loop checking each parity bit
- [ ] Wrong-parity sanity: deliberately wrong parity != DUT
- [ ] Encoder output no-X: `!$isunknown(encoder_output)`
- [ ] Encoder data passthrough: `data_out[31:0] == data_in[31:0]`
- [ ] Parity zero when ECC off: `parity == 0` when `!ecc_en`

### Category 2: ECC Decode / Error Path
- [ ] No-error passthrough: no error → output == raw data
- [ ] 1-error correction: `one_error` → output != raw data
- [ ] 2-error detection: `two_error` → `err[0]=1`
- [ ] ECC bypass: bypass → output == raw data, no error flags
- [ ] `err[1]` wiring: `err[1] == one_error`
- [ ] `err[0]` wiring: `err[0] == two_error`
- [ ] ECC disabled → no error: `!ecc_en → err == 2'b00`

### Category 3: ECC Error Response
- [ ] DED → hresp=1: 2-bit error + bus_err_type[0] → error response
- [ ] SEC → hresp=1: 1-bit error + bus_err_type[1] → error response
- [ ] Masked DED → no hresp: bus_err_type[0]=0 → no error response
- [ ] DED blocks write-back: 2-bit error during RMW → sram_wen=0

### Category 4: ECC Status / Capture / Counter
- [ ] SERR2B set on 2-bit error
- [ ] SERR1B set on 1-bit error
- [ ] ECC address captured on first error
- [ ] ECC data captured on first error
- [ ] ECC parity captured on first error
- [ ] Counter increment on 1-bit (when enabled, not saturated)
- [ ] Counter increment on 2-bit (when enabled, not saturated)
- [ ] Counter saturate at max (does not wrap)
- [ ] Counter clear on explicit clear signal
- [ ] Interrupt on 1-bit error (when INTERRTYPE enabled)
- [ ] Interrupt on 2-bit error (when INTERRTYPE enabled)

### Category 5: ECC Diagnosis
- [ ] Diag data capture: raw data stored when diag_en + rdata_vld
- [ ] Diag raw data: uncorrected data captured (even with 1-bit err)
- [ ] Diag clear: data cleared to 0 when diag_en=0

### Category 6: AHB Control
- [ ] Access detection: `ahb_access = htrans[1] & hsel & hready`
- [ ] Write detection: `ahb_write = access & hwrite & ~err`
- [ ] Read detection: `ahb_read = access & ~hwrite & ~err`
- [ ] Error → hresp 2-cycle protocol (hresp=1/hreadyout=0 then 1/1)
- [ ] Error → hreadyout=0 on first cycle
- [ ] ROM write → err_access
- [ ] Byte enable decode: word (1111)
- [ ] Byte enable decode: halfword low/high (2 checks)
- [ ] Byte enable decode: byte 0/1/2/3 (4 checks)
- [ ] SRAM CS = read_active | write_active
- [ ] Hreadyout=1 during reset
- [ ] Hreadyout=1 when idle (no error, no stall)
- [ ] Hreadyout liveness: cannot stay deasserted > N cycles
- [ ] Hrdata = sram_rdata[31:0] when read valid, no ECC error

### Category 7: Initialization FSM
- [ ] MMR-triggered init → in_progress within N cycles
- [ ] Pin-triggered init → in_progress within N cycles
- [ ] Not started without enable
- [ ] In-progress stable (stays set until abort/end/ATE)
- [ ] Address counter increments by 1 during init
- [ ] End at max address → in_progress deasserts
- [ ] Init done sticky (stays set until re-init or reset)
- [ ] Init done clear on restart
- [ ] Init done set after complete
- [ ] MMR abort stops engine immediately
- [ ] ATE_en rising edge stops engine
- [ ] End-to-end APB abort: write at addr N → engine writes N+1 then stops
- [ ] Clear request → ack handshake
- [ ] Clear ack deassert when request drops
- [ ] Reset: address = idle sentinel
- [ ] Reset: in_progress = 0
- [ ] Reset: init_done = 0

### Category 8: Interrupt / Status
- [ ] Int req = |(status & int_err_type)
- [ ] No interrupt when all types disabled
- [ ] Status set on 1-bit error (next cycle)
- [ ] Status set on 2-bit error (next cycle)
- [ ] Status bits sticky (stay set until cleared)
- [ ] Status cleared by explicit clear (no simultaneous error)
- [ ] Counter saturate at max
- [ ] Counter clear to 0 on explicit clear
- [ ] Counter increment on qualified error
- [ ] Counter no increment when type disabled
- [ ] First error captured (addr/data/parity)
- [ ] Capture not overwritten until cleared
- [ ] Reset: status = 0
- [ ] Reset: counter = 0
- [ ] Reset: no interrupt

### Category 9: Test Mode
- [ ] TM data write → sram_wen = data lanes only (e.g., 01111)
- [ ] TM parity write → sram_wen = parity lane only (e.g., 10000)
- [ ] TM data read returns raw sram_rdata[31:0]
- [ ] TM parity read returns parity in hrdata
- [ ] TM mode → no ECC correction applied

### Category 10: ROM / Memory Region
- [ ] ROM write → error response
- [ ] ROM read → no error (read OK)
- [ ] SRAM write allowed in mixed RAM/ROM mode
- [ ] Access during initialization → error response

### Category 11: Partial Writes
- [ ] Byte 0 lane: selected → `ram_write_data[7:0] = hwdata[7:0]`
- [ ] Byte 1 lane: selected → `ram_write_data[15:8] = hwdata[15:8]`
- [ ] Byte 2 lane: selected → `ram_write_data[23:16] = hwdata[23:16]`
- [ ] Byte 3 lane: selected → `ram_write_data[31:24] = hwdata[31:24]`

### Category 12: Scoreboard (explicit assertions — not just covers)
- [ ] Write data integrity: `hwdata == sram_wdata[31:0]` on write
- [ ] Read data integrity: `final_rd_data == hrdata` on valid read
- [ ] Write address consistency: write targets correct SRAM addr
- [ ] No spurious writes: `sram_wen` only when `write_active`
- [ ] No spurious reads: hrdata valid only when expected
- [ ] Write data propagation: data reaches SRAM within N cycles
- [ ] Read liveness: every read request gets response
- [ ] Write no overflow: pending count ≤ MAX_PENDING

### Category 13: APB / CSR Constraints (assumptions)
- [ ] Valid address range (≤ max register addr)
- [ ] Word-aligned address (`paddr[1:0] == 00`)
- [ ] Valid register address enumeration
- [ ] No writes to read-only registers
- [ ] Per-register reserved bits = 0
- [ ] Mode-specific CSR forcing (e.g., VERSION, sram_srom_en)

### Category 14: X-Propagation (all primary outputs)
- [ ] `!$isunknown` on every primary output after reset
  (hrdata, hreadyout, hresp, prdata, pready, pslverr, etc.)

### Category 15: Infrastructure
- [ ] ECC reference model (independent XOR equations)
- [ ] Error injection mechanism (free-var XOR mask, ≤N-bit)
- [ ] ROM behavioral model (unconstrained contents)
- [ ] RAM behavioral model (byte-lane write enables)
- [ ] All clocks declared in TCL
- [ ] All resets declared in TCL
- [ ] All tech cells in -bbox_m
- [ ] Every assertion has a companion cover (anti-vacuity)
- [ ] Parameter sweep ≥ 3 configs

---

## Output Files

```
fpv_env/
├── props/
│   ├── <ip>_assumptions.sv
│   ├── <ip>_abvip_bind.sv
│   ├── <ip>_<feature1>_props.sv
│   ├── <ip>_<feature2>_props.sv
│   ├── <ip>_scoreboard.sv
│   ├── <ip>_xprop_output_props.sv
│   └── <ip>_apb_constraints.sv
├── models/
│   ├── <ip>_fpv_ram_model.sv
│   ├── <ip>_fpv_rom_model.sv
│   └── <ip>_ecc_ref_model.sv
├── tcl/
│   ├── jg_fpv_setup.tcl
│   └── jg_run_all.tcl
├── param_configs/
│   ├── cfg_<config1>.tcl
│   └── cfg_<config2>.tcl
├── traceability/
│   └── formal_traceability.csv
└── rtl_list/
    └── filelist.f
```

## Liveness Bound Reference

| Context | Bound | Rationale |
|---------|-------|-----------|
| Slave IF return to idle | 64–128 | Memory latency |
| Master IF return to idle | 128–256 | Burst + wait states |
| Hit detection complete | 64–128 | Pipeline stages |
| Write invalidation complete | 64–128 | Comparator scan |
| Post-flush recovery | 32–64 | Simple reset sequence |
| MMR trigger → FSM start (ICG) | 512–1024 | ICG latch + 2FF sync |
| Pin trigger → FSM start (ICG) | 512–1024 | 2FF sync + ICG |
| Init complete → done flag | 32K+ | Full memory — verify in sim |
| General liveness | Scale with BUFFER_CAPACITY | Larger buffer → more cycles |

- Start with `##[1:128]` and widen progressively (256 → 512 → 1024) if bounded proofs appear.

## Quality Checklist
- [ ] Every spec requirement from verification_plan.md has ≥1 assertion
- [ ] Every assertion has a companion cover (Rule 1)
- [ ] Every assumption cites a spec section (Rule 2)
- [ ] All liveness properties are bounded (Rule 3)
- [ ] No assertions use signals from inaccessible scopes (Rule 14)
- [ ] X-prop checks on ALL primary outputs (Rule 10)
- [ ] SPEC-ID in every assertion comment (Rule 11)
- [ ] All tech cells in -bbox_m list
- [ ] Behavioral models match spec behavior
- [ ] jg_run_all.tcl has ≥3 parameter configs
- [ ] check_assumptions -conflict returns EMPTY
- [ ] check_assumptions -dead_end returns EMPTY
- [ ] No vacuous assertions (all anti-vacuity covers reachable)
- [ ] Filelist dependency audit completed (Step 3b)
- [ ] All clocks from RTL declared in TCL
- [ ] Error injection mechanism exists (if ECC/error detection)
- [ ] Scoreboard has explicit SVA assertions, not just covers (if data path)
