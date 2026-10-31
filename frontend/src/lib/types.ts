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
  shade_code?: string | null;
  depth_feedback: DepthFeedback;
  undertone_issues: UndertoneIssue[];
  description: string;
  wear_change: WearChange;
}

export interface HealthResponse {
  status: string;
  service: string;
  openai_configured: boolean;
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

/* --- Historical discovery (staging) — never feed into the matcher as verified --- */

export interface ApproxSwatchInfo {
  hex: string | null;
  hue: number | null;
  sat: number | null;
  lightness: number | null;
  colorspace: string | null;
  warning: string;
}

export interface DiscoveryShadeItem {
  id: string;
  brand: string;
  product: string;
  shade_name: string | null;
  shade_code: string | null;
  brand_shade_description: string | null;
  historical_retailer_url: string | null;
  approx_swatch: ApproxSwatchInfo | null;
  verification_status: string;
  metadata_verification_status: string;
  matching_accuracy_status: string;
  recommendation_eligible: boolean;
  data_label: "historical_unverified";
  availability_note: string;
  incomplete_flags: string[];
  dataset_collection_note: string;
  source_dataset: string;
}

export interface DiscoverySearchResponse {
  dataset: string;
  disclaimer: string;
  color_caveat: string;
  page: number;
  page_size: number;
  total_matches: number;
  total_pages: number;
  sort: string;
  order: string;
  items: DiscoveryShadeItem[];
}

export interface DiscoveryBrandCount {
  brand: string;
  shade_count: number;
}

export interface DiscoveryBrandsResponse {
  dataset: string;
  disclaimer: string;
  total_brands: number;
  items: DiscoveryBrandCount[];
}

export interface DiscoveryProductCount {
  brand: string;
  product: string;
  shade_count: number;
}

export interface DiscoveryProductsResponse {
  dataset: string;
  disclaimer: string;
  brand: string;
  total_products: number;
  items: DiscoveryProductCount[];
}

export interface DiscoverySuggestBrand {
  brand: string;
  shade_count: number;
  match_type: "prefix" | "contains";
}

export interface DiscoverySuggestProduct {
  brand: string;
  product: string;
  shade_count: number;
  match_type: "prefix" | "contains";
}

export interface DiscoverySuggestShade {
  id: string;
  brand: string;
  product: string;
  shade_name: string | null;
  shade_code: string | null;
  match_type: "prefix" | "contains";
}

export interface DiscoverySuggestResponse {
  dataset: string;
  disclaimer: string;
  query: string;
  brands: DiscoverySuggestBrand[];
  products: DiscoverySuggestProduct[];
  shades: DiscoverySuggestShade[];
}

/* --- Deterministic matcher (verified catalog only; no OpenAI) --- */

export type MatchDepthFeedback = "too_light" | "too_dark" | "correct" | "unsure";
export type MatchUndertoneIssue = "too_warm" | "too_cool" | "none" | "unsure";

export interface MatchShadeRequest {
  brand?: string | null;
  product?: string | null;
  shade_name?: string | null;
  shade_code?: string | null;
  depth_feedback: MatchDepthFeedback;
  undertone_issue: MatchUndertoneIssue;
}

export interface ShadeMatchCandidate {
  catalog_id: string;
  brand: string;
  product: string;
  shade_name: string;
  shade_code: string | null;
  selection_reasons: string[];
  limitations: string[];
  evidence_status: string;
}

export interface MatchShadeResponse {
  matched_current_shade_id: string | null;
  recommendations: ShadeMatchCandidate[];
  no_match_reason: string | null;
  global_limitations: string[];
}

/** Live catalog row (subset used by matcher demo). */
export interface LiveCatalogShade {
  id: string;
  brand: string;
  product: string;
  shade_name: string;
  shade_code: string | null;
  brand_reported_depth: string | null;
  brand_reported_undertone: string | null;
  recommendation_eligible: boolean;
  verification_status: string;
  metadata_verification_status: string;
}

export interface CatalogListResponse {
  items: LiveCatalogShade[];
  total: number;
  recommendation_eligible_count: number;
}
