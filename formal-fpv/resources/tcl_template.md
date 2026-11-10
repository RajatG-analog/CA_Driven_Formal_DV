# Step 9a — JasperGold FPV TCL Template (formal-fpv)

- Used by SKILL.md Step 9a (run flow A or C). Launched by `<cfg_dir>/RUNCMD_tcl` with `jg -fpv -tcl ... -define CFG <cfg_dir>`.
- Flow order follows the official FPV example (`<doc>/example_jasper_apps/FPV/FPV_verilog_sva_example.tcl`) and the command reference.
- Every command below is in `jasper_command_reference.pdf` 2025.09; re-check options there before adding new ones.
- Replace every `<...>`; delete blocks not used by the selected path.

```tcl
#------------------------------------------------------------------------------
# File   : jg_fpv_setup.tcl — <IP_NAME> FPV (spec: <spec> rev <rev>)
# Path   : <Path 1 | Path 2 | Path 3> (SKILL.md Step 0)
# Config : passed as Tcl variable CFG (jg -define CFG <cfg_dir>)
#------------------------------------------------------------------------------
set FPV_ROOT <formal_dir_abs>
set RTL_F    ${FPV_ROOT}/rtl_list/filelist.f
set TOP      <top_module or <ip>_fpv_wrapper>
set RES      ${FPV_ROOT}/results
# Per-config parameters (Q7): one entry per <cfg_dir>
array set PARAMS {
  default  {<PARAM1> <VAL1> <PARAM2> <VAL2>}
}
clear -all
#--- Coverage App init: BEFORE analyze (coverage user guide, Initialization)
check_cov -init -type {stimuli coi proof bound} -model all -covdut ${TOP}
#--- Path 2 / 3: scoreboard PA macros, after clear -all and before analyze
jasper_scoreboard_3 -init
#--- ABVIP location: before analyze (Q16)
abvip -set_location <abvip_dir>
#--- Analyze: RTL (compile only), then environment and properties
analyze -sv -f ${RTL_F}
analyze -sv ${FPV_ROOT}/props/<ip>_assumptions.sv
analyze -sv ${FPV_ROOT}/props/<ip>_<feature>_props.sv
analyze -sv ${FPV_ROOT}/props/<ip>_props_bind.sv
# Path 2 / 3 only:
analyze -sv ${FPV_ROOT}/models/<ip>_<model>_model.sv
analyze -sv ${FPV_ROOT}/wrapper/<ip>_fpv_wrapper.sv
#--- Elaborate
set ELAB_PARAMS {}
foreach {p v} $PARAMS($CFG) { lappend ELAB_PARAMS -parameter $p $v }
elaborate -top ${TOP} -disable_auto_bbox -create_related_covers {witness precondition} {*}$ELAB_PARAMS
# black boxes (Step 3, each with recorded impact): add -bbox_m <module> to elaborate
get_design_info
#--- Clocks (spec, Q5); successive clock commands are cumulative
clock <clk>
# clock <clk2> -factor <N>
clock -analyze
#--- Resets (spec, Q6): all spec resets in one expression
reset -expression {~<rst_n>}
# reset -expression {~<rst1_n> ~<rst2_n>}
#--- Spec-cited Tcl-level assumptions (prefer SVA files)
# assume -name asm_<CAT><NN>_<desc> {<expr>}
#--- Assumption health (Step 8)
check_assumptions -conflict
check_assumptions -dead_end
#--- Tasks (create after all constraints)
# Path 3: task -create init_<i> -copy_all -source_task <embedded>
task -create neg_sanity -copy_assumes -source_task <embedded>
assert -name neg_sanity::neg_<CAT><NN> {<deliberately wrong expectation>}
task -set <embedded>
#--- Engines / limits / bounds (Step 10, Q14)
set_prove_time_limit <t>
set_prove_per_property_time_limit <t>
# bounded sign-off run only:
# set_max_trace_length <N>
# set_prove_target_bound <N>
#--- ProofGrid (Q13)
# set_proofgrid_mode shell
# set_proofgrid_shell {bsub -J %jasper_session_id -n %jasper_engine_job_threads -K -q <queue> -R "rusage[mem=%jasper_engine_job_memory_request_mib] span[hosts=1]"}
# set_proofgrid_max_jobs <N>
# set_proofgrid_per_engine_max_jobs <M>
#--- Prove (Proof Orchestration by default); -all = all assertions and covers in all tasks
prove -all -dump_trace -dump_trace_type vcd -dump_trace_dir ${RES}/${CFG}_cex
#--- Results (neg_sanity reported separately: every neg_* must be CEX)
report -summary -results -task <embedded> -file ${RES}/${CFG}_summary.txt -force
report -csv -task <embedded> -file ${RES}/${CFG}_results.csv -force
report -summary -results -task neg_sanity -file ${RES}/${CFG}_neg_sanity.txt -force
#--- Coverage (Step 12)
check_cov -measure -type {stimuli coi proof bound} -task <embedded> -time_limit <t>
check_cov -report -type checker -report_file ${RES}/${CFG}_cov_checker.html -force -html
check_cov -report -type stimuli -report_file ${RES}/${CFG}_cov_stimuli.html -force -html
check_cov -report -type formal  -report_file ${RES}/${CFG}_cov_formal.html  -force -html
check_cov -report -type bounded -report_file ${RES}/${CFG}_cov_bounded.html -force -html
#--- Coverage waivers
# ADD WAIVERS HERE
#--- Batch mode (Q12): RUNCMD_tcl adds -batch
# exit -force
```

## Notes
- `check_cov -init` and `jasper_scoreboard_3 -init` both precede `analyze`; `clear -all` unloads previously loaded definitions, so keep `clear -all` first.
- `-create_related_covers {witness precondition}` cannot be combined with `-no_preconditions`.
- `prove -bg` + `prove -wait` may replace the blocking `prove` in interactive sessions.
- Use `analyze -sv09` instead of `-sv` only if the project language mode requires it (check the command reference `analyze` options).
- LRM mode (record in `verification_plan.md` "Methodology"; PF-46): per the command reference `analyze` options, `-sv` = `-sv05` = IEEE 1800-2005 (strong-only sequence semantics); `-sv09` / `-sv12` / `-sv17` = 2009 / 2012 / 2017 (assert / assume weak by default). The `analyze` synopsis lists the language switch as a required choice; no default mode is stated. Covers: `elaborate` default is `-witness_cover_property` (command reference `elaborate`). See `resources/sva_coding_rules.md` R3, R11.
- `{*}$ELAB_PARAMS` expands the per-config parameter list (Tcl 8.5+ syntax); if the Jasper Tcl rejects it, write the `-parameter` pairs literally per `<cfg_dir>`.
