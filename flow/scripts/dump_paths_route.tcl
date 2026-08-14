set ::env(DUMP_STAGE_PREFIX) "6_route"
set ::env(DUMP_OUT_FILE) "$::env(DUMP_DIR)/6_route_timing_paths.csv"
source flow/scripts/dump_paths_native.tcl
