"use client";

import { FormEvent, useState } from "react";
import { ApiError, analyzeShade } from "@/lib/api";
import type {
  AnalyzeShadeRequest,
  AnalyzeShadeResponse,
  DepthFeedback,
  UndertoneIssue,
  WearChange,
} from "@/lib/types";
import { ResultsPanel } from "./ResultsPanel";

const BRAND_OPTIONS = [
  "Demo Cosmetics",
  "Other / Not listed",
] as const;

const DEPTH_OPTIONS: { value: DepthFeedback; label: string; hint: string }[] = [
  { value: "too_light", label: "Too light", hint: "Looks chalky or pale" },
  { value: "correct", label: "Depth feels right", hint: "Not too light or dark" },
  { value: "too_dark", label: "Too dark", hint: "Looks muddy or deep" },
  { value: "unsure", label: "Not sure", hint: "Hard to tell" },
];

const UNDERTONE_OPTIONS: { value: UndertoneIssue; label: string }[] = [
  { value: "too_orange", label: "Too orange / golden" },
  { value: "too_pink", label: "Too pink / rosy" },
  { value: "too_yellow", label: "Too yellow" },
  { value: "too_ashy", label: "Too ashy" },
  { value: "too_red", label: "Too red" },
  { value: "looks_gray", label: "Looks gray / muddy" },
  { value: "unsure", label: "Not sure about undertone" },
  { value: "none", label: "Undertone seems fine" },
];

const WEAR_OPTIONS: { value: WearChange; label: string }[] = [
  { value: "yes", label: "Yes — it changes after wear" },
  { value: "no", label: "No — it stays similar" },
  { value: "unsure", label: "Not sure" },
];

const emptyForm: AnalyzeShadeRequest = {
  brand: "Demo Cosmetics",
  product: "",
  shade_name: "",
  depth_feedback: "correct",
  undertone_issues: [],
  description: "",
  wear_change: "unsure",
};

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
  const [form, setForm] = useState<AnalyzeShadeRequest>(emptyForm);
  const [customBrand, setCustomBrand] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeShadeResponse | null>(null);

  function toggleUndertone(issue: UndertoneIssue) {
    setForm((prev) => {
      const exists = prev.undertone_issues.includes(issue);
      const undertone_issues = exists
        ? prev.undertone_issues.filter((item) => item !== issue)
        : [...prev.undertone_issues, issue];
      return { ...prev, undertone_issues };
    });
  }

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    setResult(null);

    const brand =
      form.brand === "Other / Not listed" ? customBrand.trim() || "Other" : form.brand;

    const payload: AnalyzeShadeRequest = {
      ...form,
      brand,
      product: form.product.trim(),
      shade_name: form.shade_name.trim(),
      description: form.description.trim(),
    };

    try {
      const data = await analyzeShade(payload);
      setResult(data);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "We couldn't complete your shade guidance right now. Please try again.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-10">
      <form
        onSubmit={onSubmit}
        className="space-y-9 rounded-[1.75rem] border border-espresso/10 bg-cream/90 p-5 shadow-soft sm:space-y-10 sm:p-8 md:p-10"
        aria-labelledby="shade-form-heading"
      >
        <div className="border-b border-espresso/8 pb-6">
          <div className="mb-3 flex items-center gap-2" aria-hidden>
            <span className="h-2 w-2 rounded-full bg-[#F3E0D0]" />
            <span className="h-2 w-2 rounded-full bg-[#D9B196]" />
            <span className="h-2 w-2 rounded-full bg-[#B8886C]" />
            <span className="h-2 w-2 rounded-full bg-[#C9A09A]" />
          </div>
          <h2 id="shade-form-heading" className="font-display text-3xl text-espresso sm:text-4xl">
            Let&apos;s talk about your foundation.
          </h2>
          <p className="mt-3 max-w-2xl text-[15px] leading-relaxed text-espresso-soft sm:text-base">
            Share what you&apos;re wearing and how it looks on you. We&apos;ll help you understand
            the mismatch — this is guidance, not a guaranteed shade match.
          </p>
        </div>

        <div className="space-y-6">
          <p className="text-xs font-medium uppercase tracking-[0.18em] text-rose-deep">
            Your current foundation
          </p>
          <div className="grid gap-5 sm:grid-cols-2">
            <label className="block space-y-2 text-sm">
              <span className="font-medium text-espresso">Foundation brand</span>
              <select
                className={fieldClass}
                value={form.brand}
                onChange={(e) => setForm({ ...form, brand: e.target.value })}
                required
              >
                {BRAND_OPTIONS.map((brand) => (
                  <option key={brand} value={brand}>
                    {brand}
                  </option>
                ))}
              </select>
            </label>

            {form.brand === "Other / Not listed" && (
              <label className="block space-y-2 text-sm">
                <span className="font-medium text-espresso">Brand name</span>
                <input
                  className={fieldClass}
                  value={customBrand}
                  onChange={(e) => setCustomBrand(e.target.value)}
                  maxLength={80}
                  placeholder="Type the brand"
                  required
                />
              </label>
            )}

            <label className="block space-y-2 text-sm">
              <span className="font-medium text-espresso">Product name</span>
              <input
                className={fieldClass}
                value={form.product}
                onChange={(e) => setForm({ ...form, product: e.target.value })}
                maxLength={120}
                placeholder="e.g. Everyday Soft Matte Foundation"
                required
              />
            </label>

            <label className="block space-y-2 text-sm sm:col-span-2">
              <span className="font-medium text-espresso">Shade name or code</span>
              <input
                className={fieldClass}
                value={form.shade_name}
                onChange={(e) => setForm({ ...form, shade_name: e.target.value })}
                maxLength={80}
                placeholder="e.g. Light 2 Warm"
                required
              />
            </label>
          </div>
        </div>

        <fieldset className="space-y-4">
          <legend className="font-medium text-espresso">How does the depth look?</legend>
          <p className="text-sm text-espresso-soft">Is it too light, too dark, or about right?</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {DEPTH_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={optionClass(form.depth_feedback === option.value)}
              >
                <input
                  type="radio"
                  name="depth_feedback"
                  value={option.value}
                  checked={form.depth_feedback === option.value}
                  onChange={() => setForm({ ...form, depth_feedback: option.value })}
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
          <legend className="font-medium text-espresso">What about the color?</legend>
          <p className="text-sm text-espresso-soft">Select everything that feels true.</p>
          <div className="grid gap-3 sm:grid-cols-2">
            {UNDERTONE_OPTIONS.map((option) => {
              const checked = form.undertone_issues.includes(option.value);
              return (
                <label key={option.value} className={optionClass(checked)}>
                  <input
                    type="checkbox"
                    checked={checked}
                    onChange={() => toggleUndertone(option.value)}
                    className="mt-1 accent-rose-deep"
                  />
                  <span className="font-medium text-espresso">{option.label}</span>
                </label>
              );
            })}
          </div>
        </fieldset>

        <label className="block space-y-2 text-sm">
          <span className="font-medium text-espresso">
            What doesn&apos;t feel right about your shade?
          </span>
          <textarea
            className={`${fieldClass} min-h-32 resize-y`}
            value={form.description}
            onChange={(e) => setForm({ ...form, description: e.target.value })}
            maxLength={500}
            placeholder="Example: It matches my jaw in the store, but turns orange by lunch and looks worse in daylight photos."
          />
          <span className="text-xs text-espresso-soft">{form.description.length}/500</span>
        </label>

        <fieldset className="space-y-4">
          <legend className="font-medium text-espresso">
            Does it change after you wear it?
          </legend>
          <div className="grid gap-3">
            {WEAR_OPTIONS.map((option) => (
              <label
                key={option.value}
                className={optionClass(form.wear_change === option.value)}
              >
                <input
                  type="radio"
                  name="wear_change"
                  value={option.value}
                  checked={form.wear_change === option.value}
                  onChange={() => setForm({ ...form, wear_change: option.value })}
                  className="mt-1 accent-rose-deep"
                />
                <span className="font-medium text-espresso">{option.label}</span>
              </label>
            ))}
          </div>
        </fieldset>

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
            You&apos;ll get ideas to explore next — not a promise of one perfect bottle.
          </p>
          <button
            type="submit"
            disabled={loading}
            className="inline-flex min-h-12 w-full items-center justify-center rounded-full bg-espresso px-8 py-3.5 text-sm font-medium text-cream shadow-soft transition hover:bg-espresso-soft active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55 sm:w-auto"
          >
            {loading ? "Finding guidance…" : "Find My Better Match"}
          </button>
        </div>
      </form>

      {result && <ResultsPanel result={result} />}
    </div>
  );
}
