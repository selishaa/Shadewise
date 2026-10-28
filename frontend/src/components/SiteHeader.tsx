import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-20 border-b border-espresso/10 bg-cream/85 backdrop-blur-md">
      <div className="mx-auto flex max-w-5xl items-center justify-between gap-4 px-5 py-3.5 sm:px-8 sm:py-4">
        <Link
          href="/"
          className="font-display text-2xl tracking-tight text-espresso transition hover:text-rose-deep"
        >
          ShadeWise
        </Link>
        <nav
          aria-label="Primary"
          className="flex items-center gap-3 text-sm text-espresso-soft sm:gap-6"
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
