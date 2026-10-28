/** Types mirroring the FastAPI / Pydantic response shapes. */

export type DepthFeedback = "too_light" | "correct" | "too_dark" | "unsure";

export type UndertoneIssue =
  | "too_orange"
  | "too_pink"
  | "too_yellow"
  | "too_ashy"
  | "too_red"
  | "looks_gray"
  | "unsure"
  | "none";

export type WearChange = "yes" | "no" | "unsure";

export interface AnalyzeShadeRequest {
  brand: string;
  product: string;
  shade_name: string;
  depth_feedback: DepthFeedback;
  undertone_issues: UndertoneIssue[];
  description: string;
  wear_change: WearChange;
}

export interface ShadeAnalysis {
  summary: string;
  reported_depth_match: "matches" | "too_light" | "too_dark" | "unclear";
  reported_color_issues: string[];
  reported_wear_change: WearChange;
  possible_explanations: string[];
  undertone_adjustments_to_try: string[];
  suggested_next_steps: string[];
  uncertainties: string[];
  analysis_vs_recommendation_note: string;
}

export interface GuidanceItem {
  title: string;
  detail: string;
  source: "general_guidance" | "illustrative_catalog";
}

export interface CatalogProduct {
  id: string;
  brand: string;
  product: string;
  shade_name: string;
  depth_family: string;
  undertone_family: string;
  notes: string;
  data_status: "illustrative";
}

export interface AnalyzeShadeResponse {
  analysis: ShadeAnalysis;
  guidance: GuidanceItem[];
  catalog_hints: CatalogProduct[];
  model_used: string | null;
  prompt_version: string;
}
