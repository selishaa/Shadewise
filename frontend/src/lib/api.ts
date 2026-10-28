/**
 * Browser → FastAPI client.
 *
 * The Next.js app never holds OPENAI_API_KEY. It only talks to our backend.
 */

import type { AnalyzeShadeRequest, AnalyzeShadeResponse } from "./types";

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

export async function analyzeShade(
  payload: AnalyzeShadeRequest,
): Promise<AnalyzeShadeResponse> {
  const url = `${getApiBaseUrl()}/api/analyze-shade`;

  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new ApiError(
      "Could not reach the ShadeWise backend. Is it running on port 8000?",
      0,
    );
  }

  if (!response.ok) {
    let detail = "Shade analysis failed.";
    try {
      const data = (await response.json()) as { detail?: string | unknown };
      if (typeof data.detail === "string") {
        detail = data.detail;
      } else if (Array.isArray(data.detail)) {
        detail = "Please check the form fields and try again.";
      }
    } catch {
      // keep default message
    }
    throw new ApiError(detail, response.status);
  }

  return (await response.json()) as AnalyzeShadeResponse;
}
