"use client";

import { useEffect, useId, useRef } from "react";
import { isValidCssHex, shadeDisplayName } from "@/lib/discoverFormat";
import type { DiscoveryShadeItem } from "@/lib/types";

type Props = {
  item: DiscoveryShadeItem | null;
  onClose: () => void;
};

export function ShadeDetailPanel({ item, onClose }: Props) {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!item) return;
    closeRef.current?.focus();
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [item, onClose]);

  if (!item) return null;

  const label = shadeDisplayName(item);
  const hex = item.approx_swatch?.hex;
  const hasSwatch = isValidCssHex(hex);

  return (
    <div className="fixed inset-0 z-40 flex justify-end" role="presentation">
      <button
        type="button"
        className="absolute inset-0 bg-espresso/35 backdrop-blur-[2px]"
        aria-label="Close shade details"
        onClick={onClose}
      />
      <aside
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        className="relative z-10 flex h-full w-full max-w-md flex-col overflow-y-auto border-l border-espresso/10 bg-cream shadow-soft animate-fade-up"
      >
        <div className="flex items-start justify-between gap-4 border-b border-espresso/10 px-5 py-4 sm:px-6">
          <div>
            <p className="section-eyebrow">Historical record</p>
            <h2 id={titleId} className="mt-2 font-display text-3xl text-espresso">
              {label}
            </h2>
            <p className="mt-1 text-sm text-espresso-soft">
              {item.brand} · {item.product}
            </p>
          </div>
          <button
            ref={closeRef}
            type="button"
            onClick={onClose}
            className="inline-flex min-h-10 min-w-10 items-center justify-center rounded-full border border-espresso/15 text-espresso-soft transition hover:border-espresso/30 hover:text-espresso"
          >
            <span className="sr-only">Close</span>
            <span aria-hidden className="text-lg leading-none">
              ×
            </span>
          </button>
        </div>

        <div className="space-y-6 px-5 py-6 sm:px-6">
          <div className="flex items-center gap-4">
            <div
              className="h-20 w-20 rounded-2xl border border-espresso/10"
              style={hasSwatch ? { backgroundColor: hex } : undefined}
              aria-hidden
            >
              {!hasSwatch && (
                <div className="flex h-full w-full items-center justify-center rounded-2xl bg-parchment text-[10px] uppercase tracking-wider text-espresso-soft/70">
                  No swatch
                </div>
              )}
            </div>
            <p className="text-sm leading-relaxed text-espresso-soft">
              {hasSwatch
                ? "Approximate digital swatch from a historical retailer image — not a calibrated measurement."
                : "No approximate swatch color is available for this record."}
            </p>
          </div>

          <div className="rounded-2xl border border-burgundy/20 bg-rose/10 px-4 py-3 text-sm leading-relaxed text-espresso-soft">
            <strong className="font-medium text-burgundy">Not a verified recommendation.</strong>{" "}
            {item.availability_note}
          </div>

          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">Shade name</dt>
              <dd className="mt-1 text-espresso">{item.shade_name ?? "Unavailable"}</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">Shade code</dt>
              <dd className="mt-1 text-espresso">{item.shade_code ?? "Unavailable"}</dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">
                Historical description
              </dt>
              <dd className="mt-1 text-espresso-soft">
                {item.brand_shade_description ?? "No description in the historical record."}
              </dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">
                Historical retailer source
              </dt>
              <dd className="mt-1 break-all text-espresso-soft">
                {item.historical_retailer_url ? (
                  <a
                    href={item.historical_retailer_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline decoration-espresso/25 underline-offset-2 hover:text-espresso"
                  >
                    {item.historical_retailer_url}
                  </a>
                ) : (
                  "No URL recorded"
                )}
              </dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">
                Verification status
              </dt>
              <dd className="mt-1 text-espresso-soft">
                {item.verification_status} · {item.metadata_verification_status} · matching{" "}
                {item.matching_accuracy_status}
                <br />
                recommendation_eligible: {String(item.recommendation_eligible)}
              </dd>
            </div>
            <div>
              <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">Dataset</dt>
              <dd className="mt-1 text-espresso-soft">{item.dataset_collection_note}</dd>
            </div>
            {item.incomplete_flags.length > 0 && (
              <div>
                <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">
                  Incomplete fields
                </dt>
                <dd className="mt-1 text-espresso-soft">{item.incomplete_flags.join(", ")}</dd>
              </div>
            )}
            {item.approx_swatch?.warning && (
              <div>
                <dt className="text-[11px] uppercase tracking-[0.2em] text-burgundy">
                  Color caveat
                </dt>
                <dd className="mt-1 text-espresso-soft">{item.approx_swatch.warning}</dd>
              </div>
            )}
          </dl>

          <p className="text-sm leading-relaxed text-espresso-soft">
            Want guided next steps with verified candidates when available? Use{" "}
            <a
              href="/find-your-shade"
              className="font-medium text-burgundy underline-offset-2 hover:underline"
            >
              Find My Shade
            </a>
            .
          </p>
        </div>
      </aside>
    </div>
  );
}
