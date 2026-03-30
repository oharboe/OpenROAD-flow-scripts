# Coarse synthesis + keep_hierarchy decision.
# Produces kept_modules.json listing modules to preserve.
# This is the first half of synth.tcl (lines 34-85) extracted so
# the keep list can be used to partition parallel synthesis jobs.

source $::env(SCRIPTS_DIR)/synth_preamble.tcl
read_checkpoint $::env(RESULTS_DIR)/1_1_yosys_canonicalize.rtlil

hierarchy -check -top $::env(DESIGN_NAME)

if { [env_var_exists_and_non_empty SYNTH_KEEP_MODULES] } {
  foreach module $::env(SYNTH_KEEP_MODULES) {
    select -module $module
    setattr -mod -set keep_hierarchy 1
    select -clear
  }
}

# Coarse synthesis without flattening to get module sizes
synth -run :fine

if { [env_var_exists_and_non_empty SYNTH_MINIMUM_KEEP_SIZE] } {
  set ungroup_threshold $::env(SYNTH_MINIMUM_KEEP_SIZE)
  puts "Keep modules above estimated size of $ungroup_threshold gate equivalents"
  convert_liberty_areas
  keep_hierarchy -min_cost $ungroup_threshold
} else {
  keep_hierarchy
}

# Export kept module list as JSON
set kept_raw [tee -q -s result.string ls -q A:keep_hierarchy=1]
set kept_modules {}
foreach line [split $kept_raw "\n"] {
  set m [string trim $line]
  if { $m ne "" } {
    lappend kept_modules $m
  }
}

set fp [open $::env(RESULTS_DIR)/kept_modules.json "w"]
puts -nonewline $fp "\{\"modules\": \["
set first 1
foreach m $kept_modules {
  if { !$first } { puts -nonewline $fp ", " }
  puts -nonewline $fp "\"$m\""
  set first 0
}
puts $fp "\]\}"
close $fp

# Save RTLIL checkpoint after keep_hierarchy decisions for partition reuse
write_rtlil $::env(RESULTS_DIR)/1_1_yosys_keep.rtlil

puts "Kept [llength $kept_modules] modules: $kept_modules"
