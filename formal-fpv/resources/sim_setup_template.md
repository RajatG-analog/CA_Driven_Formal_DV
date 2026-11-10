# Step 9b — Adsim `sim.setup` Template (formal-fpv)

- Used by SKILL.md Step 9b (run flow B or C). Launched by `<cfg_dir>/RUNCMD`.
- Header / results-area format: same as the `formal-connectivity` reference (`/proj/adip_digital/rgulghan/adip/adip_digital/adip_pinmux/dv/formal/formal_pinmux/1_io/peri_8/sim.setup`).
- Variables and hooks: `adsim` skill `resources/formal.md` (`FML_TCL_COMMANDS`, `FML_INSTTOP`, `FORMAL_ALWAYS_ONE_STEP_FLOW`, `pre_analyze.tcl`, `pre_exit.tcl`, `PRE_SIM_COMMANDS` copy pattern, prefix-scoped `<switch>_FML_TCL_COMMANDS`).
- Replace every `<...>`; one file per `<cfg_dir>`.

## sim.setup Rules
- adsim issues its own `prove -all` after `FML_TCL_COMMANDS`: no `prove` in `sim.setup`.
- No `check_cov -init`: adsim `-jgcov` issues `cov_init` (ECOV081 if both).
- `abvip -set_location` and `jasper_scoreboard_3 -init` must precede `analyze` → `pre_analyze.tcl`.
- Reports that need proof results (summary, CSV, coverage export) → `pre_exit.tcl`.
- `neg_sanity` expected-CEX properties run only with the custom switch `-neg_sanity` (a CEX marks a regression run FAIL).

```
#------------------------------------------------------------------------------
# Title            : <IP_NAME> Formal Property Verification Setup (<CFG_NAME>)
# Project          : ADIP DIGITAL
#------------------------------------------------------------------------------
# File             : sim.setup
# Author           : <USER>
# Created          : <DD.MM.YYYY>
# Last modified    : <DD.MM.YYYY>
#------------------------------------------------------------------------------
# Description :
# Adsim setup for JasperGold FPV of <IP_NAME> in configuration <CFG_NAME>.
# Path <1|2|3> (formal-fpv Step 0). Properties derived from <spec> rev <rev>.
#------------------------------------------------------------------------------
# Copyright (c) <YYYY> by Analog Devices. This model is the confidential and
# proprietary property of Analog Devices and the possession or use of this
# file requires a written license from Analog Devices.
#------------------------------------------------------------------------------
# Modification history :
#  <DD/Month/YYYY> : Initial Version
#------------------------------------------------------------------------------
# Configuration Parameters:
#  - <PARAM1> : <VAL1>
#
# Formal Settings:
#  - Top module     : <TOP>
#  - Clocks         : <clk> (spec <sec>)
#  - Resets         : <rst_n> active-low (spec <sec>)
#  - Proof time     : <t> limit
#  - Coverage time  : <t> limit
#------------------------------------------------------------------------------
#Sim Top and Results area
RESULTS_HOME : $GPMS_NOBACKUP
WEBRPT_DIR : ${GPMS_NOBACKUP}/../public_html/$USER/
WEBRPT_ADDR : https://www.engawsap1.analog.com/${GPMS_NOBACKUP}/../$USER/

#Testbench architectures defines
SHARED_COMPILE : 1
PATTERN_EXT : .v+.sv

#Compile: RTL (compile only), then environment and properties
EXTRA_COMPILE_OPTIONS : -f <formal_dir_abs>/rtl_list/filelist.f
EXTRA_COMPILE_OPTIONS : <formal_dir_abs>/props/<ip>_assumptions.sv
EXTRA_COMPILE_OPTIONS : <formal_dir_abs>/props/<ip>_<feature>_props.sv
EXTRA_COMPILE_OPTIONS : <formal_dir_abs>/props/<ip>_props_bind.sv
#Path 2 / 3 only
EXTRA_COMPILE_OPTIONS : <formal_dir_abs>/models/<ip>_<model>_model.sv
EXTRA_COMPILE_OPTIONS : <formal_dir_abs>/wrapper/<ip>_fpv_wrapper.sv

#Formal Command Variables
#Do NOT add "check_cov -init": adsim -jgcov already issues cov_init (ECOV081).
FML_TCL_COMMANDS : elaborate -top <TOP> -disable_auto_bbox -create_related_covers {witness precondition} -parameter <PARAM1> <VAL1>
FML_TCL_COMMANDS : get_design_info
FML_TCL_COMMANDS : clock <clk>
FML_TCL_COMMANDS : reset -expression {~<rst_n>}
FML_TCL_COMMANDS : check_assumptions -conflict
FML_TCL_COMMANDS : check_assumptions -dead_end

#Expected-CEX sanity task (only with -neg_sanity)
CUSTOM_SWITCH : neg_sanity
ADSIM_HELP    : -neg_sanity : Create the neg_sanity task (every neg_* must give a CEX)
neg_sanity_FML_TCL_COMMANDS : task -create neg_sanity -copy_assumes -source_task <embedded>
neg_sanity_FML_TCL_COMMANDS : assert -name neg_sanity::neg_<CAT><NN> {<deliberately wrong expectation>}
neg_sanity_FML_TCL_COMMANDS : task -set <embedded>

#ProofGrid settings (enable per Q13)
#FML_TCL_COMMANDS : set_proofgrid_mode shell
#FML_TCL_COMMANDS : set_proofgrid_shell {<bsub command>}
#FML_TCL_COMMANDS : set_proofgrid_max_jobs <N>
#FML_TCL_COMMANDS : set_proofgrid_per_engine_max_jobs <M>
FML_TCL_COMMANDS : set_prove_time_limit <t>
FML_TCL_COMMANDS : set_prove_per_property_time_limit <t>

#Coverage waivers
# ADD WAIVERS HERE

#Stage hooks into the run dir (formal_runs/ exists only after compile)
PRE_SIM_COMMANDS : if (-d $test_results_dir/formal_runs/formal) cp <formal_dir_abs>/<cfg_dir>/pre_analyze.tcl $test_results_dir/formal_runs/formal/pre_analyze.tcl
PRE_SIM_COMMANDS : if (-d $test_results_dir/formal_runs/formal) cp <formal_dir_abs>/<cfg_dir>/pre_exit.tcl $test_results_dir/formal_runs/formal/pre_exit.tcl

#vManager Settings (if user requests, Q19)
#ENABLE_VMGR : 1
#VMGR_PROJECT : $VMGR_PROJECT
#vPlan: enable ONLY when the vplanx exists (user chose NOW)
#ENABLE_VPLAN : 1
#VPLAN_SOURCE : <formal_dir_abs>/<IP>_Formal_VPlan_FPV.vplanx

FML_INSTTOP : <TOP>
FORMAL_ALWAYS_ONE_STEP_FLOW : 1
```

## pre_analyze.tcl

```tcl
# pre_analyze.tcl — runs before analyze (adsim hook)
abvip -set_location <abvip_dir>
# Path 2 / 3 only (scoreboard PA macros)
jasper_scoreboard_3 -init
```

## pre_exit.tcl

```tcl
# pre_exit.tcl — runs before JG exits (proof results available)
set RES <formal_dir_abs>/results
set WEB $env(GPMS_NOBACKUP)/../public_html/$env(USER)/jasper_reports
report -summary -results -task <embedded> -file ${RES}/<cfg_dir>_summary.txt -force
report -csv -task <embedded> -file ${RES}/<cfg_dir>_results.csv -force
check_cov -measure -type {stimuli coi proof bound} -task <embedded> -time_limit <t>
check_cov -report -type checker -report_file ${WEB}/<ip>_<cfg>_cov_checker.html -force -html
check_cov -report -type stimuli -report_file ${WEB}/<ip>_<cfg>_cov_stimuli.html -force -html
# ADD WAIVERS HERE
```

## Checks After the First Run (open items, verify in the JG log)
- `abvip -set_location` and `jasper_scoreboard_3 -init` appear before the first `analyze` and after any `clear -all` issued by adsim.
- `adsim` `formal.md` describes `FML_TCL_COMMANDS` as "passed to JG after elaborate", while the pinmux reference issues `elaborate` inside `FML_TCL_COMMANDS`: confirm the final `elaborate` uses the intended `-top` and `-parameter` values.
- `pre_exit.tcl` reads `$env(GPMS_NOBACKUP)` / `$env(USER)`; if either is unset in the JG process, use absolute paths (Q18).
- Whether `-jgcov` already runs `check_cov -measure` in the adsim flow is not verified; if it does, drop the `check_cov -measure` line from `pre_exit.tcl`.
