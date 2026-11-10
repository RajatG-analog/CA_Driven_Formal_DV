# Proof Accelerators (PAs) — Selection and Use (formal-fpv, Path 2 / Step 10-11)

- Sources (only these; docs win over this file):
  - PA datasheets: `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/proof_accelerators/<name>.pdf` (also Help – Proof Accelerator Datasheets)
  - CR = `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/jasper_command_reference.pdf` (2025.09): `elaborate -abstract_ram` p825, `connect` p754-755, `jasper_model_divider` p1108-1111, `jasper_model_mpram` p1112-1116, `jasper_model_multiplier` p1117, `jasper_model_ram` p1122, `jasper_scoreboard_3` p1127, `abstract` p152-157
- What a PA is (datasheets, Introduction / Description):
  - an encrypted macro (some with a supporting Tcl command) delivered with Jasper
  - Verification Component PAs = checkers (formal scoreboards, cache transparency) that add properties
  - Abstraction Component PAs = replace a hard structure (memory, FIFO, divider, multiplier, cache way) by a safe abstraction so proofs / deeper bounds become tractable (`jasper_model_fifo.pdf` p3; `jasper_model_ram.pdf` p3)
- SPEC-ONLY:
  - PA parameters (widths, depth, latency, ports, ordering, ratios) come from the spec / macro datasheet; RTL only for instance / port names
  - an abstraction is an environment decision → record the justification in `verification_plan.md` (SKILL.md Step 5) and keep a cover for each abstracted behaviour

## When to Choose (complexity gate)
- Trigger: undetermined / slow properties whose COI contains (Step 10-11; `resources/pitfalls.md`):
  - deep memories / RAM arrays / multiport RAMs → `jasper_model_ram`, `jasper_model_mpram`, `elaborate -abstract_ram`
  - large packet FIFOs / buffers on a scoreboarded datapath → `jasper_model_fifo` / `jasper_model_mem` (+ `jasper_scoreboard_2`)
  - dividers / multipliers → `jasper_model_divider`, `jasper_model_multiplier`
  - cache tag / data RAMs → `jasper_model_cache_way` (+ `jasper_cache`)
  - counters → `abstract -counter` (CR p153; Jasper abstraction command, not a PA)
  - multi-clock ratio variation → `jasper_model_frequency_jitter` (see `resources/clocking_multi_clock.md`)
- End-to-end data integrity (Path 2 / Path 3): `jasper_scoreboard_3` is the current scoreboard (datasheet September 2025); `jasper_scoreboard` is deprecated (`jasper_scoreboard.pdf` p1).
- Order: concrete model first; add an abstraction only when the complexity gate fires; record it.

## Available PAs (installed 2025.09 docs)

| PA | Category (per datasheet) | Models / checks | Clocks / resets | Use method | Datasheet |
|----|--------------------------|-----------------|-----------------|------------|-----------|
| `jasper_scoreboard_3` | verification component | in-order / out-of-order data integrity initiator → target; `data_integrity`, `no_overflow` | `clk` (`SINGLE_CLOCK=1`) or `incoming_clk` / `outgoing_clk` (`SINGLE_CLOCK=0`); `rstN` active-low async | `jasper_scoreboard_3 -init` first, then bind module | `jasper_scoreboard_3.pdf` p10-12 |
| `jasper_scoreboard_2` | Formal Scoreboard (verification component) | generic N initiators → M targets, in/out-of-order | `clk1`/`clk2`, `rst1N`/`rst2N` | wrapper requirements file; `task -link <embedded> -to <scoreboard_task>` | `jasper_scoreboard_2.pdf` p5 |
| `jasper_scoreboard_free` | Formal Scoreboard | like `_2` without restriction on data (data constrained / used as control) | `clk1`/`clk2`, `rst1N`/`rst2N` | requirements file; `analyze -sv`/`-sva`; `task -link` | `jasper_scoreboard_free.pdf` p5-6 |
| `jasper_scoreboard_priority` | Formal Scoreboard | per-priority ordering | `clk1`/`clk2`, `rst1N`/`rst2N` | requirements file | `jasper_scoreboard_priority.pdf` p5, p8 |
| `jasper_scoreboard` | Formal Scoreboard — deprecated | up to 8 → 8 integrity | `clk1`/`clk2`, `rst1N`/`rst2N` | requirements file | `jasper_scoreboard.pdf` p1, p5 |
| `jasper_datapath`, `jasper_datapath_1port`, `jasper_datapath_1port_2clk` | PA / PPM (2007) | packet / beat integrity; `_2clk` = different initiator / target clocks | `clk`/`rst` active-high; `_2clk`: `clk1`/`rst1`, `clk2`/`rst2` | requirements file | `jasper_datapath*.pdf` p2-3 |
| `jasper_datapath_fifo`, `jasper_datapath_mem` | PA / PPM (2007) | FIFO / memory model for `jasper_datapath` | `clk`, `rstN` | modeling file + `connect`, `stopat` + `assume`, `task -link` | `jasper_datapath_fifo.pdf`, `jasper_datapath_mem.pdf` p1-2 |
| `jasper_model_ram` | abstraction component | memory → up to 32 concrete locations | `clk` (also for async memory), `rstN`; `MEM_STYLE` 0 async / 1 sync | Tcl `jasper_model_ram -abstract` or SV `bind` + black-box | `jasper_model_ram.pdf` p3-7 |
| `jasper_model_mpram` | abstraction component | multiport RAM, up to `MAX_DEPTH` (32) concrete locations | `clk`, `rstN` | Tcl `jasper_model_mpram -abstract`, SV `bind`, or `elaborate -abstract_ram` | `jasper_model_mpram.pdf` p3-8 |
| `jasper_model_fifo` | abstraction component | packet FIFO for `jasper_scoreboard_2` only | `clk1`/`clk2`, `rst1N`/`rst2N`; model is asynchronous, no clock jitter modelled | modeling file + `stopat` / `assume` / `task -link` | `jasper_model_fifo.pdf` p3-7 |
| `jasper_model_fifo_priority` | abstraction component | FIFO preserving priority, with `jasper_scoreboard_priority` | `clk1`/`clk2`, `rst1N`/`rst2N` | modeling file | `jasper_model_fifo_priority.pdf` p4-5 |
| `jasper_model_mem` | abstraction component | packet memory for `jasper_scoreboard` / `_2` | `clk`, `rstN` | modeling file + `stopat` / `assume` / `task -link` | `jasper_model_mem.pdf` p5 |
| `jasper_model_mem_priority` | abstraction component | memory preserving priority, with `jasper_scoreboard_priority` | `clk`, `rstN` | modeling file | `jasper_model_mem_priority.pdf` p4-5 |
| `jasper_model_divider` | abstraction component | divider | `clk` (needed even if async), `rstN` | Tcl `jasper_model_divider -abstract` | `jasper_model_divider.pdf` p5-7; CR p1108 |
| `jasper_model_multiplier` | abstraction component | multiplier | `clk` (needed even if async), `rstN` | Tcl `jasper_model_multiplier -abstract` | `jasper_model_multiplier.pdf` p6-7; CR p1117 |
| `jasper_cache` | verification component | cache transparency to main memory | `clk`, `rstN` | requirements file | `jasper_cache.pdf` p6 |
| `jasper_model_cache_way` | abstraction component | cache way tag / data RAMs, with `jasper_cache` | `clk`, `rstN` | modeling file + `stopat` / `assume` / `task -link` | `jasper_model_cache_way.pdf` p4-5 |
| `jasper_model_frequency_jitter` | PA | fast / slow clock ratio varies in `RATIO_LOW..RATIO_HIGH` | `rstN`, `clk_fast` in, `clk_slow` out | wrapper drives DUV slow clock; `task -link` | `jasper_model_frequency_jitter.pdf` p3-5 |
| `jasper_power_sequencer` | PA | power-down / power-up FSM stimulus (LPV) | `clk`, `rst` active-high | requirements file | `jasper_power_sequencer.pdf` p5 |

- `jasper_scoreboard_free` is not compatible with `jasper_model_fifo`, `_fifo_priority`, `_mem`, `_mem_priority`, `_mpram`, `_ram` (`jasper_scoreboard_free.pdf` p3).
- `jasper_model_fifo` / `jasper_model_mem` are not standalone models; for standalone FIFO / memory abstraction the datasheets point to `jasper_model_ram` (`jasper_model_fifo.pdf` p3; `jasper_model_mem.pdf` p3).
- Path 2 in this skill uses `jasper_scoreboard_3` (`resources/path2_wrapper_scoreboard.md`); the scoreboard-coupled abstractions (`jasper_model_fifo`, `jasper_model_mem`, polarity port) are documented for `jasper_scoreboard` / `jasper_scoreboard_2` only — coupling to `jasper_scoreboard_3` is not stated in the docs.

## Memory Abstraction — `jasper_model_ram` (Tcl flow)
- Steps (`jasper_model_ram.pdf` p4-7; CR p1122):

```tcl
set_elaborate_single_run_mode off
elaborate -top <top_module>
# in the <embedded> task, after elaborate, BEFORE clock / reset (otherwise they are erased)
jasper_model_ram -abstract <mem_inst> -parameter ADDR_WIDTH <spec> -parameter DATA_WIDTH <spec> \
    -parameter MEM_STYLE <0|1> -parameter RESET_STYLE <0|1|2> \
    -connect clk <clk> -connect rstN <rstN> -connect write <we> -connect addr_wr <waddr> \
    -connect data_wr <wdata> -connect read <re> -connect addr_rd <raddr> -connect data_rd <rdata>
jasper_model_ram -init <mem_inst>
clock <clk>
reset -expression {~<rst_n>}
prove -all
# spurious CEX / cover trace using abstract values:
jasper_model_ram -suggest
jasper_model_ram -justify <mem_inst>
```

- `-abstract` replaces the instance and all like instances; inserted instance `jasper_ram_i`; single instance only → SV `bind` + black-box that instance, or elaborate it with a unique parameter (p4).
- `-auto` connects same-name ports; different widths are not auto-connected; take care with `clk` (p5).
- `-justify` needs `-init`; max 32 concrete values, so no benefit beyond 32 `-justify` (p5).
- `-suggest` returns instances whose abstract values appear in the current trace; justifying them avoids spurious CEX / cover traces (p5).
- PA management is per task: run the proof in the task where the PA was initialized (p6).
- Restrict concrete tracking to a symbolic address (`jasper_model_ram.pdf` p7-10):

```tcl
stopat <mem_inst>.jasper_ram_i.enable
assume {<mem_inst>.jasper_ram_i.enable == (<addr> == <sym_addr>)}
```

- `jasper_model_mpram`: same flow (`-abstract` / `-init [-preload <addr> [<data>]]` / `-justify` / `-suggest` / `-clear`); `READ_PORTS`, `WRITE_PORTS`, `MAX_DEPTH`; `-abstract` ties `read_allocate` / `write_allocate` to 1s, direct instantiation must connect them; `clear -all` does not clear PA data → `jasper_model_mpram -clear` (`jasper_model_mpram.pdf` p3-8; CR p1112-1116).

## `elaborate -abstract_ram`
- Replaces automatically extracted dual-port and multiport RAMs in the DUV with `jasper_model_mpram` PA instances; `-mpram_init_value (0 | 1)` sets their initial value (CR p825).
- Use it when the spec memory is an RTL array (not a vendor macro) and all extracted RAMs may be abstracted; otherwise use `jasper_model_ram` / `jasper_model_mpram -abstract <inst>` on the chosen instance.
- Follow-up `-init` / `-justify` / `-suggest` via `jasper_model_mpram` (CR p1112).

## Arithmetic Abstraction — `jasper_model_divider` / `jasper_model_multiplier`

```tcl
jasper_model_divider -abstract <div_signal> -parameter <P> <V> -connect clk <clk> -auto
jasper_model_divider -init <div_signal>
jasper_model_divider -suggest
jasper_model_divider -justify <div_signal>
```

- Run `-abstract` / `-init` after elaboration and before clock / reset (CR p1110).
- Clock: module port `clk` with `-auto`, or `-connect clk <port>`, or `clock <clk> <path>.jasper_divider_i_<signal>.clk` (CR p1110).
- Concrete results for trivial operations and for the first N masked operand pairs; `-init` / `-justify` clear proof results (`jasper_model_divider.pdf` p5-7). Multiplier: same switches (`jasper_model_multiplier.pdf` p6-7).

## Scoreboard-Coupled Abstraction (`jasper_model_fifo` / `jasper_model_mem`, with `jasper_scoreboard_2`)
- Steps (`jasper_model_fifo.pdf` p5-6; `jasper_model_mem.pdf` p5):
  - instantiate the PA in the modeling / requirements file; connect `polarity` to the scoreboard polarity (wire, or assume if in different files)
  - replace the DUV FIFO output driver and link the auto-created task:

```tcl
assume -name force_polarity {<fifo_pa>.polarity == <scoreboard>.polarity}
stopat <duv_fifo_out>
assume -name drive_fifo_out_data {<duv_fifo_out_bits> == <req_path>.<fifo_pa_dataout_bits>}
task -link <req_path.fifo_PA_inst_MODEL_FIFO> -to <req_path.sb_PACKET_INTEGRITY>
```

- Put all activating assumptions into the PA's auto-created task, so the abstraction is switched by adding / removing the link (`jasper_model_fifo.pdf` p6).
- Built-in checks `sanity_reset_activated`, `sanity_reset_toggle_once`, `sanity_polarity`, `fifo_underflow`, `fifo_overflow`: a CEX / inconclusive result means the main results are probably vacuous (`jasper_model_fifo.pdf` p3-4).

## Binding a PA (generic)
- Requirements / modeling file: `analyze -sv -req <file>` (or `analyze -verilog -req`), then `connect <model> <inst> -auto` (`jasper_datapath_fifo.pdf` p1-2).
- `connect -bind <pa_module> <inst> -connect <formal> <actual> -parameter <P> <V> -elaborate` (CR p755 example with `jasper_scoreboard_2`).
- SV `bind <parent_of_mem> jasper_model_ram #(...) <inst> (...)` + black-box the replaced memory (`jasper_model_ram.pdf` p3).
- PAs cannot be the top-level module (CR, `elaborate -top`).
- Linking: link non-PA tasks to the PA task, not the reverse: `task -link my_task -to <pa_task>` (CR p1109).

## Limitations and Cautions
- Automatically extracted PA tasks can contain implicit assumptions that are not visible; constraining tasks with them makes their impact impossible to evaluate (CR p1109; `jasper_model_fifo.pdf` p6).
- Abstraction can produce spurious CEX / cover traces → `-suggest` + `-justify` before triage as RTL_BUG (`jasper_model_ram.pdf` p5).
- `jasper_model_fifo` does not model clock phase jitter between its two domains; a separate verification of the replaced FIFO's data integrity is required (`jasper_model_fifo.pdf` p5).
- Replacing DUV full / empty drivers with the PA ones is not guaranteed safe (may hide full / empty bugs) (`jasper_model_fifo.pdf` p5).
- `jasper_scoreboard_3`: no overflow in the PA does not mean no overflow in the DUV; `FREE_DATA=1` only if data is not control and unconstrained; `MAX_PENDING` = max chunks the DUV can hold (spec) (`jasper_scoreboard_3.pdf`).
- Abstracted logic is no longer verified: list every abstracted instance as a coverage limitation in `verification_plan.md`; the abstracted block needs its own verification (spec / separate run).

## Checklist
- [ ] Abstraction chosen only after the complexity gate; reason recorded
- [ ] PA parameters from the spec / datasheet; instance names from RTL (binding-only)
- [ ] Tcl PA commands after `elaborate`, before `clock` / `reset`; `set_elaborate_single_run_mode off` for `jasper_model_ram` / `_mpram`
- [ ] PA sanity checks pass; `-suggest` / `-justify` applied before CEX triage
- [ ] Abstracted instances listed as limitations; separate verification planned
