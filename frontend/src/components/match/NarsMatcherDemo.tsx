"use client";

import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { ApiError, listLiveCatalog, matchShades } from "@/lib/api";
import type {
  LiveCatalogShade,
  MatchDepthFeedback,
  MatchShadeResponse,
  MatchUndertoneIssue,
} from "@/lib/types";

const NARS_BRAND = "NARS";
const NARS_PRODUCT = "Light Reflecting Foundation";

const DEPTH_OPTIONS: { value: MatchDepthFeedback; label: string; hint: string }[] = [
  { value: "correct", label: "Depth feels right", hint: "Not too light or dark" },
  { value: "too_light", label: "Too light", hint: "Looks chalky or pale" },
  { value: "too_dark", label: "Too dark", hint: "Looks muddy or deep" },
  { value: "unsure", label: "Not sure", hint: "Skip depth comparison" },
];

const UNDERTONE_OPTIONS: { value: MatchUndertoneIssue; label: string }[] = [
  { value: "too_warm", label: "Too warm / orange" },
  { value: "too_cool", label: "Too cool / pink" },
  { value: "none", label: "Undertone seems fine" },
  { value: "unsure", label: "Not sure about undertone" },
];

const fieldClass =
  "w-full min-h-12 rounded-2xl border border-espresso/12 bg-ivory px-4 py-3.5 text-[15px] text-espresso shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition focus:border-rose/50 focus:ring-2 focus:ring-rose/25";

function optionClass(selected: boolean) {
  return [
    "flex min-h-12 cursor-pointer items-start gap-3 rounded-2xl border px-4 py-3.5 text-[15px] transition active:scale-[0.99]",
    selected
      ? "border-rose-deep/45 bg-rose/20 shadow-sm ring-1 ring-rose/30"
      : "border-espresso/10 bg-ivory/90 hover:border-nude hover:bg-cream",
  ].join(" ");
}

export function NarsMatcherDemo() {
  const [shades, setShades] = useState<LiveCatalogShade[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [shadeId, setShadeId] = useState("");
  const [depth, setDepth] = useState<MatchDepthFeedback>("correct");
  const [undertone, setUndertone] = useState<MatchUndertoneIssue>("too_warm");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<MatchShadeResponse | null>(null);

  useEffect(() => {
    let cancelled = false;
    listLiveCatalog({ brand: NARS_BRAND, recommendationEligibleOnly: true })
      .then((data) => {
        if (cancelled) return;
        const nars = data.items.filter(
          (item) =>
            item.brand === NARS_BRAND &&
            item.product === NARS_PRODUCT &&
            item.recommendation_eligible,
        );
        setShades(nars);
        if (nars[0]) setShadeId(nars[0].id);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setLoadError(
            err instanceof ApiError ? err.message : "Could not load verified NARS shades.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () => shades.find((s) => s.id === shadeId) ?? null,
    [shades, shadeId],
  );

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!selected) {
      setError("Select a verified NARS shade first.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      // Only live catalog identity — never staged historical discovery ids.
      const response = await matchShades({
        brand: selected.brand,
        product: selected.product,
        shade_name: selected.shade_name,
        shade_code: selected.shade_code,
        depth_feedback: depth,
        undertone_issue: undertone,
      });
      setResult(response);
    } catch (err: unknown) {
      setError(err instanceof ApiError ? err.message : "Matching failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="bg-ivory-wash">
      <section className="border-b border-espresso/10">
        <div className="page-shell section-pad">
          <p className="section-eyebrow">Internal lab</p>
          <h1 className="mt-3 max-w-2xl font-display text-4xl leading-tight text-espresso sm:text-5xl">
            NARS matching sandbox
          </h1>
          <p className="section-body mt-4 max-w-2xl">
            Kept for internal testing of verified NARS suggestions. The customer journey lives on{" "}
            <Link
              href="/find-your-shade"
              className="font-medium text-burgundy underline-offset-2 hover:underline"
            >
              Find My Shade
            </Link>
            . Historical browsing remains in the{" "}
            <Link href="/explore" className="font-medium text-burgundy underline-offset-2 hover:underline">
              shade archive
            </Link>
            .
          </p>
        </div>
      </section>

      <section className="page-shell section-pad pt-10">
        {loadError && (
          <div role="alert" className="mb-6 rounded-2xl border border-burgundy/25 bg-rose/15 px-4 py-4 text-sm">
            {loadError}
          </div>
        )}

        <form onSubmit={onSubmit} className="mx-auto max-w-2xl space-y-8">
          <label className="block">
            <span className="mb-2 block text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
              Current NARS shade
            </span>
            <select
              className={fieldClass}
              value={shadeId}
              onChange={(e) => setShadeId(e.target.value)}
              disabled={shades.length === 0}
              required
            >
              {shades.length === 0 && <option value="">Loading verified shades…</option>}
              {shades.map((shade) => (
                <option key={shade.id} value={shade.id}>
                  {shade.shade_name}
                  {shade.shade_code ? ` (${shade.shade_code})` : ""}
                  {shade.brand_reported_depth ? ` · ${shade.brand_reported_depth}` : ""}
                  {shade.brand_reported_undertone
                    ? ` · ${shade.brand_reported_undertone}`
                    : ""}
                </option>
              ))}
            </select>
            {selected?.metadata_verification_status && (
              <p className="mt-2 text-[12px] text-espresso-soft">
                Live catalog · {selected.metadata_verification_status} · matching accuracy{" "}
                not claimed as proven
              </p>
            )}
          </label>

          <fieldset>
            <legend className="mb-3 text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
              Depth feedback
            </legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {DEPTH_OPTIONS.map((option) => (
                <label key={option.value} className={optionClass(depth === option.value)}>
                  <input
                    type="radio"
                    className="mt-1"
                    name="depth"
                    value={option.value}
                    checked={depth === option.value}
                    onChange={() => setDepth(option.value)}
                  />
                  <span>
                    <span className="block font-medium text-espresso">{option.label}</span>
                    <span className="block text-sm text-espresso-soft">{option.hint}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-3 text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
              Undertone concern
            </legend>
            <div className="grid gap-2 sm:grid-cols-2">
              {UNDERTONE_OPTIONS.map((option) => (
                <label key={option.value} className={optionClass(undertone === option.value)}>
                  <input
                    type="radio"
                    className="mt-1"
                    name="undertone"
                    value={option.value}
                    checked={undertone === option.value}
                    onChange={() => setUndertone(option.value)}
                  />
                  <span className="font-medium text-espresso">{option.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <button type="submit" className="btn-primary" disabled={loading || !selected}>
            {loading ? "Matching…" : "Find nearby NARS shades"}
          </button>
        </form>

        {error && (
          <div role="alert" className="mx-auto mt-8 max-w-2xl rounded-2xl border border-burgundy/25 bg-rose/15 px-4 py-4 text-sm">
            {error}
          </div>
        )}

        {result && (
          <div className="mx-auto mt-10 max-w-2xl space-y-6" aria-live="polite">
            <div>
              <h2 className="font-display text-3xl text-espresso">Matcher response</h2>
              <p className="mt-2 text-sm text-espresso-soft">
                Matched current shade id:{" "}
                {result.matched_current_shade_id ?? "not found in catalog"}
              </p>
            </div>

            {result.no_match_reason && (
              <div className="rounded-2xl border border-espresso/10 bg-cream px-4 py-4 text-sm leading-relaxed text-espresso-soft">
                <strong className="font-medium text-espresso">No match: </strong>
                {result.no_match_reason}
              </div>
            )}

            {result.recommendations.length > 0 && (
              <ul className="space-y-4">
                {result.recommendations.map((rec) => (
                  <li
                    key={rec.catalog_id}
                    className="rounded-[1.35rem] border border-espresso/10 bg-cream/80 p-5 shadow-soft"
                  >
                    <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
                      {rec.brand}
                    </p>
                    <p className="mt-1 font-display text-2xl text-espresso">
                      {rec.shade_name}
                      {rec.shade_code ? ` · ${rec.shade_code}` : ""}
                    </p>
                    <p className="mt-1 text-sm text-espresso-soft">{rec.product}</p>
                    <div className="mt-4 space-y-2 text-sm text-espresso-soft">
                      <p className="font-medium text-espresso">Why selected</p>
                      <ul className="list-disc space-y-1 pl-5">
                        {rec.selection_reasons.map((reason) => (
                          <li key={reason}>{reason}</li>
                        ))}
                      </ul>
                      <p className="font-medium text-espresso">Limitations</p>
                      <ul className="list-disc space-y-1 pl-5">
                        {rec.limitations.map((limit) => (
                          <li key={limit}>{limit}</li>
                        ))}
                      </ul>
                      <p className="text-[12px] leading-relaxed">{rec.evidence_status}</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}

            {result.global_limitations.length > 0 && (
              <div className="rounded-2xl border border-espresso/10 bg-parchment/50 px-4 py-4">
                <p className="text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
                  Global limitations
                </p>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-espresso-soft">
                  {result.global_limitations.map((limit) => (
                    <li key={limit}>{limit}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
