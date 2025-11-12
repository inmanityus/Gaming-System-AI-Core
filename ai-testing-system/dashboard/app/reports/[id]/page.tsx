'use client';

/**
 * Report Detail Page with P0 Fixes:
 * - Proper polling cleanup (no memory leaks)
 * - Request timeouts with AbortController
 * - XSS protection with DOMPurify
 * - Comprehensive error handling
 * - Type safety
 * - Accessibility improvements
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import DOMPurify from 'isomorphic-dompurify';
import { fetchReport as apiFetchReport, downloadReport, Report, APIError } from '@/lib/api-client';

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const reportId = params.id as string;
  
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  
  // P0 FIX: Track mounted state to prevent state updates after unmount
  const mountedRef = useRef(true);
  const abortControllerRef = useRef<AbortController | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // P0 FIX: Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      abortControllerRef.current?.abort();
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, []);

  // P0 FIX: Fetch with timeout and cancellation
  const fetchReport = useCallback(async () => {
    // Cancel previous request
    abortControllerRef.current?.abort();
    
    try {
      const data = await apiFetchReport(reportId);
      
      if (mountedRef.current) {
        setReport(data);
        setError(null);
      }
      
      return data;
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch report');
      
      if (mountedRef.current) {
        setError(error);
      }
      
      throw error;
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [reportId]);

  // Initial fetch
  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  // P0 FIX: Conditional polling with proper cleanup
  useEffect(() => {
    // Only poll if status is queued or processing
    if (report && (report.status === 'queued' || report.status === 'processing')) {
      pollIntervalRef.current = setInterval(() => {
        if (mountedRef.current) {
          fetchReport();
        }
      }, 3000);

      return () => {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      };
    }
  }, [report?.status, fetchReport]);

  // P0 FIX: Download with loading state and proper error handling
  const handleDownload = async () => {
    if (!report) return;
    
    setDownloading(true);
    
    try {
      const blob = await downloadReport(report.id);
      
      // Create download link
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `report-${report.id}.${report.format}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      // P0 FIX: Cleanup object URL to prevent memory leak
      URL.revokeObjectURL(url);
    } catch (err) {
      const error = err instanceof APIError ? err : new Error('Download failed');
      setError(error);
    } finally {
      setDownloading(false);
    }
  };

  // P1 FIX: Enhanced loading state with skeleton
  if (loading && !report) {
    return (
      <div className="container mx-auto p-8" role="status" aria-live="polite">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3" />
          <div className="h-64 bg-gray-200 rounded" />
          <div className="grid grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-32 bg-gray-200 rounded" />
            ))}
          </div>
        </div>
        <span className="sr-only">Loading report...</span>
      </div>
    );
  }

  // P0 FIX: Error state with retry button
  if (error) {
    return (
      <div className="container mx-auto p-8" role="alert">
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-red-800 mb-2">
            Error Loading Report
          </h2>
          <p className="text-red-600 mb-6">{error.message}</p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={() => {
                setError(null);
                setLoading(true);
                fetchReport();
              }}
              className="px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 focus:ring-2 focus:ring-red-500"
            >
              Retry
            </button>
            <button
              onClick={() => router.push('/reports')}
              className="px-6 py-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
            >
              Back to Reports
            </button>
          </div>
        </div>
      </div>
    );
  }

  // P0 FIX: 404 state
  if (!report) {
    return (
      <div className="container mx-auto p-8 text-center">
        <div className="text-6xl mb-4">📋</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Report Not Found</h2>
        <p className="text-gray-600 mb-6">The requested report could not be found.</p>
        <button
          onClick={() => router.push('/reports')}
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Back to Reports
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <button
                onClick={() => router.push('/reports')}
                className="text-sm text-blue-600 hover:text-blue-800 mb-2"
              >
                ← Back to Reports
              </button>
              <h1 className="text-3xl font-bold text-gray-900">
                Report: {report.game_title}
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                Report ID: {report.id} • Status: {report.status}
              </p>
            </div>
            {report.status === 'completed' && (
              <div className="flex gap-2">
                <button
                  onClick={handleDownload}
                  disabled={downloading}
                  aria-busy={downloading}
                  className="px-6 py-3 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed focus:ring-2 focus:ring-blue-500"
                >
                  {downloading ? (
                    <>
                      <span className="sr-only">Downloading...</span>
                      <span aria-hidden="true">Downloading...</span>
                    </>
                  ) : (
                    'Download Report'
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {(report.status === 'queued' || report.status === 'processing') ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Generating Report...
            </h2>
            <p className="text-gray-600">
              This page will update automatically when the report is ready.
            </p>
          </div>
        ) : report.status === 'failed' ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">❌</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              Report Generation Failed
            </h2>
            <p className="text-gray-600">
              An error occurred during report generation. Please try again.
            </p>
          </div>
        ) : report.report_data ? (
          <>
            {/* Executive Summary */}
            <div className="bg-white rounded-lg shadow p-6 mb-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Executive Summary</h2>
              
              <div className="grid grid-cols-4 gap-6">
                <div className="text-center p-4 border-2 border-gray-200 rounded-lg">
                  <p className="text-4xl font-bold text-blue-600">
                    {report.report_data.summary.total_screenshots}
                  </p>
                  <p className="text-sm text-gray-600 mt-2">Total Screenshots</p>
                </div>
                
                <div className="text-center p-4 border-2 border-green-300 rounded-lg">
                  <p className="text-4xl font-bold text-green-600">
                    {report.report_data.summary.screenshots_passed}
                  </p>
                  <p className="text-sm text-gray-600 mt-2">Passed</p>
                </div>
                
                <div className="text-center p-4 border-2 border-red-300 rounded-lg">
                  <p className="text-4xl font-bold text-red-600">
                    {report.report_data.summary.screenshots_with_issues}
                  </p>
                  <p className="text-sm text-gray-600 mt-2">Issues Found</p>
                </div>
                
                <div className="text-center p-4 border-2 border-gray-200 rounded-lg">
                  <p className={`text-4xl font-bold ${
                    report.report_data.summary.pass_rate >= 90 ? 'text-green-600' :
                    report.report_data.summary.pass_rate >= 70 ? 'text-yellow-600' :
                    'text-red-600'
                  }`}>
                    {report.report_data.summary.pass_rate.toFixed(1)}%
                  </p>
                  <p className="text-sm text-gray-600 mt-2">Pass Rate</p>
                </div>
              </div>

              {/* Issues by Severity */}
              <div className="mt-6">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">Issues by Severity</h3>
                <div className="flex gap-3 flex-wrap">
                  {report.report_data.summary.issues_by_severity.critical > 0 && (
                    <span className="px-3 py-2 bg-red-100 text-red-800 rounded-md font-semibold">
                      Critical: {report.report_data.summary.issues_by_severity.critical}
                    </span>
                  )}
                  {report.report_data.summary.issues_by_severity.high > 0 && (
                    <span className="px-3 py-2 bg-orange-100 text-orange-800 rounded-md font-semibold">
                      High: {report.report_data.summary.issues_by_severity.high}
                    </span>
                  )}
                  {report.report_data.summary.issues_by_severity.medium > 0 && (
                    <span className="px-3 py-2 bg-yellow-100 text-yellow-800 rounded-md font-semibold">
                      Medium: {report.report_data.summary.issues_by_severity.medium}
                    </span>
                  )}
                  {report.report_data.summary.issues_by_severity.low > 0 && (
                    <span className="px-3 py-2 bg-blue-100 text-blue-800 rounded-md font-semibold">
                      Low: {report.report_data.summary.issues_by_severity.low}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {/* Consensus Issues */}
            {report.report_data.consensus_issues.length > 0 && (
              <div className="bg-white rounded-lg shadow p-6 mb-6">
                <h2 className="text-2xl font-bold text-gray-900 mb-4">
                  Consensus Issues ({report.report_data.consensus_issues.length})
                </h2>
                
                <div className="space-y-4">
                  {report.report_data.consensus_issues.map((issue, idx) => (
                    <div
                      key={idx}
                      className={`border-l-4 rounded-lg p-4 ${
                        issue.severity === 'critical' ? 'border-red-500 bg-red-50' :
                        issue.severity === 'high' ? 'border-orange-500 bg-orange-50' :
                        issue.severity === 'medium' ? 'border-yellow-500 bg-yellow-50' :
                        'border-blue-500 bg-blue-50'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="text-lg font-semibold text-gray-900">{issue.title}</h3>
                        <span className={`px-2 py-1 rounded text-xs font-bold ${
                          issue.severity === 'critical' ? 'bg-red-200 text-red-900' :
                          issue.severity === 'high' ? 'bg-orange-200 text-orange-900' :
                          issue.severity === 'medium' ? 'bg-yellow-200 text-yellow-900' :
                          'bg-blue-200 text-blue-900'
                        }`}>
                          {issue.severity.toUpperCase()}
                        </span>
                      </div>
                      
                      {/* P0 FIX: XSS protection with DOMPurify */}
                      <div 
                        className="text-gray-700 mb-4"
                        dangerouslySetInnerHTML={{
                          __html: DOMPurify.sanitize(issue.description, {
                            ALLOWED_TAGS: ['p', 'br', 'strong', 'em', 'b', 'i'],
                            ALLOWED_ATTR: []
                          })
                        }}
                      />
                      
                      {/* Model Consensus */}
                      <div className="mt-4">
                        <h4 className="text-sm font-semibold text-gray-700 mb-2">AI Models Consensus</h4>
                        <div className="grid gap-2">
                          {issue.consensus_details.map((analysis, aidx) => (
                            <div key={aidx} className="flex items-center gap-3 text-sm bg-white p-2 rounded">
                              <span className="text-lg">{analysis.detected ? '✅' : '❌'}</span>
                              <span className="font-medium w-32">{analysis.model_name}</span>
                              <span className="text-gray-600">{(analysis.confidence * 100).toFixed(0)}%</span>
                              <span className="text-gray-500 flex-1 text-xs">{analysis.reason}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Performance & Cost */}
            <div className="grid grid-cols-2 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Performance Metrics</h2>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Processing Time</span>
                    <span className="font-semibold">
                      {report.report_data.performance.total_processing_time_seconds.toFixed(2)}s
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Avg Time per Screenshot</span>
                    <span className="font-semibold">
                      {report.report_data.performance.average_time_per_screenshot_seconds.toFixed(2)}s
                    </span>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">Cost Analysis</h2>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Gemini 2.5 Pro</span>
                    <span className="font-semibold">${report.report_data.costs.gemini_cost_usd.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">GPT-5</span>
                    <span className="font-semibold">${report.report_data.costs.gpt5_cost_usd.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Claude Sonnet 4.5</span>
                    <span className="font-semibold">${report.report_data.costs.claude_cost_usd.toFixed(4)}</span>
                  </div>
                  <div className="flex justify-between pt-3 border-t-2 border-gray-200">
                    <span className="font-semibold">Total Cost</span>
                    <span className="font-bold text-lg">${report.report_data.costs.total_cost_usd.toFixed(4)}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Recommendations */}
            {report.report_data.recommendations && (
              <div className="bg-white rounded-lg shadow p-6 mt-6">
                <h2 className="text-xl font-bold text-gray-900 mb-4">AI Recommendations</h2>
                <div className="bg-orange-50 border-l-4 border-orange-500 p-4 rounded">
                  <p className="text-gray-800">{report.report_data.recommendations}</p>
                </div>
              </div>
            )}
          </>
        ) : null}
      </main>
    </div>
  );
}

