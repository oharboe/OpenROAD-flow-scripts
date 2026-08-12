# Runs OpenROAD flow up to placement and evaluates minimum achievable clock period.

set ::env(KEEP_VARS) 1
set ::env(WRITE_ODB_AND_SDC_EACH_STAGE) 0

set ::flow_expected [glob -nocomplain -directory $::env(RESULTS_DIR) *.odb *.sdc]

proc flow_source { script } {
  uplevel #0 [list source $::env(SCRIPTS_DIR)/$script]
  foreach f [glob -nocomplain -directory $::env(RESULTS_DIR) *.odb *.sdc] {
    if { [lsearch -exact $::flow_expected $f] == -1 } {
      error "$script wrote $f: with WRITE_ODB_AND_SDC_EACH_STAGE=0 stage scripts must not write .odb/.sdc files"
    }
  }
}

# Run the flow up to place
flow_source synth_odb.tcl
flow_source floorplan.tcl
flow_source macro_place.tcl
flow_source tapcell.tcl
flow_source pdn.tcl
flow_source global_place_skip_io.tcl
flow_source io_placement.tcl
flow_source global_place.tcl
flow_source resize.tcl
flow_source detail_place.tcl

# Evaluate target function (measures clock / WNS)
flow_source target-function.tcl
