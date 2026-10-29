import Link from "next/link";
import { ShadeWiseLogo } from "./ShadeWiseLogo";

export function SiteFooter() {
  return (
    <footer className="border-t border-espresso/10 bg-cream">
      <div className="page-shell flex flex-col gap-5 py-8 sm:flex-row sm:items-center sm:justify-between sm:gap-10">
        <div>
          <ShadeWiseLogo />
          <p className="mt-2.5 max-w-sm text-sm leading-relaxed text-espresso-soft">
            Guidance for shade mismatches — not a guaranteed match.
          </p>
        </div>
        <nav
          aria-label="Footer"
          className="flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-espresso-soft"
        >
          <Link href="/" className="transition hover:text-espresso">
            Home
          </Link>
          <Link href="/#how-it-works" className="transition hover:text-espresso">
            How it works
          </Link>
          <Link href="/find-your-shade" className="transition hover:text-espresso">
            Find My Shade
          </Link>
        </nav>
      </div>
    </footer>
  );
}
