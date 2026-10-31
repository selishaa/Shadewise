/** Helpers for distinguishing historical archive picks vs verified live catalog. */

import type { DiscoveryShadeItem, LiveCatalogShade } from "./types";

export type SelectedFoundation = {
  brand: string;
  product: string;
  shade_name: string | null;
  shade_code: string | null;
  /** Historical discovery id, if chosen from the archive. */
  historical_id: string | null;
  /** Live catalog id when recommendation-eligible twin exists. */
  verified_catalog_id: string | null;
  source: "verified_catalog" | "historical_archive";
};

export function livesMatchIdentity(
  live: LiveCatalogShade,
  brand: string,
  product: string,
  shadeName: string | null,
  shadeCode: string | null,
): boolean {
  if (live.brand.toLowerCase() !== brand.toLowerCase()) return false;
  if (live.product.toLowerCase() !== product.toLowerCase()) return false;
  const name = shadeName?.trim().toLowerCase() ?? "";
  const code = shadeCode?.trim().toLowerCase() ?? "";
  const liveName = live.shade_name.toLowerCase();
  const liveCode = live.shade_code?.toLowerCase() ?? "";
  if (name && liveName === name) return true;
  if (code && liveCode && liveCode === code) return true;
  if (name && liveCode && liveCode === name) return true;
  return false;
}

export function findVerifiedCatalogTwin(
  candidates: LiveCatalogShade[],
  brand: string,
  product: string,
  shadeName: string | null,
  shadeCode: string | null,
): LiveCatalogShade | null {
  return (
    candidates.find(
      (row) =>
        row.recommendation_eligible &&
        livesMatchIdentity(row, brand, product, shadeName, shadeCode),
    ) ?? null
  );
}

export function selectionFromVerified(live: LiveCatalogShade): SelectedFoundation {
  return {
    brand: live.brand,
    product: live.product,
    shade_name: live.shade_name,
    shade_code: live.shade_code,
    historical_id: null,
    verified_catalog_id: live.id,
    source: "verified_catalog",
  };
}

export function selectionFromHistorical(
  item: DiscoveryShadeItem,
  verifiedTwin: LiveCatalogShade | null,
): SelectedFoundation {
  if (verifiedTwin) {
    return {
      brand: verifiedTwin.brand,
      product: verifiedTwin.product,
      shade_name: verifiedTwin.shade_name,
      shade_code: verifiedTwin.shade_code,
      historical_id: item.id,
      verified_catalog_id: verifiedTwin.id,
      source: "verified_catalog",
    };
  }
  return {
    brand: item.brand,
    product: item.product,
    shade_name: item.shade_name,
    shade_code: item.shade_code,
    historical_id: item.id,
    verified_catalog_id: null,
    source: "historical_archive",
  };
}

export function filterLiveByQuery(items: LiveCatalogShade[], q: string): LiveCatalogShade[] {
  const needle = q.trim().toLowerCase();
  if (!needle) return items.filter((i) => i.recommendation_eligible);
  return items.filter((item) => {
    if (!item.recommendation_eligible) return false;
    const blob = [
      item.brand,
      item.product,
      item.shade_name,
      item.shade_code ?? "",
    ]
      .join(" ")
      .toLowerCase();
    return blob.includes(needle);
  });
}

export function displayShadeLabel(shadeName: string | null, shadeCode: string | null): string {
  const name = shadeName?.trim();
  const code = shadeCode?.trim();
  if (name && code && name.toLowerCase() !== code.toLowerCase()) return `${name} · ${code}`;
  if (name) return name;
  if (code) return `Shade ${code}`;
  return "Shade unavailable";
}
