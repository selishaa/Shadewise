"use client";

import { isValidCssHex, shadeDisplayName } from "@/lib/discoverFormat";
import type { DiscoveryShadeItem } from "@/lib/types";

type Props = {
  item: DiscoveryShadeItem;
  onSelect: (item: DiscoveryShadeItem) => void;
};

export function ShadeResultCard({ item, onSelect }: Props) {
  const label = shadeDisplayName(item);
  const hex = item.approx_swatch?.hex;
  const hasSwatch = isValidCssHex(hex);

  return (
    <button
      type="button"
      onClick={() => onSelect(item)}
      className="group flex w-full flex-col rounded-[1.35rem] border border-espresso/10 bg-cream/70 p-4 text-left shadow-soft transition hover:border-rose/35 hover:bg-cream focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-burgundy active:scale-[0.99]"
      aria-label={`View details for ${item.brand} ${label}`}
    >
      <div className="flex items-start gap-4">
        <div
          className="relative h-16 w-16 shrink-0 overflow-hidden rounded-2xl border border-espresso/10"
          style={hasSwatch ? { backgroundColor: hex } : undefined}
          aria-hidden
        >
          {!hasSwatch && (
            <div className="flex h-full w-full items-center justify-center bg-parchment text-[10px] uppercase tracking-wider text-espresso-soft/70">
              No swatch
            </div>
          )}
          {hasSwatch && (
            <span className="absolute inset-x-0 bottom-0 bg-espresso/55 px-1 py-0.5 text-center text-[9px] font-medium uppercase tracking-wide text-cream">
              Approx.
            </span>
          )}
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
            {item.brand}
          </p>
          <p className="mt-1 truncate font-display text-xl leading-snug text-espresso">
            {label}
          </p>
          <p className="mt-1 line-clamp-2 text-sm leading-relaxed text-espresso-soft">
            {item.product}
          </p>
        </div>
      </div>
      <p className="mt-4 border-t border-espresso/8 pt-3 text-[12px] leading-relaxed text-espresso-soft">
        Historical · unverified · availability may be outdated
      </p>
    </button>
  );
}
