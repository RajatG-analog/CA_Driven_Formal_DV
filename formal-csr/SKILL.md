---
name: formal-csr
description: Spec-only Jasper CSR App flow (JasperGold 2025.09) — build the check_csr register-map CSV from the spec register table (no RTL, no Yoda/IP-XACT as requirement source), bind jasper_csr_checker / jasper_amba_apb_csr_checker / ABVIP CSR checkers, verify spec write/read protection with BUS_WRITE_ENABLE / BUS_READ_ENABLE, generate TCL setup or adsim sim.setup with run commands, CEX debug, traceability, optional vPlan and final param audit. Use when the user asks for CSR/register-map formal verification, check_csr setup, register reset/access-type checks or CSR sign-off.
---

# Formal CSR Skill — Jasper CSR App Register Verification (Spec-Only)

**Resource loading (MANDATORY):**
- `resources/...` paths are relative to this skill's directory (the directory containing this SKILL.md).
- Resources are NOT preloaded. At each step that says "Read `resources/<file>`", open that file with View BEFORE writing any output for the step.
- Never generate a CSR map CSV, bind file, sim.setup or traceability CSV from memory when a resource file exists for it.

| Step | Resource file (read when reaching the step) |
|------|---------------------------------------------|
| Step 3 — CSR map CSV (cell positions, attributes per level, blocks, examples) | `resources/csv_format_reference.md` |
| Step 6b — sim.setup | `resources/sim_setup_template.md` |
| Traceability | `resources/traceability_format.md` |

## When to Use
Activate when the user asks to:
- Create a CSR register-map CSV for the Jasper CSR App (`check_csr -load`)
- Write a CSR bind file for `jasper_csr_checker`, `jasper_csr_extended_checker`, `jasper_amba_apb_csr_checker` or an ABVIP CSR checker
- Create a JasperGold CSR TCL setup or an adsim `sim.setup` for CSR verification
- Verify register reset values, access types, field behaviour, write/read protection
- Debug CSR checker failures (parse problems, CEX on protected / HW-updated registers)

## Upfront Questions (ASK ONCE, BEFORE ANY WORK — MANDATORY)

- Ask ALL of these in ONE question round (AskUserQuestions) before Step 1.
- Do not re-ask later; reuse the answers in every step. Record them in the final summary.
- If an answer is "not known yet", continue and mark the dependent output as TODO.

| # | Question | Options / format | Used in |
|---|----------|------------------|---------|
| Q1 | Spec source | PDF / Jama / md path (+ revision) | Step 1–3 |
| Q2 | Register-map section(s) of the spec | section / table numbers, register-summary table | Step 2 |
| Q3 | Bus protocol to the registers (from spec) | APB2 (AMBA APB 2.0) / APB3 / APB4 / AHB-Lite / AXI3 / AXI4 / custom (backdoor) | Step 1, Step 4 |
| Q4 | Top module (bind target) | `<top_module>` | bind, elaborate, `FML_INSTTOP` |
| Q5 | Clock / reset names and polarity (from spec) | e.g. `PCLK`, `PRESETn` active-low | bind, `clock`, `reset` |
| Q6 | RTL filelist (compile only) | path to `filelist.f` | Step 6 |
| Q7 | Output / formal directory | e.g. `$ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>` | all outputs |
| Q8 | Run flow | A. TCL / B. adsim sim.setup / C. both | Step 6 |
| Q9 | adsim block name (if B/C) | e.g. `adip_<ip>` | RUNCMD `-block` |
| Q10 | Config list + parameter values per config | `<cfg_dir>`: `<PARAM>=<VAL>` | elaborate `-parameter`, RESET_VALUE_EXPRESSION |
| Q11 | Protection conditions (from spec) | key / lock / privilege / pin per register; value read when blocked | Step 5 |
| Q12 | Run mode | GUI / batch | RUNCMD |
| Q13 | ProofGrid | yes (bsub command) / no | proofgrid lines |
| Q14 | Prove / coverage time limit | e.g. 24h, per-property 1h | `set_prove_time_limit`, `check_cov -measure` |
| Q15 | Report location | e.g. `${GPMS_NOBACKUP}/../public_html/$USER/jasper_reports` | reports |
| Q16 | vManager / vPlan | vPlan NOW / LATER / NOT NEEDED; `formal-vplan` or `check_csr -create_vplan` | Optional vPlan step |
| Q17 | SoC context for final param audit | SoC RTL glob / SoC CSV / not available | Final Step |
| Q18 | Traceability publish | none / Jama / Confluence | Sign-Off Traceability |
| Q19 | ABVIP install path (standard buses) | e.g. `<vipcat_root>/tools/abvip` | `abvip -set_location` |
| Q20 | Spec bus-error behaviour | conditions where PSLVERR/HRESP/xRESP may be asserted, or "never used"; effect of an errored write | Step 5b |

- Only spec-gap questions are asked later (missing reset value, access type, protection condition, HW update condition, ambiguous field behaviour), since they are found during the flow.

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| **Spec** | Register-map section of the IP spec (the ONLY requirement source) | `<ip>_spec.pdf` §`<x.y>` |
| **RTL filelist** | Compile ONLY (DUT under test — never a requirement source) | `filelist.f` |
| **Top module** | Bind target / formal top | `<top_module>` |
| **Bus protocol** | Register bus from the spec | APB4 |
| **Output dir** | Where to write CSR collateral | `fpv_env/csr/` |

**SPEC-ONLY PRINCIPLE (MANDATORY):**
- The specification register table is the ONE AND ONLY source for every register, offset, width, field, bit range, access type, reset value, protection condition and HW-update behaviour.
- NEVER read RTL to derive, complete or correct the CSR map.
  - Deriving expectations from the design under test makes verification circular (RTL bugs become "expected" behaviour).
- NEVER use Yoda `.yda` or generated IP-XACT as the requirement source.
  - The `.yda` file is the source the RTL register file is generated from; checking RTL against it is circular.
  - `check_csr -load_ipxact` exists (jasper_command_reference.pdf) but is NOT used as the requirement source in this flow.
- RTL is only compiled by JG.
- Names for BINDING only (bind target module, bus port names, clock/reset port names) may be taken from the RTL top-level port list when the spec does not name them.
  - This is not a requirement source; record it in the bind file header comment.
  - Expected values (reset, access, protection, HW behaviour) never come from RTL.
- If a spec item is missing or ambiguous: log a SPEC GAP and ASK the user — do NOT fill it from RTL.

**TOOL DOCUMENTATION (MANDATORY):**
- For all Jasper command/CSV syntax, always refer to the installed Cadence docs at `/cad/adi/apps/cadence/jasper/2025.09-p002/doc`.
- Docs win over memory or examples in this skill.
- Consult:

| Topic | Document |
|-------|----------|
| CSR app flow, CSV keywords and cell positions, access types, attributes, checker modules and ports, ABVIP integration | `jasper_csr_userguide.pdf` |
| `check_csr` (all switches), `task`, `analyze`, `elaborate`, `clock`, `reset`, `report`, `abvip`, `jg -csr` / `-batch` | `jasper_command_reference.pdf` |
| Coverage, `check_cov` init/measure/report/waivers | `jasper_cov_userguide.pdf` |
| ProofGrid settings | `jasper_proofgrid_manager.pdf` |
| Engine selection | `jasper_engine_selection.pdf` |
| Official CSR example (TCL, bind, CSV) | `example_jasper_apps/CSR/` |
| Browsable HTML docs | `HTML/` |

**KEY PRINCIPLES (per `jasper_csr_userguide.pdf` and `jasper_command_reference.pdf`):**
- Elaborate the design before any `check_csr` operation.
- The CSR app cannot be used together with SEC, SPV or X-Prop (command reference, `check_csr` note) — run those in separate sessions.
- The CSR app models each register with a shadow value; properties compare bus/direct reads against it.
- Constraints are generally in `<embedded>`; copy them to the CSR task with `task -edit CSR -copy_all -source_task <embedded>`.
- Recommended for bring-up: `-partitioned_checks` (finer per-field properties, easier debug); default is unified (`AST_DATA_INTEGRITY`).
- Protection and HW behaviour are MODELLED with attributes (verified), not assumed away.

---

## Step-by-Step Procedure

### Step 1: Choose the CSR Checker (from spec bus protocol, Q3)

| Spec bus | Checker | Notes (jasper_csr_userguide.pdf, Instance Interface) |
|----------|---------|-------------------------------------------------------|
| AMBA APB 2.0 (ARM IHI 0024C) | ABVIP `cdn_abvip_apb_master` with `.CONFIG_CSR_INTERFACE(1)` (MANDATORY) | `abvip -set_location`; legal-stimulus assumptions + DUT response assertions |
| APB3 / APB4 | ABVIP `cdn_abvip_apb3_master` / `cdn_abvip_apb4_master` with `.CONFIG_CSR_INTERFACE(1)` (MANDATORY) | `abvip -set_location`; CSR check discarded on PSLVERR error response |
| AHB-Lite | ABVIP `cdn_abvip_ahb_lite_master` (MANDATORY) | CSR check discarded on HRESP ERROR |
| AXI3 / AXI4 | ABVIP `cdn_abvip_axi3_master` / `cdn_abvip_axi4_master` with `.CONFIG_CSR_INTERFACE(1)` | `CONFIG_CSR_DISCARD_ON_ERROR` selects discard on SLVERR/DECERR |
| AMBA APB 2.0 — fallback only (no ABVIP licence/path, user-approved) | `jasper_amba_apb_csr_checker` | "Constrains port signal behavior: No" → spec-derived APB assumptions required; PSLVERR handling not documented in UG |
| Custom / internal register bus (backdoor) | `jasper_csr_checker` (`clk, rstN, wr, rd, addr, din, dout`) | adapter logic builds `wr`/`rd` valid pulses (UG Appendix A); does not constrain ports |
| Byte enables, bit masks, separate rd/wr address, secure maps | `jasper_csr_extended_checker` | tie unused masks / byte enables high (UG Appendix A) |

**ABVIP is MANDATORY for every standard bus (APB2/3/4, AHB-Lite, AXI3/4):**
- Built-in checkers (`jasper_csr_checker`, `jasper_csr_extended_checker`, `jasper_amba_apb_csr_checker`, `jasper_amba_ahb_lite_csr_checker`) do NOT constrain ports (UG, Instance Interface): formal can drive illegal bus sequences → false CEX, and the DUT's responses are not protocol-checked.
- ABVIP master in CSR mode gives:
  - assumptions on master-driven signals → only legal transfers reach the DUT
  - assertions on DUT (slave) responses → DUT protocol compliance
  - protocol covers → legal writes/reads reachable
  - CSR shadow model + CSR properties (ABVIP instance = `check_csr -instance`)
- ABVIP property names / parameters: ABVIP user guide (Help – ABVIP User Guides) — do not invent names.
- Built-in checker only for custom/backdoor buses, or as user-approved fallback; then every bus assumption comes from the bus spec and is listed as `ASSUME` in traceability.
- **ABVIP discard-on-error (UG, Instance Interface):**
  - APB3/APB4: "Check discarded on pslverr error response"; AHB-Lite: discarded on HRESP ERROR; no switch documented to disable it.
  - AXI3/AXI4: `CONFIG_CSR_DISCARD_ON_ERROR` — set `0` (errored transfers still checked) unless the spec defines error responses for legal accesses.
  - Risk: a DUT that wrongly errors on a legal access hides CSR bugs (proof still passes) → Step 5b is MANDATORY.

- Bind as close to the register block as the spec interface allows (UG Appendix A: binding at large-design primary inputs adds sequential depth).
- The IPK checkers (`jasper_amba_apb_sv` etc.) are deprecated — do not use.
- Confirm the spec APB revision against the checker: the UG lists the built-in APB checker as "AMBA APB Version 2.0 (ARM IHI 0024C)".

### Step 2: Extract the Register Map from the Spec (ONLY)
- For EACH register in the spec register-map section (Q2):
  1. Name, byte address/offset, width, register access type, register reset value, spec section.
  2. For EACH field: name, MSB, LSB, access type, reset value, description.
  3. Special behaviour stated by the spec: W1C/W1S/toggle, write-once, self-clearing pulse, read-clear/set, HW-updated status (and its update condition), write/read protection, HW-vs-SW priority, parameter-dependent reset, aliases, reserved bits/addresses.
- Record every register and field as a row in `req_extraction.csv` (Traceability section) with SPEC_ID and spec section.
- Spec RESERVED fields: declare them as the spec states (e.g. `RO` reset 0, or `RZ`); see Step 3.
- **CRITICAL:** any missing reset value, access type, update condition or protection condition is a SPEC GAP → ask the user. Do NOT open RTL to find it.

### Step 3: Create the CSR Map CSV
- Read `resources/csv_format_reference.md` when doing this step.
- **Row formats (jasper_csr_userguide.pdf, Keywords table):**
```
DATA_WIDTH,32
ADDR_OFFSET,0
# <REG> — spec §<x.y>
CSR,,<REG>,<width>,<byte_addr>,<access>,<reset>,<description>
ATTR,<REG_LEVEL_ATTR>,<value>
,FIELD,<FIELD>,<msb>,<lsb>,<access>,<reset>,<description>
,ATTR,<FIELD_LEVEL_ATTR>,<value>
```
- Cell positions:
  - `CSR` row: keyword, EMPTY cell, name, size, byte address, access type, reset, description.
  - `FIELD` row: EMPTY cell BEFORE the keyword, then name, end bit (MSB), start bit (LSB), access type, reset, description.
  - `ATTR` row: keyword, attribute name, value(s); applies to the last preceding CSR row or the last preceding FIELD row.
    - Keywords are recognised in the first non-empty cell; the leading comma is not what sets the scope — position does.
    - Project style: register-level `ATTR,...` placed directly after the CSR row (before the first FIELD); field-level `,ATTR,...` directly after its FIELD row.
```
RIGHT: ,FIELD,<FIELD>,7,0,RW,8'h00,<desc>
WRONG: FIELD,,<FIELD>,7,0,RW,8'h00,<desc>    (name lands in the MSB cell — every column shifts)
RIGHT: CSR,,<REG>,32,0x10,RW,32'h0000_0000,<desc>
WRONG: REG,,<REG>,...  /  CSR,<REG>,...       (REG is not a keyword; CSR needs the empty cell)
```
- **Rules:**

| Item | Rule (doc) |
|------|------------|
| Reset value | any valid Verilog expression (UG); `0x..` is accepted. Project rule: sized literals `32'h0000_0830` for clarity |
| Field reset | overrides the CSR reset; both blank = no reset value (NOT "volatile") |
| Parameter-dependent reset | `,ATTR,RESET_VALUE_EXPRESSION,<expr>` — module parameter by hierarchical path, package parameter as `<pkg>.<PARAM>` (2024.03p002+); parameter name from the spec |
| Comments | `#` in any cell; all cells to its right are a comment |
| Blank lines | not required (rows are found by keyword); allowed for readability |
| `DATA_WIDTH` | default data width (default 8); per-CSR size overrides it |
| `ADDR_WIDTH` keyword | still accepted (backward compatibility); must match the checker `ADDR_WIDTH` parameter. Prefer the checker parameter |
| `ADDR_OFFSET` | once, before all CSR rows; added to every register address |
| Names | legal Verilog identifiers; hierarchical references must start with the top module name |
| Unassigned bits | allowed. Spec RESERVED fields → declare per spec; or `check_csr -load ... -unassigned_field_checks (constant \| zero)` (initial release) |
| Duplicate field names (e.g. many `RESERVED`) | `check_csr -load ... -use_long_field_names` postfixes property names with `_msb_lsb` |

- **Access types (jasper_csr_userguide.pdf, Access Types):**

| Access | Meaning |
|--------|---------|
| `RW` | read-write through the interface |
| `RO` | read-only; interface cannot write |
| `RC` | read-clear: a read sets every bit to 0 |
| `RS` | read-set: a read sets every bit to 1 |
| `RR` | read-reset: a read sets the register to its reset value |
| `WO` | write-only; reads verified only through another register / aliasing (or `DIRECT_READ`) |
| `R1` | reads return 1 in every bit |
| `RZ` | reads return 0 in every bit |

- There is no W1C / W1S / write-once access type — these are attributes (table below).
- The register access type is the default for its fields; a field access type overrides it.

**Spec behaviour → CSV mapping (replaces any RTL-derived mapping):**

| Spec behaviour | Access | Reset cell | ATTR rows (field level unless noted) |
|----------------|--------|------------|--------------------------------------|
| Normal read/write | `RW` | spec reset | — |
| Read-only constant (ID, capability) | `RO` | spec value | — |
| Always reads 0 / 1 | `RZ` / `R1` | spec value | — |
| Clear / set / reset on read | `RC` / `RS` / `RR` | spec reset | `ACCESS_PRIORITY` if the spec defines HW update vs read order |
| Write-only | `WO` | spec reset | `,ATTR,DIRECT_READ,<en>,<data>,<lat>` only if the spec names an observable output |
| HW-updated status, spec defines the update source/condition | `RO` | spec reset | `,ATTR,DIRECT_WRITE,<en>,<data>,<latency>,<modified_write_value>` |
| HW-updated status, spec gives NO update condition | `RO` | spec reset | `,ATTR,BUS_READ_CHECK,read_undefined` + SPEC GAP (read data not checked) |
| W1C (write 1 to clear), HW set | `RW` | spec reset | `,ATTR,MODIFIED_WRITE_VALUE,oneToClear` + `,ATTR,DIRECT_WRITE,<hw_set_expr>,<set_data>` |
| W1S / W1T / W0C / W0S / W0T | `RW` | spec reset | `MODIFIED_WRITE_VALUE` = `oneToSet` / `oneToToggle` / `zeroToClear` / `zeroToSet` / `zeroToToggle` |
| Any write clears / sets all bits | `RW` | spec reset | `MODIFIED_WRITE_VALUE` = `clear` / `set` |
| Write-once | `RW` | spec reset | `,ATTR,BUS_WRITE_CHECK,write_once` |
| Self-clearing one-cycle pulse on write | per spec | spec reset | `,ATTR,BUS_WRITE_CHECK,write_pulse,ACTIVE_HIGH` (or `ACTIVE_LOW`) |
| Writes ignored (no effect) | per spec | spec reset | `,ATTR,BUS_WRITE_CHECK,write_no_effect` |
| Write-protected by spec condition | spec access | spec reset | `ATTR,BUS_WRITE_ENABLE,<prot_expr>` (Step 5) |
| Read-protected by spec condition | spec access | spec reset | `ATTR,BUS_READ_ENABLE,<prot_expr>,read_zero\|read_one\|read_undefined` (Step 5) |
| Writes outside a spec range ignored | `RW` | spec reset | `,ATTR,BUS_WRITE_ENABLE,<expr on write data>` |
| HW and SW access on the same cycle, spec defines order | — | — | `ATTR,ACCESS_PRIORITY,<event>,<event>[,...]` (≥ 2 values) |
| Spec latency between bus and register | — | — | `BUS_WRITE_LATENCY` / `BUS_READ_LATENCY` / `BUS_LATENCIES` |
| Parameter / input dependent reset | per spec | — | `RESET_VALUE_EXPRESSION,<expr>` |
| Register reset by a separate (soft) reset | per spec | spec reset | `ATTR,RESET_SIGNAL,<active_low_expr>` |
| Bits without a known reset | per spec | spec reset | `ATTR,RESET_MASK,<mask>` |
| Same register at two addresses | per spec | same | `ATTR,REGISTER_ALIAS_FOR,<REG>` / `,ATTR,FIELD_ALIAS_FOR,<REG>,<FIELD>` |
| Spec says SW must not write / read | per spec | spec reset | `BUS_WRITE_CHECK,write_forbidden` / `BUS_READ_CHECK,read_forbidden` (default generates ASSUMPTIONS; `TEST_OPTION,assert_bus_constraint` makes them assertions) |

- `MODIFIED_WRITE_VALUE` applies to bus writes only; a direct write takes its modified write value in `DIRECT_WRITE` cell n+4.
- Multiple `DIRECT_WRITE` rows: the first matching row wins; all latencies must be equal.
- `DIRECT_WRITE` / `DIRECT_READ` enable and data are expressions; take signal names from the spec (top-level ports, prefixed with the top module name). If the spec names no observable signal → SPEC GAP; use `read_undefined` meanwhile.
- Reference other registers/fields by shadow value with `${<REG>.<FIELD>}` (UG, Referencing Register/Field Name).
- `WRITE_VALUE_CONSTRAINT` (field level) and `write_forbidden` / `read_forbidden` / `write_reset` generate assumptions by default — list each as `ASSUME` in traceability.
- Address blocks, reserved address ranges (`ADDR_BLOCK` + `RESERVED`, task `CSR_RESERVED_CHECKS`), `REGISTER_MAP`/`REMAP_STATE` secure maps, `INDIRECT_ADDR_MAP`/`ACCESSED_BY` windowed CSRs: see `resources/csv_format_reference.md`.

### Step 4: Create the CSR Bind File
- Bind target module and port names: from the spec port/interface table; if absent, from the RTL top-level port list (binding only — state this in the file header).
- Always set `ADDR_WIDTH` / `DATA_WIDTH` explicitly (UG checker parameter defaults: 16 / 8).
- `check_csr -instance` = hierarchical path of the checker instance below the top.
  - Bind into `<top_module>` → `<ip>_csr`; checker inside an adapter module → `<adapter_inst>.<checker_inst>` (official example: `i_jasper_csr.jasper_csr_checker0`).
- **Backdoor / custom bus** (`jasper_csr_checker`):
```systemverilog
// Binding names: <spec section> (or RTL top-level port list — binding only)
bind <top_module> jasper_csr_checker
  #(.ADDR_WIDTH(<AW>), .DATA_WIDTH(<DW>))
  <ip>_csr (
    .clk  (<clk>),
    .rstN (<rst_n>),          // active low; invert an active-high spec reset
    .wr   (<wr_valid_expr>),  // one valid write per transfer
    .rd   (<rd_valid_expr>),  // asserted when read data is valid on dout
    .addr (<addr>),
    .din  (<wdata>),
    .dout (<rdata>)
  );
```
- **APB 2.0 frontdoor** (`jasper_amba_apb_csr_checker`, UG port list):
```systemverilog
bind <top_module> jasper_amba_apb_csr_checker
  #(.ADDR_WIDTH(<AW>), .DATA_WIDTH(<DW>))
  <ip>_csr (
    .PCLK    (<PCLK>),
    .PRESETn (<PRESETn>),
    .PSELx   (<PSEL>),        // UG prototype says PSELx, UG port table says PSEL — confirm at elaborate
    .PENABLE (<PENABLE>),
    .PREADY  (<PREADY>),
    .PADDR   (<PADDR>),
    .PWRITE  (<PWRITE>),
    .PPROT   (<PPROT>),
    .PWDATA  (<PWDATA>),
    .PSTRB   (<PSTRB>),
    .PRDATA  (<PRDATA>),
    .PSLVERR (<PSLVERR>)
  );
```
  - Signals the spec bus does not have (e.g. `PPROT`, `PSTRB`, `PSLVERR`): tie to the protocol-neutral value stated by the bus spec and record it as an assumption in traceability.
- **APB3 / APB4 / AHB-Lite / AXI via ABVIP:**
```systemverilog
bind <top_module> cdn_abvip_apb4_master #(.CONFIG_CSR_INTERFACE(1) /* + ABVIP width params */) <ip>_apb_csr (/* ABVIP ports per ABVIP doc */);
```
  - TCL: `abvip -set_location <abvip_dir>` before analyze; `check_csr -load <csv> -instance <ip>_apb_csr` (instance = ABVIP instance).
  - ABVIP parameter / port names: ABVIP user guide (Help – ABVIP User Guides, after `abvip -set_location`).
- **Extended** (`jasper_csr_extended_checker`): ports `clk, rstN, wr, wr_addr, din, wr_secure, wr_bit_mask, wr_byte_enable, rd, rd_addr, dout, rd_secure, rd_bit_mask`; tie unused masks/byte enables high, secure bits to a fixed value.

### Step 5: Write / Read Protection — VERIFY the Spec Condition (MANDATORY)
- Every spec protection (key register, lock bit, privilege, test-mode pin) is modelled with attributes so the CSR app VERIFIES both the protected and the unprotected behaviour:
```
CSR,,<REG>,32,<addr>,RW,32'h0000_0000,<desc>
ATTR,BUS_WRITE_ENABLE,<prot_expr>                       # writes update the shadow only when <prot_expr> is true
ATTR,BUS_READ_ENABLE,<prot_expr>,read_zero              # blocked reads: read_zero | read_one | read_undefined per spec
,FIELD,<FIELD>,7,0,RW,8'h00,<desc>
,ATTR,BUS_WRITE_ENABLE,<field_prot_expr>                # field-level protection, if the spec protects per field
```
- Build `<prot_expr>` from the spec only:
  - Register/field-based condition → shadow reference, e.g. `${<LOCK_REG>.<LOCK>} == 1'b0`, `${<KEY_REG>.<KEY>} == 32'h<spec_key>`.
  - Pin/port-based condition → `<top_module>.<port>` (top module name prepended, UG Worksheet Format).
  - Key sequences, write-only/self-clearing key registers or internal-only state that cannot be expressed this way → SPEC GAP; ask the user how to observe the unlock condition. Do not guess an internal signal.
- Blocked-read value (`read_zero` / `read_one` / `read_undefined`) comes from the spec; if the spec is silent → `read_undefined` + SPEC GAP.
- The app creates `COV_BUS_WRITE_ENABLE_CHANGED` / `COV_BUS_READ_ENABLE_CHANGED`; both must be covered (proves locked and unlocked states are reachable).
- **Do NOT assume the key open by default.**
  - `assume {<key_signal> == <unlock>}` removes the protection path from the proof: a broken lock passes.
  - Only if the user explicitly asks: add the assumption (in `<embedded>` before the task copy, or after `task -set CSR`), and log it as a COVERAGE GAP (`req_extraction.csv` Notes, `formal_traceability.csv` Property_Type `ASSUME`, final summary).

### Step 5b: Bus Error Response (MANDATORY — both ABVIP and built-in checkers)

- The CSR app has no CSV attribute for bus-error behaviour → small SVA file `<ip>_bus_err_chk.sv` (bound like the checker), spec-derived only.
- Inputs: Q20 + spec bus/register sections. Missing → SPEC GAP, ask the user; do not derive from RTL.
- Checks (APB shown; AHB-Lite HRESP / AXI BRESP·RRESP analogous):
  1. **Error conditions list** from spec (unmapped address, protected/locked write, PPROT not allowed, ...) → `<spec_err_cond>`; "never used" → `1'b0`.
  2. **No error on legal access** (closes the ABVIP discard gap):
     - `ast_no_err_legal: assert property (@(posedge PCLK) disable iff (!PRESETn) PSEL && PENABLE && PREADY && !(<spec_err_cond>) |-> !PSLVERR);`
  3. **Error when required** (only if the spec requires it):
     - `ast_err_required: assert property (@(posedge PCLK) disable iff (!PRESETn) PSEL && PENABLE && PREADY && (<spec_err_cond>) |-> PSLVERR);`
  4. **Errored write has no effect** (if spec says so): no CSR check covers it (transfer discarded) → assert the target field keeps its value, via spec-visible read-back or a spec-named signal.
  5. **Per-register reachability:** one cover per register, read completing with no error:
     - `cov_rd_ok_<REG>: cover property (@(posedge PCLK) PSEL && PENABLE && PREADY && !PWRITE && PADDR == <addr> && !PSLVERR);`
     - Unreachable → all CSR checks for that register were discarded → finding.
- Load: `analyze -sv <ip>_bus_err_chk.sv` before elaborate; properties land in `<embedded>` → copied to the CSR task by `task -edit CSR -copy_all`.
- Traceability: category `BUS_ERR`, one SPEC_ID per check.
- Failing `ast_no_err_legal` / `ast_err_required` = DUT bug or spec gap → `formal-cex-debug`.

### Step 6: Choose Run Flow (ASK THE USER — MANDATORY)
- Use the Upfront Questions answer Q8 (ask now only if it was not answered):

| Option | Output | Run command |
|--------|--------|-------------|
| **A. Standalone TCL** | `jg_csr_setup.tcl` + `<cfg_dir>/RUNCMD_tcl` (Step 6a) | see Step 6a run command |
| **B. Adsim `sim.setup`** | `<cfg_dir>/sim.setup` + `<cfg_dir>/RUNCMD` (Step 6b) | see Step 6b run command |
| **C. Both** | Both files, kept consistent | — |

- Do NOT pick a default silently.

### Step 6a: Create the CSR TCL Setup (if user selects A or C)
- Clock / reset from the spec (Q5) — the CSR app needs a global clock and reset (UG flow step 3), unlike the connectivity app.
- Order follows the UG flow: analyze → elaborate → clock/reset → constraints → `check_csr -load` → task copy → `check_csr -prove`.
```tcl
clear -all
set FPV_ROOT <absolute_path>

# ABVIP (MANDATORY for standard buses, Q19)
abvip -set_location <abvip_dir>
# Bus-error checks (Step 5b)
analyze -sv ${FPV_ROOT}/csr/<ip>_bus_err_chk.sv

# [Optional coverage] check_cov -init -model all -type all

analyze -sv09 -f ${FPV_ROOT}/rtl_list/filelist.f
analyze -sv09 ${FPV_ROOT}/csr/<ip>_csr_bind.sv

elaborate -top <top_module> \
    -parameter <PARAM1> <val1>

# Clock / reset from spec §<x.y>
clock <clk>
reset -expression {!<rst_n>}

# Spec operating conditions only (e.g. DFT inactive) — goes to <embedded>
# assume -name asm_<name> {<spec_operating_condition>}

# Load the spec-derived CSR map (instance = checker instance path)
check_csr -load ${FPV_ROOT}/csr/<ip>_csr_map.csv -instance <ip>_csr -partitioned_checks
# Debug the parse before proving:
# check_csr -list register -instance <ip>_csr
# check_csr -list field -instance <ip>_csr -register <REG>
# check_csr -list reset_value -instance <ip>_csr -register <REG>

# Copy <embedded> assumptions (and other properties) into the CSR task
task -edit CSR -copy_all -source_task <embedded>
task -set CSR

# Coverage waivers: ADD WAIVERS HERE (source waiver TCL files once available)

# ProofGrid (per Q13)
# set_proofgrid_mode shell
# set_proofgrid_shell {<bsub command>}
set_prove_time_limit <limit>

check_csr -prove

file mkdir ${FPV_ROOT}/results
report -summary -results -file ${FPV_ROOT}/results/report_csr.txt -force

# [Optional coverage]
# check_cov -measure -task {CSR} -type {stimuli coi proof} -time_limit <limit>
# check_cov -report -task {CSR} -report_file ${FPV_ROOT}/results/report_csr_cov.html -force -html
```
- `task -edit CSR -copy_all -source_task <embedded>` copies the `<embedded>` assumptions into the CSR task (UG flow step 4); assumptions added after `task -set CSR` go into the CSR task directly.
- Reserved-register checks run in task `CSR_RESERVED_CHECKS`; copy the needed assumptions there too (UG, Verification for Reserved Registers).
- Optional switches on `check_csr -load`: `-addr_interaction_covers`, `-unassigned_field_checks (constant|zero)`, `-use_long_field_names`, `-create_vplan`, `-load_extension <ext_csv>`.
- After all checks pass, `-unified_check` (command reference spelling; UG text says `-unified_checks`) may be used for regression; partitioned stays the debug recommendation.
- Re-prove a subset: `check_csr -prove -instance <inst> -register <REG> [-field <FIELD>]`.
- **CRITICAL — absolute paths:** define `FPV_ROOT` and prefix every file; JG runs from `jgproject/`.

**TCL run command (MANDATORY — generate per config):**
- Write it to `<cfg_dir>/RUNCMD_tcl` and print it to the user.
- GUI: `jg -csr <abs_cfg_dir>/jg_csr_setup.tcl`
- Batch (Q12): `jg -csr -batch <abs_cfg_dir>/jg_csr_setup.tcl`
- `-csr` launches the CSR Verification App (command reference, Command-Line Options); official example: `jg -csr CSR_verilog_example.tcl`.

### Step 6b: Adsim `sim.setup` (if user selects B or C)
- Read `resources/sim_setup_template.md` when doing this step.
- One `sim.setup` per config dir; clock/reset from the spec; `check_csr` and `task` lines in `FML_TCL_COMMANDS`; NO `clock -none` / `reset -none`.

**sim.setup rules:**
- Keep the header block; fill Configuration Parameters from the spec.
- Use `$ADIP_BLOCKS_ROOT`-relative paths, never absolute workarea paths.
- The bind file is compiled via `EXTRA_COMPILE_OPTIONS`.
- No `check_cov -init` (adsim `-jgcov` issues cov_init, ECOV081).
- Reports needing proof results go in `pre_exit.tcl`, staged via `PRE_SIM_COMMANDS`.
- `FML_INSTTOP` must equal the elaborate `-top`.

**sim.setup run command (MANDATORY — generate per config):**
- Write it to `<cfg_dir>/RUNCMD` and print it to the user.
```
adsim -clean -block <ip_block> -gui -jgcov -jasper -formal \
      -resdir <abs_cfg_dir>/Result_ \
      -force_setup <abs_cfg_dir>/sim.setup
```
- **TODO (open — confirm with the `adsim` skill / user before first run):** how adsim launches JG with the CSR app (`jg -csr`).
  - Candidate: `FML_CMDLINE_OPTIONS : -csr` (adsim skill `formal.md`: "Extra options passed to the jg command line") — not yet confirmed for `-formal` mode.
  - Do NOT invent an adsim switch. adsim `-regval` is IP-XACT based (`FML_REG_IPXACT`) and is not used (spec-only).
- `-jgcov` requires one-step mode; `-gui` provides it (Q12).
- One RUNCMD per config directory; `-resdir` and `-force_setup` point to the same config dir.

### Step 7: Validate the Parse and Results
- **Parse check (before prove):**
  - `check_csr -list register -instance <inst>` → every spec register present.
  - `check_csr -list field -instance <inst> -register <REG>` → every spec field present.
  - `check_csr -list (msb|lsb|access_type|reset_value) -instance <inst> -register <REG> -field <FIELD>` → matches the spec table.
  - Missing registers/fields or shifted values → CSV cell-position error (Step 3 RIGHT/WRONG).
- **Generated property names (documented):**
  - Unified (default): `AST_DATA_INTEGRITY` (reset value + read-after-write checks).
  - Partitioned (`-partitioned_checks`): `AST_RESET_VALUE`, `AST_BUS_READ_AFTER_BUS_WRITE`, `AST_BUS_READ_AFTER_DIRECT_WRITE`, `AST_BUS_WRITE_BUS_READ_IMMEDIATE`, `AST_BUS_WRITE_DIRECT_READ_IMMEDIATE`, `AST_DIRECT_READ_AFTER_BUS_WRITE`, `AST_DIRECT_READ_AFTER_DIRECT_WRITE`, `AST_DIRECT_WRITE_BUS_READ_IMMEDIATE`, `AST_DIRECT_WRITE_DIRECT_READ_IMMEDIATE`.
  - Attribute-driven: `AST_/ASM_FORBID_READ`, `AST_/ASM_FORBID_WRITE`, `AST_/ASM_BUS_WRITE_VALUE_EQUAL_TO_RESET_VALUE`, `AST_/ASM_BUS_WRITE_ENUMERATED_VALUES`, `..._MINIMUM_VALUE`, `..._MAXIMUM_VALUE`, `..._AS_READ`.
  - Covers: `COV_BUS_WRITE`, `COV_READ`, `COV_BUS_WRITE_ENABLE_CHANGED`, `COV_BUS_READ_ENABLE_CHANGED`, `COV_DIRECT_WRITE_CHANGED`, `COV_DIRECT_READ_CHANGED`, `COV_RESET_CHANGED` (only with `RESET_SIGNAL`), address-interaction covers with `-addr_interaction_covers`.
- Do not use a fixed "checks per field" count; compare the property list against the parsed registers/fields.
- Every assertion proven, every cover covered; any unreachable cover → investigate (constraint over-restricting or unreachable protection state).

### Step 8: CEX Debug — use the `formal-cex-debug` skill (MANDATORY on any failing property)
- Load skill `formal-cex-debug` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-cex-debug/SKILL.md`).
- Trigger: any failing `AST_*`, any unreachable `COV_*`.
- The CSR proof accelerator adds debug signals to violation traces automatically; in the GUI use "Plot Debugging Signals" on a FIELD/CSR (UG, GUI Orientation).
- CSR-specific first checks (in order):
  1. Parse: `check_csr -list ...` matches the spec (Step 7).
  2. Spec behaviour modelled? HW-updated field without `DIRECT_WRITE`, W1C without `MODIFIED_WRITE_VALUE`, protection without `BUS_WRITE_ENABLE`, latency without `BUS_*_LATENCY`, HW/SW collision without `ACCESS_PRIORITY`.
  3. Bind: `wr`/`rd` valid timing, `rstN` polarity, address width/byte addressing, checker instance path.
  4. Constraints copied to the CSR task (`task -edit CSR -copy_all -source_task <embedded>`).
- Classification → action:
  - RTL bug (RTL differs from the spec) → design finding; keep the check failing.
  - CSV/bind error vs spec → fix CSV/bind, re-run.
  - Spec gap / ambiguity → log in `req_extraction.csv`, ask the user.
- Never change the CSV to match RTL behaviour.
- Output: `fpv_env/rca/cex_<property>.md` per failure (+ batch summary).

## Traceability (MANDATORY)
- Generate TWO CSV files in `fpv_env/traceability/`; column definitions, categories and examples: read `resources/traceability_format.md`.
- **File 1 `req_extraction.csv`:** one row per register AND per field (and per spec behaviour: protection, HW update, priority, reset expression) from the spec.
  - Columns: `SPEC_ID,PDF_Section,Category,Requirement_Text,Formally_Verifiable,Notes`.
  - Every row cites a spec section; `PDF_Section=RTL` / `Yoda` / `IP-XACT` is NOT allowed.
  - Spec gaps are separate rows with `Formally_Verifiable=NO`, Notes `Spec gap — awaiting spec update`.
- **File 2 `formal_traceability.csv`:** maps each SPEC_ID to the generated CSR properties.
  - Columns: `SPEC_ID,Property_Type,Property_Label,Property_File,Bind_Target,Config,Status`.
  - Property_Label = JG property name as reported (`report` / Property Table), Property_File = the CSR map CSV.
- **Completeness check:**
  1. Every register and field row in `req_extraction.csv` with `Formally_Verifiable=CSR`/`YES` has ≥ 1 `MAPPED` row.
  2. Every CSR/FIELD row in the CSV has a SPEC_ID (CSV `#` comment on the row with the SPEC_ID).
  3. Every generated assumption (forbidden/constraint attributes, user-requested key assumption) appears as `ASSUME`.
  4. No `UNMAPPED` rows remain unless justified.

### Sign-Off Traceability — use the `formal-traceability` skill (MANDATORY after proofs)
- Load skill `formal-traceability` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-traceability/SKILL.md`).
- Run after all configs are proven and CEXs are resolved; before vPlan creation and the Final Audit.
- Reuse (do not regenerate) `req_extraction.csv` and `formal_traceability.csv` as its Step 1/3 inputs; its Status value `CSR` may be used for CSR-checker mappings.
- Execute: property collection per config, `signoff_matrix.csv`, completeness audit; Jama / Confluence publish ONLY per Q18.
- Output: `fpv_env/traceability/signoff_matrix.csv` (+ audit report).

## Output Files

```
fpv_env/csr/
├── <ip>_csr_map.csv          Spec-derived CSR map (DATA_WIDTH, CSR/FIELD/ATTR rows)
├── <ip>_csr_bind.sv          Checker bind (jasper_csr_checker / APB / ABVIP / extended)
├── jg_csr_setup.tcl          JG CSR TCL (flow A/C)
├── <cfg_dir>/RUNCMD_tcl      jg -csr run command (flow A/C)
├── <cfg_dir>/sim.setup       Adsim setup per config (flow B/C)
├── <cfg_dir>/RUNCMD          adsim run command (flow B/C)
└── <cfg_dir>/pre_exit.tcl    Post-prove reports hook (flow B/C)

fpv_env/traceability/
├── req_extraction.csv        Spec register/field requirements (SPEC_ID → spec section)
├── formal_traceability.csv   SPEC_ID → CSR property mapping
└── signoff_matrix.csv        Per-config sign-off (formal-traceability)

fpv_env/rca/
└── cex_<property>.md         CEX root-cause reports (formal-cex-debug)

fpv_env/results/
├── report_csr.txt            JG results summary
└── report_csr_cov.html       Coverage report (optional)
```

## Optional Step: vPlan Creation (USER DECIDES — now or later)
- Use the Upfront Questions answer Q16 (ask now only if not answered; do NOT decide silently):
  - **NOW** → after traceability is complete, before the Final Audit.
  - **LATER** → skip; keep `ENABLE_VPLAN` / `VPLAN_SOURCE` commented in sim.setup; list it as pending in the final summary.
  - **NOT NEEDED** → skip; remove the vPlan lines from sim.setup.
- Option 1 — `formal-vplan` skill (spec-driven vplanx):
  - Load skill `formal-vplan` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-vplan/SKILL.md`) and follow its steps; CSR section = one entry per spec register (offset, access, reset, all fields).
  - Output: `<IP>_Formal_VPlan_CSR.vplanx`; set `VPLAN_SOURCE`, enable `ENABLE_VPLAN : 1`, re-run RUNCMD.
- Option 2 — `check_csr -load ... -create_vplan`: exports `csr_vplan.csv` to the session directory, structured by register → field → checks (command reference).
  - Built from the loaded CSV, so it inherits the spec-only CSV; still keep SPEC_IDs in traceability.

## Final Step: Parameter & Default-Value Audit (MANDATORY — run LAST)
- After proofs, traceability (and vPlan if NOW), run the `param-spec-audit` skill.
  - Load skill `param-spec-audit` (file: `/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/param-spec-audit/SKILL.md`) and follow its Steps 1–4 in full.
- Why: CSR proofs cover the configs that were run; the audit catches parameter-dependent reset values / widths that are hardcoded in RTL or never exercised.
- Inputs reused (do not re-ask): IP name, top module, filelist, spec, reset values / `RESET_VALUE_EXPRESSION` parameters from `req_extraction.csv`, DV dir = this CSR directory, SoC context from Q17.
- Spec-only rule: RTL is read only as the item UNDER AUDIT, never to define expected values.
- Feed results back: DV gap → add config / CSR row, re-run; spec gap → log and ask; RTL non-compliant → design finding.
- Output: `fpv_env/reports/<ip>_param_audit.html`.

## Reference
- Authoritative Jasper documentation (ALWAYS consult first): `/cad/adi/apps/cadence/jasper/2025.09-p002/doc` — see the TOOL DOCUMENTATION table.
- Skill resources (`resources/`, read when doing the referenced step):
  - `resources/csv_format_reference.md` — keyword cell positions, attributes per level, blocks (ADDR_BLOCK, REGISTER_MAP, INDIRECT_ADDR_MAP), RIGHT/WRONG rows, generic worked example
  - `resources/sim_setup_template.md` — Step 6b adsim `sim.setup` template for CSR
  - `resources/traceability_format.md` — `req_extraction.csv` / `formal_traceability.csv` for CSR
- Sibling skills: `formal-cex-debug`, `formal-traceability`, `formal-vplan`, `param-spec-audit` (absolute paths in the steps above).

## Quality Checklist

### Spec-Only
- [ ] Upfront Questions Q1–Q18 asked once; answers recorded in the final summary
- [ ] Every register/field/reset/access/protection from the spec register table; no value from RTL, Yoda `.yda` or IP-XACT
- [ ] Binding names taken from RTL ports (if any) documented as binding-only in the bind header
- [ ] Every spec gap logged in `req_extraction.csv` and raised to the user

### CSR Map CSV
- [ ] `CSR,,<name>,<size>,<addr>,<access>,<reset>,<desc>` and `,FIELD,<name>,<msb>,<lsb>,<access>,<reset>,<desc>` cell positions
- [ ] ATTR rows directly after the CSR (register level) or FIELD (field level) they apply to
- [ ] Reset values as sized Verilog literals; parameter-dependent resets via `RESET_VALUE_EXPRESSION`
- [ ] Only documented access types (RW, RO, RC, RS, RR, WO, R1, RZ); W1C/W1S/write-once/pulse via attributes
- [ ] HW-updated fields: `DIRECT_WRITE` from spec signals, or `read_undefined` + spec gap
- [ ] Spec RESERVED fields declared per spec (or `-unassigned_field_checks` chosen deliberately)
- [ ] Each CSR/FIELD row carries its SPEC_ID in a `#` comment

### Protection
- [ ] Every spec protection modelled with `BUS_WRITE_ENABLE` / `BUS_READ_ENABLE` (blocked-read value from spec)
- [ ] `COV_BUS_WRITE_ENABLE_CHANGED` / `COV_BUS_READ_ENABLE_CHANGED` covered
- [ ] No "key open" assumption unless the user asked; if present, logged as a coverage gap

### Bind / TCL / sim.setup
- [ ] Checker chosen from the spec bus protocol (Step 1); `ADDR_WIDTH`/`DATA_WIDTH` set explicitly
- [ ] `check_csr -instance` equals the checker instance path
- [ ] elaborate → clock/reset (spec) → constraints → `check_csr -load` → `task -edit CSR -copy_all -source_task <embedded>` → `task -set CSR` → `check_csr -prove`
- [ ] `-partitioned_checks` used for bring-up
- [ ] No SEC / SPV / X-Prop in the same session
- [ ] Absolute paths (`FPV_ROOT`) in TCL; `$ADIP_BLOCKS_ROOT` paths in sim.setup
- [ ] `RUNCMD_tcl` (`jg -csr ...`) and/or `RUNCMD` (adsim) generated per config; adsim CSR-app TODO resolved with the user
- [ ] "Coverage waivers: ADD WAIVERS HERE" placeholder present

### Protocol Compliance / Bus Errors
- [ ] ABVIP master (`CONFIG_CSR_INTERFACE(1)`) used for every standard bus; built-in checker only for custom bus or user-approved fallback
- [ ] ABVIP assumptions present in the CSR task after `task -edit CSR -copy_all`
- [ ] ABVIP protocol covers reachable (no over-constraint)
- [ ] Every ABVIP response assertion proven; failures reported as DUT protocol bugs
- [ ] AXI: `CONFIG_CSR_DISCARD_ON_ERROR(0)` unless spec defines errors on legal accesses
- [ ] Step 5b: `ast_no_err_legal`, `ast_err_required` (if spec), errored-write-no-effect (if spec) proven
- [ ] `cov_rd_ok_<REG>` covered for every register
- [ ] Spec error behaviour (Q20) recorded; gaps raised to the user

### Results / Debug
- [ ] `check_csr -list` output matches the spec for every register and field
- [ ] All assertions proven, all covers covered; failures analysed with `formal-cex-debug` (RCA per failure)
- [ ] No CSV change made to match RTL; RTL deviations reported as findings

### Traceability / Sign-off
- [ ] `req_extraction.csv`: one row per register and per field, every row cites a spec section
- [ ] `formal_traceability.csv`: every YES/CSR requirement MAPPED; assumptions listed as `ASSUME`
- [ ] `formal-traceability` run; `signoff_matrix.csv` generated per config
- [ ] vPlan choice (NOW / LATER / NOT NEEDED) recorded; if NOW, vplanx or `csr_vplan.csv` generated
- [ ] `param-spec-audit` run LAST; report generated; FAILs closed or reported
