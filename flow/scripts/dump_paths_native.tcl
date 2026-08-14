# Native Tcl script to extract path details directly from OpenSTA into CSV
# Usage: source dump_paths_native.tcl

set out_file $::env(DUMP_OUT_FILE)
set stage_prefix $::env(DUMP_STAGE_PREFIX)

if {![info exists ::env(DUMP_OUT_FILE)] || ![info exists ::env(DUMP_STAGE_PREFIX)]} {
    puts "Error: DUMP_OUT_FILE or DUMP_STAGE_PREFIX not set."
    exit 1
}

puts "Extracting paths natively for stage: $stage_prefix to $out_file"

set fp [open $out_file w]
# We only write the header if the file is empty (we might append in Python, or write standalone)
puts $fp "startpoint,endpoint,${stage_prefix}_slack,${stage_prefix}_path_delay,${stage_prefix}_net_delay,${stage_prefix}_logic_delay,${stage_prefix}_total_cap,${stage_prefix}_buffers"

# Get top 2000 paths
set paths [find_timing_paths -path_delay max -group_count 2000]

foreach path_end $paths {
    set slack [$path_end slack]
    set path_delay [$path_end arrival]
    
    set start_path [$path_end start_path]
    set start_pin [$start_path pin]
    set end_pin [$path_end pin]
    
    set startpoint [get_name $start_pin]
    set endpoint [get_name $end_pin]
    
    # Capture the detailed report for this path in memory
    utl::redirectStringBegin
    report_checks -path $path_end -digits 4 -fields {capacitance net slew}
    set report_str [utl::redirectStringEnd]
    
    set net_delay 0.0
    set logic_delay 0.0
    set total_cap 0.0
    set buffers 0
    
    # Parse the report lines
    set lines [split $report_str "\n"]
    foreach line $lines {
        # Check for cap: looking for a line with cap value and delay
        # Format typical: cap net delay
        if {[regexp {^\s+([0-9\.]+)\s+([0-9\.]+)\s+([0-9\.]+)\s+([v\^])\s+([^\s]+)\s+\(([^\)]+)\)} $line -> cap slew delay edge pin_name cell_type]} {
            set total_cap [expr {$total_cap + $cap}]
            if {[regexp {^sky130_fd_sc_hd__(buf|dly)} $cell_type] || [regexp {^BUFx} $cell_type]} {
                incr buffers
            }
        }
        
        # In OpenSTA report_checks, net delay lines often have net name
        if {[regexp {^\s+([0-9\.]+)\s+([0-9\.]+)\s+([v\^])\s+([^\s]+)\s+\(net\)} $line -> incr_delay total_delay edge net_name]} {
             set net_delay [expr {$net_delay + $incr_delay}]
        }
        # Wait, the column format is different with -fields {capacitance net slew}. Let's be careful.
    }
    
    # Since exact regex parsing of report_checks column is brittle, an easier way is to just know
    # that Path_delay = Net_delay + Logic_delay.
    # Actually, logic delay lines have the cell instance name. Let's do it robustly:
    set logic_delay 0.0
    set net_delay 0.0
    foreach line $lines {
        if {[regexp {^\s+([0-9\.]+)\s+[0-9\.]+\s+[v\^]\s+[^\s]+\s+\((net|in|out|.*)\)} $line -> incr_delay type]} {
             if {$type == "net"} {
                 set net_delay [expr {$net_delay + $incr_delay}]
             } elseif {$type != "in" && $type != "out"} {
                 # Cell delay
                 set logic_delay [expr {$logic_delay + $incr_delay}]
                 if {[regexp {buf|dly} $type] || [regexp {BUF} $type]} {
                     incr buffers
                 }
             }
        }
        if {[regexp {^\s+([0-9\.]+)\s+[0-9\.]+\s+[0-9\.]+\s+[0-9\.]+\s+[v\^]\s+[^\s]+\s+\(net\)} $line -> cap]} {
             set total_cap [expr {$total_cap + $cap}]
        }
    }
    
    puts $fp "$startpoint,$endpoint,$slack,$path_delay,$net_delay,$logic_delay,$total_cap,$buffers"
}

close $fp
puts "Dump complete."
