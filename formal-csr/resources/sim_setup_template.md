# Step 6b — Adsim `sim.setup` Template (formal-csr)

- Used by SKILL.md Step 6b (run flow B or C).
- Modelled on the formal-connectivity template (`/proj/adip_digital/rgulghan/workareas/wrk_rgulghan/Handoff/skills/formal-connectivity/resources/sim_setup_template.md`), adapted for the CSR app.
- Replace every `<...>`; one file per config dir.
- Apply the "sim.setup rules" and RUNCMD rules listed in SKILL.md Step 6b.
- Differences from connectivity:
  - Global clock and reset FROM THE SPEC (no `clock -none` / `reset -none`).
  - `check_csr -load`, `task -edit CSR -copy_all -source_task <embedded>`, `task -set CSR`, `check_csr -prove` instead of `check_conn`.
  - The CSR bind file is compiled with `EXTRA_COMPILE_OPTIONS`.
- **OPEN TODO:** how adsim launches JG with the CSR app (`jg -csr`) is not confirmed.
  - Candidate line below (`FML_CMDLINE_OPTIONS : -csr`, adsim skill `resources/formal.md`: "Extra options passed to the jg command line") — confirm with the `adsim` skill / user before use.
  - Do NOT invent an adsim switch.
- **OPEN TODO:** confirm whether adsim issues its own `prove -all` after `FML_TCL_COMMANDS` (formal-connectivity template note); if so, `check_csr -prove` may be redundant or run twice — check the JG log of the first run.

```
#------------------------------------------------------------------------------
# Title            : <IP_NAME> Formal CSR Verification Setup (<CFG_NAME>)
# Project          : ADIP DIGITAL
#------------------------------------------------------------------------------
# File             : sim.setup
# Author           : <USER>
# Created          : <DD.MM.YYYY>
# Last modified    : <DD.MM.YYYY>
#------------------------------------------------------------------------------
# Description :
# Adsim setup for JasperGold CSR App verification of <IP_NAME> in
# configuration <CFG_NAME>. The CSR map CSV is derived from the spec register
# table ONLY (<spec name> rev <r>, section <x.y>); no RTL / Yoda / IP-XACT source.
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
#  - <PARAM2> : <VAL2>
#
# RTL Files:
#  - <file>.sv : <one-line purpose from spec>
#
# Formal Settings:
#  - Top module     : <TOP>
#  - CSR checker    : <jasper_csr_checker | jasper_amba_apb_csr_checker | ABVIP> instance <CSR_INST>
#  - Clock          : <clk> (spec section <x.y>)
#  - Reset          : <rst_n> active-low (spec section <x.y>)
#  - Proof time     : <24h> limit
#------------------------------------------------------------------------------
#Sim Top and Results area
RESULTS_HOME : $GPMS_NOBACKUP
WEBRPT_DIR : ${GPMS_NOBACKUP}/../public_html/$USER/
WEBRPT_ADDR : https://www.engawsap1.analog.com/${GPMS_NOBACKUP}/../$USER/

#Testbench architectures defines
SHARED_COMPILE : 1
PATTERN_EXT : .v+.sv

#Extra compile options (one line per RTL file; compile only)
EXTRA_COMPILE_OPTIONS : $ADIP_BLOCKS_ROOT/<ip>/digital/rtl/<file>.sv
EXTRA_COMPILE_OPTIONS : +libext+.v+.sv
SIM_INCDIR : $ADIP_BLOCKS_ROOT/<ip>/digital/rtl/
#CSR checker bind (spec-derived map is loaded by check_csr below)
EXTRA_COMPILE_OPTIONS : $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/csr/<ip>_csr_bind.sv

#Launch JG with the CSR app — OPEN TODO: confirm with adsim skill / user before enabling
#FML_CMDLINE_OPTIONS : -csr

#[ABVIP checkers only] abvip -set_location goes in pre_analyze.tcl (adsim formal.md, ABVIP)
#PRE_SIM_COMMANDS : if (-d $test_results_dir/formal_runs/formal) cp $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<cfg_dir>/pre_analyze.tcl $test_results_dir/formal_runs/formal/pre_analyze.tcl

#Formal Command Variables
#Do NOT add "check_cov -init": adsim -jgcov already issues cov_init (ECOV081).
FML_TCL_COMMANDS : elaborate -top <TOP> -parameter <PARAM1> <VAL1> -parameter <PARAM2> <VAL2>
#Clock / reset from spec section <x.y>
FML_TCL_COMMANDS : clock <clk>
FML_TCL_COMMANDS : reset -expression {!<rst_n>}
#Spec operating conditions only (e.g. DFT inactive); never a protection key
#FML_TCL_COMMANDS : assume -name asm_<name> {<spec_operating_condition>}

#Spec-derived CSR map (partitioned checks for bring-up)
FML_TCL_COMMANDS : check_csr -load $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/csr/<ip>_csr_map.csv -instance <CSR_INST> -partitioned_checks
#Copy <embedded> assumptions into the CSR task
FML_TCL_COMMANDS : task -edit CSR -copy_all -source_task <embedded>
FML_TCL_COMMANDS : task -set CSR

#Coverage waivers: ADD WAIVERS HERE (source waiver TCL files once available)

#ProofGrid settings (enable per user choice)
#FML_TCL_COMMANDS : set_proofgrid_mode shell
#FML_TCL_COMMANDS : set_proofgrid_shell {<bsub command>}
#FML_TCL_COMMANDS : set_proofgrid_per_engine_max_jobs 10
FML_TCL_COMMANDS : set_prove_time_limit <24h>

FML_TCL_COMMANDS : check_csr -prove

#Reports needing proof results go in pre_exit.tcl, e.g.:
#  report -summary -results -file <results>/report_csr.txt -force
#  check_cov -measure -task {CSR} -type {stimuli coi proof} -time_limit <24h>
#  check_cov -report -task {CSR} -report_file ${GPMS_NOBACKUP}/../public_html/$USER/jasper_reports/<ip>_<cfg>_csr_cov.html -force -html

#Stage post-prove hook into run dir
PRE_SIM_COMMANDS : if (-d $test_results_dir/formal_runs/formal) cp $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<cfg_dir>/pre_exit.tcl $test_results_dir/formal_runs/formal/pre_exit.tcl

#vManager Settings (if user requests)
ENABLE_VMGR : 1
VMGR_PROJECT : $VMGR_PROJECT
#vPlan: enable ONLY when the vplanx exists (user chose NOW); keep commented if LATER/NOT
#ENABLE_VPLAN : 1
#VPLAN_SOURCE : $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<IP>_Formal_VPlan_CSR.vplanx

FML_INSTTOP : <TOP>
```

- RUNCMD (write to `<cfg_dir>/RUNCMD`):
```
adsim -clean -block <ip_block> -gui -jgcov -jasper -formal \
      -resdir <abs_cfg_dir>/Result_ \
      -force_setup <abs_cfg_dir>/sim.setup
```
