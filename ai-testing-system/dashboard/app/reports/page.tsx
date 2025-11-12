'use client';

/**
 * Reports List Page with P0 Fixes:
 * - Proper fetch error handling
 * - Type safety
 * - Accessibility improvements
 * - Loading/empty/error states
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { fetchReports, generateReport, Report, APIError } from '@/lib/api-client';

export default function ReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);
  const [error, setError] = useState<Error | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [filters, setFilters] = useState({
    gameTitle: 'all',
    status: 'all',
  });

  // P0 FIX: Track mounted state
  const mountedRef = useRef(true);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  // P0 FIX: Fetch with proper error handling
  const fetchReportsList = useCallback(async () => {
    try {
      const data = await fetchReports({
        gameTitle: filters.gameTitle !== 'all' ? filters.gameTitle : undefined,
        status: filters.status !== 'all' ? filters.status : undefined,
      });
      
      if (mountedRef.current) {
        setReports(data.reports || []);
        setError(null);
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to fetch reports');
      
      if (mountedRef.current) {
        setError(error);
      }
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, [filters]);

  useEffect(() => {
    fetchReportsList();
  }, [fetchReportsList]);

  // P0 FIX: Generate with loading state and error handling
  async function generateNewReport() {
    setGenerating(true);
    
    try {
      const data = await generateReport({
        test_run_id: 'marvel-rivals-latest',
        format: 'html',
        include_screenshots: true
      });
      
      alert(`Report generation started! Report ID: ${data.report_id}`);
      
      // Refresh list after short delay
      setTimeout(() => fetchReportsList(), 1000);
    } catch (err) {
      const error = err instanceof APIError ? err : new Error('Failed to generate report');
      setError(error);
    } finally {
      setGenerating(false);
    }
  }

  function getStatusColor(status: string) {
    switch (status) {
      case 'completed': return 'text-green-600';
      case 'generating': return 'text-blue-600';
      case 'failed': return 'text-red-600';
      default: return 'text-gray-600';
    }
  }

  function getPassRateColor(rate: number) {
    if (rate >= 90) return 'text-green-600';
    if (rate >= 70) return 'text-yellow-600';
    return 'text-red-600';
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Validation Reports
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                AI-Driven Game Testing System • The Body Broker
              </p>
            </div>
            <div className="flex gap-2">
              <Link 
                href="/"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                ← Back to Issues
              </Link>
              <button
                onClick={generateNewReport}
                disabled={generating}
                aria-busy={generating}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed focus:ring-2 focus:ring-blue-500"
              >
                {generating ? 'Generating...' : 'Generate New Report'}
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Filter:</span>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="px-3 py-1 border border-gray-300 rounded-md text-sm"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="generating">Generating</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>

        {/* P0 FIX: Error state */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6 mb-6" role="alert">
            <div className="flex items-center gap-3">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <h3 className="font-semibold text-red-800">Error Loading Reports</h3>
                <p className="text-red-600 text-sm">{error.message}</p>
              </div>
              <button
                onClick={() => {
                  setError(null);
                  setLoading(true);
                  fetchReportsList();
                }}
                className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Reports List */}
        {loading ? (
          <div className="container mx-auto p-8" role="status" aria-live="polite">
            <div className="animate-pulse grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {[...Array(6)].map((_, i) => (
                <div key={i} className="h-64 bg-gray-200 rounded-lg" />
              ))}
            </div>
            <span className="sr-only">Loading reports...</span>
          </div>
        ) : reports.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              No Reports Found
            </h2>
            <p className="text-gray-600 mb-6">
              Generate your first validation report to get started.
            </p>
            <button
              onClick={generateNewReport}
              disabled={generating}
              aria-busy={generating}
              className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed focus:ring-2 focus:ring-blue-500"
            >
              {generating ? 'Generating...' : 'Generate First Report'}
            </button>
          </div>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {reports.map((report) => (
              <article key={report.id} role="article" aria-labelledby={`report-title-${report.id}`}>
                <Link 
                  href={`/reports/${report.id}`}
                  className="block bg-white rounded-lg shadow hover:shadow-lg transition-shadow p-6 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                  aria-describedby={`report-status-${report.id}`}
                >
                  <div>
                  {/* Header */}
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 id={`report-title-${report.id}`} className="font-semibold text-lg text-gray-900">
                        {report.game_title}
                      </h3>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(report.created_at).toLocaleDateString()} {new Date(report.created_at).toLocaleTimeString()}
                      </p>
                    </div>
                    <span 
                      id={`report-status-${report.id}`}
                      role="status"
                      aria-label={`Report status: ${report.status}`}
                      className={`text-xs font-semibold px-2 py-1 rounded ${
                        report.status === 'completed' ? 'bg-green-100 text-green-800' :
                        report.status === 'processing' || report.status === 'queued' ? 'bg-blue-100 text-blue-800' :
                        'bg-red-100 text-red-800'
                      }`}
                    >
                      {report.status.toUpperCase()}
                    </span>
                  </div>

                  {/* Summary Stats */}
                  {report.report_data && report.status === 'completed' && (
                    <>
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-2xl font-bold text-gray-900">
                            {report.report_data.summary.total_screenshots}
                          </p>
                          <p className="text-sm text-gray-600">Total Tests</p>
                        </div>
                        <div>
                          <p className={`text-2xl font-bold ${getPassRateColor(report.report_data.summary.pass_rate)}`}>
                            {report.report_data.summary.pass_rate.toFixed(1)}%
                          </p>
                          <p className="text-sm text-gray-600">Pass Rate</p>
                        </div>
                      </div>

                      {/* Issues */}
                      <div className="flex gap-2 mb-4 flex-wrap">
                        {report.report_data.summary.issues_by_severity.critical > 0 && (
                          <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium">
                            {report.report_data.summary.issues_by_severity.critical} Critical
                          </span>
                        )}
                        {report.report_data.summary.issues_by_severity.high > 0 && (
                          <span className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium">
                            {report.report_data.summary.issues_by_severity.high} High
                          </span>
                        )}
                        {report.report_data.summary.issues_by_severity.medium > 0 && (
                          <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs font-medium">
                            {report.report_data.summary.issues_by_severity.medium} Medium
                          </span>
                        )}
                      </div>

                      {/* Cost */}
                      {report.report_data.costs && (
                        <div className="pt-4 border-t">
                          <p className="text-sm text-gray-600">
                            Cost: <span className="font-semibold">${report.report_data.costs.total_cost_usd.toFixed(4)}</span>
                          </p>
                        </div>
                      )}
                    </>
                  )}

                  {/* Format Badge */}
                  <div className="mt-4 pt-4 border-t">
                    <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                      {report.format.toUpperCase()}
                    </span>
                    {report.file_size_bytes && (
                      <span className="text-xs text-gray-500 ml-2">
                        {(report.file_size_bytes / 1024).toFixed(1)} KB
                      </span>
                    )}
                  </div>
                  </div>
                </Link>
              </article>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}

