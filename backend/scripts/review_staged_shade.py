#!/usr/bin/env python3
"""
Review and promote staged historical shades into the live catalog (manual only).

Examples (from backend/):

  # Exact search
  python -m scripts.review_staged_shade search \\
    --brand Maybelline \\
    --product "Fit Me Matte + Poreless Liquid Foundation" \\
    --shade-code 110

  # Show one staged id (with swatch warnings)
  python -m scripts.review_staged_shade show --id pudding-...

  # Write a review template JSON
  python -m scripts.review_staged_shade template --id pudding-... --out reviews/draft.json

  # Promote only after you edit confirms to true (refuses without --i-confirm-promotion)
  python -m scripts.review_staged_shade promote \\
    --review reviews/draft.json \\
    --i-confirm-promotion
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.services.catalog_promotion import (
    find_staged_by_id,
    find_staged_exact,
    format_staged_for_review,
    load_review_form,
    promote_reviewed_shade,
    write_review_template,
)
from app.services.pudding_importer import load_staging_manifest

DEFAULT_STAGING = Path("app/data/staging/pudding_all_shades.json")


def _load_shades(staging: Path):
    if not staging.exists():
        raise FileNotFoundError(
            f"Staging file not found: {staging}. "
            "Run python -m scripts.import_pudding_shades first."
        )
    return load_staging_manifest(staging).shades


def cmd_search(args: argparse.Namespace) -> int:
    shades = _load_shades(args.staging)
    try:
        hits = find_staged_exact(
            shades,
            brand=args.brand,
            product=args.product,
            shade_name=args.shade_name,
            shade_code=args.shade_code,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Exact matches: {len(hits)}")
    for shade in hits[: args.limit]:
        print(f"- {shade.id}")
        print(f"    {shade.brand} / {shade.product}")
        print(f"    name={shade.shade_name!r} code={shade.shade_code!r}")
        print(f"    eligible={shade.recommendation_eligible}")
    if len(hits) > args.limit:
        print(f"... {len(hits) - args.limit} more")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    shades = _load_shades(args.staging)
    shade = find_staged_by_id(shades, args.id)
    if shade is None:
        print(f"ERROR: staged id not found: {args.id}", file=sys.stderr)
        return 1
    print(format_staged_for_review(shade))
    return 0


def cmd_template(args: argparse.Namespace) -> int:
    shades = _load_shades(args.staging)
    shade = find_staged_by_id(shades, args.id)
    if shade is None:
        print(f"ERROR: staged id not found: {args.id}", file=sys.stderr)
        return 1
    path = write_review_template(shade, args.out)
    print(f"Wrote review template: {path}")
    print("Edit the file: set official_source_url, set confirms to true only after checking.")
    print("Then: python -m scripts.review_staged_shade promote --review ... --i-confirm-promotion")
    return 0


def cmd_promote(args: argparse.Namespace) -> int:
    if not args.i_confirm_promotion and not args.dry_run:
        print(
            "ERROR: Refusing to write the live catalog without --i-confirm-promotion.\n"
            "Use --dry-run to validate without writing.",
            file=sys.stderr,
        )
        return 1

    try:
        review = load_review_form(args.review)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: invalid review file: {exc}", file=sys.stderr)
        return 1

    result = promote_reviewed_shade(
        review,
        staging_path=args.staging,
        catalog_file=args.catalog,
        dry_run=args.dry_run,
    )
    if result.rejection_reasons:
        print(result.message)
        for reason in result.rejection_reasons:
            print(f"  - {reason}")
        return 2

    print(result.message)
    if result.catalog_id:
        print(f"  catalog_id: {result.catalog_id}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Search, review, and promote staged foundation shades (manual verification)."
    )
    parser.add_argument(
        "--staging",
        type=Path,
        default=DEFAULT_STAGING,
        help=f"Staging JSON (default: {DEFAULT_STAGING})",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_search = sub.add_parser("search", help="Exact-match search of staged records")
    p_search.add_argument("--brand", type=str, default=None)
    p_search.add_argument("--product", type=str, default=None)
    p_search.add_argument("--shade-name", type=str, default=None)
    p_search.add_argument("--shade-code", type=str, default=None)
    p_search.add_argument("--limit", type=int, default=50)
    p_search.set_defaults(func=cmd_search)

    p_show = sub.add_parser("show", help="Display one staged record with warnings")
    p_show.add_argument("--id", required=True, help="Staged record id")
    p_show.set_defaults(func=cmd_show)

    p_template = sub.add_parser("template", help="Write a review JSON template")
    p_template.add_argument("--id", required=True, help="Staged record id")
    p_template.add_argument("--out", type=Path, required=True, help="Output review JSON path")
    p_template.set_defaults(func=cmd_template)

    p_promote = sub.add_parser("promote", help="Promote a completed review into the live catalog")
    p_promote.add_argument("--review", type=Path, required=True, help="Filled review JSON")
    p_promote.add_argument(
        "--catalog",
        type=Path,
        default=None,
        help="Catalog JSON path (default: app/data/foundation_catalog.json)",
    )
    p_promote.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only; do not write the catalog",
    )
    p_promote.add_argument(
        "--i-confirm-promotion",
        action="store_true",
        help="Required explicit flag to write foundation_catalog.json",
    )
    p_promote.set_defaults(func=cmd_promote)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
