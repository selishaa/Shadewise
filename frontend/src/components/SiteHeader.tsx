import Link from "next/link";
import { ShadeWiseLogo } from "./ShadeWiseLogo";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-20 border-b border-espresso/10 bg-cream/85 backdrop-blur-md">
      <div className="page-shell flex items-center justify-between gap-4 py-3 sm:py-3.5">
        <ShadeWiseLogo />
        <nav
          aria-label="Primary"
          className="flex flex-wrap items-center justify-end gap-x-3 gap-y-1 text-sm text-espresso-soft sm:gap-x-5"
        >
          <Link
            href="/#how-it-works"
            className="hidden min-h-10 items-center sm:inline-flex hover:text-espresso"
          >
            How it works
          </Link>
          <Link
            href="/find-your-shade"
            className="inline-flex min-h-10 items-center rounded-full bg-espresso px-4 py-2 text-cream transition hover:bg-espresso-soft active:scale-[0.98]"
          >
            Find My Shade
          </Link>
        </nav>
      </div>
    </header>
  );
}
