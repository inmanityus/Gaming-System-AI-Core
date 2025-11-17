"""
Content Governance Dashboard Configuration
==========================================

Defines metrics, visualizations, and alerts for Content Governance monitoring.
"""

from typing import Dict, List, Any


CONTENT_GOVERNANCE_DASHBOARD = {
    "title": "Content Governance - ETHELRED QA",
    "refresh": "30s",
    "panels": [
        # Row 1: Overview
        {
            "title": "Active Content Policies",
            "type": "stat",
            "gridPos": {"h": 4, "w": 6, "x": 0, "y": 0},
            "targets": [
                {
                    "expr": "sum(content_active_policies)",
                    "legendFormat": "Total Active"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 1000},
                            {"color": "red", "value": 5000}
                        ]
                    }
                }
            }
        },
        {
            "title": "Violation Rate (per min)",
            "type": "gauge",
            "gridPos": {"h": 4, "w": 6, "x": 6, "y": 0},
            "targets": [
                {
                    "expr": "sum(rate(content_violations_total[1m]) * 60)",
                    "legendFormat": "Violations/min"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "max": 100,
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 10},
                            {"color": "red", "value": 50}
                        ]
                    }
                }
            }
        },
        {
            "title": "Policy Lookup Latency (p95)",
            "type": "stat",
            "gridPos": {"h": 4, "w": 6, "x": 12, "y": 0},
            "targets": [
                {
                    "expr": "histogram_quantile(0.95, sum(rate(content_policy_lookup_duration_seconds_bucket[5m])) by (le)) * 1000",
                    "legendFormat": "p95 latency (ms)"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "unit": "ms",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 10},
                            {"color": "red", "value": 50}
                        ]
                    }
                }
            }
        },
        {
            "title": "Moderation Block Rate",
            "type": "stat",
            "gridPos": {"h": 4, "w": 6, "x": 18, "y": 0},
            "targets": [
                {
                    "expr": "sum(rate(content_moderation_requests_total{allowed=\"false\"}[5m])) / sum(rate(content_moderation_requests_total[5m])) * 100",
                    "legendFormat": "Block %"
                }
            ],
            "fieldConfig": {
                "defaults": {
                    "unit": "percent",
                    "thresholds": {
                        "mode": "absolute",
                        "steps": [
                            {"color": "green", "value": None},
                            {"color": "yellow", "value": 5},
                            {"color": "red", "value": 20}
                        ]
                    }
                }
            }
        },
        
        # Row 2: Violations by Category
        {
            "title": "Violations by Category",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 4},
            "targets": [
                {
                    "expr": "sum by (category) (rate(content_violations_total[5m]) * 60)",
                    "legendFormat": "{{category}}"
                }
            ],
            "yaxes": [
                {"format": "short", "label": "Violations/min"},
                {"format": "short"}
            ],
            "legend": {"show": True, "rightSide": False}
        },
        {
            "title": "Violation Severity Distribution",
            "type": "piechart",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 4},
            "targets": [
                {
                    "expr": "sum by (severity) (content_violations_total)",
                    "legendFormat": "{{severity}}"
                }
            ],
            "options": {
                "pieType": "donut",
                "legend": {"displayMode": "table", "placement": "right"}
            }
        },
        
        # Row 3: Profile Distribution
        {
            "title": "Active Policies by Profile",
            "type": "bargauge",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 12},
            "targets": [
                {
                    "expr": "content_active_policies",
                    "legendFormat": "{{profile_name}}"
                }
            ],
            "options": {
                "orientation": "horizontal",
                "displayMode": "gradient"
            }
        },
        {
            "title": "Content Level Violations Heatmap",
            "type": "heatmap",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 12},
            "targets": [
                {
                    "expr": "content_violation_level_difference",
                    "format": "heatmap",
                    "legendFormat": "{{category}}"
                }
            ],
            "options": {
                "calculate": True,
                "calculation": {
                    "xBuckets": {"mode": "count", "value": "10"},
                    "yBuckets": {"mode": "count", "value": "5"}
                },
                "color": {
                    "mode": "spectrum",
                    "scheme": "RdYlGn",
                    "reverse": True
                }
            }
        },
        
        # Row 4: Performance Metrics
        {
            "title": "Policy Lookup Performance",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 0, "y": 20},
            "targets": [
                {
                    "expr": "histogram_quantile(0.50, sum(rate(content_policy_lookup_duration_seconds_bucket[5m])) by (le)) * 1000",
                    "legendFormat": "p50"
                },
                {
                    "expr": "histogram_quantile(0.95, sum(rate(content_policy_lookup_duration_seconds_bucket[5m])) by (le)) * 1000",
                    "legendFormat": "p95"
                },
                {
                    "expr": "histogram_quantile(0.99, sum(rate(content_policy_lookup_duration_seconds_bucket[5m])) by (le)) * 1000",
                    "legendFormat": "p99"
                }
            ],
            "yaxes": [
                {"format": "ms", "label": "Latency"},
                {"format": "short"}
            ]
        },
        {
            "title": "Cache Hit Rate",
            "type": "graph",
            "gridPos": {"h": 8, "w": 12, "x": 12, "y": 20},
            "targets": [
                {
                    "expr": "sum(rate(content_policy_lookup_duration_seconds_count{cache_hit=\"true\"}[5m])) / sum(rate(content_policy_lookup_duration_seconds_count[5m])) * 100",
                    "legendFormat": "Cache Hit %"
                }
            ],
            "yaxes": [
                {"format": "percent", "label": "Hit Rate", "min": 0, "max": 100},
                {"format": "short"}
            ],
            "fieldConfig": {
                "defaults": {
                    "custom": {
                        "fillOpacity": 20,
                        "gradientMode": "opacity"
                    }
                }
            }
        }
    ],
    "tags": ["ethelred", "content-governance", "qa"],
    "templating": {
        "list": [
            {
                "name": "datasource",
                "type": "datasource",
                "query": "prometheus"
            },
            {
                "name": "profile",
                "type": "query",
                "datasource": "$datasource",
                "query": "label_values(content_active_policies, profile_name)",
                "multi": True,
                "includeAll": True
            },
            {
                "name": "category",
                "type": "query", 
                "datasource": "$datasource",
                "query": "label_values(content_violations_total, category)",
                "multi": True,
                "includeAll": True
            }
        ]
    }
}


CONTENT_GOVERNANCE_ALERTS = [
    {
        "name": "HighViolationRate",
        "expr": "sum(rate(content_violations_total[5m]) * 60) > 50",
        "for": "2m",
        "severity": "warning",
        "annotations": {
            "summary": "High content violation rate detected",
            "description": "Content violations exceeding 50/min for 2 minutes"
        }
    },
    {
        "name": "CriticalViolationSpike",
        "expr": "sum(rate(content_violations_total{severity=\"critical\"}[1m]) * 60) > 5",
        "for": "30s",
        "severity": "critical",
        "annotations": {
            "summary": "Critical content violations spike",
            "description": "Critical violations exceeding 5/min"
        }
    },
    {
        "name": "PolicyLookupLatency",
        "expr": "histogram_quantile(0.99, sum(rate(content_policy_lookup_duration_seconds_bucket[5m])) by (le)) > 0.1",
        "for": "5m",
        "severity": "warning",
        "annotations": {
            "summary": "High policy lookup latency",
            "description": "p99 latency exceeding 100ms for 5 minutes"
        }
    },
    {
        "name": "LowCacheHitRate",
        "expr": "sum(rate(content_policy_lookup_duration_seconds_count{cache_hit=\"true\"}[5m])) / sum(rate(content_policy_lookup_duration_seconds_count[5m])) < 0.8",
        "for": "10m",
        "severity": "warning",
        "annotations": {
            "summary": "Low policy cache hit rate",
            "description": "Cache hit rate below 80% for 10 minutes"
        }
    },
    {
        "name": "ModerationServiceSlow",
        "expr": "content_moderation_latency_seconds{quantile=\"0.95\"} > 0.5",
        "for": "5m",
        "severity": "warning",
        "annotations": {
            "summary": "Content moderation service slow",
            "description": "95th percentile moderation latency exceeding 500ms"
        }
    }
]


def generate_grafana_dashboard() -> Dict[str, Any]:
    """Generate complete Grafana dashboard JSON."""
    return {
        "dashboard": CONTENT_GOVERNANCE_DASHBOARD,
        "overwrite": True,
        "message": "Updated Content Governance dashboard"
    }


def generate_prometheus_rules() -> Dict[str, Any]:
    """Generate Prometheus alerting rules."""
    return {
        "groups": [
            {
                "name": "content_governance",
                "interval": "30s",
                "rules": CONTENT_GOVERNANCE_ALERTS
            }
        ]
    }

