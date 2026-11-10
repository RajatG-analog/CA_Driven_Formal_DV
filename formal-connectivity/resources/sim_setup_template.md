# Step 4b — Adsim `sim.setup` Template (formal-connectivity)

- Used by SKILL.md Step 4b (run flow B or C).
- Reference format: `/proj/adip_digital/rgulghan/adip/adip_digital/adip_pinmux/dv/formal/formal_pinmux/1_io/peri_8/sim.setup`.
- Replace every `<...>`; one file per config dir.
- Apply the "sim.setup rules" and RUNCMD rules listed in SKILL.md Step 4b.

```
#------------------------------------------------------------------------------
# Title            : <IP_NAME> Formal Verification Setup (<CFG_NAME>)
# Project          : ADIP DIGITAL
#------------------------------------------------------------------------------
# File             : sim.setup
# Author           : <USER>
# Created          : <DD.MM.YYYY>
# Last modified    : <DD.MM.YYYY>
#------------------------------------------------------------------------------
# Description :
# Adsim simulation setup for JasperGold formal verification of <IP_NAME>
# in configuration <CFG_NAME>. Uses Jasper Connectivity Checking App to
# verify spec-derived CSV connectivity rules.
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
#  - Clock          : none (global; per-connection CLOCK rows in CSV if sequential)
#  - Reset          : none (global; per-connection DISABLE rows in CSV if sequential)
#  - Proof time     : <48h> limit
#  - Coverage time  : <48h> limit
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
EXTRA_COMPILE_OPTIONS : $ADIP_BLOCKS_ROOT/adip_common/digital/rtl/adip_boxes.sv
SIM_INCDIR : $ADIP_BLOCKS_ROOT/adip_common
SIM_INCDIR : $ADIP_BLOCKS_ROOT/adip_common/digital/include
SIM_INCDIR : $ADIP_BLOCKS_ROOT/<ip>/digital/rtl/

#Formal Command Variables
#Do NOT add "check_cov -init": adsim -jgcov already issues cov_init (ECOV081).
FML_TCL_COMMANDS : elaborate -top <TOP> -disable_auto_bbox -param <PARAM1> <VAL1> -param <PARAM2> <VAL2>
FML_TCL_COMMANDS : clock -none
FML_TCL_COMMANDS : reset -none
FML_TCL_COMMANDS : elaborate -create_related_covers {witness} -extract_covergroups

#Spec-Derived Connectivity CSVs (one check_conn -load per CSV category)
#<category description>
FML_TCL_COMMANDS : check_conn -load $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<cfg_dir>/spec_<category>.csv

#Default / isolation checks (constant-source c_df_ rows)
FML_TCL_COMMANDS : check_conn -load $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<cfg_dir>/spec_default_connections.csv
#Mode priority checks (c_pri_ winner / release rows)
FML_TCL_COMMANDS : check_conn -load $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<cfg_dir>/spec_mode_priority.csv
#Negative tests: ALL rows intentionally WRONG, each must give a CEX (no ILLEGAL keyword in 2025.09)
#A CEX can mark a regression config FAIL: load always, disable unless the user selected this config
FML_TCL_COMMANDS : check_conn -load $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<cfg_dir>/spec_negative_tests.csv
FML_TCL_COMMANDS : check_conn -disable [lsearch -inline -all [check_conn -list connection] {neg_*}]

#ProofGrid settings (enable per user choice)
#FML_TCL_COMMANDS : set_proofgrid_mode shell
#FML_TCL_COMMANDS : set_proofgrid_shell {<bsub command>}
#FML_TCL_COMMANDS : set_proofgrid_per_engine_max_jobs 10
FML_TCL_COMMANDS : set_prove_time_limit <48h>

FML_TCL_COMMANDS : check_conn -generate_toggle_checks {}
FML_TCL_COMMANDS : check_conn -validate -include all

#Coverage waivers: ADD WAIVERS HERE (source waiver TCL files once available)

FML_TCL_COMMANDS : check_cov -measure -task {Connectivity} -type {stimuli proof} -time_limit <48h> -per_property_time_limit <1h> -verbose -skip_deadcode
FML_TCL_COMMANDS : check_cov -report -task {Connectivity} -html -report_file ${GPMS_NOBACKUP}/../public_html/$USER/jasper_reports/<ip>_<cfg>_coverage_report.html -exclude {unreachable waived deadcode} -force -no_return
FML_TCL_COMMANDS : check_cov -report -html -report_file ${GPMS_NOBACKUP}/../public_html/$USER/jasper_reports/<ip>_<cfg>_code_functional_coverage.html -exclude {unreachable waived deadcode} -force -no_return
#UCD export goes in pre_exit.tcl (FML_TCL_COMMANDS run before prove -all)
#pre_exit.tcl must also generate the sign-off reports (need proof results):
#  check_conn -report -file <results>/conn_report.csv -csv -full_name -show_rtl_info -sort_by classification -force
#  check_conn -signoff -port -file <results>/conn_signoff_port.csv -csv -full_name -force

#Stage post-prove hook into run dir
PRE_SIM_COMMANDS : if (-d $test_results_dir/formal_runs/formal) cp $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<cfg_dir>/pre_exit.tcl $test_results_dir/formal_runs/formal/pre_exit.tcl

#vManager Settings (if user requests)
ENABLE_VMGR : 1
VMGR_PROJECT : $VMGR_PROJECT
#vPlan: enable ONLY when the vplanx exists (user chose NOW); keep commented if LATER/NOT
ENABLE_VPLAN : 1
VPLAN_SOURCE : $ADIP_BLOCKS_ROOT/<ip>/dv/formal/<formal_dir>/<IP>_Formal_VPlan_Connectivity.vplanx

FML_INSTTOP : <TOP>
```
