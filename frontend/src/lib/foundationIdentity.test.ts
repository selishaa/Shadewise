import { describe, expect, it } from "vitest";
import {
  findVerifiedCatalogTwin,
  selectionFromHistorical,
  selectionFromVerified,
  filterLiveByQuery,
  livesMatchIdentity,
} from "./foundationIdentity";
import type { DiscoveryShadeItem, LiveCatalogShade } from "./types";

const punjabLive: LiveCatalogShade = {
  id: "nars-lrf-punjab-m1",
  brand: "NARS",
  product: "Light Reflecting Foundation",
  shade_name: "Punjab",
  shade_code: "M1",
  brand_reported_depth: "medium",
  brand_reported_undertone: "warm",
  recommendation_eligible: true,
  verification_status: "brand_verified",
  metadata_verification_status: "source_checked",
};

const sheerGlowHistorical: DiscoveryShadeItem = {
  id: "pudding-nars-sheer-glow-punjab",
  brand: "NARS",
  product: "Sheer Glow Foundation",
  shade_name: "Punjab",
  shade_code: null,
  brand_shade_description: "Punjab",
  historical_retailer_url: "https://example.com",
  approx_swatch: null,
  verification_status: "estimated",
  metadata_verification_status: "unreviewed",
  matching_accuracy_status: "not_evaluated",
  recommendation_eligible: false,
  data_label: "historical_unverified",
  availability_note: "outdated",
  incomplete_flags: [],
  dataset_collection_note: "2021",
  source_dataset: "the_pudding_foundation_names",
};

describe("verified vs historical selection", () => {
  it("marks live catalog picks as verified", () => {
    const selected = selectionFromVerified(punjabLive);
    expect(selected.source).toBe("verified_catalog");
    expect(selected.verified_catalog_id).toBe("nars-lrf-punjab-m1");
  });

  it("does not treat a different NARS product as the verified twin", () => {
    const twin = findVerifiedCatalogTwin(
      [punjabLive],
      sheerGlowHistorical.brand,
      sheerGlowHistorical.product,
      sheerGlowHistorical.shade_name,
      sheerGlowHistorical.shade_code,
    );
    expect(twin).toBeNull();
    const selected = selectionFromHistorical(sheerGlowHistorical, twin);
    expect(selected.source).toBe("historical_archive");
    expect(selected.verified_catalog_id).toBeNull();
  });

  it("matches identical brand/product/shade identity", () => {
    expect(
      livesMatchIdentity(
        punjabLive,
        "NARS",
        "Light Reflecting Foundation",
        "Punjab",
        "M1",
      ),
    ).toBe(true);
  });

  it("filters live catalog by query for verified hits", () => {
    const hits = filterLiveByQuery([punjabLive], "punjab");
    expect(hits).toHaveLength(1);
    expect(filterLiveByQuery([punjabLive], "fenty")).toHaveLength(0);
  });
});
