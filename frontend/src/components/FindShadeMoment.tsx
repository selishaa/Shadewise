import Image from "next/image";

/** Separate editorial moment — flatlay sits away from the portrait above. */
export function FindShadeMoment() {
  return (
    <aside className="border-b border-espresso/10 bg-cream/50" aria-label="Inspiration">
      <div className="page-shell py-10 sm:py-12">
        <div className="mx-auto max-w-2xl">
          <p className="section-eyebrow text-center">The ritual</p>
          <figure className="mt-5 overflow-hidden border border-espresso/10 bg-mist">
            <Image
              src="/find/editorial-wide.jpg"
              alt="Soft beauty flatlay with foundation and makeup tools"
              width={1024}
              height={674}
              sizes="(max-width: 768px) 100vw, 672px"
              className="editorial-photo h-auto w-full"
            />
          </figure>
          <p className="mt-4 text-center font-display text-lg text-espresso-soft sm:text-xl">
            Your shade exists. We&apos;ll help you recognize it.
          </p>
        </div>
      </div>
    </aside>
  );
}
