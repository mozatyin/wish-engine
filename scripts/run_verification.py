#!/usr/bin/env python3
"""Run the full verification framework — all fulfillers × literary characters."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from wish_engine.verification.validator import validate_all


def main():
    print("=" * 70)
    print("LITERARY CHARACTER VERIFICATION FRAMEWORK")
    print("=" * 70)

    report = validate_all()

    # Print results grouped by fulfiller
    current_fulfiller = ""
    for r in report.results:
        if r.fulfiller != current_fulfiller:
            current_fulfiller = r.fulfiller
            print(f"\n--- {current_fulfiller} ---")

        status = "✅" if r.passed else ("❌ ERROR" if r.error else "❌ FAIL")
        print(f"  {status} {r.character}: {r.reason[:60]}")
        if r.passed:
            print(f"       Recs: {r.recommendations[:3]}")
        elif r.error:
            print(f"       Error: {r.error[:80]}")
        else:
            print(f"       Expected: {r.expected_tags}")
            print(f"       Got: {r.actual_tags[:5]}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  Total validations: {report.total}")
    print(f"  Passed: {report.passed} ({report.pass_rate:.0%})")
    print(f"  Failed: {report.failed}")
    print(f"  Errors: {report.errors}")
    print(f"  Pass rate: {report.pass_rate:.0%}")

    if report.unmapped_fulfillers:
        print(f"\n  ⚠️  {len(report.unmapped_fulfillers)} fulfillers without character validation:")
        for f in sorted(report.unmapped_fulfillers)[:20]:
            print(f"     - {f}")
        if len(report.unmapped_fulfillers) > 20:
            print(f"     ... and {len(report.unmapped_fulfillers) - 20} more")

    # Save report
    out_dir = Path("/Users/michael/wish-engine/experiment_results")
    out_dir.mkdir(exist_ok=True)
    with open(out_dir / "verification_report.json", "w") as f:
        import json
        json.dump(report.model_dump(), f, indent=2, ensure_ascii=False)
    print(f"\n  Report saved to {out_dir}/verification_report.json")


if __name__ == "__main__":
    main()
