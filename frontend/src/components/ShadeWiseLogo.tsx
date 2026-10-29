import Link from "next/link";

type ShadeWiseLogoProps = {
  href?: string;
  withWordmark?: boolean;
  className?: string;
};

/**
 * ShadeWise logo — bold "S" swatch ribbon in a soft disc + display wordmark.
 */
export function ShadeWiseLogo({
  href = "/",
  withWordmark = true,
  className = "",
}: ShadeWiseLogoProps) {
  const mark = (
    <span className={`inline-flex items-center gap-3 ${className}`}>
      <svg
        width="44"
        height="44"
        viewBox="0 0 80 80"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        aria-hidden={withWordmark}
        role={withWordmark ? "presentation" : "img"}
        className="shrink-0"
      >
        {!withWordmark && <title>ShadeWise</title>}
        <circle cx="40" cy="40" r="38" fill="#F7F1E8" />
        <circle
          cx="40"
          cy="40"
          r="38"
          stroke="#2C1810"
          strokeWidth="1.25"
          strokeOpacity="0.12"
        />
        <path
          d="M52 26.5c-2.2-3.8-7.2-6.2-13.2-6.2-8.6 0-14.2 4.2-14.2 10.4 0 5.4 3.8 8.2 12.4 10.2l3.2.75c5.6 1.3 7.6 2.9 7.6 5.8 0 3.6-3.5 5.9-9.2 5.9-5.2 0-9.1-2-11.4-5.4"
          stroke="#2C1810"
          strokeWidth="5.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M52 26.5c-2.2-3.8-7.2-6.2-13.2-6.2-8.6 0-14.2 4.2-14.2 10.4 0 5.4 3.8 8.2 12.4 10.2l3.2.75c5.6 1.3 7.6 2.9 7.6 5.8 0 3.6-3.5 5.9-9.2 5.9-5.2 0-9.1-2-11.4-5.4"
          stroke="#C9A09A"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {withWordmark && (
        <span className="font-display text-[1.75rem] leading-none tracking-tight text-espresso sm:text-3xl">
          ShadeWise
        </span>
      )}
    </span>
  );

  if (!href) return mark;

  return (
    <Link
      href={href}
      className="inline-flex items-center transition hover:opacity-80"
      aria-label="ShadeWise home"
    >
      {mark}
    </Link>
  );
}
