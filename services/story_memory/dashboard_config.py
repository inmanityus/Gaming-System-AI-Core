"""
Story Memory Dashboard Configuration
====================================

Grafana dashboard configuration for monitoring the Story Memory System.
"""

from typing import Dict, Any, List


def get_story_memory_dashboard() -> Dict[str, Any]:
    """Get complete Grafana dashboard configuration."""
    
    return {
        "dashboard": {
            "title": "Story Memory System",
            "tags": ["ethelred", "story", "narrative"],
            "timezone": "UTC",
            "refresh": "30s",
            "time": {
                "from": "now-6h",
                "to": "now"
            },
            "panels": _get_panels(),
            "templating": _get_template_variables()
        }
    }


def _get_panels() -> List[Dict[str, Any]]:
    """Get dashboard panels configuration."""
    
    panels = []
    y_pos = 0
    panel_id = 1
    
    # Row: System Overview
    panels.append({
        "id": panel_id,
        "type": "row",
        "title": "System Overview",
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos}
    })
    panel_id += 1
    y_pos += 1
    
    # Active Sessions
    panels.append({
        "id": panel_id,
        "type": "stat",
        "title": "Active Story Sessions",
        "targets": [{
            "expr": "story_active_sessions",
            "refId": "A"
        }],
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": y_pos},
        "options": {
            "colorMode": "value",
            "graphMode": "area"
        }
    })
    panel_id += 1
    
    # Event Rate
    panels.append({
        "id": panel_id,
        "type": "stat",
        "title": "Event Rate",
        "targets": [{
            "expr": "rate(story_events_ingested_total[5m])",
            "refId": "A"
        }],
        "gridPos": {"h": 4, "w": 6, "x": 6, "y": y_pos},
        "unit": "events/sec"
    })
    panel_id += 1
    
    # Cache Hit Rate
    panels.append({
        "id": panel_id,
        "type": "gauge",
        "title": "Cache Hit Rate",
        "targets": [{
            "expr": "story_cache_hit_rate",
            "refId": "A"
        }],
        "gridPos": {"h": 4, "w": 6, "x": 12, "y": y_pos},
        "options": {
            "thresholds": {
                "steps": [
                    {"color": "red", "value": 0},
                    {"color": "yellow", "value": 0.8},
                    {"color": "green", "value": 0.95}
                ]
            },
            "max": 1,
            "min": 0
        }
    })
    panel_id += 1
    
    # Drift Alerts
    panels.append({
        "id": panel_id,
        "type": "stat",
        "title": "Drift Alerts (24h)",
        "targets": [{
            "expr": "increase(story_drift_alerts_total[24h])",
            "refId": "A"
        }],
        "gridPos": {"h": 4, "w": 6, "x": 18, "y": y_pos},
        "options": {
            "colorMode": "background",
            "graphMode": "area"
        }
    })
    panel_id += 1
    y_pos += 5
    
    # Row: Performance Metrics
    panels.append({
        "id": panel_id,
        "type": "row",
        "title": "Performance Metrics",
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos}
    })
    panel_id += 1
    y_pos += 1
    
    # Snapshot Latency
    panels.append({
        "id": panel_id,
        "type": "graph",
        "title": "Snapshot Generation Latency",
        "targets": [
            {
                "expr": 'histogram_quantile(0.5, rate(story_snapshot_latency_seconds_bucket[5m]))',
                "legendFormat": "p50",
                "refId": "A"
            },
            {
                "expr": 'histogram_quantile(0.95, rate(story_snapshot_latency_seconds_bucket[5m]))',
                "legendFormat": "p95",
                "refId": "B"
            },
            {
                "expr": 'histogram_quantile(0.99, rate(story_snapshot_latency_seconds_bucket[5m]))',
                "legendFormat": "p99",
                "refId": "C"
            }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": y_pos},
        "yaxes": [{
            "format": "s",
            "label": "Latency"
        }]
    })
    panel_id += 1
    
    # Event Processing Lag
    panels.append({
        "id": panel_id,
        "type": "graph",
        "title": "Event Processing Lag",
        "targets": [
            {
                "expr": 'histogram_quantile(0.5, rate(story_event_processing_lag_seconds_bucket[5m]))',
                "legendFormat": "p50",
                "refId": "A"
            },
            {
                "expr": 'histogram_quantile(0.95, rate(story_event_processing_lag_seconds_bucket[5m]))',
                "legendFormat": "p95",
                "refId": "B"
            }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": y_pos},
        "yaxes": [{
            "format": "s",
            "label": "Lag"
        }]
    })
    panel_id += 1
    y_pos += 9
    
    # Row: Narrative Analytics
    panels.append({
        "id": panel_id,
        "type": "row",
        "title": "Narrative Analytics",
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos}
    })
    panel_id += 1
    y_pos += 1
    
    # Event Types Distribution
    panels.append({
        "id": panel_id,
        "type": "piechart",
        "title": "Event Types Distribution",
        "targets": [{
            "expr": 'sum by (event_type) (increase(story_events_ingested_total[1h]))',
            "format": "time_series",
            "refId": "A"
        }],
        "gridPos": {"h": 8, "w": 8, "x": 0, "y": y_pos},
        "options": {
            "pieType": "donut",
            "displayLabels": ["name", "percent"]
        }
    })
    panel_id += 1
    
    # Arc Progress Distribution
    panels.append({
        "id": panel_id,
        "type": "bargauge",
        "title": "Arc Progress States",
        "targets": [{
            "expr": 'sum by (progress_state) (increase(arc_progress_updates_total[1h]))',
            "refId": "A"
        }],
        "gridPos": {"h": 8, "w": 8, "x": 8, "y": y_pos},
        "options": {
            "orientation": "horizontal",
            "displayMode": "gradient"
        }
    })
    panel_id += 1
    
    # Moral Alignment Distribution
    panels.append({
        "id": panel_id,
        "type": "heatmap",
        "title": "Player Moral Alignment Distribution",
        "targets": [{
            "expr": "story_moral_alignment",
            "format": "heatmap",
            "refId": "A"
        }],
        "gridPos": {"h": 8, "w": 8, "x": 16, "y": y_pos},
        "options": {
            "calculate": false,
            "yBucketBound": "auto"
        }
    })
    panel_id += 1
    y_pos += 9
    
    # Row: Drift & Conflicts
    panels.append({
        "id": panel_id,
        "type": "row",
        "title": "Narrative Drift & Conflicts",
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos}
    })
    panel_id += 1
    y_pos += 1
    
    # Drift Types
    panels.append({
        "id": panel_id,
        "type": "graph",
        "title": "Narrative Drift by Type",
        "targets": [{
            "expr": 'sum by (drift_type) (rate(story_drift_alerts_total[5m]))',
            "refId": "A"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": y_pos},
        "stack": true,
        "options": {
            "alertThreshold": true
        }
    })
    panel_id += 1
    
    # Conflict Severity
    panels.append({
        "id": panel_id,
        "type": "bargauge",
        "title": "Conflicts by Severity",
        "targets": [{
            "expr": 'sum by (severity) (increase(story_conflicts_detected_total[1h]))',
            "refId": "A"
        }],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": y_pos},
        "options": {
            "displayMode": "gradient",
            "orientation": "horizontal"
        }
    })
    panel_id += 1
    y_pos += 9
    
    # Row: System Health
    panels.append({
        "id": panel_id,
        "type": "row",
        "title": "System Health",
        "gridPos": {"h": 1, "w": 24, "x": 0, "y": y_pos}
    })
    panel_id += 1
    y_pos += 1
    
    # Drift Check Performance
    panels.append({
        "id": panel_id,
        "type": "graph",
        "title": "Drift Check Performance",
        "targets": [{
            "expr": 'story_drift_check_duration_seconds{quantile="0.99"}',
            "legendFormat": "Duration (p99)",
            "refId": "A"
        }],
        "gridPos": {"h": 6, "w": 12, "x": 0, "y": y_pos},
        "yaxes": [{
            "format": "s",
            "label": "Duration"
        }]
    })
    panel_id += 1
    
    # Error Rate
    panels.append({
        "id": panel_id,
        "type": "graph",
        "title": "Error Rate",
        "targets": [{
            "expr": 'sum(rate(story_errors_total[5m]))',
            "legendFormat": "Errors/sec",
            "refId": "A"
        }],
        "gridPos": {"h": 6, "w": 12, "x": 12, "y": y_pos},
        "alert": {
            "conditions": [{
                "evaluator": {
                    "params": [0.1],
                    "type": "gt"
                },
                "operator": {
                    "type": "and"
                },
                "query": {
                    "params": ["A", "5m", "now"]
                },
                "reducer": {
                    "params": [],
                    "type": "avg"
                },
                "type": "query"
            }],
            "executionErrorState": "alerting",
            "for": "5m",
            "frequency": "1m",
            "handler": 1,
            "name": "High Story Memory Error Rate",
            "noDataState": "no_data",
            "notifications": []
        }
    })
    
    return panels


def _get_template_variables() -> Dict[str, List[Dict[str, Any]]]:
    """Get template variables for the dashboard."""
    
    return {
        "list": [
            {
                "name": "player_id",
                "type": "query",
                "datasource": "Prometheus",
                "query": 'label_values(story_events_ingested_total, player_id)',
                "refresh": 2,
                "regex": "",
                "multi": False,
                "includeAll": True,
                "allValue": ".*"
            },
            {
                "name": "event_type",
                "type": "query",
                "datasource": "Prometheus",
                "query": 'label_values(story_events_ingested_total, event_type)',
                "refresh": 2,
                "regex": "",
                "multi": True,
                "includeAll": True,
                "allValue": ".*"
            }
        ]
    }


def export_dashboard_json() -> str:
    """Export dashboard as JSON string for Grafana import."""
    import json
    
    dashboard_config = get_story_memory_dashboard()
    return json.dumps(dashboard_config, indent=2)


# Alerting rules for Prometheus
ALERTING_RULES = """
groups:
  - name: story_memory_alerts
    interval: 30s
    rules:
      - alert: HighSnapshotLatency
        expr: histogram_quantile(0.99, rate(story_snapshot_latency_seconds_bucket[5m])) > 0.1
        for: 5m
        labels:
          severity: warning
          service: story_memory
        annotations:
          summary: "High story snapshot generation latency"
          description: "99th percentile snapshot latency is {{ $value }}s (threshold: 100ms)"
      
      - alert: LowCacheHitRate
        expr: story_cache_hit_rate < 0.8
        for: 10m
        labels:
          severity: warning
          service: story_memory
        annotations:
          summary: "Low story cache hit rate"
          description: "Cache hit rate is {{ $value }} (threshold: 80%)"
      
      - alert: HighDriftRate
        expr: rate(story_drift_alerts_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
          service: story_memory
        annotations:
          summary: "High narrative drift rate"
          description: "Drift alerts rate is {{ $value }}/s"
      
      - alert: EventProcessingLag
        expr: histogram_quantile(0.95, rate(story_event_processing_lag_seconds_bucket[5m])) > 5
        for: 5m
        labels:
          severity: warning
          service: story_memory
        annotations:
          summary: "High event processing lag"
          description: "95th percentile event lag is {{ $value }}s (threshold: 5s)"
      
      - alert: StoryMemoryErrors
        expr: rate(story_errors_total[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
          service: story_memory
        annotations:
          summary: "High error rate in Story Memory"
          description: "Error rate is {{ $value }}/s"
"""

