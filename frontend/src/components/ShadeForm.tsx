"use client";

import { FormEvent, useState } from "react";
import { ApiError, analyzeShade, getHealth, matchShades } from "@/lib/api";
import { mapJourneyToAnalyzeRequest } from "@/lib/analyzeRequest";
import type { SelectedFoundation } from "@/lib/foundationIdentity";
import {
  buildJourneyGuidance,
  guidanceFromShadeAnalysis,
  type JourneyGuidance,
} from "@/lib/journeyGuidance";
import type {
  MatchDepthFeedback,
  MatchShadeResponse,
  MatchUndertoneIssue,
  WearChange,
} from "@/lib/types";
import { FoundationAutocomplete } from "./find/FoundationAutocomplete";
import { JourneyResults } from "./find/JourneyResults";

const DEPTH_OPTIONS: { value: MatchDepthFeedback; label: string; hint: string }[] = [
  { value: "too_light", label: "Too light", hint: "Looks chalky or pale" },
  { value: "correct", label: "Depth feels right", hint: "Not too light or dark" },
  { value: "too_dark", label: "Too dark", hint: "Looks muddy or deep" },
  { value: "unsure", label: "Not sure", hint: "Hard to tell" },
];

const UNDERTONE_OPTIONS: { value: MatchUndertoneIssue; label: string }[] = [
  { value: "too_warm", label: "Too warm / orange" },
  { value: "too_cool", label: "Too cool / pink" },
  { value: "none", label: "Undertone seems fine" },
  { value: "unsure", label: "Not sure about undertone" },
];

const WEAR_OPTIONS: { value: WearChange; label: string }[] = [
  { value: "yes", label: "Yes — it changes after wear" },
  { value: "no", label: "No — it stays similar" },
  { value: "unsure", label: "Not sure" },
];

const fieldClass =
  "w-full min-h-12 rounded-2xl border border-espresso/12 bg-ivory px-4 py-3.5 text-[15px] text-espresso shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition placeholder:text-espresso/35 focus:border-rose/50 focus:ring-2 focus:ring-rose/25";

function optionClass(selected: boolean) {
  return [
    "flex min-h-12 cursor-pointer items-start gap-3 rounded-2xl border px-4 py-3.5 text-[15px] transition active:scale-[0.99]",
    selected
      ? "border-rose-deep/45 bg-rose/20 shadow-sm ring-1 ring-rose/30"
      : "border-espresso/10 bg-ivory/90 hover:border-nude hover:bg-cream",
  ].join(" ");
}

export function ShadeForm() {
  const [selected, setSelected] = useState<SelectedFoundation | null>(null);
  const [depth, setDepth] = useState<MatchDepthFeedback>("correct");
  const [undertone, setUndertone] = useState<MatchUndertoneIssue>("too_warm");
  const [wear, setWear] = useState<WearChange>("unsure");
  const [description, setDescription] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [guidance, setGuidance] = useState<JourneyGuidance | null>(null);
  const [matchResult, setMatchResult] = useState<MatchShadeResponse | null>(null);

  async function onAnalyze(event: FormEvent) {
    event.preventDefault();
    if (!selected) {
      setError("Search and select your exact foundation shade first.");
      return;
    }
    if (!selected.shade_name && !selected.shade_code) {
      setError("Please choose an exact shade — a brand alone is not enough.");
      return;
    }

    setLoading(true);
    setError(null);
    setGuidance(null);
    setMatchResult(null);

    try {
      const canMatch =
        selected.source === "verified_catalog" && Boolean(selected.verified_catalog_id);

      const matchPromise: Promise<MatchShadeResponse | null> = canMatch
        ? matchShades({
            brand: selected.brand,
            product: selected.product,
            shade_name: selected.shade_name,
            shade_code: selected.shade_code,
            depth_feedback: depth,
            undertone_issue: undertone,
          })
        : Promise.resolve(null);

      const analyzePromise = (async () => {
        let openaiConfigured = false;
        try {
          const health = await getHealth();
          openaiConfigured = health.openai_configured;
        } catch {
          openaiConfigured = false;
        }
        if (!openaiConfigured) return null;

        try {
          return await analyzeShade(
            mapJourneyToAnalyzeRequest({
              foundation: selected,
              depth,
              undertone,
              wear,
              description,
            }),
          );
        } catch (err) {
          // Soft-fail AI: keep rule-based guidance. Surface capacity errors gently.
          if (err instanceof ApiError && err.status === 429) {
            setError(
              "AI analysis is briefly at capacity. Showing guided next steps instead.",
            );
          }
          return null;
        }
      })();

      const [match, ai] = await Promise.all([matchPromise, analyzePromise]);
      setMatchResult(match);

      const rules = buildJourneyGuidance({
        foundation: selected,
        depth,
        undertone,
        wear,
        description,
        matchResult: match,
      });

      if (ai?.analysis) {
        setGuidance(
          guidanceFromShadeAnalysis({
            analysis: ai.analysis,
            matchResult: match,
            canSuggestCandidates: canMatch,
          }),
        );
      } else {
        setGuidance(rules);
      }

      requestAnimationFrame(() => {
        document.getElementById("results")?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "We couldn't complete your shade guidance right now. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-10">
      <div className="space-y-9 rounded-[1.75rem] border border-espresso/10 bg-cream/90 p-5 shadow-soft sm:space-y-10 sm:p-8 md:p-10">
        <div className="border-b border-espresso/8 pb-6">
          <div className="mb-3 flex items-center gap-2" aria-hidden>
            <span className="h-2 w-2 rounded-full bg-[#F3E0D0]" />
            <span className="h-2 w-2 rounded-full bg-[#D9B196]" />
            <span className="h-2 w-2 rounded-full bg-[#B8886C]" />
            <span className="h-2 w-2 rounded-full bg-[#C9A09A]" />
          </div>
          <h2 className="font-display text-3xl text-espresso sm:text-4xl">
            Start with the foundation you wear now
          </h2>
          <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-espresso-soft sm:text-base">
            Type a brand to see suggestions, then choose your product and exact shade. We&apos;ll
            share clear next steps — and nearby shade ideas when we can do so carefully.
          </p>
        </div>

        <section className="space-y-4" aria-labelledby="identify-heading">
          <p
            id="identify-heading"
            className="text-xs font-medium uppercase tracking-[0.18em] text-rose-deep"
          >
            1 · Identify your shade
          </p>
          <FoundationAutocomplete
            selected={selected}
            onSelect={(foundation) => {
              setSelected(foundation);
              setGuidance(null);
              setMatchResult(null);
              setError(null);
            }}
            onClear={() => {
              setSelected(null);
              setGuidance(null);
              setMatchResult(null);
            }}
          />
        </section>

        <form onSubmit={onAnalyze} className="space-y-8" aria-labelledby="feedback-heading">
          <p
            id="feedback-heading"
            className="text-xs font-medium uppercase tracking-[0.18em] text-rose-deep"
          >
            2 · What isn&apos;t working?
          </p>

          <fieldset className="space-y-4">
            <legend className="font-medium text-espresso">How does the depth look?</legend>
            <div className="grid gap-3 sm:grid-cols-2">
              {DEPTH_OPTIONS.map((option) => (
                <label key={option.value} className={optionClass(depth === option.value)}>
                  <input
                    type="radio"
                    name="depth_feedback"
                    value={option.value}
                    checked={depth === option.value}
                    onChange={() => setDepth(option.value)}
                    className="mt-1 accent-rose-deep"
                  />
                  <span>
                    <span className="block font-medium text-espresso">{option.label}</span>
                    <span className="mt-0.5 block text-sm text-espresso-soft">{option.hint}</span>
                  </span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="space-y-4">
            <legend className="font-medium text-espresso">Undertone concern</legend>
            <div className="grid gap-3 sm:grid-cols-2">
              {UNDERTONE_OPTIONS.map((option) => (
                <label key={option.value} className={optionClass(undertone === option.value)}>
                  <input
                    type="radio"
                    name="undertone"
                    value={option.value}
                    checked={undertone === option.value}
                    onChange={() => setUndertone(option.value)}
                    className="mt-1 accent-rose-deep"
                  />
                  <span className="font-medium text-espresso">{option.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <fieldset className="space-y-4">
            <legend className="font-medium text-espresso">Does it change after you wear it?</legend>
            <div className="grid gap-3">
              {WEAR_OPTIONS.map((option) => (
                <label key={option.value} className={optionClass(wear === option.value)}>
                  <input
                    type="radio"
                    name="wear_change"
                    value={option.value}
                    checked={wear === option.value}
                    onChange={() => setWear(option.value)}
                    className="mt-1 accent-rose-deep"
                  />
                  <span className="font-medium text-espresso">{option.label}</span>
                </label>
              ))}
            </div>
          </fieldset>

          <label className="block space-y-2 text-sm">
            <span className="font-medium text-espresso">Anything else we should know?</span>
            <textarea
              className={`${fieldClass} min-h-28 resize-y`}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              placeholder="Example: Looks fine in the store, but turns orange by lunch in daylight."
            />
            <span className="text-xs text-espresso-soft">{description.length}/500</span>
          </label>

          {error && (
            <div
              role="alert"
              className="rounded-2xl border border-rose-deep/35 bg-rose/20 px-4 py-3.5 text-sm leading-relaxed text-espresso"
            >
              {error}
            </div>
          )}

          <div className="flex flex-col gap-3 border-t border-espresso/8 pt-6 sm:flex-row sm:items-center sm:justify-between">
            <p className="max-w-sm text-sm text-espresso-soft">
              Choose your exact shade first — then we&apos;ll walk through what might help.
            </p>
            <button
              type="submit"
              disabled={loading || !selected}
              className="inline-flex min-h-12 w-full items-center justify-center rounded-full bg-espresso px-8 py-3.5 text-sm font-medium text-cream shadow-soft transition hover:bg-espresso-soft active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55 sm:w-auto"
            >
              {loading ? "Preparing your analysis…" : "See my shade analysis"}
            </button>
          </div>
        </form>
      </div>

      {guidance && <JourneyResults guidance={guidance} matchResult={matchResult} />}
    </div>
  );
}
