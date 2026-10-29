import Link from "next/link";

export function ClosingBanner() {
  return (
    <section className="bg-espresso" aria-labelledby="closing-heading">
      <div className="page-shell flex flex-col items-start gap-7 py-14 sm:py-16 lg:flex-row lg:items-end lg:justify-between lg:gap-12">
        <div className="max-w-xl">
          <h2
            id="closing-heading"
            className="text-balance font-display text-4xl leading-tight text-cream sm:text-5xl"
          >
            Makeup should feel like you.
          </h2>
          <p className="mt-4 max-w-md text-[15px] leading-relaxed text-cream/75 sm:text-base">
            Finding your shade shouldn&apos;t feel like a guessing game.
          </p>
        </div>
        <Link href="/find-your-shade" className="btn-on-dark">
          Find My Shade
        </Link>
      </div>
    </section>
  );
}
