"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";

type PreviewChoice = "orange" | "ashy" | "dark";

const options: { id: PreviewChoice; label: string; explanation: string }[] = [
  {
    id: "orange",
    label: "My foundation looks too orange",
    explanation:
      "Your foundation might be too warm for your complexion, even if the depth looks right.",
  },
  {
    id: "ashy",
    label: "My foundation looks gray or ashy",
    explanation:
      "A gray or ashy appearance can have several causes, including differences in shade depth or undertone.",
  },
  {
    id: "dark",
    label: "My foundation looks too dark",
    explanation:
      "You may need to explore a lighter shade while checking that the undertone still works for you.",
  },
];

export function ShadePreview() {
  const [selected, setSelected] = useState<PreviewChoice>("orange");
  const active = options.find((option) => option.id === selected) ?? options[0];

  return (
    <section
      className="border-b border-espresso/10 bg-ivory"
      aria-labelledby="shade-preview-heading"
    >
      <div className="page-shell section-pad">
        {/* Title row */}
        <div className="max-w-2xl">
          <p className="section-eyebrow">Quick preview</p>
          <h2 id="shade-preview-heading" className="section-title mt-3">
            Let&apos;s talk about your shade.
          </h2>
          <p className="section-body mt-3">
            Sometimes the smallest color difference makes the biggest difference.
          </p>
          <p className="mt-2 text-sm text-espresso-soft/85">
            Educational preview only — not a personalized diagnosis.
          </p>
        </div>

        {/* Full landscape photo + interaction — sized to show the whole image */}
        <div className="mt-8 grid items-stretch gap-6 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,0.75fr)] lg:gap-8">
          <figure className="overflow-hidden border border-espresso/10 bg-mist">
            <Image
              src="/landing/preview-editorial.jpg"
              alt="Editorial beauty portrait for shade guidance"
              width={1024}
              height={682}
              sizes="(max-width: 1024px) 100vw, 640px"
              className="editorial-photo h-auto w-full"
            />
            <figcaption className="border-t border-espresso/10 bg-cream/90 px-4 py-3.5 sm:px-5">
              <p className="font-display text-lg text-espresso sm:text-xl">
                Perfect at first. Different later.
              </p>
              <p className="mt-1 text-sm leading-relaxed text-espresso-soft">
                Some foundations shift after they dry down or after a few hours of wear.
              </p>
            </figcaption>
          </figure>

          <div className="flex flex-col border border-espresso/10 bg-cream/90 p-5 sm:p-6">
            <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-burgundy">
              What are you noticing?
            </p>

            <fieldset className="mt-4">
              <legend className="sr-only">What does your foundation look like?</legend>
              <div className="space-y-2.5" role="radiogroup" aria-label="Shade concern">
                {options.map((option) => {
                  const isActive = selected === option.id;
                  return (
                    <label
                      key={option.id}
                      className={[
                        "flex min-h-12 cursor-pointer items-center gap-3 border px-4 py-3.5 text-sm transition sm:text-[15px]",
                        isActive
                          ? "border-burgundy/45 bg-burgundy/[0.07] text-espresso"
                          : "border-espresso/10 bg-ivory text-espresso-soft hover:border-nude hover:text-espresso",
                      ].join(" ")}
                    >
                      <input
                        type="radio"
                        name="shade-preview"
                        value={option.id}
                        checked={isActive}
                        onChange={() => setSelected(option.id)}
                        className="accent-burgundy"
                      />
                      <span className="font-medium leading-snug">{option.label}</span>
                    </label>
                  );
                })}
              </div>
            </fieldset>

            <div
              className="mt-6 border-t border-espresso/10 pt-5 lg:mt-auto"
              aria-live="polite"
              key={active.id}
            >
              <p className="text-[11px] font-medium uppercase tracking-[0.2em] text-burgundy">
                What this can mean
              </p>
              <p className="mt-3 font-display text-xl leading-snug text-espresso sm:text-2xl">
                {active.explanation}
              </p>
              <Link href="/find-your-shade" className="btn-primary mt-6">
                Explore My Shade
              </Link>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
