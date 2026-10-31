/**
 * Rule-based consultation copy for Find My Shade (no OpenAI).
 * Written for customers — never invents product matches or confidence scores.
 */

import type { SelectedFoundation } from "./foundationIdentity";
import { displayShadeLabel } from "./foundationIdentity";
import type {
  MatchDepthFeedback,
  MatchShadeResponse,
  MatchUndertoneIssue,
  ShadeAnalysis,
  WearChange,
} from "./types";

/** Honest provenance — never label rules as AI. */
export type GuidanceSource = "ai" | "rules";

export type JourneyGuidance = {
  mode_label: string;
  summary: string;
  possible_explanations: string[];
  what_to_try_next: string[];
  limitations: string[];
  can_suggest_candidates: boolean;
  source: GuidanceSource;
  source_note: string | null;
};

function shadePhrase(foundation: SelectedFoundation): string {
  const label = displayShadeLabel(foundation.shade_name, foundation.shade_code);
  return `${foundation.brand} ${label}`;
}

/** Soften backend matcher strings before showing them to customers. */
export function softenCustomerFacingText(raw: string): string {
  let text = raw;
  text = text.replace(/brand-reported/gi, "brand-labeled");
  text = text.replace(/catalog[- ]?metadata/gi, "product details");
  text = text.replace(/source_checked/gi, "reviewed");
  text = text.replace(/recommendation_eligible/gi, "ready for suggestions");
  text = text.replace(/not_evaluated/gi, "not yet wear-tested");
  text = text.replace(/deterministic/gi, "");
  text = text.replace(/No suitable real catalog shades met the conservative depth\/undertone rules\./gi,
    "We don’t have a close enough option in our checked product set to suggest confidently right now.");
  text = text.replace(/\s{2,}/g, " ").trim();
  return text;
}

export function buildJourneyGuidance(input: {
  foundation: SelectedFoundation;
  depth: MatchDepthFeedback;
  undertone: MatchUndertoneIssue;
  wear: WearChange;
  description: string;
  matchResult: MatchShadeResponse | null;
}): JourneyGuidance {
  const { foundation, depth, undertone, wear, description, matchResult } = input;
  const verified = foundation.source === "verified_catalog";
  const hasCandidates = Boolean(matchResult && matchResult.recommendations.length > 0);
  const you = shadePhrase(foundation);

  const explanations: string[] = [];
  const nextSteps: string[] = [];
  const limitations: string[] = [];

  // Depth — personalized
  if (depth === "too_light") {
    explanations.push(
      `${you} may be reading lighter than your skin, which can leave a chalky or ashy finish — especially around the jaw.`,
    );
    nextSteps.push(
      "In natural light, compare one slightly deeper shade beside what you’re wearing now. Store lighting can hide a mismatch.",
    );
  } else if (depth === "too_dark") {
    explanations.push(
      `${you} may be sitting deeper than your skin, which can look muddy or leave a visible line where face meets neck.`,
    );
    nextSteps.push(
      "Swatch a gently lighter option next to your current shade and check both jaw and neck together.",
    );
  } else if (depth === "correct") {
    explanations.push(
      `Since the depth of ${you} feels close, the issue is less likely “go much lighter or darker,” and more about undertone or how the formula settles on your skin.`,
    );
  } else {
    explanations.push(
      `Depth can be tricky to judge indoors. A quick daylight check of ${you} along your jaw usually tells a clearer story.`,
    );
    nextSteps.push(
      "Step to a window (or outside) with your current shade before you change depth families.",
    );
  }

  // Undertone — personalized
  if (undertone === "too_warm") {
    explanations.push(
      "That warm or orange cast often means the shade is pulling more golden than your skin.",
    );
    nextSteps.push(
      "Look for cooler or more balanced options in a similar depth, and compare them side by side on your jaw — not on the back of your hand.",
    );
  } else if (undertone === "too_cool") {
    explanations.push(
      "That pink or cool cast often means the shade is pulling rosier than your skin.",
    );
    nextSteps.push(
      "Try warmer or more balanced options nearby in depth, and give each a moment to settle before you decide.",
    );
  } else if (undertone === "none") {
    explanations.push(
      "If the undertone feels right, focus on depth, how the shade wears through the day, or the finish — rather than jumping to a totally different color story.",
    );
  } else {
    explanations.push(
      "Undertone is personal, and brands don’t all use the same words for warm, cool, or neutral — trust what you see on your skin more than the label.",
    );
  }

  if (wear === "yes") {
    explanations.push(
      "If the color shifts after wear, skin oils or dry-down can quietly change how the shade reads by midday.",
    );
    nextSteps.push(
      "Check again after 30–60 minutes before you rule a shade out forever.",
    );
  }

  if (description.trim()) {
    nextSteps.push(
      "Keep the details you shared in mind when you compare options in person — your own notes are often the best guide.",
    );
  }

  if (verified && hasCandidates) {
    nextSteps.push(
      "Below are a few shades from the same product family that may be worth trying based on what you described. Always confirm them on your skin.",
    );
  } else if (verified && matchResult?.no_match_reason) {
    nextSteps.push(
      "We don’t have a nearby option we’re comfortable suggesting from this product family yet. An in-person swatch is the kindest next step.",
    );
    limitations.push(softenCustomerFacingText(matchResult.no_match_reason));
  } else if (!verified) {
    explanations.push(
      `We can use ${you} to understand what you’re wearing, but this listing may be outdated — so we won’t invent replacement shades from it.`,
    );
    nextSteps.push(
      "Use the guidance above while you shop, and lean on in-person swatches or the brand’s own shade tools for that exact product line.",
    );
    limitations.push(
      "Some product listings in our library are older and may no longer match what’s sold today.",
    );
  }

  // One concise "good to know" stack — avoid repetitive tech disclaimers
  limitations.push(
    "Lighting, formula finish, and your skin can all change how a shade looks from morning to night.",
  );
  limitations.push(
    "ShadeWise offers thoughtful starting points — not a guaranteed perfect match, price, or stock status.",
  );

  if (matchResult?.global_limitations?.length) {
    for (const item of matchResult.global_limitations) {
      if (/catalog metadata|not_evaluated|source_checked|recommendation_eligible|deterministic/i.test(item)) {
        continue;
      }
      const softened = softenCustomerFacingText(item);
      if (
        /calibrated measurement|wear-validated|brand-labeled labels|few nearby shades/i.test(softened)
      ) {
        // Fold into friendlier, non-duplicative notes instead of dumping backend text.
        continue;
      }
      if (softened && !limitations.includes(softened)) {
        limitations.push(softened);
      }
    }
  }

  const summary = verified
    ? hasCandidates
      ? `Here’s a clear read on ${you}, based on what you shared — plus a few shades from the same family that may be worth trying.`
      : `Here’s a clear read on ${you}, based on what you shared. We’re not forcing a product suggestion when the fit isn’t clear enough.`
    : `Here’s a clear read on ${you}, based on what you shared. Because this listing may be outdated, we’re focusing on guidance rather than naming replacements.`;

  return {
    mode_label: "Your Shade Analysis",
    summary,
    possible_explanations: explanations,
    what_to_try_next: nextSteps,
    limitations: Array.from(new Set(limitations)),
    can_suggest_candidates: verified,
    source: "rules",
    source_note: null,
  };
}

/**
 * Map structured AI analysis into the same JourneyResults shape.
 * Product suggestions stay with the matcher — never use catalog_hints here.
 */
export function guidanceFromShadeAnalysis(input: {
  analysis: ShadeAnalysis;
  matchResult: MatchShadeResponse | null;
  canSuggestCandidates: boolean;
}): JourneyGuidance {
  const { analysis, matchResult, canSuggestCandidates } = input;
  const hasCandidates = Boolean(matchResult && matchResult.recommendations.length > 0);

  const explanations = [
    ...analysis.possible_explanations,
    ...analysis.undertone_adjustments_to_try,
  ].filter(Boolean);

  const nextSteps = [...analysis.suggested_next_steps];
  if (canSuggestCandidates && hasCandidates) {
    nextSteps.push(
      "Below are a few shades from the same product family that may be worth trying based on what you described. Always confirm them on your skin.",
    );
  } else if (canSuggestCandidates && matchResult?.no_match_reason) {
    nextSteps.push(
      "We don’t have a nearby option we’re comfortable suggesting from this product family yet. An in-person swatch is the kindest next step.",
    );
  }

  const limitations: string[] = [
    ...analysis.uncertainties,
    analysis.analysis_vs_recommendation_note,
  ].filter(Boolean);

  if (canSuggestCandidates && matchResult?.no_match_reason && !hasCandidates) {
    limitations.push(softenCustomerFacingText(matchResult.no_match_reason));
  }

  limitations.push(
    "Your notes may be shared with our analysis partner to interpret this report — we don’t use photos or account details.",
  );
  limitations.push(
    "ShadeWise offers thoughtful starting points — not a guaranteed perfect match, price, or stock status.",
  );

  return {
    mode_label: "Your Shade Analysis",
    summary: analysis.summary,
    possible_explanations: explanations.length
      ? explanations
      : ["We’re still piecing together what might be off — trust what you see in daylight on your skin."],
    what_to_try_next: nextSteps.length
      ? nextSteps
      : ["Compare options along your jaw in natural light before you buy."],
    limitations: Array.from(new Set(limitations)),
    can_suggest_candidates: canSuggestCandidates,
    source: "ai",
    source_note: "AI-assisted interpretation of what you shared — not a verified shade match.",
  };
}
