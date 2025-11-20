param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-ml-cluster"
)

Write-Host "=== Installing Prometheus and Grafana Monitoring Stack ===" -ForegroundColor Cyan

# Check prerequisites
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] kubectl not found. Install kubectl first." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command helm -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] Helm not found. Installing Helm..." -ForegroundColor Yellow
    # Install Helm
    Invoke-WebRequest -Uri "https://get.helm.sh/helm-v3.13.3-windows-amd64.zip" -OutFile "helm.zip"
    Expand-Archive -Path "helm.zip" -DestinationPath "helm" -Force
    $env:Path += ";$(Get-Location)\helm\windows-amd64"
    Remove-Item "helm.zip"
}

# Add Prometheus Helm repository
Write-Host "`nAdding Prometheus Helm repository..." -ForegroundColor Yellow
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Create monitoring namespace
Write-Host "`nCreating monitoring namespace..." -ForegroundColor Yellow
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Label namespace for network policies
kubectl label namespace monitoring name=monitoring --overwrite

# Create values file for Prometheus
Write-Host "`nCreating Prometheus configuration..." -ForegroundColor Yellow

$prometheusValues = @"
prometheus:
  prometheusSpec:
    replicas: 2
    retention: 30d
    retentionSize: 50GB
    
    # Resource limits
    resources:
      requests:
        memory: 2Gi
        cpu: 500m
      limits:
        memory: 4Gi
        cpu: 2000m
    
    # Storage configuration
    storageSpec:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 100Gi
    
    # Service monitors
    serviceMonitorSelectorNilUsesHelmValues: false
    serviceMonitorNamespaceSelector: {}
    serviceMonitorSelector: {}
    
    # Pod monitors
    podMonitorSelectorNilUsesHelmValues: false
    podMonitorNamespaceSelector: {}
    podMonitorSelector: {}
    
    # Additional scrape configs for GPU metrics
    additionalScrapeConfigs:
    - job_name: 'nvidia-dcgm'
      kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
          - gpu-operator-resources
      relabel_configs:
      - source_labels: [__meta_kubernetes_endpoints_name]
        action: keep
        regex: 'nvidia-dcgm-exporter'
      - source_labels: [__meta_kubernetes_endpoint_port_name]
        action: keep
        regex: 'metrics'
    
    # ML-specific metrics
    - job_name: 'ml-models'
      kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
          - ml-workloads
      relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__address__, __meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: \$1:\$2
        target_label: __address__

# Prometheus Operator configuration
prometheusOperator:
  resources:
    requests:
      cpu: 200m
      memory: 200Mi
    limits:
      cpu: 500m
      memory: 500Mi
  
  # High availability
  replicas: 1

# Alertmanager configuration
alertmanager:
  alertmanagerSpec:
    replicas: 2
    retention: 120h
    storage:
      volumeClaimTemplate:
        spec:
          storageClassName: gp3
          accessModes: ["ReadWriteOnce"]
          resources:
            requests:
              storage: 10Gi
    
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
      limits:
        cpu: 500m
        memory: 512Mi

# Grafana configuration
grafana:
  enabled: true
  replicas: 2
  
  resources:
    requests:
      cpu: 100m
      memory: 128Mi
    limits:
      cpu: 500m
      memory: 512Mi
  
  persistence:
    enabled: true
    storageClassName: gp3
    size: 10Gi
  
  adminPassword: "$(New-Guid)"
  
  # Data sources
  sidecar:
    datasources:
      enabled: true
      defaultDatasourceEnabled: true
    dashboards:
      enabled: true
      searchNamespace: ALL
  
  # Pre-installed dashboards
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
      - name: 'ml-dashboards'
        orgId: 1
        folder: 'ML Workloads'
        type: file
        disableDeletion: false
        editable: true
        options:
          path: /var/lib/grafana/dashboards/ml-dashboards

# Node exporter for system metrics
nodeExporter:
  enabled: true

# Kube-state-metrics for Kubernetes metrics
kubeStateMetrics:
  enabled: true

# Additional exporters
additionalPrometheusRulesMap:
  ml-alerts:
    groups:
    - name: ml-workload-alerts
      interval: 30s
      rules:
      - alert: HighGPUUtilization
        expr: |
          avg by (instance) (
            DCGM_FI_DEV_GPU_UTIL
          ) > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High GPU utilization on {{ \$labels.instance }}"
          description: "GPU utilization has been above 90% for 5 minutes"
      
      - alert: GPUMemoryPressure
        expr: |
          (DCGM_FI_DEV_MEM_COPY_UTIL / DCGM_FI_DEV_MEM_COPY_UTIL_TOTAL) * 100 > 90
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "GPU memory pressure on {{ \$labels.instance }}"
          description: "GPU memory utilization above 90%"
      
      - alert: MLModelLatencyHigh
        expr: |
          histogram_quantile(0.99, sum(rate(model_inference_duration_seconds_bucket[5m])) by (le, model)) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High inference latency for model {{ \$labels.model }}"
          description: "99th percentile latency is above 1 second"
"@

$prometheusValues | Out-File -FilePath "prometheus-values.yaml" -Encoding UTF8

# Install kube-prometheus-stack
Write-Host "`nInstalling kube-prometheus-stack (this may take several minutes)..." -ForegroundColor Yellow
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack `
    --namespace monitoring `
    --values prometheus-values.yaml `
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false `
    --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false `
    --wait `
    --timeout 10m

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Prometheus stack installed successfully" -ForegroundColor Green
} else {
    Write-Host "[WARNING] Prometheus stack installation had issues" -ForegroundColor Yellow
}

# Install NVIDIA GPU Operator for GPU monitoring
Write-Host "`nChecking for GPU nodes..." -ForegroundColor Yellow
$gpuNodes = kubectl get nodes -L accelerator --no-headers | Where-Object { $_ -match "nvidia-gpu" }

if ($gpuNodes) {
    Write-Host "GPU nodes found. Installing NVIDIA GPU Operator..." -ForegroundColor Yellow
    
    helm repo add nvidia https://helm.ngc.nvidia.com/nvidia
    helm repo update
    
    helm upgrade --install gpu-operator nvidia/gpu-operator `
        --namespace gpu-operator-resources `
        --create-namespace `
        --set driver.enabled=true `
        --set dcgm.enabled=true `
        --set dcgmExporter.enabled=true `
        --set migManager.enabled=false `
        --wait `
        --timeout 10m
    
    Write-Host "✓ GPU Operator installed" -ForegroundColor Green
} else {
    Write-Host "No GPU nodes found. Skipping GPU Operator installation." -ForegroundColor White
}

# Create custom Grafana dashboards for ML workloads
Write-Host "`nCreating ML-specific Grafana dashboards..." -ForegroundColor Yellow

$mlDashboard = @'
{
  "dashboard": {
    "id": null,
    "uid": "ml-workloads",
    "title": "ML Workloads Overview",
    "panels": [
      {
        "datasource": "Prometheus",
        "fieldConfig": {
          "defaults": {
            "unit": "percent"
          }
        },
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 0,
          "y": 0
        },
        "id": 1,
        "options": {
          "orientation": "auto",
          "reduceOptions": {
            "calcs": ["lastNotNull"],
            "fields": "",
            "values": false
          }
        },
        "pluginVersion": "8.0.0",
        "targets": [
          {
            "expr": "avg(DCGM_FI_DEV_GPU_UTIL)",
            "refId": "A"
          }
        ],
        "title": "Average GPU Utilization",
        "type": "gauge"
      },
      {
        "datasource": "Prometheus",
        "gridPos": {
          "h": 8,
          "w": 12,
          "x": 12,
          "y": 0
        },
        "id": 2,
        "targets": [
          {
            "expr": "sum(rate(model_inference_count_total[5m])) by (model)",
            "refId": "A"
          }
        ],
        "title": "Model Inference Rate",
        "type": "graph"
      }
    ]
  },
  "folderId": 0,
  "overwrite": true
}
'@

# Create ConfigMap with dashboard
$dashboardConfigMap = @"
apiVersion: v1
kind: ConfigMap
metadata:
  name: ml-workloads-dashboard
  namespace: monitoring
  labels:
    grafana_dashboard: "1"
data:
  ml-workloads.json: |
$(($mlDashboard | ConvertFrom-Json | ConvertTo-Json -Depth 10 -Compress) -split "`n" | ForEach-Object { "    $_" })
"@

$dashboardConfigMap | kubectl apply -f -

# Create service monitors for Istio
if (kubectl get namespace istio-system -o name 2>$null) {
    Write-Host "`nCreating ServiceMonitors for Istio..." -ForegroundColor Yellow
    
    $istioServiceMonitor = @"
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: istio-component-monitor
  namespace: monitoring
spec:
  jobLabel: istio
  targetLabels: [app]
  selector:
    matchExpressions:
    - {key: istio, operator: In, values: [pilot, ingressgateway, egressgateway]}
  namespaceSelector:
    matchNames:
    - istio-system
  endpoints:
  - port: http-monitoring
    interval: 15s
"@
    
    $istioServiceMonitor | kubectl apply -f -
}

# Create ingress for Grafana (optional)
$grafanaIngress = @"
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: grafana
  namespace: monitoring
  annotations:
    kubernetes.io/ingress.class: alb
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
spec:
  rules:
  - host: grafana.ml.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: prometheus-grafana
            port:
              number: 80
"@

# Get Grafana admin password
$grafanaSecret = kubectl get secret prometheus-grafana -n monitoring -o json | ConvertFrom-Json
$grafanaPassword = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($grafanaSecret.data.'admin-password'))

Write-Host "`n=== Monitoring Stack Installation Complete ===" -ForegroundColor Green

Write-Host "`nAccess Information:" -ForegroundColor Cyan
Write-Host "  Grafana:" -ForegroundColor White
Write-Host "    URL: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80" -ForegroundColor White
Write-Host "    Username: admin" -ForegroundColor White
Write-Host "    Password: $grafanaPassword" -ForegroundColor White

Write-Host "`n  Prometheus:" -ForegroundColor White
Write-Host "    URL: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090" -ForegroundColor White

Write-Host "`n  Alertmanager:" -ForegroundColor White
Write-Host "    URL: kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093" -ForegroundColor White

# Save monitoring configuration
$monitoringInfo = @{
    prometheus = @{
        retention = "30d"
        storage = "100Gi"
        replicas = 2
    }
    grafana = @{
        replicas = 2
        adminPassword = $grafanaPassword
        dashboards = @("ml-workloads", "kubernetes-cluster", "node-exporter")
    }
    alertmanager = @{
        retention = "120h"
        storage = "10Gi"
        replicas = 2
    }
    exporters = @(
        "node-exporter",
        "kube-state-metrics",
        "dcgm-exporter"
    )
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$monitoringInfo | ConvertTo-Json -Depth 10 | Out-File -FilePath "monitoring-config.json" -Encoding UTF8

# Create port-forward script
$portForwardScript = @'
Write-Host "Starting port-forward for monitoring services..." -ForegroundColor Cyan

# Grafana
Start-Job -Name "grafana" -ScriptBlock {
    kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
}

# Prometheus
Start-Job -Name "prometheus" -ScriptBlock {
    kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
}

# Alertmanager
Start-Job -Name "alertmanager" -ScriptBlock {
    kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-alertmanager 9093:9093
}

Write-Host "`nServices available at:" -ForegroundColor Green
Write-Host "  Grafana: http://localhost:3000" -ForegroundColor White
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  Alertmanager: http://localhost:9093" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop" -ForegroundColor Yellow

Get-Job | Wait-Job
'@

$portForwardScript | Out-File -FilePath "port-forward-monitoring.ps1" -Encoding UTF8

Write-Host "`nMonitoring Features:" -ForegroundColor Yellow
Write-Host "  ✓ Prometheus for metrics collection" -ForegroundColor White
Write-Host "  ✓ Grafana for visualization" -ForegroundColor White
Write-Host "  ✓ Alertmanager for alert routing" -ForegroundColor White
Write-Host "  ✓ GPU metrics (if GPU nodes present)" -ForegroundColor White
Write-Host "  ✓ Kubernetes cluster metrics" -ForegroundColor White
Write-Host "  ✓ Istio service mesh metrics" -ForegroundColor White

Write-Host "`nUseful commands:" -ForegroundColor Yellow
Write-Host "  - Access dashboards: .\port-forward-monitoring.ps1" -ForegroundColor White
Write-Host "  - Check metrics: kubectl top nodes" -ForegroundColor White
Write-Host "  - View alerts: kubectl get prometheusrule -A" -ForegroundColor White
Write-Host "  - Check exporters: kubectl get pods -n monitoring" -ForegroundColor White

# Clean up temporary files
Remove-Item -Path "prometheus-values.yaml" -ErrorAction SilentlyContinue
