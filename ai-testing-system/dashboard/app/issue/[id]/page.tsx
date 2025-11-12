'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Image from 'next/image';

interface Recommendation {
  issue_id: string;
  confidence: number;
  severity: string;
  git_commit: string;
  test_case: string;
  category: string;
  analysis: string;
  screenshot_path: string;
  telemetry_path: string;
  models_consensus: {
    [key: string]: {
      agrees: boolean;
      confidence: number;
    };
  };
  recommendation: {
    type: string;
    changes?: Array<{
      component?: string;
      property?: string;
      current_value?: string;
      suggested_value?: string;
      rationale?: string;
    }>;
    alternative_approaches?: string[];
    rationale?: string;
  };
  created_at: string;
}

export default function IssueDetail({ params }: { params: { id: string } }) {
  const router = useRouter();
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [loading, setLoading] = useState(true);
  const [rejectReason, setRejectReason] = useState('');
  const [showRejectForm, setShowRejectForm] = useState(false);
  
  useEffect(() => {
    fetchRecommendation();
  }, [params.id]);
  
  const fetchRecommendation = async () => {
    try {
      // TODO: Replace with actual API
      const response = await fetch(`http://localhost:8000/captures/${params.id}`);
      const data = await response.json();
      setRecommendation(data);
    } catch (error) {
      console.error('Failed to fetch recommendation:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleAccept = async () => {
    if (!recommendation) return;
    
    const confirmed = confirm(
      `Accept this recommendation and create Jira ticket?\n\nIssue: ${recommendation.issue_id}\nSeverity: ${recommendation.severity}`
    );
    
    if (confirmed) {
      try {
        // TODO: API call to accept and create Jira ticket
        await fetch(`http://localhost:8000/recommendations/${recommendation.issue_id}/accept`, {
          method: 'POST'
        });
        alert('Recommendation accepted! Jira ticket created.');
        router.push('/');
      } catch (error) {
        alert('Failed to accept recommendation');
      }
    }
  };
  
  const handleReject = async () => {
    if (!recommendation || !rejectReason.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }
    
    try {
      await fetch(`http://localhost:8000/recommendations/${recommendation.issue_id}/reject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: rejectReason })
      });
      alert('Recommendation rejected. Feedback will improve model accuracy.');
      router.push('/');
    } catch (error) {
      alert('Failed to reject recommendation');
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }
  
  if (!recommendation) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Issue Not Found</h2>
          <p className="text-gray-600 mb-4">The requested issue could not be loaded.</p>
          <button
            onClick={() => router.push('/')}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Back to Dashboard
          </button>
        </div>
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
                onClick={() => router.push('/')}
                className="text-sm text-blue-600 hover:text-blue-800 mb-2 flex items-center"
              >
                ← Back to Dashboard
              </button>
              <h1 className="text-3xl font-bold text-gray-900">
                Issue Review: {recommendation.issue_id}
              </h1>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleAccept}
                className="px-6 py-3 bg-green-600 text-white font-medium rounded-md hover:bg-green-700"
              >
                ✓ Accept & Create Ticket
              </button>
              <button
                onClick={() => setShowRejectForm(true)}
                className="px-6 py-3 bg-red-600 text-white font-medium rounded-md hover:bg-red-700"
              >
                ✗ Reject
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left Column: Visual Evidence */}
          <div className="space-y-6">
            {/* Screenshot */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Screenshot</h2>
              <div className="bg-gray-100 rounded-lg overflow-hidden">
                <img
                  src={recommendation.screenshot_path}
                  alt="Game screenshot"
                  className="w-full"
                />
              </div>
            </div>

            {/* Models Consensus */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                AI Models Consensus
              </h2>
              <div className="space-y-3">
                {Object.entries(recommendation.models_consensus).map(([model, result]) => (
                  <div key={model} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {result.agrees ? '✓' : '✗'}
                      </span>
                      <div>
                        <p className="font-medium text-gray-900">{model}</p>
                        <p className="text-sm text-gray-600">
                          Confidence: {(result.confidence * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        result.agrees
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {result.agrees ? 'Agrees' : 'Disagrees'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Analysis & Recommendation */}
          <div className="space-y-6">
            {/* Issue Details */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">Issue Details</h2>
              <div className="space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-600">Severity</label>
                  <p className="mt-1 px-3 py-1 inline-block rounded-full text-sm font-medium bg-red-100 text-red-800">
                    {recommendation.severity.toUpperCase()}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Category</label>
                  <p className="mt-1 text-gray-900">{recommendation.category}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Test Case</label>
                  <p className="mt-1 text-gray-900">{recommendation.test_case}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Git Commit</label>
                  <p className="mt-1 text-gray-900 font-mono text-sm">
                    {recommendation.git_commit}
                  </p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-600">Analysis</label>
                  <p className="mt-1 text-gray-700">{recommendation.analysis}</p>
                </div>
              </div>
            </div>

            {/* Recommendation */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Structured Recommendation
              </h2>
              
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Type</label>
                  <p className="mt-1 text-gray-900 font-medium">
                    {recommendation.recommendation.type}
                  </p>
                </div>

                {recommendation.recommendation.changes && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 mb-2 block">
                      Suggested Changes
                    </label>
                    <div className="space-y-3">
                      {recommendation.recommendation.changes.map((change, idx) => (
                        <div key={idx} className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                          {change.component && (
                            <p className="font-medium text-gray-900 mb-2">
                              Component: {change.component}
                            </p>
                          )}
                          {change.property && (
                            <p className="text-sm text-gray-700 mb-1">
                              <span className="font-medium">Property:</span> {change.property}
                            </p>
                          )}
                          {change.current_value && (
                            <p className="text-sm text-gray-700 mb-1">
                              <span className="font-medium">Current:</span> {change.current_value}
                            </p>
                          )}
                          {change.suggested_value && (
                            <p className="text-sm text-green-700 mb-1">
                              <span className="font-medium">Suggested:</span> {change.suggested_value}
                            </p>
                          )}
                          {change.rationale && (
                            <p className="text-sm text-gray-600 mt-2 italic">
                              {change.rationale}
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {recommendation.recommendation.rationale && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Rationale</label>
                    <p className="mt-1 text-gray-700">
                      {recommendation.recommendation.rationale}
                    </p>
                  </div>
                )}

                {recommendation.recommendation.alternative_approaches && (
                  <div>
                    <label className="text-sm font-medium text-gray-600 mb-2 block">
                      Alternative Approaches
                    </label>
                    <ul className="list-disc list-inside space-y-1">
                      {recommendation.recommendation.alternative_approaches.map((approach, idx) => (
                        <li key={idx} className="text-gray-700 text-sm">
                          {approach}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Reject Form Modal */}
        {showRejectForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <h3 className="text-xl font-bold text-gray-900 mb-4">
                Reject Recommendation
              </h3>
              <p className="text-gray-600 mb-4">
                Please provide a reason for rejecting this recommendation.
                This feedback helps improve model accuracy.
              </p>
              <textarea
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
                rows={4}
                placeholder="e.g., 'False positive - this lighting is intentional for this scene'"
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={() => setShowRejectForm(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  onClick={handleReject}
                  className="px-4 py-2 text-white bg-red-600 rounded-md hover:bg-red-700"
                >
                  Confirm Rejection
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

