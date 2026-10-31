/** Pure helpers for Foundation Explorer display — safe with missing fields. */

import type { DiscoveryShadeItem } from "./types";

export function shadeDisplayName(
  item: Pick<DiscoveryShadeItem, "shade_name" | "shade_code">,
): string {
  const name = item.shade_name?.trim();
  const code = item.shade_code?.trim();
  if (name && code && name.toLowerCase() !== code.toLowerCase()) {
    return `${name} · ${code}`;
  }
  if (name) return name;
  if (code) return `Shade ${code}`;
  return "Shade name unavailable";
}

export function isValidCssHex(hex: string | null | undefined): hex is string {
  if (!hex) return false;
  return /^#([0-9A-Fa-f]{6})$/.test(hex.trim());
}

export function buildDiscoverQuery(params: {
  q?: string;
  brand?: string;
  product?: string;
  shade?: string;
  page?: number;
  pageSize?: number;
}): string {
  const search = new URLSearchParams();
  if (params.q?.trim()) search.set("q", params.q.trim());
  if (params.brand?.trim()) search.set("brand", params.brand.trim());
  if (params.product?.trim()) search.set("product", params.product.trim());
  if (params.shade?.trim()) search.set("shade", params.shade.trim());
  search.set("page", String(params.page ?? 1));
  search.set("page_size", String(params.pageSize ?? 12));
  search.set("sort", "brand");
  search.set("order", "asc");
  return search.toString();
}

/** Simple debounce helper for autocomplete. */
export function debounce<T extends (...args: never[]) => void>(fn: T, waitMs: number) {
  let timer: ReturnType<typeof setTimeout> | null = null;
  const wrapped = (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), waitMs);
  };
  wrapped.cancel = () => {
    if (timer) clearTimeout(timer);
    timer = null;
  };
  return wrapped;
}
