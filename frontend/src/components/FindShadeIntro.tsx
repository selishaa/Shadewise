import Image from "next/image";

/** Page header + one quiet portrait — kept separate from the flatlay below. */
export function FindShadeIntro() {
  return (
    <header className="border-b border-espresso/10">
      <div className="page-shell section-pad">
        <div className="grid items-center gap-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.55fr)] lg:gap-16">
          <div className="max-w-xl">
            <p className="section-eyebrow">Find your shade</p>
            <h1 className="mt-3 text-balance font-display text-3xl leading-tight text-espresso sm:text-5xl">
              Let&apos;s find out why your shade isn&apos;t working.
            </h1>
            <p className="mt-4 text-[15px] leading-relaxed text-espresso-soft sm:text-base">
              Search the foundation you wear, tell us what feels off, and get a clear, honest read
              on what to try next — including shade ideas when we can suggest them carefully.
            </p>
            <p className="mt-6 border-l border-burgundy/50 pl-4 font-display text-xl leading-snug text-espresso-soft">
              A quiet consultation — not a checkout counter.
            </p>
          </div>

          <figure className="mx-auto w-full max-w-[240px] overflow-hidden border border-espresso/10 bg-mist lg:mx-0 lg:justify-self-end">
            <Image
              src="/find/editorial-portrait.jpg"
              alt="Close beauty portrait with luminous natural makeup"
              width={603}
              height={600}
              sizes="240px"
              className="editorial-photo h-auto w-full"
              priority
            />
          </figure>
        </div>
      </div>
    </header>
  );
}
