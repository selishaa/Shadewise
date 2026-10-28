import Image from "next/image";

/**
 * Editorial hero collage.
 * Swap files in /public/hero/ to refresh portraits — keep the same filenames
 * or update the `src` paths below.
 */
const portraits = [
  {
    src: "/hero/portrait-fair.jpg",
    alt: "Beauty portrait of a woman with a fair complexion and soft natural makeup",
    slot: "fair" as const,
  },
  {
    src: "/hero/portrait-medium.jpg",
    alt: "Beauty portrait of a woman with a medium-deep complexion and luminous skin",
    slot: "medium" as const,
  },
  {
    src: "/hero/portrait-tan.jpg",
    alt: "Beauty portrait of a woman with a tan complexion and dewy makeup finish",
    slot: "tan" as const,
  },
  {
    src: "/hero/portrait-deep.jpg",
    alt: "Beauty portrait of a woman with a deep complexion and radiant natural makeup",
    slot: "deep" as const,
  },
] as const;

function Portrait({
  src,
  alt,
  priority = false,
  sizes,
  className,
  objectPosition = "center 20%",
}: {
  src: string;
  alt: string;
  priority?: boolean;
  sizes: string;
  className?: string;
  objectPosition?: string;
}) {
  return (
    <div className={`relative overflow-hidden bg-mist ${className ?? ""}`}>
      <Image
        src={src}
        alt={alt}
        fill
        priority={priority}
        sizes={sizes}
        className="object-cover"
        style={{ objectPosition }}
      />
    </div>
  );
}

export function HeroPortraitCollage() {
  const fair = portraits[0];
  const medium = portraits[1];
  const tan = portraits[2];
  const deep = portraits[3];

  return (
    <figure className="relative w-full" aria-label="Editorial beauty portraits across a range of skin tones">
      {/* Desktop / tablet: asymmetric editorial collage */}
      <div className="hidden gap-2.5 sm:grid sm:grid-cols-12 sm:grid-rows-[minmax(0,1fr)_minmax(0,1fr)] sm:h-[min(520px,68vh)] lg:h-[540px]">
        <Portrait
          src={fair.src}
          alt={fair.alt}
          priority
          sizes="(max-width: 1024px) 55vw, 420px"
          objectPosition="center 18%"
          className="col-span-7 row-span-2"
        />
        <Portrait
          src={medium.src}
          alt={medium.alt}
          priority
          sizes="(max-width: 1024px) 40vw, 280px"
          objectPosition="center 15%"
          className="col-span-5 row-span-1"
        />
        <div className="col-span-5 row-span-1 grid grid-cols-2 gap-2.5">
          <Portrait
            src={tan.src}
            alt={tan.alt}
            sizes="(max-width: 1024px) 20vw, 140px"
            objectPosition="center 22%"
          />
          <Portrait
            src={deep.src}
            alt={deep.alt}
            sizes="(max-width: 1024px) 20vw, 140px"
            objectPosition="center 18%"
          />
        </div>
      </div>

      {/* Mobile: stacked asymmetric mosaic — not a flat equal grid */}
      <div className="grid grid-cols-6 grid-rows-[auto] gap-2 sm:hidden">
        <Portrait
          src={fair.src}
          alt={fair.alt}
          priority
          sizes="100vw"
          objectPosition="center 18%"
          className="col-span-6 aspect-[5/4]"
        />
        <Portrait
          src={medium.src}
          alt={medium.alt}
          sizes="50vw"
          objectPosition="center 15%"
          className="col-span-3 aspect-[3/4]"
        />
        <Portrait
          src={deep.src}
          alt={deep.alt}
          sizes="50vw"
          objectPosition="center 18%"
          className="col-span-3 aspect-[3/4]"
        />
        <Portrait
          src={tan.src}
          alt={tan.alt}
          sizes="100vw"
          objectPosition="center 20%"
          className="col-span-6 aspect-[16/10]"
        />
      </div>

      <figcaption className="sr-only">
        Four luxury beauty portraits featuring fair, medium, tan, and deep complexions.
      </figcaption>
    </figure>
  );
}
