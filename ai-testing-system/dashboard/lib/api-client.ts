/**
 * API Client with Error Handling and Timeouts
 * P0 FIX: Comprehensive error handling for production
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8010';
const DEFAULT_TIMEOUT = 10000; // 10 seconds

export class APIError extends Error {
  constructor(
    message: string,
    public statusCode: number,
    public detail?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export async function apiRequest<T>(
  url: string,
  options?: RequestInit & { timeout?: number }
): Promise<T> {
  // P0 FIX: Add timeout support
  const controller = new AbortController();
  const timeout = options?.timeout || DEFAULT_TIMEOUT;
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new APIError(
        error.message || `Request failed with status ${response.status}`,
        response.status,
        error.detail
      );
    }

    return await response.json();
  } catch (error: unknown) {
    clearTimeout(timeoutId);
    
    if (error instanceof APIError) {
      throw error;
    }
    
    if (error instanceof Error && error.name === 'AbortError') {
      throw new APIError('Request timeout - please try again', 408);
    }
    
    // Network error
    throw new APIError('Network error - check your connection', 0, error);
  }
}

// Specific API functions with proper types

export interface Report {
  id: string;
  test_run_id: string;
  game_title: string;
  format: 'json' | 'html' | 'pdf';
  status: 'queued' | 'processing' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  file_size_bytes?: number;
  report_data?: {
    summary: {
      total_screenshots: number;
      screenshots_with_issues: number;
      screenshots_passed: number;
      pass_rate: number;
      issues_by_severity: {
        critical: number;
        high: number;
        medium: number;
        low: number;
        total: number;
      };
    };
    consensus_issues: Array<{
      issue_id: string;
      title: string;
      description: string;
      severity: string;
      screenshot_url: string;
      consensus_details: Array<{
        model_name: string;
        detected: boolean;
        confidence: number;
        reason: string;
      }>;
    }>;
    costs: {
      total_cost_usd: number;
      gemini_cost_usd: number;
      gpt5_cost_usd: number;
      claude_cost_usd: number;
    };
    performance: {
      total_processing_time_seconds: number;
      average_time_per_screenshot_seconds: number;
    };
    recommendations?: string;
  };
}

export async function fetchReports(params?: {
  gameTitle?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<{ total: number; reports: Report[] }> {
  const searchParams = new URLSearchParams();
  if (params?.gameTitle) searchParams.append('game_title', params.gameTitle);
  if (params?.status) searchParams.append('status', params.status);
  if (params?.limit) searchParams.append('limit', params.limit.toString());
  if (params?.offset) searchParams.append('offset', params.offset.toString());

  return apiRequest<{ total: number; reports: Report[] }>(
    `/reports?${searchParams.toString()}`
  );
}

export async function fetchReport(id: string): Promise<Report> {
  return apiRequest<Report>(`/reports/${id}`);
}

export async function generateReport(data: {
  test_run_id: string;
  format: 'json' | 'html' | 'pdf';
  include_screenshots?: boolean;
}): Promise<{ report_id: string; status: string; message: string }> {
  return apiRequest(`/reports/generate`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function downloadReport(id: string): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/reports/${id}/download`);
  
  if (!response.ok) {
    throw new APIError('Download failed', response.status);
  }
  
  const data = await response.json();
  
  if (data.download_url) {
    // Fetch the actual file from S3
    const fileResponse = await fetch(data.download_url);
    if (!fileResponse.ok) {
      throw new APIError('File download failed', fileResponse.status);
    }
    return await fileResponse.blob();
  }
  
  throw new APIError('No download URL provided', 500);
}

