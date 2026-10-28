import Link from "next/link";
import { HeroPortraitCollage } from "@/components/HeroPortraitCollage";

const steps = [
  {
    title: "Tell us your shade",
    detail: "Share the foundation you currently use.",
  },
  {
    title: "What's not working?",
    detail:
      "Tell us if the color looks too warm, too cool, too light, too dark, or changes after wear.",
  },
  {
    title: "Get personalized guidance",
    detail:
      "Understand possible reasons for the mismatch and what to explore next.",
  },
];

const frustrations = [
  "Looks right in depth, but the undertone feels off",
  "Different brands, totally different shade names",
  "Online swatches that don't match real life",
  "A foundation that changes after a few hours",
];

export default function HomePage() {
  return (
    <>
      <section className="relative overflow-hidden border-b border-espresso/10">
        <div className="relative mx-auto max-w-6xl px-5 py-10 sm:px-8 sm:py-14 lg:py-16">
          <div className="grid items-center gap-9 lg:grid-cols-[minmax(0,0.92fr)_minmax(0,1.08fr)] lg:gap-12 xl:gap-16">
            <div className="order-2 max-w-xl lg:order-1">
              <p className="text-[11px] font-medium uppercase tracking-[0.28em] text-burgundy">
                Beauty in every shade
              </p>
              <p className="mt-4 font-display text-4xl leading-none tracking-tight text-espresso sm:text-5xl">
                ShadeWise
              </p>
              <h1 className="mt-4 text-balance font-display text-3xl leading-[1.15] text-espresso sm:text-4xl lg:text-[2.75rem]">
                Your shade exists. Let&apos;s find it.
              </h1>
              <p className="mt-5 max-w-md text-[15px] leading-relaxed text-espresso-soft sm:text-base">
                Too orange? Too pink? Perfect in the store, but different at home? Tell us what
                you&apos;ve tried, and let&apos;s get one step closer to your perfect match.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
                <Link
                  href="/find-your-shade"
                  className="inline-flex min-h-12 items-center justify-center rounded-full bg-espresso px-7 py-3.5 text-sm font-medium text-cream transition hover:bg-espresso-soft active:scale-[0.98]"
                >
                  Find My Shade
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex min-h-12 items-center justify-center px-2 text-sm font-medium text-espresso-soft underline-offset-4 transition hover:text-espresso hover:underline"
                >
                  How it works
                </a>
              </div>
            </div>

            <div className="order-1 lg:order-2">
              <HeroPortraitCollage />
            </div>
          </div>
        </div>
      </section>

      <section className="bg-cream/55">
        <div className="mx-auto max-w-5xl px-5 py-14 sm:px-8 sm:py-20">
          <h2 className="max-w-2xl text-balance font-display text-3xl text-espresso sm:text-4xl">
            Because finding your shade shouldn&apos;t be this hard.
          </h2>
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-espresso-soft sm:text-lg">
            Store lighting can trick you. Phone photos can too. And a shade that looked perfect at
            noon might look different by dinner. ShadeWise helps you sort out what&apos;s going
            wrong — so your next try feels more intentional.
          </p>
          <ul className="mt-10 grid gap-5 sm:grid-cols-2 sm:gap-6">
            {frustrations.map((item) => (
              <li
                key={item}
                className="border-l-2 border-burgundy/70 pl-4 text-[15px] leading-snug text-espresso sm:text-base"
              >
                {item}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section id="how-it-works" className="scroll-mt-24 border-t border-espresso/10">
        <div className="mx-auto max-w-5xl px-5 py-14 sm:px-8 sm:py-20">
          <h2 className="font-display text-3xl text-espresso sm:text-4xl">How it works</h2>
          <p className="mt-3 max-w-xl text-espresso-soft">
            Three simple steps. Honest guidance. No pressure.
          </p>
          <ol className="mt-10 grid gap-8 sm:gap-10 md:grid-cols-3">
            {steps.map((step, index) => (
              <li key={step.title} className="space-y-3">
                <p className="text-xs font-medium uppercase tracking-[0.2em] text-burgundy">
                  Step {index + 1}
                </p>
                <h3 className="font-display text-2xl text-espresso">{step.title}</h3>
                <p className="text-[15px] leading-relaxed text-espresso-soft">{step.detail}</p>
              </li>
            ))}
          </ol>
          <div className="mt-12">
            <Link
              href="/find-your-shade"
              className="inline-flex min-h-12 items-center justify-center rounded-full bg-espresso px-7 py-3.5 text-sm font-medium text-cream transition hover:bg-espresso-soft active:scale-[0.98]"
            >
              Find My Shade
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
