#!/usr/bin/env python3
"""
Inspect staged Pudding import records (offline).

Examples (from backend/):

  python -m scripts.inspect_pudding_staging --brand NARS
  python -m scripts.inspect_pudding_staging --brand Maybelline --product "Fit Me"
  python -m scripts.inspect_pudding_staging --brand Fenty --limit 20
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.services.pudding_importer import (
    filter_staged_shades,
    load_staging_manifest,
    summarize_brands,
)

DEFAULT_STAGING = Path("app/data/staging/pudding_all_shades.json")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Filter and print staged historical foundation records."
    )
    parser.add_argument(
        "--staging",
        type=Path,
        default=DEFAULT_STAGING,
        help=f"Staging JSON path (default: {DEFAULT_STAGING})",
    )
    parser.add_argument("--brand", type=str, default=None, help="Substring match on brand")
    parser.add_argument("--product", type=str, default=None, help="Substring match on product")
    parser.add_argument(
        "--shade",
        type=str,
        default=None,
        help="Substring match on shade name, code, or description",
    )
    parser.add_argument("--limit", type=int, default=25, help="Max rows to print")
    parser.add_argument(
        "--brands-only",
        action="store_true",
        help="Print brand counts instead of shade rows",
    )
    args = parser.parse_args(argv)

    if not args.staging.exists():
        print(
            f"ERROR: staging file not found: {args.staging}\n"
            "Run: python -m scripts.import_pudding_shades --input <allShades.csv>",
            file=sys.stderr,
        )
        return 1

    manifest = load_staging_manifest(args.staging)
    rows = filter_staged_shades(
        manifest.shades,
        brand=args.brand,
        product=args.product,
        shade=args.shade,
    )

    print(f"Staging file: {args.staging}")
    print(f"Imported at:  {manifest.imported_at}")
    print(f"Total staged: {len(manifest.shades)}")
    print(f"Filter hits:  {len(rows)}")
    print(f"Eligible?:    all recommendation_eligible=false (historical)")
    print()

    if args.brands_only:
        for brand, count in summarize_brands(rows if (args.brand or args.product) else manifest.shades):
            print(f"  {count:4d}  {brand}")
        return 0

    for shade in rows[: max(args.limit, 0)]:
        print(f"- {shade.id}")
        print(f"    brand/product: {shade.brand} / {shade.product}")
        print(f"    name/code:     {shade.shade_name!r} / {shade.shade_code!r}")
        print(f"    approx_hex:    {shade.approx_hex}  (uncalibrated swatch)")
        print(f"    url:           {shade.historical_retailer_url}")
        print(
            f"    status:        {shade.verification_status} / "
            f"{shade.metadata_verification_status} / "
            f"{shade.matching_accuracy_status} / "
            f"eligible={shade.recommendation_eligible}"
        )
        if shade.incomplete_flags:
            print(f"    incomplete:    {', '.join(shade.incomplete_flags)}")
        print()

    if len(rows) > args.limit:
        print(f"... {len(rows) - args.limit} more (raise --limit to see them)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
