import type { AnalyzeShadeResponse } from "@/lib/types";

function ListBlock({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <section className="space-y-3">
      <h3 className="font-display text-2xl text-espresso">{title}</h3>
      <ul className="space-y-2.5 text-[15px] leading-relaxed text-espresso-soft">
        {items.map((item) => (
          <li key={item} className="flex gap-3">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-deep" aria-hidden />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function friendlyDepth(value: string): string {
  const map: Record<string, string> = {
    matches: "Looks about right",
    too_light: "Feels too light",
    too_dark: "Feels too dark",
    unclear: "Hard to tell",
  };
  return map[value] ?? value.replaceAll("_", " ");
}

function friendlyWear(value: string): string {
  const map: Record<string, string> = {
    yes: "Changes after wear",
    no: "Stays similar",
    unsure: "Not sure",
  };
  return map[value] ?? value;
}

export function ResultsPanel({ result }: { result: AnalyzeShadeResponse }) {
  const { analysis, guidance, catalog_hints, prompt_version } = result;

  return (
    <div
      id="results"
      className="space-y-8 scroll-mt-8"
      aria-live="polite"
      aria-label="Shade guidance results"
    >
      <div className="rounded-[1.75rem] border border-espresso/10 bg-cream/95 p-5 shadow-soft sm:p-8">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-rose-deep">
          Your shade story
        </p>
        <h2 className="mt-2 font-display text-3xl text-espresso sm:text-4xl">
          Here&apos;s what we heard
        </h2>
        <p className="mt-4 max-w-3xl text-base leading-relaxed text-espresso-soft sm:text-lg">
          {analysis.summary}
        </p>

        <div className="mt-6 grid gap-3 text-sm sm:grid-cols-3">
          <div className="rounded-2xl bg-mist px-4 py-3.5">
            <p className="text-xs uppercase tracking-wide text-espresso-soft">Depth</p>
            <p className="mt-1 font-medium text-espresso">
              {friendlyDepth(analysis.reported_depth_match)}
            </p>
          </div>
          <div className="rounded-2xl bg-mist px-4 py-3.5">
            <p className="text-xs uppercase tracking-wide text-espresso-soft">Color notes</p>
            <p className="mt-1 font-medium text-espresso">
              {analysis.reported_color_issues.length
                ? analysis.reported_color_issues.join(", ")
                : "None highlighted"}
            </p>
          </div>
          <div className="rounded-2xl bg-mist px-4 py-3.5">
            <p className="text-xs uppercase tracking-wide text-espresso-soft">After wear</p>
            <p className="mt-1 font-medium text-espresso">
              {friendlyWear(analysis.reported_wear_change)}
            </p>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
        <div className="space-y-8 rounded-[1.75rem] border border-espresso/10 bg-ivory/90 p-5 sm:p-8">
          <ListBlock title="What might be going on" items={analysis.possible_explanations} />
          <ListBlock
            title="Undertone directions to explore"
            items={analysis.undertone_adjustments_to_try}
          />
        </div>
        <div className="space-y-8 rounded-[1.75rem] border border-espresso/10 bg-ivory/90 p-5 sm:p-8">
          <ListBlock title="What to try next" items={analysis.suggested_next_steps} />
          <ListBlock title="What we can't know yet" items={analysis.uncertainties} />
        </div>
      </div>

      <aside className="rounded-[1.75rem] border border-rose-deep/30 bg-rose/15 px-5 py-5 text-espresso sm:px-6">
        <p className="text-xs font-medium uppercase tracking-[0.18em] text-rose-deep">
          Guidance, not a guarantee
        </p>
        <p className="mt-2 text-[15px] leading-relaxed">{analysis.analysis_vs_recommendation_note}</p>
      </aside>

      <section className="space-y-4">
        <h3 className="font-display text-2xl text-espresso">Helpful next tips</h3>
        <p className="max-w-2xl text-sm text-espresso-soft">
          Practical ideas based on what you shared — not invented product matches.
        </p>
        <ul className="space-y-4">
          {guidance.map((item) => (
            <li key={item.title} className="border-b border-espresso/10 pb-4 last:border-0">
              <p className="font-medium text-espresso">{item.title}</p>
              <p className="mt-1 text-sm leading-relaxed text-espresso-soft">{item.detail}</p>
            </li>
          ))}
        </ul>
      </section>

      {catalog_hints.length > 0 && (
        <section className="space-y-4 rounded-[1.75rem] border border-dashed border-nude bg-mist/70 p-5 sm:p-6">
          <div>
            <h3 className="font-display text-2xl text-espresso">Sample shade labels</h3>
            <p className="mt-2 max-w-2xl text-sm leading-relaxed text-espresso-soft">
              Demo examples only — to show how shade families can be labeled. These are{" "}
              <strong className="font-medium text-espresso">not</strong> verified recommendations
              for your skin.
            </p>
          </div>
          <ul className="grid gap-3 sm:grid-cols-3 sm:gap-4">
            {catalog_hints.map((product) => (
              <li key={product.id} className="rounded-2xl bg-cream/90 px-4 py-4 text-sm">
                <p className="text-xs uppercase tracking-wide text-rose-deep">demo example</p>
                <p className="mt-2 font-medium text-espresso">{product.shade_name}</p>
                <p className="text-espresso-soft">
                  {product.brand} · {product.product}
                </p>
                <p className="mt-2 text-xs text-espresso-soft">
                  {product.depth_family} · {product.undertone_family}
                </p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <p className="text-xs text-espresso-soft/80">ShadeWise guidance · {prompt_version}</p>
    </div>
  );
}
