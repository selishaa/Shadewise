import Image from "next/image";

/**
 * Compact equal frames. object-contain = full photo visible, no crop.
 * Fixed height keeps both cards aligned and smaller on the page.
 */
const cards = [
  {
    title: "Right depth. Wrong undertone.",
    detail:
      "A foundation can look too orange, pink, or yellow — even when the depth feels correct.",
    src: "/landing/struggle-undertone.jpg",
    alt: "Close-up beauty portrait highlighting natural skin and foundation finish",
  },
  {
    title: "Looks different in real life?",
    detail:
      "Online swatches and store lighting can make shopping for the right shade feel confusing.",
    src: "/landing/struggle-wear.jpg",
    alt: "Beauty portrait with soft lighting that can look different across settings",
  },
] as const;

export function ShadeStruggle() {
  return (
    <section
      className="border-b border-espresso/10 bg-cream/50"
      aria-labelledby="shade-struggle-heading"
    >
      <div className="page-shell section-pad">
        <div className="mx-auto max-w-4xl text-center sm:text-left">
          <p className="section-eyebrow">The shade struggle</p>
          <h2 id="shade-struggle-heading" className="section-title mt-3">
            Because finding your shade shouldn&apos;t be this hard.
          </h2>
        </div>

        <ul className="mx-auto mt-8 grid max-w-4xl gap-6 sm:mt-9 sm:grid-cols-2 sm:gap-7">
          {cards.map((card) => (
            <li key={card.title} className="group">
              <article className="flex flex-col">
                {/* Same frame for both — slightly larger, still compact, never cropped */}
                <div className="relative h-56 w-full overflow-hidden border border-espresso/10 bg-parchment/60 sm:h-64">
                  <Image
                    src={card.src}
                    alt={card.alt}
                    fill
                    sizes="(max-width: 640px) 90vw, 360px"
                    className="editorial-photo object-contain object-center p-2 transition duration-500 ease-out group-hover:opacity-95"
                  />
                </div>
                <div className="mt-3 space-y-1 border-t border-espresso/10 pt-3">
                  <h3 className="font-display text-lg leading-snug text-espresso sm:text-xl">
                    {card.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-espresso-soft">{card.detail}</p>
                </div>
              </article>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
