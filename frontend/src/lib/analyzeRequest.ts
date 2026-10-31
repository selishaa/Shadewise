/**
 * Map Find My Shade questionnaire values onto the existing /api/analyze-shade schema.
 */

import type { SelectedFoundation } from "./foundationIdentity";
import { displayShadeLabel } from "./foundationIdentity";
import type {
  AnalyzeShadeRequest,
  MatchDepthFeedback,
  MatchUndertoneIssue,
  UndertoneIssue,
  WearChange,
} from "./types";

/** Journey undertone → AI undertone_issues list (conservative 1:1). */
export function mapUndertoneToAnalyzeIssues(
  undertone: MatchUndertoneIssue,
): UndertoneIssue[] {
  switch (undertone) {
    case "too_warm":
      return ["too_orange"];
    case "too_cool":
      return ["too_pink"];
    case "none":
      return ["none"];
    case "unsure":
    default:
      return ["unsure"];
  }
}

export function mapJourneyToAnalyzeRequest(input: {
  foundation: SelectedFoundation;
  depth: MatchDepthFeedback;
  undertone: MatchUndertoneIssue;
  wear: WearChange;
  description: string;
}): AnalyzeShadeRequest {
  const { foundation, depth, undertone, wear, description } = input;
  const shadeName =
    foundation.shade_name?.trim() ||
    displayShadeLabel(foundation.shade_name, foundation.shade_code);

  return {
    brand: foundation.brand,
    product: foundation.product,
    shade_name: shadeName || "Unknown shade",
    shade_code: foundation.shade_code,
    depth_feedback: depth,
    undertone_issues: mapUndertoneToAnalyzeIssues(undertone),
    description: description.trim().slice(0, 500),
    wear_change: wear,
  };
}
