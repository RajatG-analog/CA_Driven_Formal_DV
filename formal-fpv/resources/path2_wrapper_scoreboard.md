# Path 2 — FPV Wrapper + ABVIP + Models + jasper_scoreboard_3 + SVA (formal-fpv)

- Used by SKILL.md Step 2 when Step 0 selects Path 2 (memory controllers, bus bridges, DMA, protocol converters, FIFOs, ECC datapaths).
- Source: `formal-fpv-complete.md` Part B.3 and Part B.5 Approach B; Jasper syntax from the installed docs only.
- Concrete (example-only) instance: `resources/sram_ecc_worked_example.md`.
- Spec-only: transforms, latencies, error responses, memory map and bounds come from the spec; RTL gives port names only.

## Architecture
- `wrapper/<ip>_fpv_wrapper.sv` (formal top, `elaborate -top <ip>_fpv_wrapper`) instantiates:
  - the DUT (`<top_module>`) with the parameters of the `<cfg_dir>`
  - one ABVIP instance per bus interface (protocol assumptions on DUT inputs, protocol assertions on DUT outputs)
  - behavioral memory model(s) for memory macros (from the macro datasheet / spec timing)
  - reference model(s) for spec transforms (ECC encode / decode, width conversion, address translation)
  - one `jasper_scoreboard_3` per in-order data path that the spec defines
  - SVA for what the scoreboard does not cover (address, response, error, spurious-transfer checks)
- Wrapper bus inputs are wrapper primary inputs: the ABVIP wrapper ports are all inputs (passive); ABVIP constrains the free inputs with assumptions.
- Control features of the same IP (status, interrupts) use Path 1 bind props (`resources/path1_bind_sva.md`).

## ABVIP Selection (DUT role per interface, Q15)

| DUT interface role | Protocol | ABVIP module | Key settings |
|--------------------|----------|--------------|--------------|
| AHB5-Lite slave (DUT is subordinate) | AHB5-Lite | `cdn_abvip_ahb5_lite_wrapper` (`ahb5/rtl/`) | `VERIFY_BLK = 2` (slave: assertions on slave outputs, assumptions on master/arbiter inputs); `VERIFY_SLAVE_NUMBER = 0`; `ACTIVE_SLAVES = 32'h1`; `SLAVE0_ADDRESS_START/END` from the spec memory map |
| AHB5-Lite master (DUT is manager) | AHB5-Lite | `cdn_abvip_ahb5_lite_wrapper` | `VERIFY_BLK = 0` (master: assertions on master outputs, assumptions on inputs from arbiter and slave) |
| AHB5-Lite monitor | AHB5-Lite | `cdn_abvip_ahb5_lite_wrapper` | `VERIFY_BLK = 3` (assertions for master and slave) |
| APB4 slave (DUT is completer) | APB4 | `cdn_abvip_apb4_master` (example `apb4/examples/master_slave_b2b_bind/abvip_apb4_master_bind.sv`) | leave `PSEL_N` at its default of 1 (single slave); `MAX_WAIT_CYCLES_ON` / `MAX_WAIT_CYCLES` from the spec |

- Width parameters from the spec: `ABUS_WIDTH` (wrapper default 64), `DBUS_WIDTH` (default 32, must be a power of 2).
- `MAX_WAIT_CYCLES_READY` (AHB, default 16) = maximum wait states: take from the spec; no spec value → spec gap.
- `SLAVE_RESP_TYPES`, `CONTINUE_AFTER_ERROR_ON`, `BURST_TYPES`, `LOCKED_ACCESS_ON`, `CONFIG_EXCLUSIVE_ACCESS`, `CONFIG_SECURE_TRANSFER`, `CONFIG_USER_SIGNALS`: set from the spec feature list; disabling a check needs a spec statement (feature not supported).
- `RST_CHECKS_ON = 1` (APB4) requires `reset -formal -bound 1 <reset_expression>` (comment in the APB4 bind example).
- Unused ABVIP ports (parity `*chk`, user signals) tied per the ABVIP example tie-offs, only when the spec says the feature is absent.
- `abvip -set_location <abvip_dir>` before `analyze` (Flow A in TCL; Flow B in `pre_analyze.tcl`).

## jasper_scoreboard_3 (proof accelerator)
- Source: `<doc>/proof_accelerators/jasper_scoreboard_3.pdf`; `jasper_scoreboard_3 -init` before `analyze` and after `clear -all` (exposes the PA macros, e.g. `` `JS3_IN_ORDER ``).
- Built-in assertions: `data_integrity` (always; incoming vs outgoing data) and `no_overflow` (when `DYNAMIC = 1` or `FREE_DATA = 0` or in-order; pending chunks ≤ `MAX_PENDING`).
- A failing `no_overflow` indicates scoreboard misconfiguration (scoreboard PDF flow step 5).
- Basic parameters: `CHUNK_WIDTH`, `IN_CHUNKS`, `OUT_CHUNKS`, `SINGLE_CLOCK`, `ORDERING` (`` `JS3_IN_ORDER `` / `` `JS3_OUT_OF_ORDER ``), `MAX_PENDING` (must equal the maximum number of chunks the DUV can hold — from the spec, e.g. buffer depth).
- Optional: `LATENCY_CHECK` + `LATENCY` (use the spec latency bound), `FREE_DATA` (only if incoming data is not used as control AND not constrained — otherwise results can be incorrect), `LITE_CHECKS`, `DYNAMIC`.
- Ports: `clk` (or `incoming_clk` / `outgoing_clk` when `SINGLE_CLOCK = 0`), `rstN` (active-low asynchronous), `incoming_vld`, `incoming_data`, `outgoing_vld`, `outgoing_data`; optional `halt_latency`, outputs `incoming_selected` / `outgoing_selected`.
- `incoming_vld` / `outgoing_vld` = spec-valid transfer conditions (e.g. accepted write data phase, accepted read data phase without error response).
- Still needed as SVA (the scoreboard checks data only): address / index correctness, no spurious output transfer, response / error correctness, byte-lane behaviour, memory semantics (read returns the last write).

```systemverilog
jasper_scoreboard_3 #(
  .CHUNK_WIDTH  (<DATA_W>),
  .IN_CHUNKS    (1),
  .OUT_CHUNKS   (1),
  .SINGLE_CLOCK (1),
  .ORDERING     (`JS3_IN_ORDER),
  .MAX_PENDING  (<SPEC_MAX_OUTSTANDING>)
) u_sb_<path> (
  .clk           (<clk>),
  .rstN          (<rst_n>),
  .incoming_vld  (<spec_valid_in>),
  .incoming_data (<data_in>),
  .outgoing_vld  (<spec_valid_out>),
  .outgoing_data (<data_out>)
);
```

## Memory Semantics (Read Returns Last Write)
- In-order scoreboards fit pass-through paths (bus write data → memory write port; reference-model read data → bus read data).
- For storage semantics use a symbolic address in the wrapper:
  - `sym_addr` is an undriven wrapper input with `asm_SYM01: assume property ($stable(sym_addr));`
  - track the last spec-valid write to `sym_addr` (data + byte enables); assert that a spec-valid read of `sym_addr` returns it (after the spec read latency)
  - add `cov_SYM01` (write then read of `sym_addr`) and covers for first / last address and partial writes when the spec defines them

## Behavioral Memory Model
- Options (choose one, record in `verification_plan.md`):
  - compile a behavioral model with the macro's module name and port list (macro datasheet: latency, write-enable / byte-mask polarity, chip-enable) instead of the vendor view
  - `elaborate -abstract_ram` (replaces automatically extracted dual-port / multiport RAMs with `jasper_model_mpram` PA instances; command reference p825) or `jasper_model_ram -abstract <inst>` — see `resources/proof_accelerators.md`
  - `elaborate -bbox_m <macro>` and drive the black-box outputs in the wrapper from the model (outputs of a black box are free — unconstrained outputs produce false CEX)
- Model behaviour comes from the macro datasheet / spec; no behaviour copied from the RTL using it.

## Reference Model
- Implements the spec algorithm (e.g. ECC code from the spec H-matrix, address mapping, data packing) as standalone SV.
- Has its own sanity asserts / covers (e.g. encode → decode round trip with 0 errors returns the data).
- Never instantiate or copy DUT submodules as the reference.

## Error Injection (only if the spec defines error handling)
- Free mask inputs (`err_mask`) XOR-ed onto model read data; constrain the number of flipped bits to the spec classes (e.g. correctable / detectable).
- Cover each injected class and each spec response (corrected data, error flag, interrupt, bus error).

## Wrapper Template

```systemverilog
//------------------------------------------------------------------------------
// File        : <ip>_fpv_wrapper.sv
// Spec        : <spec> rev <rev>; memory map <sec>; interface <sec>
// Binding-only: DUT port names from <top_module> port list
//------------------------------------------------------------------------------
module <ip>_fpv_wrapper #(
  parameter int <PARAM> = <SPEC_DEFAULT>
) (
  input  logic                  <clk>,
  input  logic                  <rst_n>,
  // free bus inputs (constrained by ABVIP assumptions)
  input  logic [<AW>-1:0]       haddr,
  input  logic [1:0]            htrans,
  input  logic                  hwrite,
  input  logic [2:0]            hsize,
  input  logic [2:0]            hburst,
  input  logic [6:0]            hprot,
  input  logic [<DW>-1:0]       hwdata,
  input  logic                  hsel,
  input  logic                  hready,
  input  logic [<AW>-1:0]       sym_addr
);
  logic [<DW>-1:0] hrdata;
  logic            hreadyout, hresp;
  <top_module> #(.<PARAM>(<PARAM>)) u_dut (
    .<clk_port>  (<clk>),
    .<rst_port>  (<rst_n>),
    // ... spec bus ports ...
    .<mem_ports> (/* memory model */)
  );
  cdn_abvip_ahb5_lite_wrapper #(
    .VERIFY_BLK            (2),
    .VERIFY_SLAVE_NUMBER   (0),
    .ABUS_WIDTH            (<AW>),
    .DBUS_WIDTH            (<DW>),
    .ACTIVE_SLAVES         (32'h1),
    .SLAVE0_ADDRESS_START  (<SPEC_BASE>),
    .SLAVE0_ADDRESS_END    (<SPEC_END>),
    .MAX_WAIT_CYCLES_READY (<SPEC_MAX_WAIT>)
  ) u_abvip (
    .hclk (<clk>), .hresetn (<rst_n>),
    .haddr (haddr), .htrans (htrans), .hwrite (hwrite), .hsize (hsize),
    .hburst (hburst), .hprot (hprot), .hwdata (hwdata), .hsel (hsel),
    .hrdata (hrdata), .hready (hreadyout), .hresp (hresp), .hready_global (hready)
    // remaining ports per the wrapper port list; tie absent features per the ABVIP examples
  );
  // memory model, reference model, scoreboards, SVA (sym_addr checks) follow
endmodule
```

- AHB port mapping (`hready` = slave HREADYOUT vs global HREADY) must follow the ABVIP wrapper port comments; check against the ABVIP example top before the first run.
- Single-subordinate integration: if the spec / integration guide connects HREADY = HREADYOUT, drive the DUT HREADY input from `hreadyout` instead of a free input; otherwise keep it free and let ABVIP constrain it. Record the choice with its spec citation.

## Path 2 Checklist
- [ ] ABVIP role per interface matches the DUT role; memory map from the spec
- [ ] Scoreboard `MAX_PENDING` = spec maximum outstanding; `no_overflow` proven
- [ ] Address / response / spurious-transfer / memory-semantics SVA present
- [ ] Memory model and reference model sourced from datasheet / spec, with sanity covers
- [ ] Error injection only for spec error classes, each covered
