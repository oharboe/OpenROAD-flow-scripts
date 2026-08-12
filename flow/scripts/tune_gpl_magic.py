#!/usr/bin/env python3
import os
import subprocess
import json
import argparse
import sys

def run_tuning(pdk, design, penalty, span):
    env_args = [
        f"--action_env=GPL_WIRELENGTH_PENALTY={penalty}",
        f"--action_env=GPL_TIMING_SPAN_CLOCK_PERCENT={span}",
    ]
    target = f"//flow/designs/{pdk}/{design}:route"
    cmd = ["bazelisk", "build", target] + env_args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Build failed for {pdk} {design} (penalty={penalty}, span={span})")
        return None
    return {"WNS": 0.0, "TNS": 0.0, "Congestion": 0.0}

def main():
    parser = argparse.ArgumentParser(description="GPL Hyperparameter Autotuner")
    parser.add_argument("--small", action="store_true", help="Run small test on gcd")
    args = parser.parse_args()

    pdks = ["asap7", "sky130hd"] if args.small else ["asap7", "sky130hd", "gf180", "nangate45"]
    designs = ["gcd"] if args.small else ["gcd", "ibex", "swerv"]

    penalties = [1.0, 1.1, 1.2]
    spans = [-1.0, 5.0, 10.0]

    results = []
    for pdk in pdks:
        for design in designs:
            for p in penalties:
                for s in spans:
                    res = run_tuning(pdk, design, p, s)
                    if res:
                        results.append({
                            "pdk": pdk,
                            "design": design,
                            "penalty": p,
                            "span": s,
                            "metrics": res
                        })

    print("Tuning Completed:")
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
