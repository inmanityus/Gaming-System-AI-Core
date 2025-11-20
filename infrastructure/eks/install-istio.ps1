param(
    [string]$Region = "us-east-1",
    [string]$ClusterName = "ai-core-ml-cluster",
    [string]$IstioVersion = "1.20.1"
)

Write-Host "=== Installing Istio Service Mesh ===" -ForegroundColor Cyan
Write-Host "Istio Version: $IstioVersion" -ForegroundColor White

# Check prerequisites
if (-not (Get-Command kubectl -ErrorAction SilentlyContinue)) {
    Write-Host "[ERROR] kubectl not found. Install kubectl first." -ForegroundColor Red
    exit 1
}

# Download Istio
Write-Host "`nDownloading Istio $IstioVersion..." -ForegroundColor Yellow
$istioUrl = "https://github.com/istio/istio/releases/download/$IstioVersion/istio-$IstioVersion-win.zip"
$istioZip = "istio-$IstioVersion.zip"
$istioDir = "istio-$IstioVersion"

if (-not (Test-Path $istioDir)) {
    Invoke-WebRequest -Uri $istioUrl -OutFile $istioZip
    Expand-Archive -Path $istioZip -DestinationPath . -Force
    Remove-Item $istioZip
}

$istioctlPath = Join-Path $istioDir "bin\istioctl.exe"
Write-Host "✓ Istio downloaded to: $istioDir" -ForegroundColor Green

# Check if Istio is already installed
Write-Host "`nChecking existing Istio installation..." -ForegroundColor Yellow
$existingIstio = & $istioctlPath version --remote=false 2>$null
if ($existingIstio) {
    Write-Host "✓ Istio already installed: $existingIstio" -ForegroundColor Yellow
} else {
    Write-Host "No existing Istio installation found" -ForegroundColor White
}

# Create Istio system namespace
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f -

# Install Istio with production configuration
Write-Host "`nInstalling Istio with production profile..." -ForegroundColor Yellow

# Create custom Istio configuration
$istioConfig = @"
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: ai-core-istio
spec:
  profile: production
  hub: docker.io/istio
  tag: $IstioVersion
  
  components:
    base:
      enabled: true
    pilot:
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 2048Mi
          limits:
            cpu: 2000m
            memory: 4096Mi
        hpaSpec:
          minReplicas: 2
          maxReplicas: 5
          metrics:
          - type: Resource
            resource:
              name: cpu
              target:
                type: Utilization
                averageUtilization: 60
        affinity:
          podAntiAffinity:
            preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: istiod
                topologyKey: kubernetes.io/hostname
    
    # Ingress gateways
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 200m
            memory: 256Mi
          limits:
            cpu: 1000m
            memory: 1024Mi
        service:
          type: LoadBalancer
          ports:
          - port: 15021
            targetPort: 15021
            name: status-port
          - port: 80
            targetPort: 8080
            name: http2
          - port: 443
            targetPort: 8443
            name: https
          - port: 15443
            targetPort: 15443
            name: tls
        hpaSpec:
          minReplicas: 2
          maxReplicas: 10
          metrics:
          - type: Resource
            resource:
              name: cpu
              target:
                type: Utilization
                averageUtilization: 80
    
    # Egress gateway for controlled external access
    egressGateways:
    - name: istio-egressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
  
  meshConfig:
    accessLogFile: /dev/stdout
    accessLogFormat: |
      [%START_TIME%] "%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%" %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT% %DURATION% "%REQ(X-FORWARDED-FOR)%" "%REQ(USER-AGENT)%" "%REQ(X-REQUEST-ID)%" "%REQ(:AUTHORITY)%" "%UPSTREAM_HOST%"
    defaultConfig:
      proxyStatsMatcher:
        inclusionRegexps:
        - ".*outlier_detection.*"
        - ".*osconfig.*"
        - ".*circuit_breakers.*"
        - ".*upstream_rq_retry.*"
        - ".*upstream_rq_pending.*"
        - ".*_cx_.*"
        inclusionSuffixes:
        - "upstream_rq_retry"
        - "upstream_rq_pending_overflow"
        - "upstream_rq_pending_failure_eject"
        - "upstream_rq_pending_overflow"
        - "upstream_rq_pending_total"
        - "upstream_rq_total"
      holdApplicationUntilProxyStarts: true
    extensionProviders:
    - name: prometheus
      prometheus:
        service: prometheus.istio-system.svc.cluster.local
        port: 9090
    - name: skywalking
      envoyOtelAls:
        service: skywalking-oap.istio-system.svc.cluster.local
        port: 11800
    - name: zipkin
      zipkin:
        service: zipkin.istio-system.svc.cluster.local
        port: 9411
        
  values:
    telemetry:
      v2:
        prometheus:
          configOverride:
            inboundSidecar:
              disable_host_header_fallback: true
            outboundSidecar:
              disable_host_header_fallback: true
            gateway:
              disable_host_header_fallback: true
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        holdApplicationUntilProxyStarts: true
        autoInject: enabled
    pilot:
      env:
        PILOT_ENABLE_WORKLOAD_ENTRY_AUTOREGISTRATION: true
        PILOT_ENABLE_CROSS_CLUSTER_WORKLOAD_ENTRY: true
"@

$istioConfig | Out-File -FilePath "istio-operator.yaml" -Encoding UTF8

# Install Istio
Write-Host "Installing Istio (this may take a few minutes)..." -ForegroundColor Yellow
& $istioctlPath install -f istio-operator.yaml -y

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Istio installed successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to install Istio" -ForegroundColor Red
    exit 1
}

# Wait for Istio components to be ready
Write-Host "`nWaiting for Istio components to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=Ready pods --all -n istio-system --timeout=300s

# Install Istio addons (Kiali, Prometheus, Grafana, Jaeger)
Write-Host "`nInstalling Istio observability addons..." -ForegroundColor Yellow

$addonPath = Join-Path $istioDir "samples\addons"
kubectl apply -f $addonPath\prometheus.yaml
kubectl apply -f $addonPath\grafana.yaml
kubectl apply -f $addonPath\jaeger.yaml
kubectl apply -f $addonPath\kiali.yaml

# Create namespace for ML workloads with Istio injection
Write-Host "`nCreating ML workloads namespace with automatic sidecar injection..." -ForegroundColor Yellow
$mlNamespace = @"
apiVersion: v1
kind: Namespace
metadata:
  name: ml-workloads
  labels:
    istio-injection: enabled
    name: ml-workloads
"@

$mlNamespace | kubectl apply -f -

# Configure Istio traffic policies
Write-Host "`nConfiguring Istio traffic policies..." -ForegroundColor Yellow

# Default destination rule for circuit breaking
$destinationRule = @"
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: default-circuit-breaker
  namespace: istio-system
spec:
  host: "*.local"
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 100
        maxRequestsPerConnection: 3
    loadBalancer:
      simple: ROUND_ROBIN
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 30
"@

$destinationRule | kubectl apply -f -

# PeerAuthentication for strict mTLS
$peerAuth = @"
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT
"@

$peerAuth | kubectl apply -f -

# AuthorizationPolicy for default deny
$authPolicy = @"
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-ml-workloads
  namespace: ml-workloads
spec:
  action: ALLOW
  rules:
  - to:
    - operation:
        methods: ["GET", "POST", "PUT", "DELETE"]
    from:
    - source:
        namespaces: ["ml-workloads", "istio-system", "kube-system"]
"@

$authPolicy | kubectl apply -f -

# Create Gateway for ingress traffic
$gateway = @"
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: ai-core-gateway
  namespace: istio-system
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "*"
  - port:
      number: 443
      name: https
      protocol: HTTPS
    tls:
      mode: SIMPLE
      credentialName: ai-core-tls
    hosts:
    - "*"
"@

$gateway | kubectl apply -f -

# Configure Horizontal Pod Autoscaling for Istio components
Write-Host "`nConfiguring autoscaling for Istio components..." -ForegroundColor Yellow
kubectl autoscale deployment istiod -n istio-system --min=2 --max=5 --cpu-percent=60
kubectl autoscale deployment istio-ingressgateway -n istio-system --min=2 --max=10 --cpu-percent=80
kubectl autoscale deployment istio-egressgateway -n istio-system --min=1 --max=5 --cpu-percent=80

# Verify installation
Write-Host "`nVerifying Istio installation..." -ForegroundColor Yellow
& $istioctlPath verify-install

# Get ingress gateway LoadBalancer IP/hostname
Write-Host "`nGetting Istio Ingress Gateway details..." -ForegroundColor Yellow
$ingressService = kubectl get svc istio-ingressgateway -n istio-system -o json | ConvertFrom-Json
$ingressEndpoint = $ingressService.status.loadBalancer.ingress[0]

if ($ingressEndpoint.hostname) {
    $endpoint = $ingressEndpoint.hostname
} elseif ($ingressEndpoint.ip) {
    $endpoint = $ingressEndpoint.ip
} else {
    $endpoint = "pending..."
}

Write-Host "Ingress Gateway Endpoint: $endpoint" -ForegroundColor Green

# Save Istio configuration
$istioInfo = @{
    version = $IstioVersion
    profile = "production"
    ingressEndpoint = $endpoint
    componentsInstalled = @(
        "istiod",
        "istio-ingressgateway",
        "istio-egressgateway",
        "prometheus",
        "grafana",
        "jaeger",
        "kiali"
    )
    namespaces = @{
        system = "istio-system"
        workloads = "ml-workloads"
    }
    security = @{
        mtls = "STRICT"
        authorizationPolicies = @("allow-ml-workloads")
    }
    observability = @{
        prometheusUrl = "http://prometheus.istio-system:9090"
        grafanaUrl = "http://grafana.istio-system:3000"
        kialiUrl = "http://kiali.istio-system:20001"
        jaegerUrl = "http://tracing.istio-system:16686"
    }
    creationDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
}

$istioInfo | ConvertTo-Json -Depth 10 | Out-File -FilePath "istio-config.json" -Encoding UTF8

# Create port-forwarding script for accessing dashboards
$portForwardScript = @'
# Port-forward Istio dashboards
Write-Host "Starting port-forward for Istio dashboards..." -ForegroundColor Cyan

# Kiali Dashboard
Start-Job -Name "kiali" -ScriptBlock {
    kubectl port-forward svc/kiali -n istio-system 20001:20001
}

# Grafana Dashboard
Start-Job -Name "grafana" -ScriptBlock {
    kubectl port-forward svc/grafana -n istio-system 3000:3000
}

# Prometheus
Start-Job -Name "prometheus" -ScriptBlock {
    kubectl port-forward svc/prometheus -n istio-system 9090:9090
}

# Jaeger
Start-Job -Name "jaeger" -ScriptBlock {
    kubectl port-forward svc/tracing -n istio-system 16686:16686
}

Write-Host "`nDashboards available at:" -ForegroundColor Green
Write-Host "  Kiali: http://localhost:20001" -ForegroundColor White
Write-Host "  Grafana: http://localhost:3000" -ForegroundColor White
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor White
Write-Host "  Jaeger: http://localhost:16686" -ForegroundColor White
Write-Host "`nPress Ctrl+C to stop port forwarding" -ForegroundColor Yellow

# Wait
Get-Job | Wait-Job
'@

$portForwardScript | Out-File -FilePath "port-forward-istio.ps1" -Encoding UTF8

Write-Host "`n=== Istio Installation Complete ===" -ForegroundColor Green
Write-Host "Configuration saved to: istio-config.json" -ForegroundColor Cyan

Write-Host "`nIstio Features Enabled:" -ForegroundColor Yellow
Write-Host "  ✓ Automatic sidecar injection" -ForegroundColor White
Write-Host "  ✓ Mutual TLS (mTLS) encryption" -ForegroundColor White
Write-Host "  ✓ Circuit breaking and retry policies" -ForegroundColor White
Write-Host "  ✓ Load balancing and failover" -ForegroundColor White
Write-Host "  ✓ Distributed tracing" -ForegroundColor White
Write-Host "  ✓ Metrics and monitoring" -ForegroundColor White

Write-Host "`nAccess dashboards:" -ForegroundColor Yellow
Write-Host "  Run: .\port-forward-istio.ps1" -ForegroundColor White

Write-Host "`nUseful commands:" -ForegroundColor Yellow
Write-Host "  - Check proxy status: $istioctlPath proxy-status" -ForegroundColor White
Write-Host "  - Analyze configuration: $istioctlPath analyze" -ForegroundColor White
Write-Host "  - View mesh topology: Open Kiali dashboard" -ForegroundColor White
Write-Host "  - Monitor traffic: Open Grafana dashboard" -ForegroundColor White
