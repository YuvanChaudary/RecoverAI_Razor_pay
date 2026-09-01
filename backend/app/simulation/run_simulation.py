"""
CLI Entrypoint for RecoverAI Phase 10 500-Case Simulation
Usage: python -m backend.app.simulation.run_simulation [--seed 42] [--count 500]
"""

import sys
import time
import argparse
from backend.app.simulation.engine import RecoverySimulationEngine


def main():
    parser = argparse.ArgumentParser(description="RecoverAI Phase 10 — 500-Case Recovery Simulation Engine")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for deterministic generation (default: 42)")
    parser.add_argument("--count", type=int, default=500, help="Number of synthetic cases (default: 500)")
    args = parser.parse_args()

    start_time = time.perf_counter()
    engine = RecoverySimulationEngine(seed=args.seed)
    result, metrics = engine.run(count=args.count)
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    print("=" * 60)
    print("              RecoverAI - Phase 10 Simulation")
    print("=" * 60)
    print(f"Seed:       {result.seed}")
    print(f"Cases:      {result.total_cases}")
    print(f"Runtime:    {duration_ms:.2f} ms")
    print()
    print("Failure Category Distribution")
    print("-----------------------------")
    for category, cnt in sorted(result.diagnosis_distribution.items()):
        pct = (cnt / result.total_cases) * 100.0
        print(f"  {category:<28}: {cnt:4d} ({pct:5.1f}%)")
    print()
    print("Governance & Safety Analysis")
    print("----------------------------")
    print(f"  Allowed:             {result.governance_allowed:4d} ({metrics.governance_pass_rate}%)")
    print(f"  Denied:              {result.governance_denied:4d} ({100.0 - metrics.governance_pass_rate:.2f}%)")
    print(f"  Execution Eligible:  {result.execution_eligible:4d}")
    print(f"  Terminal Declines:   {result.terminal_declines:4d}")
    print()
    print("Revenue & Financial Metrics")
    print("---------------------------")
    print(f"  Revenue at Risk:     INR {result.total_revenue_at_risk_paise / 100:,.2f} ({result.total_revenue_at_risk_paise:,} paise)")
    print(f"  Simulated Recovered: INR {result.simulated_recovered_paise / 100:,.2f} ({result.simulated_recovered_paise:,} paise)")
    print(f"  Recovery Rate:       {metrics.revenue_recovery_rate}%")
    print(f"  Avg Risk / Case:     INR {metrics.average_revenue_at_risk_paise / 100:,.2f}")
    print(f"  Avg Rec / Case:      INR {metrics.average_recovered_paise / 100:,.2f}")
    print()
    print("OPA Governance Rule Violation Breakdown")
    print("---------------------------------------")
    for rule, count in sorted(result.rule_violations.items()):
        print(f"  {rule:<12}: {count:3d} violations")
    print()
    print("Idempotency & Invariant Verification")
    print("------------------------------------")
    print(f"  Duplicate Events Tested:    {result.duplicate_event_count}")
    print(f"  Double Recoveries:          {result.double_recovery_count}")
    print(f"  Unsafe Recovery Claims:     {result.unsafe_recovery_claim_count}")
    print(f"  All Safety Invariants:      {'PASS' if result.invariants_passed else 'FAIL'}")
    print("=" * 60)


if __name__ == "__main__":
    main()
