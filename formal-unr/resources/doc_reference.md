# Doc Reference — formal-unr

- Used by every step of `SKILL.md`; every command / option in the skill was checked against the documents below.
- Docs win over the ADI lab kit, the adsim skill, and memory.
- Items that could not be confirmed in a document are marked `UNCONFIRMED — verify in <doc>` in SKILL.md and the templates.

## Installed Documents (authoritative)

| ID | Document | Path | Version |
|----|----------|------|---------|
| D1 | Jasper Coverage Unreachability App User Guide | `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/jasper_unr_userguide.pdf` | 2025.09 |
| D2 | Jasper Apps Command Reference Manual | `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/jasper_command_reference.pdf` | 2025.09 |
| D3 | Jasper Coverage App User Guide | `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/jasper_cov_userguide.pdf` | 2025.09 |
| D4 | Jasper Engine Selection Guide | `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/jasper_engine_selection.pdf` | 2025.09 |
| D5 | Jasper ProofGrid Manager | `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/jasper_proofgrid_manager.pdf` | 2025.09 |
| D6 | Official UNR example (README, RUNME, `tcl/jg.tcl`, `tcl/jg_init.tcl`, `covfile.cf`, `irun.f`) | `/cad/adi/apps/cadence/jasper/2025.09-p002/doc/example_jasper_apps/UNR/` | 2025.09 |
| D7 | Integrated Metrics Center (IMC) User Guide | `/cad/adi/apps/cadence/mdv/linux/26.03-s30/doc/imcuser/imcuser.pdf` (`current` → `26.03-s30`) | 26.03 |
| D8 | adsim variable manual database | `/cad/adi/apps/adi/adsim/man_db/1.40/adsim_man.db` (`current` → `1.40`) | man_db 1.40 |
| D9 | adsim skill (prefix list, UNR section) | `~/.config/chipagents/auto/skills/adsim/resources/project_setup.md`, `coverage.md` §6 | skill (not a vendor doc) |

- Text extractions used during authoring (regenerate with `pdftotext -layout <pdf> <out>` if needed):
  - D1 → `Handoff/.tmp/unr_ug_full_<timestamp>.txt`
  - D2 → `Handoff/.tmp/cmd_ref.txt`
  - D3 → `Handoff/.tmp/jasper_cov_userguide.txt`
  - D7 → `Handoff/.tmp/imcuser_<timestamp>.txt`

## Sections Used

| Topic | Doc | Section | Key facts used |
|-------|-----|---------|----------------|
| Flow overview, prerequisites | D1 | Ch. 1 Introduction; Ch. 2 intro | UNR reads uncovered items from the Xcelium coverage test directory; simulation coverage must exist |
| Supported coverage items | D1 | Supported Coverage Items | block (conditional statements only), expression (SOP + control scoring only; no parity / vector / FCC), toggle (incl. SV enum since 2020.03), FSM (state, transition, arc), functional |
| Formal vs sim differences | D1 | RTL Constructs that Cause Formal (UNR) and Simulation Differences | no UNR for an enum assigned X |
| Xcelium compatibility | D1 | Xcelium Version Dependency | Xcelium ≥ 22.07.a071 incompatible with Jasper ≤ 2022.06 FCS |
| Clock / reset | D1 | Clock and Reset Configuration | `unr::config_clock`, `unr::config_reset` (`reset -init_state` dummy file); recommended init: `reset -shm <db> [-time <t> -time_scale <u> -exact]` |
| Launch + covdb | D1 | Reading the Coverage Database; Mandatory / Optional Options | `xrun -unr -jg -R -inst_top <path> -input <tcl> -covdb <covwork>/<covscope>/<covtest>`; P2P default; `-gui`; `-covfile`, `-jg_coverage (all\|b\|e\|t\|f)`, `-covtest` (default `unr`), `-covworkdir`, `-covscope`, `-covoverwrite`, `-jg_pre_tcl`, `-jg_bbmod[list]`, `-jg_bbinst[list]`, `-jg_periodicexport`, `-load_refinement`, `-jg_analyze_opts`, `-jg_elab_opts`, `-s`, `-dutinst` |
| Default input TCL | D1 | Optional Options, `-input` | `check_unr -setup`; `clock -none`; `exec touch dummy`; `reset -init_state dummy`; `check_unr -prove` (default 24 h); `database -export_unicov` |
| `-inst_top` modelling | D1 | Modeling of RTL at -inst_top Hierarchy | inputs of the instance severed from parent drivers, except constants in its port list / directly connected parent constants |
| Constraints | D1 | Applying Stopats and Constraints; Adding Tcl Assumptions; Enabling Embedded SVA Assumptions | drop the TB top-module name from signal paths; `stopat -env` BEFORE `check_unr -setup`; Tcl `assume` before or after setup; SVA assumes disabled by default → `check_unr -init -enable_assumption` in `-jg_pre_tcl` or xrun `-jg_unr_assumption` |
| Functional coverage | D1 | Reading the Coverage Database (note) | `-jg_pre_tcl` with `set_unr_functional_coverage true` + `-jg_coverage all` or `u`; mode via `set_unr_functional_coverage_mode (covergroup\|assertion\|all)` |
| Multi-step flow | D1 | UNR Compatibility with Xcelium Multi-Step Flow | `xmsim -unr -64bit <snapshot> -covdb ... -inst_top ... -jg_coverage (all\|b\|e\|t\|f\|u)` |
| Partitioning | D1 / D2 | Running the UNR Auto Partition Flow; `check_unr -generate_partition/-load_partition/-run_partition` | `xrun -jg_unr_partition [-jg_unr_partition_args "..."]`; threshold ≈ 2.4 M items; `set_unr_partition_max_jobs`; `session -set_remote_mode shell` / `-set_remote_shell` |
| `check_unr` syntax | D2 | Regular Commands — check_unr (pp. 667–675); D1 UNR-Specific Commands | `-init` (BEFORE elaborate; `-coverage`, `-covdb`, `-dutinst`, `-load_refinement`, `-enable_assumption`, `-covtest/-covscope/-covworkdir`, `-inst_top`, `-write_metrics`, `-covoverwrite`, `-jg_periodicexport`); `-setup [-task]`; `-enable_property` / `-disable_property`; `-list [-type reachable\|unreachable\|bounded\|unprocessed\|enabled\|disabled] [-regexp] [-task]`; `-clear`; `-prove [...]`; `-reason [-file]` |
| Status codes | D2 / D1 | `check_unr -list` | BND bounded (no conclusive result), DSB disabled, RCH reachable, UNP unprocessed, UNR unreachable |
| Setup side effects | D2 / D1 | `check_unr -setup` | creates task `unr`; user assumptions enabled; no other `<embedded>` environment copied; `discarded_items_report.txt` in session dir; second `-setup` needs `-clear` |
| Prove tuning | D2 / D1 | `check_unr -prove`; Appendix B | `-time_limit`, `-engine_mode`, `-max_chunks` (default 6, hard), `-max_properties_per_chunk` (default 100000, soft), `-shallow_analysis`, `-persistent_grid_jobs`, `-save_ppd/-with_ppd`, `-keep_trace` (trace suppression default on), `-bg` |
| Reasons | D1 | Appendix A | `check_unr -reason -file <root>` → `<root>.txt` + `<root>.cmd` (IMC excludes with "Unreachable Cause" comments + `save -refinement`); only constant / assumption causes |
| Property names | D1 | Naming Conventions for Embedded Cover Properties | `block_cov_line_<n>_<col>`, `expr_cov_line_<n>_<col>`, `toggle_cov_<sig>_{fall\|rise}`, `fsm_cov_reach_<fsm>_<state>`, `fsm_cov_tran_<fsm>_<from>_<to>_arc<id>` |
| Export | D1 / D2 | Generating a Coverage Database; `database` (pp. 784–787) | on-demand `database -export_unicov`; automatic on exit since 2023.12 if missing; periodic `database -init_unicov -app unr -interval <t>` before setup; `-init_unicov -app` default `all` = all apps EXCEPT UNR |
| Merge script | D1 / D6 | Generating a Coverage Database; example README | `<PROJ_DIR>/sessionLogs/<SESSION_ID>/<TASK_NAME>_imc_coverage_merge.cmd` → `jgproject/sessionLogs/session_0/unr_imc_coverage_merge.cmd` (D1 body text also names it `imc_coverage_unr_merge.cmd`) |
| Exclusion | D1 / D7 | Converting Unreachable to Excluded in IMC; IMC `exclude` (`-unr`, `-comment`), "Excluding Unreachable Items" | UNR does not change the coverage score until items are excluded; do not exclude partial-UNR icons; analyze each before excluding all; `exclude -inst <i> -block <n> -unr`, `-toggle <sig>\[<b>.rise\] -unr`, `-expression <id> -unr`, `-metrics <m> -unr` |
| IMC launch / refinement | D7 | Launching IMC; `save`; `load`; `report_metrics` | `imc -exec <file>` (batch, exits); `-init <file>`; `-nostdout`; `save -refinement <file>`; `load -refinement <f1>,<f2>`; `report_metrics -out <dir> -overwrite -detail ...` |
| IMC UNR markers | D7 | UNR column | red = Fully Unreachable, orange = Partially Unreachable, gray = Excluded Unreachable (U-EXCL) |
| Coverage-option consistency | D1 | Assumptions and Recommendations; `-covfile` | same `-covfile` / coverage options for sim and UNR and for all merged DBs; glitch settings `set_toggle_strobe 1fs` or `set_toggle_scoring -regeot`, and `set_glitch_strobe` |
| Limitations | D1 | Limitations | branch-scoring multi-expression case tags; VHDL packages; formalbuild-optimised blocks; machine errors not reported |
| Clock loops | D1 / D2 | Assumptions and Recommendations; `set_unr_break_clock_loop (on\|off)` | self-disabling clock loops (WCK111, ECK113, ECK114) auto-stopat'ed |
| Resilient compilation | D1 | set_resilient_compilation(_mode) | default on, mode `all`; blackboxes / ignores erroneous code — check the summary |
| Coverage App interaction | D3 | Coverage App Main Flow | Coverage App runs concurrently with FPV and other apps EXCEPT UNR → no `check_cov` in a UNR session |
| Proof orchestration | D4 | Proof Orchestration | ProofMaster compatible with `check_unr -prove` |
| ProofGrid | D2 | `set_proofgrid_mode`, `set_proofgrid_shell`, `set_proofgrid_manager`, `set_proofgrid_per_engine_max_jobs`, `set_prove_time_limit` | command names confirmed in the command list |
| `clock` / `reset` / `stopat` / `assume` / `report` | D2 | Regular Commands | `clock <sig> [-both_edges]`, `clock -none`; `reset [-expression] <constraints>`, `reset -init_state`, `reset -shm`, `reset -none`; `stopat -env <sig>`; `assume [-env] -name <n> {<expr>}`; `report -summary -task <t> -file <f> -force` |
| adsim UNR variables | D8 | `FML_COVERAGE`, `FML_COVDB`, `FML_INSTTOP`, `FML_TCL_FILE`, `FML_BBLIST`, `COVERAGE_REFINE_FILE`, `SIM_COMPLETE_FLAG`, `CUSTOM_SWITCH` | `{X}_` = any prefix allowed; `FML_COVERAGE`/`FML_COVDB` "considered only when the -unr switch is used"; `FML_BBLIST` = module names, one per line; `COVERAGE_REFINE_FILE` = IMC `.vRefine` files, Xcelium only, global only |
| adsim `UNR_` prefix, `!` negation | D9 | project_setup.md prefix table, "Negation with !" | `UNR_` active only for `-unr`; `!UNR_X : v` = active when NOT `-unr` |

## Doc-internal Inconsistencies (follow the syntax block)

| Item | Where | Resolution in this skill |
|------|-------|--------------------------|
| `check_unr -setup -coverage {...} -covdb test -load_refinement ...` | D1 / D2 `check_unr` Examples | syntax block lists `-coverage`, `-covdb`, `-load_refinement` under `-init` only; `-setup` takes only `[-task]` → use `-init` options (or the xrun switches) |
| Merge script name `imc_coverage_unr_merge.cmd` vs `<TASK_NAME>_imc_coverage_merge.cmd` | D1 "Generating a Coverage Database" | use the file found in `jgproject/sessionLogs/session_<n>/` (D6 README: `unr_imc_coverage_merge.cmd`) |
| Auto-partition minimum Xcelium MAIN `23.09-s001` (D1) vs `22.09-s001` (D2 Appendix K) | D1 / D2 | treat `23.09-s001` as minimum (stricter) |
| `-jg_coverage` values `all\|b\|e\|t\|f` (xrun) vs `all\|b\|e\|t\|f\|u` (xmsim) | D1 | `u` (functional) documented for xmsim and in the functional-coverage note for xrun |

## Not Found Locally

- adsim user guide pages referenced by the kit (`http://cad.analog.com/tools/adsim/user-guide`, `.../adsim-sim.setup-variables`) and `https://dvmt.web.analog.com/SitePages/formal/unreachability.aspx` — not opened (network); D8 used instead.
- The mapping of adsim `UNR_FML_*` variables to xrun switches is not documented in D8 → marked UNCONFIRMED in `sim_setup_template.md`.
- Xcelium coverage-configuration (ccf) command reference — not checked; ccf command spelling in the kit (`set_covergroup -per_instance_default_one`) is UNCONFIRMED.
