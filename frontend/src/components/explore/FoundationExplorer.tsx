"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { ApiError, discoverBrands, discoverShades } from "@/lib/api";
import type { DiscoveryBrandCount, DiscoverySearchResponse, DiscoveryShadeItem } from "@/lib/types";
import { ShadeDetailPanel } from "./ShadeDetailPanel";
import { ShadeResultCard } from "./ShadeResultCard";

const PAGE_SIZE = 12;
const fieldClass =
  "w-full min-h-12 rounded-2xl border border-espresso/12 bg-ivory px-4 py-3.5 text-[15px] text-espresso shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition placeholder:text-espresso/35 focus:border-rose/50 focus:ring-2 focus:ring-rose/25";

export function FoundationExplorer() {
  const [queryInput, setQueryInput] = useState("");
  const [activeQuery, setActiveQuery] = useState("");
  const [brand, setBrand] = useState("");
  const [page, setPage] = useState(1);
  const [brands, setBrands] = useState<DiscoveryBrandCount[]>([]);
  const [brandsError, setBrandsError] = useState<string | null>(null);
  const [result, setResult] = useState<DiscoverySearchResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<DiscoveryShadeItem | null>(null);

  useEffect(() => {
    let cancelled = false;
    discoverBrands(200)
      .then((data) => {
        if (!cancelled) {
          setBrands(data.items);
          setBrandsError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setBrandsError(
            err instanceof ApiError ? err.message : "Could not load brand list.",
          );
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const loadPage = useCallback(async (nextPage: number, q: string, brandFilter: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await discoverShades({
        q: q || undefined,
        brand: brandFilter || undefined,
        page: nextPage,
        pageSize: PAGE_SIZE,
      });
      setResult(data);
      setPage(nextPage);
    } catch (err: unknown) {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Search failed.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadPage(1, activeQuery, brand);
  }, [activeQuery, brand, loadPage]);

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    setActiveQuery(queryInput.trim());
  }

  const totalPages = result?.total_pages ?? 0;
  const totalMatches = result?.total_matches ?? 0;

  return (
    <div className="bg-ivory-wash">
      <section className="border-b border-espresso/10">
        <div className="page-shell section-pad">
          <p className="section-eyebrow">Foundation Explorer</p>
          <h1 className="mt-3 max-w-2xl font-display text-4xl leading-tight text-espresso sm:text-5xl">
            Browse thousands of historical foundation shades
          </h1>
          <p className="section-body mt-4 max-w-2xl">
            Browse a research archive of historical retailer listings. These records help with
            identification only — not verified recommendations. For the full guided experience,
            start with{" "}
            <Link
              href="/find-your-shade"
              className="font-medium text-burgundy underline-offset-2 hover:underline"
            >
              Find My Shade
            </Link>
            .
          </p>

          <form
            onSubmit={onSubmit}
            className="mt-8 grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end lg:grid-cols-[minmax(0,1.4fr)_minmax(0,0.9fr)_auto]"
          >
            <label className="block">
              <span className="mb-2 block text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
                Search
              </span>
              <input
                type="search"
                value={queryInput}
                onChange={(e) => setQueryInput(e.target.value)}
                placeholder="Brand, product, shade name, or code"
                className={fieldClass}
                autoComplete="off"
              />
            </label>
            <label className="block">
              <span className="mb-2 block text-[11px] font-medium uppercase tracking-[0.22em] text-burgundy">
                Brand
              </span>
              <select
                value={brand}
                onChange={(e) => setBrand(e.target.value)}
                className={fieldClass}
                aria-describedby={brandsError ? "brands-error" : undefined}
              >
                <option value="">All brands</option>
                {brands.map((b) => (
                  <option key={b.brand} value={b.brand}>
                    {b.brand} ({b.shade_count})
                  </option>
                ))}
              </select>
            </label>
            <button type="submit" className="btn-primary w-full sm:w-auto">
              Search
            </button>
          </form>
          {brandsError && (
            <p id="brands-error" className="mt-3 text-sm text-burgundy" role="status">
              Brand list unavailable: {brandsError}
            </p>
          )}
        </div>
      </section>

      <section className="page-shell section-pad pt-10">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h2 className="font-display text-2xl text-espresso sm:text-3xl">Results</h2>
            <p className="mt-1 text-sm text-espresso-soft" aria-live="polite">
              {loading
                ? "Loading…"
                : error
                  ? " "
                  : `${totalMatches.toLocaleString()} historical match${totalMatches === 1 ? "" : "es"}`}
            </p>
          </div>
          {result && (
            <p className="max-w-md text-right text-[12px] leading-relaxed text-espresso-soft">
              Approximate swatches are uncalibrated digital previews — never treat them as true
              color.
            </p>
          )}
        </div>

        {error && (
          <div
            role="alert"
            className="mt-6 rounded-2xl border border-burgundy/25 bg-rose/15 px-4 py-4 text-sm leading-relaxed text-espresso"
          >
            {error}
          </div>
        )}

        {loading && (
          <div
            className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
            aria-busy="true"
            aria-label="Loading foundation results"
          >
            {Array.from({ length: 6 }).map((_, index) => (
              <div
                key={index}
                className="h-40 animate-pulse rounded-[1.35rem] border border-espresso/8 bg-parchment/80"
              />
            ))}
          </div>
        )}

        {!loading && !error && result && result.items.length === 0 && (
          <div className="mt-10 rounded-[1.5rem] border border-dashed border-espresso/15 bg-cream/60 px-6 py-12 text-center">
            <p className="font-display text-2xl text-espresso">No shades matched</p>
            <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-espresso-soft">
              Try a broader search, clear the brand filter, or browse another brand from the list.
            </p>
          </div>
        )}

        {!loading && !error && result && result.items.length > 0 && (
          <>
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {result.items.map((item) => (
                <ShadeResultCard key={item.id} item={item} onSelect={setSelected} />
              ))}
            </div>

            <nav
              className="mt-10 flex flex-wrap items-center justify-between gap-4 border-t border-espresso/10 pt-6"
              aria-label="Results pagination"
            >
              <p className="text-sm text-espresso-soft">
                Page {page} of {Math.max(totalPages, 1)}
              </p>
              <div className="flex gap-3">
                <button
                  type="button"
                  className="inline-flex min-h-11 items-center rounded-full border border-espresso/15 px-5 text-sm text-espresso transition hover:border-espresso/30 disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={page <= 1 || loading}
                  onClick={() => void loadPage(page - 1, activeQuery, brand)}
                >
                  Previous
                </button>
                <button
                  type="button"
                  className="inline-flex min-h-11 items-center rounded-full border border-espresso/15 px-5 text-sm text-espresso transition hover:border-espresso/30 disabled:cursor-not-allowed disabled:opacity-40"
                  disabled={page >= totalPages || loading}
                  onClick={() => void loadPage(page + 1, activeQuery, brand)}
                >
                  Next
                </button>
              </div>
            </nav>

            {result.disclaimer && (
              <p className="mt-8 text-[12px] leading-relaxed text-espresso-soft">{result.disclaimer}</p>
            )}
          </>
        )}
      </section>

      <ShadeDetailPanel item={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
