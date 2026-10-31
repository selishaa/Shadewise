/**
 * Browser → FastAPI client.
 *
 * The Next.js app never holds OPENAI_API_KEY. It only talks to our backend.
 */

import { buildDiscoverQuery } from "./discoverFormat";
import type {
  AnalyzeShadeRequest,
  AnalyzeShadeResponse,
  CatalogListResponse,
  DiscoveryBrandsResponse,
  DiscoveryProductsResponse,
  DiscoverySearchResponse,
  DiscoveryShadeItem,
  DiscoverySuggestResponse,
  HealthResponse,
  MatchShadeRequest,
  MatchShadeResponse,
} from "./types";

const DEFAULT_API_BASE = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") || DEFAULT_API_BASE;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function parseErrorDetail(response: Response, fallback: string): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string | unknown };
    if (typeof data.detail === "string") return data.detail;
    if (Array.isArray(data.detail)) return "Please check the request and try again.";
  } catch {
    // keep fallback
  }
  return fallback;
}

async function apiFetch(url: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init);
  } catch {
    throw new ApiError(
      "Could not reach the ShadeWise backend. Is it running on port 8000?",
      0,
    );
  }
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await apiFetch(`${getApiBaseUrl()}/health`);
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Could not reach the ShadeWise backend."),
      response.status,
    );
  }
  return (await response.json()) as HealthResponse;
}

export async function analyzeShade(
  payload: AnalyzeShadeRequest,
): Promise<AnalyzeShadeResponse> {
  const url = `${getApiBaseUrl()}/api/analyze-shade`;
  const response = await apiFetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new ApiError(await parseErrorDetail(response, "Shade analysis failed."), response.status);
  }

  return (await response.json()) as AnalyzeShadeResponse;
}

export async function discoverShades(params: {
  q?: string;
  brand?: string;
  product?: string;
  shade?: string;
  page?: number;
  pageSize?: number;
}): Promise<DiscoverySearchResponse> {
  const qs = buildDiscoverQuery(params);
  const response = await apiFetch(`${getApiBaseUrl()}/api/discover/shades?${qs}`);
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Could not search historical foundations."),
      response.status,
    );
  }
  return (await response.json()) as DiscoverySearchResponse;
}

export async function discoverSuggest(
  q: string,
  limit = 8,
): Promise<DiscoverySuggestResponse> {
  const params = new URLSearchParams({
    q: q.trim(),
    limit: String(limit),
  });
  const response = await apiFetch(`${getApiBaseUrl()}/api/discover/suggest?${params}`);
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Could not load foundation suggestions."),
      response.status,
    );
  }
  return (await response.json()) as DiscoverySuggestResponse;
}

export async function discoverProducts(brand: string): Promise<DiscoveryProductsResponse> {
  const params = new URLSearchParams({ brand });
  const response = await apiFetch(`${getApiBaseUrl()}/api/discover/products?${params}`);
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Could not load products for that brand."),
      response.status,
    );
  }
  return (await response.json()) as DiscoveryProductsResponse;
}

export async function discoverShadeById(id: string): Promise<DiscoveryShadeItem> {
  const response = await apiFetch(
    `${getApiBaseUrl()}/api/discover/shades/${encodeURIComponent(id)}`,
  );
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Could not load shade details."),
      response.status,
    );
  }
  return (await response.json()) as DiscoveryShadeItem;
}

export async function discoverBrands(limit = 200): Promise<DiscoveryBrandsResponse> {
  const response = await apiFetch(
    `${getApiBaseUrl()}/api/discover/brands?limit=${limit}`,
  );
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Could not load brands."),
      response.status,
    );
  }
  return (await response.json()) as DiscoveryBrandsResponse;
}

/** Verified / live catalog only — safe source for the matcher demo. */
export async function listLiveCatalog(params?: {
  brand?: string;
  recommendationEligibleOnly?: boolean;
}): Promise<CatalogListResponse> {
  const search = new URLSearchParams();
  if (params?.brand) search.set("brand", params.brand);
  if (params?.recommendationEligibleOnly) {
    search.set("recommendation_eligible_only", "true");
  }
  const qs = search.toString();
  const response = await apiFetch(
    `${getApiBaseUrl()}/api/catalog${qs ? `?${qs}` : ""}`,
  );
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Could not load the verified catalog."),
      response.status,
    );
  }
  return (await response.json()) as CatalogListResponse;
}

/** Deterministic matcher — no OpenAI key required. */
export async function matchShades(
  payload: MatchShadeRequest,
): Promise<MatchShadeResponse> {
  const response = await apiFetch(`${getApiBaseUrl()}/api/match-shades`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new ApiError(
      await parseErrorDetail(response, "Shade matching failed."),
      response.status,
    );
  }
  return (await response.json()) as MatchShadeResponse;
}
