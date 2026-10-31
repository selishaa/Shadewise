import { describe, expect, it } from "vitest";
import { buildDiscoverQuery, isValidCssHex, shadeDisplayName } from "./discoverFormat";

describe("shadeDisplayName", () => {
  it("combines distinct name and code", () => {
    expect(shadeDisplayName({ shade_name: "Porcelain", shade_code: "110" })).toBe(
      "Porcelain · 110",
    );
  });

  it("handles missing name with code only", () => {
    expect(shadeDisplayName({ shade_name: null, shade_code: "100" })).toBe("Shade 100");
  });

  it("handles fully missing identity", () => {
    expect(shadeDisplayName({ shade_name: null, shade_code: null })).toBe(
      "Shade name unavailable",
    );
  });
});

describe("isValidCssHex", () => {
  it("accepts normalized hex", () => {
    expect(isValidCssHex("#FFDEC3")).toBe(true);
  });

  it("rejects missing or malformed values", () => {
    expect(isValidCssHex(null)).toBe(false);
    expect(isValidCssHex("FFDEC3")).toBe(false);
    expect(isValidCssHex("not-a-hex")).toBe(false);
  });
});

describe("buildDiscoverQuery", () => {
  it("keeps page size modest and encodes filters", () => {
    const qs = buildDiscoverQuery({
      q: "Punjab",
      brand: "NARS",
      product: "Light Reflecting Foundation",
      page: 2,
      pageSize: 12,
    });
    const params = new URLSearchParams(qs);
    expect(params.get("q")).toBe("Punjab");
    expect(params.get("brand")).toBe("NARS");
    expect(params.get("product")).toBe("Light Reflecting Foundation");
    expect(params.get("page")).toBe("2");
    expect(params.get("page_size")).toBe("12");
    expect(Number(params.get("page_size"))).toBeLessThanOrEqual(100);
  });
});
