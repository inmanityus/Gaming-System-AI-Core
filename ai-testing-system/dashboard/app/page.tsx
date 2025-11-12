'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface Issue {
  issue_id: string;
  confidence: number;
  severity: 'low' | 'medium' | 'high' | 'critical';
  category: string;
  analysis: string;
  screenshot_path: string;
  created_at: string;
  status?: 'pending' | 'accepted' | 'rejected';
}

export default function TriageDashboard() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  
  useEffect(() => {
    fetchIssues();
  }, [filter]);
  
  const fetchIssues = async () => {
    try {
      // TODO: Replace with actual API URL
      const response = await fetch(`http://54.174.89.122:8000/consensus/issues`);
      const data = await response.json();
      setIssues(data.issues || []);
    } catch (error) {
      console.error('Failed to fetch issues:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-300';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case 'low': return 'bg-blue-100 text-blue-800 border-blue-300';
      default: return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };
  
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'atmosphere': return '🌑';
      case 'ux': return '🎨';
      case 'visual_bug': return '🐛';
      case 'performance': return '⚡';
      default: return '📋';
    }
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading issues...</p>
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
              <h1 className="text-3xl font-bold text-gray-900">
                Triage Dashboard
              </h1>
              <p className="mt-1 text-sm text-gray-500">
                AI-Driven Game Testing System • The Body Broker
              </p>
            </div>
            <div className="flex gap-2">
              <Link 
                href="/stats"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Statistics
              </Link>
              <Link 
                href="/captures"
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
              >
                All Captures
              </Link>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Filters */}
        <div className="bg-white rounded-lg shadow p-4 mb-6">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-gray-700">Filter:</span>
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1 rounded-md text-sm font-medium ${
                filter === 'all'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({issues.length})
            </button>
            <button
              onClick={() => setFilter('critical')}
              className={`px-3 py-1 rounded-md text-sm font-medium ${
                filter === 'critical'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Critical
            </button>
            <button
              onClick={() => setFilter('high')}
              className={`px-3 py-1 rounded-md text-sm font-medium ${
                filter === 'high'
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              High
            </button>
            <button
              onClick={() => setFilter('pending')}
              className={`px-3 py-1 rounded-md text-sm font-medium ${
                filter === 'pending'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Pending Review
            </button>
          </div>
        </div>

        {/* Issues List */}
        {issues.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <div className="text-6xl mb-4">🎉</div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">
              No Issues Found
            </h2>
            <p className="text-gray-600">
              All flagged issues have been reviewed. Great work!
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {issues.map((issue) => (
              <div
                key={issue.issue_id}
                className="bg-white rounded-lg shadow hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      {/* Issue Header */}
                      <div className="flex items-center gap-3 mb-3">
                        <span className="text-2xl">
                          {getCategoryIcon(issue.category)}
                        </span>
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-lg font-semibold text-gray-900">
                              {issue.issue_id}
                            </h3>
                            <span
                              className={`px-2 py-1 rounded text-xs font-medium border ${getSeverityColor(
                                issue.severity
                              )}`}
                            >
                              {issue.severity.toUpperCase()}
                            </span>
                            <span className="px-2 py-1 rounded text-xs font-medium bg-purple-100 text-purple-800 border border-purple-300">
                              {issue.category}
                            </span>
                          </div>
                          <p className="text-sm text-gray-500 mt-1">
                            Confidence: {(issue.confidence * 100).toFixed(1)}% •
                            Created: {new Date(issue.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>

                      {/* Issue Description */}
                      <p className="text-gray-700 mb-4">{issue.analysis}</p>

                      {/* Actions */}
                      <div className="flex gap-2">
                        <Link
                          href={`/issue/${issue.issue_id}`}
                          className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
                        >
                          Review & Accept
                        </Link>
                        <button
                          className="px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-300"
                          onClick={() => {
                            // TODO: Implement reject
                            alert('Reject functionality coming soon');
                          }}
                        >
                          Reject
                        </button>
                        <button
                          className="px-4 py-2 bg-white border border-gray-300 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-50"
                          onClick={() => {
                            // TODO: Implement view screenshot
                            window.open(issue.screenshot_path, '_blank');
                          }}
                        >
                          View Screenshot
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
