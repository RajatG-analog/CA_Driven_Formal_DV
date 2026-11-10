# Spec Inventory Template (`<out_dir>/spec_inventory.md`)

- Used by `formal-methodology-select` Step 1.
- Fill from the SPEC ONLY; every row carries a citation `§<section>` + `p.<page>` (PDF) or item ID (Jama).
- RTL names may appear only in the "Binding name (optional)" column, marked `binding-only`.
- A value the spec does not give is written `NOT STATED` and gets a `GAP-NNN` entry in `spec_gaps.md`.
- Keep every table even if empty; write `none in spec (checked §<list>)` instead of deleting it.

## Header

- IP: `<ip>`
- Spec: `<file / Jama ID>`, revision `<rev>`, date `<date>`
- Additional documents read: `<protocol standards, integration guide, SoC spec>` (or none)
- Sections read (all): `<§1 … §N, appendices>`; total pages `<N>`
- Text extraction: `.tmp/<ip>_spec_<ts>.txt` (pdftotext) + pdfMarkdown pages `<list>` for tables / diagrams

## 1. Features

| ID | Feature | Description (spec words) | Spec § / page | Parameter-dependent? |
|----|---------|--------------------------|---------------|----------------------|
| F-001 | `<name>` | `<text>` | §`<x.y>` p.`<n>` | yes (`<PARAM>`) / no |

## 2. Interfaces and Protocols

| ID | Interface | Protocol + revision | Role (DUT initiator / target) | Width / params | Clock / reset | Spec § |
|----|-----------|---------------------|-------------------------------|----------------|---------------|--------|
| I-001 | `<name>` | APB4 / AHB5-Lite / AXI4 / custom | target | `<widths>` | `<clk>` / `<rst>` | §`<x.y>` |

## 3. Clocks, Resets and Domains

| ID | Clock / reset | Type (clock / async reset / sync reset) | Polarity / edge | Frequency / ratio | Domain | Gating / sequencing | Spec § |
|----|---------------|------------------------------------------|-----------------|-------------------|--------|---------------------|--------|
| K-001 | `<name>` | clock | posedge | `<ratio to other clocks>` | D1 | `<gating rule>` | §`<x.y>` |

- Domain crossings stated by the spec: `<list with §>` (feeds overlay C8).

## 4. Memories and Storage

| ID | Memory / FIFO / buffer | Depth × width | Type (RAM / ROM / FIFO / CAM) | Protection (ECC / parity) | Init / reset content | Spec § |
|----|------------------------|---------------|-------------------------------|---------------------------|----------------------|--------|
| M-001 | `<name>` | `<D>` × `<W>` | RAM | SECDED | NOT STATED | §`<x.y>` |

## 5. FSMs and State Diagrams

| ID | FSM | States (spec names) | Transitions + conditions | Outputs per state | Spec figure / § |
|----|-----|---------------------|--------------------------|-------------------|-----------------|
| S-001 | `<name>` | `<IDLE, …>` | `<IDLE→RUN when start>` | `<busy=1 in RUN>` | Fig.`<n>` §`<x.y>` |

## 6. Registers

| ID | Register | Offset | Width | Fields (access, reset) | Protection / lock | HW update | Spec § |
|----|----------|--------|-------|------------------------|-------------------|-----------|--------|
| R-001 | `<REG>` | `0x00` | 32 | `<EN[0] RW 0>` | `<key>` | `<status set by HW>` | §`<x.y>` |

- Bus-error behaviour for register accesses: `<text>` §`<x.y>` (or NOT STATED).

## 7. Parameters and Configurations

| ID | Parameter / option | Legal range | Default | Features affected | Static during operation? | Spec § |
|----|--------------------|-------------|---------|-------------------|--------------------------|--------|
| P-001 | `<PARAM>` | `<1..32>` | `<8>` | F-00x | yes | §`<x.y>` |

## 8. Datapaths and Transformations

| ID | Datapath | Input → output | Transform (spec formula / standard) | Ordering / latency | Spec § |
|----|----------|----------------|-------------------------------------|--------------------|--------|
| D-001 | `<name>` | `<wdata>` → `<mem>` | `<ECC encode per §>` | in-order, `<N>` cycles | §`<x.y>` |

## 9. Latency and Timing Requirements

| ID | Requirement | Bound (cycles / clock) | Type (exact / max / min) | Spec § |
|----|-------------|------------------------|--------------------------|--------|
| T-001 | `<ack after req>` | `<≤ 4 hclk>` | max | §`<x.y>` |

- Statements with "eventually", "after", "within" but no number → `NOT STATED` + gap.

## 10. Error Handling and Safety

| ID | Error / safety item | Condition | Required response | Detection / diagnostic requirement | Spec § |
|----|---------------------|-----------|-------------------|------------------------------------|--------|
| E-001 | `<illegal access>` | `<cond>` | `<PSLVERR=1>` | — | §`<x.y>` |

## 11. Test / Scan / Debug Modes

| ID | Mode | Entry condition | Effect on functional behaviour | In formal scope? (spec-based reason) | Spec § |
|----|------|-----------------|--------------------------------|--------------------------------------|--------|
| X-001 | scan | `<scan_en=1>` | functional outputs undefined | no — DFT-only | §`<x.y>` |

## 12. Power, Low-Power and Security Items

| ID | Item | Requirement | Spec § |
|----|------|-------------|--------|
| W-001 | `<power domain / isolation / key>` | `<text>` | §`<x.y>` |

## 13. Assumptions of Use / Integration Rules

| ID | AoU / integration rule | Applies to | Spec § |
|----|------------------------|------------|--------|
| A-001 | `<inputs stable while busy>` | F-00x | §`<x.y>` |

## 14. Reading Log (completeness evidence)

| Spec section | Pages | Read (Y) | Inventory rows produced | Notes |
|--------------|-------|----------|-------------------------|-------|
| §1 Introduction | 1–3 | Y | F-001 | — |
