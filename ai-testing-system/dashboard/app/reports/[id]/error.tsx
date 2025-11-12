'use client';

/**
 * Error Boundary for Report Detail Page
 * P0 FIX: Prevents blank screen on component crashes
 */

export default function ReportDetailError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center" role="alert">
      <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full">
        <div className="text-center mb-6">
          <div className="text-6xl mb-4">❌</div>
          <h2 className="text-2xl font-bold text-red-600 mb-2">
            Error Loading Report
          </h2>
          <p className="text-gray-600 mb-4">
            {error.message || 'Failed to load report details'}
          </p>
          {error.digest && (
            <p className="text-xs text-gray-400 font-mono">
              Error ID: {error.digest}
            </p>
          )}
        </div>
        
        <div className="space-y-3">
          <button
            onClick={reset}
            className="w-full px-4 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:ring-2 focus:ring-blue-500"
          >
            Try Again
          </button>
          
          <button
            onClick={() => window.location.href = '/reports'}
            className="w-full px-4 py-3 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
          >
            Back to Reports
          </button>
        </div>
      </div>
    </div>
  );
}

