import { ShadeForm } from "@/components/ShadeForm";

export const metadata = {
  title: "Find Your Shade — ShadeWise",
  description:
    "Tell us about your foundation and get friendly guidance on what to try next.",
};

export default function FindYourShadePage() {
  return (
    <div className="mx-auto max-w-3xl px-5 py-10 sm:px-8 sm:py-14">
      <div className="mb-9 sm:mb-11">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-rose-deep">
          Find your shade
        </p>
        <h1 className="mt-3 max-w-2xl text-balance font-display text-3xl leading-tight text-espresso sm:text-5xl">
          Let&apos;s find out why your shade isn&apos;t working.
        </h1>
        <p className="mt-4 max-w-2xl text-[15px] leading-relaxed text-espresso-soft sm:text-base">
          A few quick questions about what you&apos;ve tried — then clear, honest ideas for what
          to look for next.
        </p>
      </div>
      <ShadeForm />
    </div>
  );
}
