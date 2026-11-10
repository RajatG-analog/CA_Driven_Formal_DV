# Step 4a — UNR TCL Templates (formal-unr)

- Used by SKILL.md Step 4a (flow A = xrun) and Step 4b (flow B = adsim, same input TCL via `UNR_FML_TCL_FILE`).
- Replace every `<...>`; delete optional blocks that are not used; keep every constraint comment (reason + spec section).
- Doc basis: D1 "Reading the Coverage Database", "Applying Stopats and Constraints", "UNR-Specific Commands", "Generating a Coverage Database", Appendix A/B; D2 `check_unr`, `database`, `clock`, `reset`, `stopat`, `assume`, `report` (see `doc_reference.md`).
- Signal paths: drop the TB top-module name (D1).
  - `-inst_top <tb_top>.<inst>` → signals are `<inst>.<sig>`.
  - `-inst_top <tb_top>.<l1>.<inst>` → signals are `<l1>.<inst>.<sig>`.
- The xrun P2P flow generates analyze / elaborate / `check_unr -init` itself; the input TCL starts at `check_unr -setup` (D1 default `-input` content).

## File 1 — `jg_unr.tcl` (input TCL: xrun `-input` / `UNR_FML_TCL_FILE`)

```tcl
#------------------------------------------------------------------------------
# <IP_NAME> — Jasper UNR input TCL (<CFG_NAME>)
# Jasper <jasper_version>, Xcelium <xcelium_version>
# inst_top : <tb_top>.<inst>
# covdb    : <covwork>/<covscope>/<covtest>
# Results valid ONLY under the constraints listed in this file.
#------------------------------------------------------------------------------
set UNR_RES <abs_results_dir>
file mkdir ${UNR_RES}

# [Optional] periodic export during prove (D1) — must precede check_unr -setup
# database -init_unicov -app unr -interval <30m>

#--- Clock (spec §<x.y>) -------------------------------------------------------
# Single spec clock:
clock <inst>.<clk>
# Both edges used by the RTL (spec §<x.y>):
# clock <inst>.<clk> -both_edges
# Several asynchronous clocks / unknown: UG default
# clock -none

#--- Reset / initial state (choose ONE, record the choice — Q12) ---------------
# R1 spec reset (UNR = unreachable from the reset state):
reset -expression {!<inst>.<rst_n>}
# R2 un-initialised flops (UG default, most conservative):
# exec touch [get_proj_dir]/dummy_reset
# reset -init_state [get_proj_dir]/dummy_reset
# R3 state loaded from a simulation waveform (UG recommended initialisation):
# reset -shm <abs_path>/<wave>.shm -time <t> -time_scale ns -exact

#--- Constraints (spec-derived ONLY; one reason per line — Q14) ----------------
# Stopats BEFORE check_unr -setup, with -env (D1):
# stopat -env <inst>.<internal_sig>                 ;# reason: <spec §x.y>
# Mode tie-offs from the spec (scan / test / DFT inactive in functional mode):
# assume -env -name asm_unr_<name> {<inst>.<scan_en> == 1'b0}   ;# spec §<x.y>: <quote>
# assume -env -name asm_unr_<name> {<inst>.<test_mode> == 1'b0} ;# spec §<x.y>: <quote>
# Static configuration pins fixed by the spec for this config:
# assume -env -name asm_unr_<name> {<inst>.<cfg_pin> == <val>}  ;# spec §<x.y>
# Coverage waivers: ADD WAIVERS HERE (refinement files of already-reviewed holes are
# passed with xrun -load_refinement / check_unr -init -load_refinement, not here)

#--- Targets -------------------------------------------------------------------
check_unr -setup
# discarded_items_report.txt is written to the session dir by -setup (D2)
# [Optional] restrict targets (D2 -enable_property / -disable_property):
# check_unr -disable_property {.*toggle_cov_.*} -regexp
check_unr -list -type enabled

#--- Prove ---------------------------------------------------------------------
# ProofGrid (Q16):
# set_proofgrid_mode shell
# set_proofgrid_shell {<bsub command>}
# set_proofgrid_per_engine_max_jobs <N>
set_prove_time_limit <24h>
# Chunking (Appendix B; defaults 6 chunks / 100000 properties per chunk):
# set_unr_prove_max_chunks <N>
# set_unr_prove_max_properties_per_chunk <N>
check_unr -prove
# Re-run options: -time_limit <t> -engine_mode {<engines>} -persistent_grid_jobs
#                 -save_ppd ${UNR_RES}/unr.ppd | -with_ppd ${UNR_RES}/unr.ppd
#                 -keep_trace (witness traces for reachable items)

#--- Results -------------------------------------------------------------------
check_unr -list -type unreachable
check_unr -list -type bounded
check_unr -list -type unprocessed
# Reasons for constant / assumption-caused UNRs (Appendix A): <root>.txt + <root>.cmd
check_unr -reason -file ${UNR_RES}/unr_reason
report -summary -task unr -file ${UNR_RES}/unr_summary.txt -force

#--- Export UNR coverage DB + IMC merge script ---------------------------------
database -export_unicov
# Merge script: <jgproject>/sessionLogs/session_<n>/unr_imc_coverage_merge.cmd
```

- `check_unr -list` output to a file: the return value format is not documented ("Multiple return values", D2) — capture from `jg.log`, or try `set fh [open ${UNR_RES}/unr_list.txt w]; puts $fh [check_unr -list -type unreachable]; close $fh` — UNCONFIRMED, verify in D2 / first run.
- Do NOT add `check_cov` (D3: Coverage App does not run with the UNR App).
- Do NOT add `check_unr -setup -coverage ...` (K1) or `database -init_unicov` without `-app unr` (K2).

## File 2 — `jg_unr_pre.tcl` (optional, xrun `-jg_pre_tcl`; runs BEFORE analyze/elaborate)

```tcl
# Only if needed — each line needs a reason in the run summary
# Functional coverage (D1; also requires -jg_coverage all or u):
# set_unr_functional_coverage true
# set_unr_functional_coverage_mode <all|covergroup|assertion>
# Embedded SVA assumes (D1; disabled by default) — or xrun -jg_unr_assumption:
# check_unr -init -enable_assumption
# Resilient compilation (default on, mode all) — change only with a reason:
# set_resilient_compilation <on|off>
# set_resilient_compilation_mode {<modes>}
# Clock-loop stopats (D2):
# set_unr_break_clock_loop <on|off>
```

- Whether the xrun-generated `check_unr -init` merges with a user `check_unr -init -enable_assumption` in the pre TCL: D1/D2 state this usage; prefer `-jg_unr_assumption` on Xcelium ≥ 21.09-s001 (D1).

## File 3 — `unr.bblist` (xrun `-jg_bbmodlist` / `UNR_FML_BBLIST`)

```
# one module name per line; each with a reason (simulation-only model, analog model, memory)
<module_name>
```

- Black-boxed module: its outputs become free inputs (over-approximation); its internal coverage items are not analysed (they stay holes).
- `-jg_bbinst` / `-jg_bbinstlist` take instance paths that INCLUDE the top-level module (D1).

## File 4 — `RUNCMD_xrun` (flow A)

```
xrun -64bit -jg -unr -R \
     -covdb <abs_covwork>/<covscope>/<covtest> \
     -inst_top <tb_top>.<inst> \
     -input <abs_unr_dir>/jg_unr.tcl \
     -covfile <abs_ccf_1> -covfile <abs_ccf_2> \
     -jg_coverage <b:e:t:f> \
     -jg_bbmodlist <abs_unr_dir>/unr.bblist \
     -covworkdir <abs_writable_covwork> -covtest unr_<cfg> -covoverwrite \
     -jg_project <abs_unr_dir>/<cfg>/jgproject \
     -log <abs_unr_dir>/<cfg>/xrun_unr.log
```

- Optional switches (D1/D2 App. K): `-gui`, `-jg_pre_tcl <abs>/jg_unr_pre.tcl`, `-jg_unr_assumption`, `-load_refinement <abs>/<reviewed>.vRefine`, `-jg_periodicexport <t>`, `-jg_unr_partition [-jg_unr_partition_args "-auto_partition_threshold <N> -max_partition_jobs <N>"]`, `-jg_elab_opts "<opts>"`, `-jg_analyze_opts "<opts>"`, `-s` (interactive, no exit).
- `-R` reuses the last snapshot (D1 Mandatory Options); without a reusable snapshot, compile with the SAME sources, defines, parameters and `-coverage`/`-covfile` as the simulation (D6 RUNME / `irun.f`) — the exact recompile command line is project specific.
- `-covoverwrite`: without it a second run into the same covtest fails fatally (D1).
- `-covworkdir` / `-covscope`: Xcelium ≥ 23.01-a071 / 23.03-s001 (D1).
- Merge / view (flow A): `imc -nostdout -init <abs_unr_dir>/<cfg>/jgproject/sessionLogs/session_0/unr_imc_coverage_merge.cmd` (D6 RUNME uses `imc -init`; `-nostdout` from D7).

## Alternative — standalone `jg -unr` (UNCONFIRMED)

- D2 documents `jg -unr` and `check_unr -init -covdb ... -inst_top ...` (must precede `elaborate`), and D1 uses `jg -unr` only for save/restore.
- A standalone analyze/elaborate flow is NOT described in D1 for reading the covdb — UNCONFIRMED — verify in D1 / Cadence support before use; default to the xrun flow.
