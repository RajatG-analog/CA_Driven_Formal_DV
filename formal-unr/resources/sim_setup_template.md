# Step 4b — Adsim `sim.setup` UNR Template (formal-unr)

- Used by SKILL.md Step 4b (run flow B or C).
- The UNR block is ADDED to the EXISTING simulation `sim.setup` of the block (the UNR compile must reuse the sim sources, defines, parameters and coverage config); a separate UNR-only sim.setup is allowed only if it sources the same compile settings (`SOURCE_SIM_SETUP`).
- `UNR_` prefix = active only for `adsim -unr` (D9); variables `FML_COVERAGE`, `FML_COVDB`, `FML_INSTTOP`, `FML_TCL_FILE`, `FML_BBLIST` documented in D8 (`{X}_` prefix allowed).
- Replace every `<...>`; use `$ADIP_BLOCKS_ROOT` (or the project root variable already used in the file), never absolute workarea paths.
- **OPEN TODO (UNCONFIRMED — verify in the adsim-generated xrun command line / D8):** mapping of adsim variables to xrun switches. Expected (from the kit + D1), not documented in D8:

| adsim variable | Expected xrun switch (D1) | Status |
|----------------|---------------------------|--------|
| `UNR_FML_COVDB` | `-covdb` | UNCONFIRMED — verify in run log |
| `UNR_FML_INSTTOP` | `-inst_top` | UNCONFIRMED — verify in run log |
| `UNR_FML_TCL_FILE` | `-input` | UNCONFIRMED — verify in run log |
| `UNR_FML_COVERAGE` | `-jg_coverage` | UNCONFIRMED — verify; D8 text says only `b:e:t` (old IEV) |
| `UNR_FML_BBLIST` | `-jg_bbmodlist` | UNCONFIRMED — verify (D8: module names, one per line) |
| `UNR_EXTRA_COMPILE_OPTIONS` | compile options (kit: `-covfile`) | kit usage; D8 generic `EXTRA_COMPILE_OPTIONS` |
| `-jg_pre_tcl`, `-jg_unr_assumption`, `-covworkdir`, `-covtest`, `-covoverwrite`, `-load_refinement` | — | no adsim variable found; UNCONFIRMED — candidate `UNR_EXTRA_RUN_OPTIONS` / `UNR_EXTRA_COMPILE_OPTIONS`, verify in D8 / adsim help |

- After the first run: open the adsim run directory log / generated simulator script, copy the actual xrun command into the run summary, and close the TODO rows above.

```
#------------------------------------------------------------------------------
# UNR (coverage unreachability) settings for <IP_NAME> (<CFG_NAME>)
# Active only with: adsim -block <ip_block> -unr ...
# Jasper <jasper_version> / Xcelium <xcelium_version>
# Results valid ONLY under the constraints in UNR_FML_TCL_FILE.
#------------------------------------------------------------------------------
#Coverage types (b block, e expression, t toggle, f fsm; per Q6)
UNR_FML_COVERAGE          : <b:e:t>

#Merged simulation coverage test dir: <covwork>/<covscope>/<covtest>
UNR_FML_COVDB             : <abs_or_$GPMS_NOBACKUP_path>/coverage/cov_work/scope/<merged_test>

#Formal top = DUT instance in the simulation TB (Q8)
UNR_FML_INSTTOP           : <tb_top>.<inst>

#Input TCL (resources/unr_tcl_template.md File 1)
UNR_FML_TCL_FILE          : $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/unr/jg_unr.tcl

#Black-box list (module names; each with a reason in the file — Q13)
#UNR_FML_BBLIST           : $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/unr/unr.bblist

#SAME coverage config as the simulation — every sim -covfile, same order (K6)
UNR_EXTRA_COMPILE_OPTIONS : -covfile $ADIP_BLOCKS_ROOT/<ip>/<path>/<sim_ccf_1>
UNR_EXTRA_COMPILE_OPTIONS : -covfile $ADIP_BLOCKS_ROOT/<ip>/<path>/<sim_ccf_2>

#Optional pre-elaboration TCL (functional coverage / SVA assumes) — UNCONFIRMED switch path
#UNR_EXTRA_RUN_OPTIONS    : -jg_pre_tcl $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/unr/jg_unr_pre.tcl

#Coverage waivers: ADD WAIVERS HERE (reviewed UNR refinement for later sim merges)
#COVERAGE_REFINE_FILE     : $ADIP_BLOCKS_ROOT/<ip>/dv/coverage/<ip>_unr.vRefine

#Sim pass string only for NON-UNR runs ("!" = negated prefix, kit pattern)
#!UNR_SIM_COMPLETE_FLAG   : <sim pass string>

#Optional: override the covdb from the command line (D8 CUSTOM_SWITCH; adsim skill pattern)
#CUSTOM_SWITCH            : covPath
#covPath_UNR_FML_COVDB    : CUSTOM_OPTION
```

- `COVERAGE_REFINE_FILE` (D8): global only, Xcelium only, accepts IMC `.vrefine` files; multiple lines allowed.
- Do NOT add `-jgcov` / `check_cov` (D3: Coverage App does not run with UNR).
- Custom-switch prefix stacking `covPath_UNR_FML_COVDB` — UNCONFIRMED (adsim skill shows `covPath_FML_COVDB`); verify in D8 `CUSTOM_SWITCH`.

## RUNCMD (write to `<cfg_dir>/RUNCMD`)

```
# 1. Simulation coverage (if no DB yet — Q4); merged DB path → UNR_FML_COVDB
adsim -block <ip_block> -regr <test.list> -cov -cov_merge -clean -batch -no_vmgr -rp S
# 2. UNR analysis (GUI or batch per Q17)
adsim -block <ip_block> -unr -clean [-gui] [-resdir <abs_cfg_dir>/Result_] [-force_setup <abs_cfg_dir>/sim.setup]
# 3. Review / merge in IMC (Step 7)
imc -nostdout -init <results>/formal_runs/unr/jgproject/sessionLogs/session_0/unr_imc_coverage_merge.cmd
```

- Step 1 command and the `formal_runs/unr/jgproject` location are taken from the kit README (adsim 6.06) — UNCONFIRMED for the installed adsim; locate the actual `jgproject` with `find <results> -name unr_imc_coverage_merge.cmd`.
- `-64` (kit README) is UNCONFIRMED (K13); use `ENABLE_64 : TRUE` in sim.setup if 64-bit is required.
- `-resdir` / `-force_setup` usage follows the sibling formal skills; confirm they apply to `-unr`.
