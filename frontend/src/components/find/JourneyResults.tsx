"use client";

import type { JourneyGuidance } from "@/lib/journeyGuidance";
import { softenCustomerFacingText } from "@/lib/journeyGuidance";
import type { MatchShadeResponse } from "@/lib/types";

type Props = {
  guidance: JourneyGuidance;
  matchResult: MatchShadeResponse | null;
};

function softenReasons(reasons: string[]): string[] {
  return reasons
    .map(softenCustomerFacingText)
    .filter((text) => text.length > 0)
    .filter(
      (text) =>
        !/metadata verification|matching accuracy|not proof|wear-test evidence/i.test(text),
    );
}

export function JourneyResults({ guidance, matchResult }: Props) {
  const candidates = matchResult?.recommendations ?? [];

  return (
    <div
      id="results"
      className="space-y-8 scroll-mt-8"
      aria-live="polite"
      aria-label="Your shade analysis"
    >
      <div className="rounded-[1.75rem] border border-espresso/10 bg-cream/95 p-5 shadow-soft sm:p-8">
        <h2 className="font-display text-3xl text-espresso sm:text-4xl">
          {guidance.mode_label}
        </h2>
        {guidance.source_note && (
          <p className="mt-2 text-xs font-medium uppercase tracking-[0.18em] text-rose-deep">
            {guidance.source_note}
          </p>
        )}
        {guidance.source === "rules" && (
          <p className="mt-2 text-xs font-medium uppercase tracking-[0.18em] text-espresso-soft">
            Guided analysis from your answers
          </p>
        )}
        <p className="mt-4 max-w-3xl text-base leading-relaxed text-espresso-soft sm:text-lg">
          {guidance.summary}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
        <section className="space-y-4 rounded-[1.75rem] border border-espresso/10 bg-ivory/90 p-5 sm:p-8">
          <h3 className="font-display text-2xl text-espresso">What might be happening</h3>
          <ul className="space-y-3 text-[15px] leading-relaxed text-espresso-soft">
            {guidance.possible_explanations.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-deep" aria-hidden />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="space-y-4 rounded-[1.75rem] border border-espresso/10 bg-ivory/90 p-5 sm:p-8">
          <h3 className="font-display text-2xl text-espresso">What to try next</h3>
          <ul className="space-y-3 text-[15px] leading-relaxed text-espresso-soft">
            {guidance.what_to_try_next.map((item) => (
              <li key={item} className="flex gap-3">
                <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-deep" aria-hidden />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </section>
      </div>

      <section className="space-y-5 rounded-[1.75rem] border border-espresso/10 bg-cream/90 p-5 sm:p-8">
        <div>
          <h3 className="font-display text-2xl text-espresso">Shades worth trying</h3>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-espresso-soft">
            These appear only when we can carefully compare within a product family we&apos;ve
            reviewed. They&apos;re starting points — always confirm on your skin.
          </p>
        </div>

        {!guidance.can_suggest_candidates && (
          <p className="rounded-2xl bg-mist px-4 py-3.5 text-sm leading-relaxed text-espresso-soft">
            We don&apos;t have nearby shade suggestions for this selection yet. Your guidance above
            still stands — especially for in-person swatching.
          </p>
        )}

        {guidance.can_suggest_candidates && candidates.length === 0 && (
          <p className="rounded-2xl bg-mist px-4 py-3.5 text-sm leading-relaxed text-espresso-soft">
            {matchResult?.no_match_reason
              ? softenCustomerFacingText(matchResult.no_match_reason)
              : "We don’t have a close enough option to suggest confidently right now."}
          </p>
        )}

        {candidates.length > 0 && (
          <ul className="space-y-4">
            {candidates.map((rec) => {
              const reasons = softenReasons(rec.selection_reasons);
              const tip = softenReasons(rec.limitations)[0];
              return (
                <li
                  key={rec.catalog_id}
                  className="rounded-[1.35rem] border border-espresso/10 bg-ivory/95 p-5 sm:p-6"
                >
                  <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
                    {rec.brand}
                  </p>
                  <p className="mt-1.5 font-display text-2xl text-espresso sm:text-[1.75rem]">
                    {rec.shade_name}
                    {rec.shade_code ? ` · ${rec.shade_code}` : ""}
                  </p>
                  <p className="mt-1 text-sm text-espresso-soft">{rec.product}</p>
                  {reasons.length > 0 && (
                    <ul className="mt-4 space-y-2 text-sm leading-relaxed text-espresso-soft">
                      {reasons.map((reason) => (
                        <li key={reason} className="flex gap-3">
                          <span
                            className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-nude"
                            aria-hidden
                          />
                          <span>{reason}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                  {tip && (
                    <p className="mt-4 border-t border-espresso/8 pt-3 text-[13px] leading-relaxed text-espresso-soft">
                      {tip}
                    </p>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <aside className="rounded-[1.75rem] border border-rose-deep/25 bg-rose/10 px-5 py-5 text-espresso sm:px-6">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-rose-deep">
          Good to know
        </p>
        <ul className="mt-3 space-y-2.5 text-[15px] leading-relaxed text-espresso-soft">
          {guidance.limitations.map((item) => (
            <li key={item} className="flex gap-3">
              <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-deep/80" aria-hidden />
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
