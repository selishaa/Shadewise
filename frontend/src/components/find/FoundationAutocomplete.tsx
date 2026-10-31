"use client";

import {
  KeyboardEvent,
  useCallback,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
} from "react";
import {
  ApiError,
  discoverProducts,
  discoverShades,
  discoverSuggest,
  listLiveCatalog,
} from "@/lib/api";
import { shadeDisplayName } from "@/lib/discoverFormat";
import {
  displayShadeLabel,
  findVerifiedCatalogTwin,
  selectionFromHistorical,
  selectionFromVerified,
  type SelectedFoundation,
} from "@/lib/foundationIdentity";
import type {
  DiscoveryProductCount,
  DiscoveryShadeItem,
  LiveCatalogShade,
} from "@/lib/types";

const fieldClass =
  "w-full min-h-12 rounded-2xl border border-espresso/12 bg-ivory px-4 py-3.5 text-[15px] text-espresso shadow-[inset_0_1px_0_rgba(255,255,255,0.6)] outline-none transition placeholder:text-espresso/35 focus:border-rose/50 focus:ring-2 focus:ring-rose/25";

type Step = "query" | "product" | "shade";

type Option =
  | { id: string; kind: "verified_shade"; label: string; detail: string; live: LiveCatalogShade }
  | { id: string; kind: "brand"; label: string; detail: string; brand: string }
  | { id: string; kind: "product"; label: string; detail: string; brand: string; product: string }
  | {
      id: string;
      kind: "historical_shade";
      label: string;
      detail: string;
      item: DiscoveryShadeItem;
      twin: LiveCatalogShade | null;
    };

type Props = {
  selected: SelectedFoundation | null;
  onSelect: (foundation: SelectedFoundation) => void;
  onClear: () => void;
};

export function FoundationAutocomplete({ selected, onSelect, onClear }: Props) {
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [query, setQuery] = useState("");
  const [step, setStep] = useState<Step>("query");
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [options, setOptions] = useState<Option[]>([]);
  const [activeIndex, setActiveIndex] = useState(0);
  const [liveCatalog, setLiveCatalog] = useState<LiveCatalogShade[]>([]);
  const [pickedBrand, setPickedBrand] = useState<string | null>(null);
  const [pickedProduct, setPickedProduct] = useState<string | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const requestIdRef = useRef(0);

  useEffect(() => {
    let cancelled = false;
    listLiveCatalog({ recommendationEligibleOnly: true })
      .then((data) => {
        if (!cancelled) setLiveCatalog(data.items);
      })
      .catch(() => {
        /* historical search can still work */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const statusMessage = useMemo(() => {
    if (loading) return "Searching foundations…";
    if (error) return error;
    if (!open) return null;
    if (query.trim().length < 2 && step === "query") {
      return "Type at least 2 characters to search brands, products, and shades.";
    }
    if (options.length === 0) return "No foundations matched. Try another spelling.";
    return `${options.length} suggestion${options.length === 1 ? "" : "s"}`;
  }, [loading, error, open, query, step, options.length]);

  const buildVerifiedOptions = useCallback(
    (needle: string, brandFilter?: string, productFilter?: string): Option[] => {
      const n = needle.trim().toLowerCase();
      return liveCatalog
        .filter((row) => {
          if (!row.recommendation_eligible) return false;
          if (brandFilter && row.brand.toLowerCase() !== brandFilter.toLowerCase()) return false;
          if (productFilter && row.product.toLowerCase() !== productFilter.toLowerCase()) {
            return false;
          }
          if (!n) return Boolean(brandFilter || productFilter);
          const blob = `${row.brand} ${row.product} ${row.shade_name} ${row.shade_code ?? ""}`.toLowerCase();
          return blob.includes(n);
        })
        .slice(0, 8)
        .map((live) => ({
          id: `v-${live.id}`,
          kind: "verified_shade" as const,
          label: `${live.brand} · ${displayShadeLabel(live.shade_name, live.shade_code)}`,
          detail: `${live.product} · Nearby shade ideas available`,
          live,
        }));
    },
    [liveCatalog],
  );

  const runSuggest = useCallback(
    async (raw: string) => {
      const q = raw.trim();
      const reqId = ++requestIdRef.current;
      if (q.length < 2) {
        setOptions([]);
        setLoading(false);
        setError(null);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const suggestPromise = discoverSuggest(q, 8);
        const livePromise = listLiveCatalog({ recommendationEligibleOnly: true }).catch(
          () => ({
            items: liveCatalog,
            total: liveCatalog.length,
            recommendation_eligible_count: liveCatalog.length,
          }),
        );
        const [suggest, live] = await Promise.all([suggestPromise, livePromise]);
        if (reqId !== requestIdRef.current) return;
        setLiveCatalog(live.items);

        const verified = buildVerifiedOptions(q);
        const brandOpts: Option[] = suggest.brands.map((b) => ({
          id: `b-${b.brand}`,
          kind: "brand",
          label: b.brand,
          detail: `${b.shade_count} shades · choose a product next`,
          brand: b.brand,
        }));
        const productOpts: Option[] = suggest.products.map((p) => ({
          id: `p-${p.brand}-${p.product}`,
          kind: "product",
          label: `${p.brand} · ${p.product}`,
          detail: `${p.shade_count} shades · choose an exact shade next`,
          brand: p.brand,
          product: p.product,
        }));
        const shadeOpts: Option[] = suggest.shades.map((s) => {
          const asItem: DiscoveryShadeItem = {
            id: s.id,
            brand: s.brand,
            product: s.product,
            shade_name: s.shade_name,
            shade_code: s.shade_code,
            brand_shade_description: null,
            historical_retailer_url: null,
            approx_swatch: null,
            verification_status: "estimated",
            metadata_verification_status: "unreviewed",
            matching_accuracy_status: "not_evaluated",
            recommendation_eligible: false,
            data_label: "historical_unverified",
            availability_note: "Historical archive listing",
            incomplete_flags: [],
            dataset_collection_note: "",
            source_dataset: "the_pudding_foundation_names",
          };
          const twin = findVerifiedCatalogTwin(
            live.items,
            s.brand,
            s.product,
            s.shade_name,
            s.shade_code,
          );
          return {
            id: `h-${s.id}`,
            kind: "historical_shade" as const,
            label: `${s.brand} · ${shadeDisplayName(s)}`,
            detail: twin
              ? `${s.product} · We can carefully suggest nearby shades`
              : `${s.product} · Listing may be outdated · guidance only`,
            item: asItem,
            twin,
          };
        });

        // Prefer verified exact shades, then brands (for "NARS"), then products, then archive shades.
        const merged = [...verified, ...brandOpts, ...productOpts, ...shadeOpts].slice(0, 12);
        setOptions(merged);
        setActiveIndex(0);
        setStep("query");
      } catch (err) {
        if (reqId !== requestIdRef.current) return;
        // Still try to show verified-only matches if discovery is down.
        const verifiedOnly = buildVerifiedOptions(q);
        setOptions(verifiedOnly);
        setActiveIndex(0);
        setError(
          verifiedOnly.length
            ? err instanceof ApiError
              ? `${err.message} Showing the shades we can suggest from right now.`
              : "Broader search is briefly unavailable. Showing the shades we can suggest from right now."
            : err instanceof ApiError
              ? err.message
              : "Could not search foundations right now. Please try again in a moment.",
        );
      } finally {
        if (reqId === requestIdRef.current) setLoading(false);
      }
    },
    [buildVerifiedOptions, liveCatalog],
  );

  const loadProductsForBrand = useCallback(
    async (brand: string) => {
      const reqId = ++requestIdRef.current;
      setLoading(true);
      setError(null);
      setPickedBrand(brand);
      setPickedProduct(null);
      setStep("product");
      setQuery(brand);
      try {
        const [products, live] = await Promise.all([
          discoverProducts(brand),
          listLiveCatalog({ brand, recommendationEligibleOnly: true }).catch(() => ({
            items: liveCatalog.filter((r) => r.brand.toLowerCase() === brand.toLowerCase()),
            total: 0,
            recommendation_eligible_count: 0,
          })),
        ]);
        if (reqId !== requestIdRef.current) return;
        setLiveCatalog((prev) => {
          const map = new Map(prev.map((r) => [r.id, r]));
          for (const row of live.items) map.set(row.id, row);
          return Array.from(map.values());
        });

        const verifiedProducts = new Set(
          live.items.map((r) => r.product.toLowerCase()),
        );
        const verifiedOpts: Option[] = Array.from(
          new Map(
            live.items.map((r) => [
              r.product,
              {
                id: `vp-${r.brand}-${r.product}`,
                kind: "product" as const,
                label: `${r.brand} · ${r.product}`,
                detail: "Product line with shade ideas available · choose a shade next",
                brand: r.brand,
                product: r.product,
              },
            ]),
          ).values(),
        );

        const historicalOpts: Option[] = products.items
          .filter((p: DiscoveryProductCount) => !verifiedProducts.has(p.product.toLowerCase()))
          .map((p) => ({
            id: `p-${p.brand}-${p.product}`,
            kind: "product" as const,
            label: `${p.brand} · ${p.product}`,
            detail: `${p.shade_count} shades · choose an exact shade next`,
            brand: p.brand,
            product: p.product,
          }));

        const merged = [...verifiedOpts, ...historicalOpts].slice(0, 20);
        setOptions(merged);
        setActiveIndex(0);
        setOpen(true);
      } catch (err) {
        if (reqId !== requestIdRef.current) return;
        setOptions([]);
        setError(
          err instanceof ApiError
            ? err.message
            : "Could not load products for that brand.",
        );
      } finally {
        if (reqId === requestIdRef.current) setLoading(false);
      }
    },
    [liveCatalog],
  );

  const loadShadesForProduct = useCallback(
    async (brand: string, product: string) => {
      const reqId = ++requestIdRef.current;
      setLoading(true);
      setError(null);
      setPickedBrand(brand);
      setPickedProduct(product);
      setStep("shade");
      setQuery(`${brand} · ${product}`);
      try {
        const [discovery, live] = await Promise.all([
          discoverShades({ brand, product, page: 1, pageSize: 40 }),
          listLiveCatalog({ brand, recommendationEligibleOnly: true }).catch(() => ({
            items: liveCatalog.filter((r) => r.brand.toLowerCase() === brand.toLowerCase()),
            total: 0,
            recommendation_eligible_count: 0,
          })),
        ]);
        if (reqId !== requestIdRef.current) return;

        const verified = live.items
          .filter((r) => r.product.toLowerCase() === product.toLowerCase())
          .map((liveRow) => ({
            id: `v-${liveRow.id}`,
            kind: "verified_shade" as const,
            label: displayShadeLabel(liveRow.shade_name, liveRow.shade_code),
            detail: `${liveRow.product} · Nearby shade ideas available`,
            live: liveRow,
          }));

        const historical = discovery.items
          .filter((item) => {
            const twin = findVerifiedCatalogTwin(
              live.items,
              item.brand,
              item.product,
              item.shade_name,
              item.shade_code,
            );
            return !twin;
          })
          .map((item) => ({
            id: `h-${item.id}`,
            kind: "historical_shade" as const,
            label: shadeDisplayName(item),
            detail: `${item.product} · Listing may be outdated · guidance only`,
            item,
            twin: null as LiveCatalogShade | null,
          }));

        const merged: Option[] = [...verified, ...historical].slice(0, 40);
        setOptions(merged);
        setActiveIndex(0);
        setOpen(true);
        if (merged.length === 0) {
          setError("No shades found for that product in our library.");
        }
      } catch (err) {
        if (reqId !== requestIdRef.current) return;
        setOptions([]);
        setError(
          err instanceof ApiError ? err.message : "Could not load shades for that product.",
        );
      } finally {
        if (reqId === requestIdRef.current) setLoading(false);
      }
    },
    [liveCatalog],
  );

  function scheduleSuggest(value: string) {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      void runSuggest(value);
    }, 300);
  }

  function chooseOption(option: Option) {
    if (option.kind === "brand") {
      void loadProductsForBrand(option.brand);
      return;
    }
    if (option.kind === "product") {
      void loadShadesForProduct(option.brand, option.product);
      return;
    }
    if (option.kind === "verified_shade") {
      onSelect(selectionFromVerified(option.live));
      setOpen(false);
      setOptions([]);
      setQuery(
        `${option.live.brand} · ${option.live.product} · ${displayShadeLabel(option.live.shade_name, option.live.shade_code)}`,
      );
      return;
    }
    onSelect(selectionFromHistorical(option.item, option.twin));
    setOpen(false);
    setOptions([]);
    setQuery(
      `${option.item.brand} · ${option.item.product} · ${shadeDisplayName(option.item)}`,
    );
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!open && (event.key === "ArrowDown" || event.key === "Enter")) {
      setOpen(true);
    }
    if (event.key === "Escape") {
      setOpen(false);
      return;
    }
    if (!open || options.length === 0) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((i) => (i + 1) % options.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((i) => (i - 1 + options.length) % options.length);
    } else if (event.key === "Enter") {
      event.preventDefault();
      const option = options[activeIndex];
      if (option) chooseOption(option);
    }
  }

  function clearAll() {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setQuery("");
    setOptions([]);
    setOpen(false);
    setError(null);
    setPickedBrand(null);
    setPickedProduct(null);
    setStep("query");
    onClear();
    inputRef.current?.focus();
  }

  return (
    <div className="space-y-3">
      <div className="relative">
        <label className="block space-y-2 text-sm">
          <span className="font-medium text-espresso">Search your foundation</span>
          <input
            ref={inputRef}
            className={fieldClass}
            role="combobox"
            aria-expanded={open}
            aria-controls={listId}
            aria-autocomplete="list"
            aria-activedescendant={
              open && options[activeIndex] ? `${listId}-${options[activeIndex].id}` : undefined
            }
            value={query}
            placeholder="Start typing a brand — e.g. NARS, Maybelline, Fenty…"
            autoComplete="off"
            onChange={(e) => {
              const value = e.target.value;
              setQuery(value);
              setOpen(true);
              setStep("query");
              setPickedBrand(null);
              setPickedProduct(null);
              if (selected) onClear();
              scheduleSuggest(value);
            }}
            onFocus={() => setOpen(true)}
            onKeyDown={onKeyDown}
          />
        </label>

        {open && (
          <div
            className="absolute z-30 mt-2 w-full overflow-hidden rounded-2xl border border-espresso/12 bg-cream shadow-soft"
            role="listbox"
            id={listId}
          >
            <div className="border-b border-espresso/8 px-4 py-2 text-[12px] text-espresso-soft">
              {step === "query" && "Suggestions · pick a brand, product, or exact shade"}
              {step === "product" && `Products for ${pickedBrand}`}
              {step === "shade" && `Shades for ${pickedBrand} · ${pickedProduct}`}
            </div>
            {loading && (
              <p className="px-4 py-3 text-sm text-espresso-soft" role="status">
                Searching…
              </p>
            )}
            {!loading && error && (
              <p className="px-4 py-3 text-sm text-burgundy" role="alert">
                {error}
              </p>
            )}
            {!loading && !error && options.length === 0 && query.trim().length >= 2 && (
              <p className="px-4 py-3 text-sm text-espresso-soft" role="status">
                No foundations matched. Try another spelling.
              </p>
            )}
            {!loading && options.length > 0 && (
              <ul className="max-h-72 overflow-y-auto">
                {options.map((option, index) => {
                  const active = index === activeIndex;
                  return (
                    <li key={option.id} role="presentation">
                      <button
                        type="button"
                        id={`${listId}-${option.id}`}
                        role="option"
                        aria-selected={active}
                        className={[
                          "flex w-full flex-col gap-0.5 px-4 py-3 text-left transition",
                          active ? "bg-rose/20" : "hover:bg-mist",
                        ].join(" ")}
                        onMouseEnter={() => setActiveIndex(index)}
                        onClick={() => chooseOption(option)}
                      >
                        <span className="font-medium text-espresso">{option.label}</span>
                        <span className="text-[12px] text-espresso-soft">{option.detail}</span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
            <div className="flex items-center justify-between gap-3 border-t border-espresso/8 px-4 py-2">
              <p className="text-[11px] text-espresso-soft">
                ↑↓ to move · Enter to select · Esc to close
              </p>
              <button
                type="button"
                className="text-[12px] font-medium text-burgundy underline-offset-2 hover:underline"
                onClick={() => {
                  setOpen(false);
                  if (query.trim().length >= 2) void runSuggest(query);
                  setOpen(true);
                }}
              >
                Refresh
              </button>
            </div>
          </div>
        )}
      </div>

      <p className="text-[12px] text-espresso-soft" aria-live="polite">
        {statusMessage}
      </p>

      {selected && (
        <div className="rounded-2xl border border-espresso/10 bg-mist/80 px-4 py-4">
          <p className="text-[11px] font-medium uppercase tracking-[0.18em] text-burgundy">
            Selected foundation
          </p>
          <p className="mt-1 font-display text-2xl text-espresso">
            {displayShadeLabel(selected.shade_name, selected.shade_code)}
          </p>
          <p className="mt-1 text-sm text-espresso-soft">
            {selected.brand}
            <span aria-hidden> · </span>
            {selected.product}
          </p>
          <p className="mt-3 text-sm leading-relaxed text-espresso-soft">
            {selected.source === "verified_catalog"
              ? "We’ve reviewed this product line, so we can carefully suggest nearby shades when your feedback supports it."
              : "This listing may be outdated. We’ll help you understand what you’re wearing — without inventing replacement shades from it alone."}
          </p>
          <button
            type="button"
            className="mt-3 text-sm font-medium text-burgundy underline-offset-2 hover:underline"
            onClick={clearAll}
          >
            Clear selection
          </button>
        </div>
      )}
    </div>
  );
}
