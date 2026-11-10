# Formal X-Propagation Skill — Unknown State Output Checks

## When to Use
Activate when the user asks to:
- Create X-propagation checks for an IP
- Verify no X/Z on primary outputs after reset
- Write `$isunknown` assertion checks
- Debug X-propagation failures (X on outputs)

## Inputs Required

| Input | Description | Example |
|-------|-------------|---------|
| **RTL top module** | DUT top for formal | `sram_top_scan_wrapper` |
| **Output port list** | All output ports of the DUT | From RTL module header |
| **Clock/Reset** | Clock and reset signal names | `HCLK`, `HRESETn` |
| **Output dir** | Where to write xprop file | `fpv_env/props/` |

## Overview

- X-propagation (xprop) properties verify that NO primary output of the DUT contains X or Z values after reset de-asserts.
- This catches:
- Uninitialized registers driving outputs
- Unconnected wires
- Multi-driver conflicts
- Incomplete case/if-else (inferred latches with X)
- Black-boxed modules leaking X through outputs

- This implements **Rule 10** from Part V of the golden prompt.

## Step-by-Step Procedure

### Step 1: Extract ALL Output Ports
- Read the RTL top module and list every `output` port:
```
grep -n "output" <top_module>.sv
```

Categorize outputs:
- **AHB outputs**: `hrdata`, `hreadyout`, `hresp`, `hexokay`
- **APB outputs**: `prdata`, `pready`, `pslverr`
- **Interrupt outputs**: `sram_ecc_interrupt`, `mpc_irq`
- **Memory outputs**: `mem0_clk`, `mem0_a`, `mem0_me_n`, `mem0_we_n`, `mem0_wem`, `mem0_d`
- **Handshake outputs**: `sram_clr_ack`
- **Scan outputs**: `scan_out` (skip — DFT only)

### Step 2: Create X-Prop Property File

Create `props/<ip>_xprop_props.sv`:

```systemverilog
module <ip>_xprop_props (
  input logic        CLK,
  input logic        RSTn,
  // ALL output ports
  input logic [31:0] hrdata,
  input logic        hreadyout,
  input logic        hresp,
  input logic        hexokay,
  input logic [31:0] prdata,
  input logic        pready,
  input logic        pslverr,
  input logic        sram_ecc_interrupt
);
  default clocking fpv_clk @(posedge CLK); endclocking
  default disable iff (!RSTn);

  // AHB outputs
  ast_xprop_hrdata:    assert property (!$isunknown(hrdata));
  cov_xprop_hrdata:    cover property (!$isunknown(hrdata));

  ast_xprop_hreadyout: assert property (!$isunknown(hreadyout));
  cov_xprop_hreadyout: cover property (!$isunknown(hreadyout));

  ast_xprop_hresp:     assert property (!$isunknown(hresp));
  cov_xprop_hresp:     cover property (!$isunknown(hresp));

  ast_xprop_hexokay:   assert property (!$isunknown(hexokay));

  // APB outputs
  ast_xprop_prdata:    assert property (!$isunknown(prdata));
  cov_xprop_prdata:    cover property (!$isunknown(prdata));

  ast_xprop_pready:    assert property (!$isunknown(pready));
  cov_xprop_pready:    cover property (!$isunknown(pready));

  ast_xprop_pslverr:   assert property (!$isunknown(pslverr));
  cov_xprop_pslverr:   cover property (!$isunknown(pslverr));

  // Interrupt outputs
  ast_xprop_ecc_int:   assert property (!$isunknown(sram_ecc_interrupt));
  cov_xprop_ecc_int:   cover property (!$isunknown(sram_ecc_interrupt));
endmodule
```

### Step 3: Create Bind Statement

```systemverilog
bind <top_module> <ip>_xprop_props u_xprop_props (
  .CLK(HCLK),
  .RSTn(HRESETn),
  .hrdata(hrdata),
  .hreadyout(hreadyout),
  .hresp(hresp),
  .hexokay(hexokay),
  .prdata(prdata),
  .pready(pready),
  .pslverr(pslverr),
  .sram_ecc_interrupt(sram_ecc_interrupt)
);
```

- Put the bind in the SAME file, after `endmodule`.

### Step 4: Decide Which Outputs to Include

**ALWAYS include:**
- All bus interface outputs (AHB hrdata/hreadyout/hresp, APB prdata/pready/pslverr)
- All interrupt outputs
- All status/handshake outputs

**SKIP (with justification):**
- `scan_out` — only valid in scan mode (which is assumed off)
- Memory interface outputs that go to black-boxed macros — these are DUT-internal,
  not primary outputs visible to the system
- Outputs gated by `ifdef` blocks that are not enabled in this config

**CONDITIONALLY include (via generate):**
```systemverilog
generate if (SECEXT_ENABLED) begin : gen_mpc
  ast_xprop_mpc_irq: assert property (!$isunknown(mpc_irq));
end endgenerate
```

### Step 5: Handle Common X-Prop Failures

| Failure | Root Cause | Fix |
|---------|-----------|-----|
| X on `hrdata` at time 0 | Uninitialized read data reg | Add reset to read data register in RTL (RTL bug) |
| X on `prdata` | Uninitialized APB read mux | Verify all case branches covered in MMR |
| X from black-boxed module | bbox outputs are free variables | Add `-bbox_m` in TCL, or create behavioral model |
| X on `mem0_d` | ECC encoder output depends on X inputs | Expected if memory model is bbox — skip this output |
| X after valid operation | Incomplete if/else or case | RTL bug — missing default case |

**When X-prop fails due to black-boxed modules:**
1. Check if the output is truly a primary output (visible to system)
2. If yes — create a behavioral model for the bbox module
3. If no (internal wire to bbox) — skip this output with comment

## Property Pattern

- The canonical pattern is simple:
```systemverilog
ast_xprop_<signal>: assert property (!$isunknown(<signal>));
```

- `$isunknown(expr)` returns 1 if ANY bit in `expr` is X or Z
- This is a **safety property** — no temporal operators needed
- It checks EVERY cycle after reset (via `default disable iff (!rst_n)`)
- Companion covers are optional but recommended for completeness

## Output Files

```
fpv_env/props/
└── <ip>_xprop_props.sv     X-propagation checks + bind statement
```

- Single file.
- The bind statement goes at the bottom of the same file.

## Quality Checklist
- [ ] Every primary output port has an `!$isunknown` assertion
- [ ] Bind connects to correct signals at top module
- [ ] Scan-only outputs excluded (scan_out when scan_mode assumed off)
- [ ] Black-box-internal outputs excluded with comment
- [ ] Conditional outputs (ifdef) handled via generate
- [ ] Companion covers for bus interface outputs (hrdata, prdata, etc.)
- [ ] File integrates into existing FPV TCL (analyzed with other props)
