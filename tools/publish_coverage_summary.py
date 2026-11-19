import argparse
import os
import sys
from decimal import Decimal
from pathlib import Path

MAX_DROP = Decimal("1.0")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("label", choices=["Backend", "Frontend"])
    parser.add_argument("coverage", type=Decimal)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args()

    title = f"{args.label} coverage"
    current = args.coverage
    rows = [f"## {title}", "", f"Line coverage: **{current:.2f}%**"]
    regression = None
    if args.baseline:
        baseline = Decimal(args.baseline.read_text().strip())
        change = current - baseline
        rows.append(f"Base commit: **{baseline:.2f}%** · Change: **{change:+.2f} pp**")
        if change <= -MAX_DROP:
            regression = (
                f"Line coverage fell from {baseline:.2f}% to {current:.2f}% "
                f"({change:+.2f} pp). A drop of {MAX_DROP} pp or more fails this check."
            )
            rows.extend(["", regression])
    elif os.environ["GITHUB_EVENT_NAME"] == "pull_request":
        rows.append("No coverage measurement is available for the base commit.")

    rows.extend(["", f"[Download HTML report]({os.environ['REPORT_URL']})", ""])
    with Path(os.environ["GITHUB_STEP_SUMMARY"]).open("a") as summary:
        summary.write("\n".join(rows))

    if regression:
        sys.stdout.write(f"::error title={title} regression::{regression}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
