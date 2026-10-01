/**
 * Shared API response type definitions (API Contract v2).
 *
 * These types are used for runtime validation and TypeScript inference
 * across Server and Client Components. They must match the backend
 * Pydantic schemas exactly.
 */

// ─── Standard Error Envelope (API Contract v2 §6) ──────────────────────────

export interface ApiErrorDetail {
  field?: string;
  message: string;
}

export interface ApiError {
  code: string;
  message: string;
  request_id: string;
  details: ApiErrorDetail[];
}

export interface ApiErrorResponse {
  error: ApiError;
}

// ─── Health Endpoints (API Contract v2 §84) ─────────────────────────────────

export interface LivenessResponse {
  status: "live";
  timestamp: string;
}

export interface ReadinessCheck {
  [key: string]: string;
}

export interface ReadinessResponse {
  status: "ready" | "unhealthy";
  checks: ReadinessCheck;
  timestamp: string;
}

export interface ApiHealthResponse {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  service: string;
  environment: string;
  version: string;
}

// ─── Generic Result Wrapper ──────────────────────────────────────────────────

export type ApiResult<T> =
  | { ok: true; data: T; requestId: string }
  | { ok: false; error: ApiError; requestId: string };
