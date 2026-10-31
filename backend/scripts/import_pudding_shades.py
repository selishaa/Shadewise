#!/usr/bin/env python3
"""
Import The Pudding allShades.csv into a staging JSON file.

Example (from backend/):

  python -m scripts.import_pudding_shades \\
    --input app/data/external/pudding/allShades.csv \\
    --output app/data/staging/pudding_all_shades.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.services.pudding_importer import import_all_shades_csv

DEFAULT_INPUT = Path("app/data/external/pudding/allShades.csv")
DEFAULT_OUTPUT = Path("app/data/staging/pudding_all_shades.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Offline import of The Pudding foundation-names allShades.csv "
            "into ShadeWise staging JSON (never the live catalog)."
        )
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to allShades.csv (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Staging JSON output path (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--omit-skipped-rows",
        action="store_true",
        help="Do not embed full skipped raw rows in the staging file (smaller output).",
    )
    args = parser.parse_args(argv)

    try:
        manifest = import_all_shades_csv(
            args.input,
            output_path=args.output,
            write_skipped=not args.omit_skipped_rows,
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    report = manifest.report
    print("Pudding import complete (staging only).")
    print(f"  source:     {report.source_path}")
    print(f"  output:     {report.output_path}")
    print(f"  imported:   {report.imported}")
    print(f"  skipped:    {report.skipped}")
    print(f"  duplicates: {report.duplicates}")
    print(f"  incomplete: {report.incomplete} (imported but missing some fields)")
    print(f"  brands:     {report.brands_imported}")
    print(f"  products:   {report.products_imported}")
    if report.skip_reasons:
        print("  skip reasons:")
        for reason, count in sorted(report.skip_reasons.items()):
            print(f"    - {reason}: {count}")
    print()
    print("Next: python -m scripts.inspect_pudding_staging --brand NARS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
