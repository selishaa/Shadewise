import { describe, expect, it } from "vitest";
import {
  buildJourneyGuidance,
  guidanceFromShadeAnalysis,
  softenCustomerFacingText,
} from "./journeyGuidance";
import type { SelectedFoundation } from "./foundationIdentity";
import type { MatchShadeResponse, ShadeAnalysis } from "./types";

const verified: SelectedFoundation = {
  brand: "NARS",
  product: "Light Reflecting Foundation",
  shade_name: "Punjab",
  shade_code: "M1",
  historical_id: null,
  verified_catalog_id: "nars-lrf-punjab-m1",
  source: "verified_catalog",
};

const historical: SelectedFoundation = {
  brand: "Maybelline",
  product: "Fit Me Matte + Poreless Liquid Foundation",
  shade_name: "Porcelain",
  shade_code: "110",
  historical_id: "pudding-maybelline-110",
  verified_catalog_id: null,
  source: "historical_archive",
};

const matchWithCandidates: MatchShadeResponse = {
  matched_current_shade_id: "nars-lrf-punjab-m1",
  recommendations: [
    {
      catalog_id: "nars-lrf-patagonia-m1-2",
      brand: "NARS",
      product: "Light Reflecting Foundation",
      shade_name: "Patagonia",
      shade_code: "M1.2",
      selection_reasons: ["Same product line"],
      limitations: ["Try in person"],
      evidence_status: "not proof",
    },
  ],
  no_match_reason: null,
  global_limitations: ["Brand labels are approximate."],
};

const noMatch: MatchShadeResponse = {
  matched_current_shade_id: "nars-lrf-punjab-m1",
  recommendations: [],
  no_match_reason: "No suitable real catalog shades met the conservative depth/undertone rules.",
  global_limitations: [],
};

function allCopy(guidance: ReturnType<typeof buildJourneyGuidance>): string {
  return [
    guidance.mode_label,
    guidance.summary,
    ...guidance.possible_explanations,
    ...guidance.what_to_try_next,
    ...guidance.limitations,
  ].join(" ");
}

describe("buildJourneyGuidance", () => {
  it("allows candidates for reviewed foundations with matches", () => {
    const guidance = buildJourneyGuidance({
      foundation: verified,
      depth: "correct",
      undertone: "too_warm",
      wear: "unsure",
      description: "",
      matchResult: matchWithCandidates,
    });
    expect(guidance.can_suggest_candidates).toBe(true);
    expect(guidance.mode_label).toBe("Your Shade Analysis");
    expect(guidance.summary.toLowerCase()).toContain("worth trying");
    expect(guidance.possible_explanations.length).toBeGreaterThan(0);
    expect(guidance.what_to_try_next.length).toBeGreaterThan(0);
    expect(guidance.limitations.some((l) => /starting points|perfect match/i.test(l))).toBe(
      true,
    );
    expect(guidance.source).toBe("rules");
    expect(guidance.source_note).toBeNull();
    expect(allCopy(guidance)).not.toMatch(/ai key|no ai|deterministic|api key/i);
  });

  it("handles reviewed no-match without inventing products", () => {
    const guidance = buildJourneyGuidance({
      foundation: verified,
      depth: "too_light",
      undertone: "none",
      wear: "no",
      description: "",
      matchResult: noMatch,
    });
    expect(guidance.can_suggest_candidates).toBe(true);
    expect(guidance.limitations.join(" ")).toMatch(/close enough|confidently|checked product/i);
    expect(guidance.summary.toLowerCase()).toContain("not forcing");
  });

  it("blocks candidate framing for outdated listings", () => {
    const guidance = buildJourneyGuidance({
      foundation: historical,
      depth: "correct",
      undertone: "too_cool",
      wear: "yes",
      description: "Turns pink indoors",
      matchResult: null,
    });
    expect(guidance.can_suggest_candidates).toBe(false);
    expect(guidance.summary.toLowerCase()).toMatch(/outdated|guidance rather than naming/);
    expect(guidance.limitations.join(" ")).toMatch(/older|outdated|no longer match/i);
    expect(guidance.possible_explanations.join(" ")).toMatch(/won.?t invent|outdated/i);
    expect(allCopy(guidance)).not.toMatch(/historical archive|verified catalog/i);
  });

  it("keeps customer copy free of internal jargon", () => {
    const guidance = buildJourneyGuidance({
      foundation: verified,
      depth: "correct",
      undertone: "too_warm",
      wear: "unsure",
      description: "",
      matchResult: {
        ...matchWithCandidates,
        global_limitations: [
          "catalog metadata verification",
          "source_checked rows only",
          "Brand labels are approximate.",
        ],
      },
    });
    const blob = allCopy(guidance);
    expect(blob).not.toMatch(
      /source_checked|deterministic|recommendation_eligible|not_evaluated|api key|openai/i,
    );
  });

  it("softens matcher no-match language for customers", () => {
    const softened = softenCustomerFacingText(noMatch.no_match_reason!);
    expect(softened.toLowerCase()).not.toContain("conservative");
    expect(softened.toLowerCase()).not.toContain("catalog shades");
    expect(softened).toMatch(/close enough|confidently/i);
  });
});

const sampleAnalysis: ShadeAnalysis = {
  summary: "Depth feels close; warmth may be pulling orange.",
  reported_depth_match: "matches",
  reported_color_issues: ["too orange"],
  reported_wear_change: "unsure",
  possible_explanations: ["The shade may run warmer than your skin."],
  undertone_adjustments_to_try: ["Compare a cooler option at the same depth."],
  suggested_next_steps: ["Swatch along the jaw in daylight."],
  uncertainties: ["We cannot confirm undertone from text alone."],
  analysis_vs_recommendation_note: "This is interpretive analysis, not a verified match.",
};

describe("guidanceFromShadeAnalysis", () => {
  it("labels AI provenance and keeps matcher for candidates only", () => {
    const guidance = guidanceFromShadeAnalysis({
      analysis: sampleAnalysis,
      matchResult: matchWithCandidates,
      canSuggestCandidates: true,
    });
    expect(guidance.source).toBe("ai");
    expect(guidance.source_note?.toLowerCase()).toContain("ai-assisted");
    expect(guidance.summary).toBe(sampleAnalysis.summary);
    expect(guidance.possible_explanations.join(" ")).toMatch(/warmer|cooler/i);
    expect(guidance.what_to_try_next.join(" ")).toMatch(/jaw|daylight|worth trying/i);
    expect(guidance.limitations.join(" ")).toMatch(/interpretive|analysis partner/i);
    expect(allCopy(guidance)).not.toMatch(/catalog_hints|demo example/i);
  });

  it("never claims AI when built from rules", () => {
    const rules = buildJourneyGuidance({
      foundation: verified,
      depth: "correct",
      undertone: "too_warm",
      wear: "unsure",
      description: "",
      matchResult: null,
    });
    expect(rules.source).toBe("rules");
    expect(rules.source_note).toBeNull();
    expect(allCopy(rules).toLowerCase()).not.toContain("ai-assisted");
  });
});
