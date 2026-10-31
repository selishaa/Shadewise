import { describe, expect, it } from "vitest";
import {
  mapJourneyToAnalyzeRequest,
  mapUndertoneToAnalyzeIssues,
} from "./analyzeRequest";
import type { SelectedFoundation } from "./foundationIdentity";

const foundation: SelectedFoundation = {
  brand: "NARS",
  product: "Light Reflecting Foundation",
  shade_name: "Punjab",
  shade_code: "M1",
  historical_id: null,
  verified_catalog_id: "nars-lrf-punjab-m1",
  source: "verified_catalog",
};

describe("mapUndertoneToAnalyzeIssues", () => {
  it("maps journey undertones onto AI schema values", () => {
    expect(mapUndertoneToAnalyzeIssues("too_warm")).toEqual(["too_orange"]);
    expect(mapUndertoneToAnalyzeIssues("too_cool")).toEqual(["too_pink"]);
    expect(mapUndertoneToAnalyzeIssues("none")).toEqual(["none"]);
    expect(mapUndertoneToAnalyzeIssues("unsure")).toEqual(["unsure"]);
  });
});

describe("mapJourneyToAnalyzeRequest", () => {
  it("includes shade_code and mapped undertone issues", () => {
    const payload = mapJourneyToAnalyzeRequest({
      foundation,
      depth: "correct",
      undertone: "too_warm",
      wear: "yes",
      description: "  Turns orange outdoors.  ",
    });
    expect(payload.brand).toBe("NARS");
    expect(payload.product).toBe("Light Reflecting Foundation");
    expect(payload.shade_name).toBe("Punjab");
    expect(payload.shade_code).toBe("M1");
    expect(payload.depth_feedback).toBe("correct");
    expect(payload.undertone_issues).toEqual(["too_orange"]);
    expect(payload.wear_change).toBe("yes");
    expect(payload.description).toBe("Turns orange outdoors.");
  });
});
