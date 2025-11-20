param(
    [string]$DomainName = "ai-core-opensearch",
    [string]$ConfigFile = "opensearch-endpoints.json"
)

Write-Host "=== Setting up OpenSearch Index Patterns and Policies ===" -ForegroundColor Cyan

# Load configuration
if (-not (Test-Path $ConfigFile)) {
    Write-Host "[ERROR] Configuration file not found: $ConfigFile" -ForegroundColor Red
    Write-Host "Please run deploy-opensearch-domain.ps1 first" -ForegroundColor Yellow
    exit 1
}

$config = Get-Content -Path $ConfigFile | ConvertFrom-Json
$endpoint = $config.Endpoint
$secretName = $config.SecretName

# Get credentials from Secrets Manager
Write-Host "Retrieving credentials from Secrets Manager..." -ForegroundColor Yellow
$credentials = aws secretsmanager get-secret-value --secret-id $secretName --query SecretString --output text | ConvertFrom-Json
$username = $credentials.username
$password = $credentials.password

# Create base64 encoded credentials for basic auth
$authString = "${username}:${password}"
$authBytes = [System.Text.Encoding]::UTF8.GetBytes($authString)
$authBase64 = [System.Convert]::ToBase64String($authBytes)
$headers = @{
    "Authorization" = "Basic $authBase64"
    "Content-Type" = "application/json"
}

Write-Host "✓ Credentials retrieved" -ForegroundColor Green

# Function to make OpenSearch API calls
function Invoke-OpenSearchAPI {
    param(
        [string]$Method,
        [string]$Path,
        [object]$Body = $null
    )
    
    $uri = "$endpoint$Path"
    
    try {
        if ($Body) {
            $response = Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -Body ($Body | ConvertTo-Json -Depth 10) -SkipCertificateCheck
        } else {
            $response = Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -SkipCertificateCheck
        }
        return $response
    } catch {
        Write-Host "[ERROR] API call failed: $_" -ForegroundColor Red
        return $null
    }
}

# Create index lifecycle policies
Write-Host "`nCreating Index State Management (ISM) policies..." -ForegroundColor Yellow

# Application logs policy
$appLogsPolicy = @{
    policy = @{
        description = "Policy for application logs with hot-warm-delete lifecycle"
        default_state = "hot"
        states = @(
            @{
                name = "hot"
                actions = @(
                    @{
                        rollover = @{
                            min_size = "10gb"
                            min_index_age = "1d"
                        }
                    }
                )
                transitions = @(
                    @{
                        state_name = "warm"
                        conditions = @{
                            min_index_age = "7d"
                        }
                    }
                )
            },
            @{
                name = "warm"
                actions = @(
                    @{
                        replica_count = @{
                            number_of_replicas = 1
                        }
                    },
                    @{
                        shrink = @{
                            num_new_shards = 1
                            target_index_name_template = @{
                                source = "{{ctx.index}}"
                                lang = "mustache"
                            }
                        }
                    }
                )
                transitions = @(
                    @{
                        state_name = "delete"
                        conditions = @{
                            min_index_age = "30d"
                        }
                    }
                )
            },
            @{
                name = "delete"
                actions = @(
                    @{
                        delete = @{}
                    }
                )
                transitions = @()
            }
        )
        ism_template = @(
            @{
                index_patterns = @("app-logs-*", "service-logs-*")
                priority = 100
            }
        )
    }
}

$result = Invoke-OpenSearchAPI -Method PUT -Path "/_plugins/_ism/policies/app-logs-policy" -Body $appLogsPolicy
if ($result) {
    Write-Host "✓ Created app-logs-policy" -ForegroundColor Green
}

# Metrics policy
$metricsPolicy = @{
    policy = @{
        description = "Policy for metrics data with shorter retention"
        default_state = "hot"
        states = @(
            @{
                name = "hot"
                actions = @(
                    @{
                        rollover = @{
                            min_size = "5gb"
                            min_index_age = "1d"
                        }
                    }
                )
                transitions = @(
                    @{
                        state_name = "delete"
                        conditions = @{
                            min_index_age = "7d"
                        }
                    }
                )
            },
            @{
                name = "delete"
                actions = @(
                    @{
                        delete = @{}
                    }
                )
                transitions = @()
            }
        )
        ism_template = @(
            @{
                index_patterns = @("metrics-*", "performance-*")
                priority = 100
            }
        )
    }
}

$result = Invoke-OpenSearchAPI -Method PUT -Path "/_plugins/_ism/policies/metrics-policy" -Body $metricsPolicy
if ($result) {
    Write-Host "✓ Created metrics-policy" -ForegroundColor Green
}

# Create index templates
Write-Host "`nCreating index templates..." -ForegroundColor Yellow

# Application logs template
$appLogsTemplate = @{
    index_patterns = @("app-logs-*", "service-logs-*")
    priority = 100
    template = @{
        settings = @{
            number_of_shards = 3
            number_of_replicas = 2
            "index.refresh_interval" = "5s"
            "index.codec" = "best_compression"
        }
        mappings = @{
            properties = @{
                "@timestamp" = @{
                    type = "date"
                }
                level = @{
                    type = "keyword"
                }
                service = @{
                    type = "keyword"
                }
                message = @{
                    type = "text"
                    fields = @{
                        keyword = @{
                            type = "keyword"
                            ignore_above = 256
                        }
                    }
                }
                trace_id = @{
                    type = "keyword"
                }
                user_id = @{
                    type = "keyword"
                }
                request_id = @{
                    type = "keyword"
                }
                duration_ms = @{
                    type = "long"
                }
                error = @{
                    type = "object"
                    properties = @{
                        type = @{
                            type = "keyword"
                        }
                        message = @{
                            type = "text"
                        }
                        stack_trace = @{
                            type = "text"
                        }
                    }
                }
            }
        }
    }
}

$result = Invoke-OpenSearchAPI -Method PUT -Path "/_index_template/app-logs-template" -Body $appLogsTemplate
if ($result) {
    Write-Host "✓ Created app-logs-template" -ForegroundColor Green
}

# Metrics template
$metricsTemplate = @{
    index_patterns = @("metrics-*", "performance-*")
    priority = 100
    template = @{
        settings = @{
            number_of_shards = 1
            number_of_replicas = 1
            "index.refresh_interval" = "10s"
        }
        mappings = @{
            properties = @{
                "@timestamp" = @{
                    type = "date"
                }
                metric_name = @{
                    type = "keyword"
                }
                value = @{
                    type = "double"
                }
                unit = @{
                    type = "keyword"
                }
                service = @{
                    type = "keyword"
                }
                instance = @{
                    type = "keyword"
                }
                environment = @{
                    type = "keyword"
                }
                tags = @{
                    type = "object"
                }
            }
        }
    }
}

$result = Invoke-OpenSearchAPI -Method PUT -Path "/_index_template/metrics-template" -Body $metricsTemplate
if ($result) {
    Write-Host "✓ Created metrics-template" -ForegroundColor Green
}

# Create initial indices
Write-Host "`nCreating initial indices..." -ForegroundColor Yellow

$initialIndices = @(
    "app-logs-000001",
    "service-logs-000001",
    "metrics-000001",
    "performance-000001"
)

foreach ($index in $initialIndices) {
    $indexSettings = @{
        aliases = @{
            $index.Replace("-000001", "-write") = @{}
            $index.Replace("-000001", "-read") = @{
                is_write_index = $false
            }
        }
    }
    
    $result = Invoke-OpenSearchAPI -Method PUT -Path "/$index" -Body $indexSettings
    if ($result) {
        Write-Host "✓ Created index: $index" -ForegroundColor Green
    }
}

# Set up anomaly detector for application errors
Write-Host "`nSetting up anomaly detection..." -ForegroundColor Yellow

$anomalyDetector = @{
    name = "application-error-detector"
    description = "Detect anomalous error rates in application logs"
    time_field = "@timestamp"
    indices = @("app-logs-*", "service-logs-*")
    feature_attributes = @(
        @{
            feature_name = "error_count"
            feature_enabled = $true
            aggregation_query = @{
                error_count = @{
                    filter = @{
                        term = @{
                            level = "error"
                        }
                    }
                    aggs = @{
                        error_count = @{
                            value_count = @{
                                field = "_index"
                            }
                        }
                    }
                }
            }
        }
    )
    detection_interval = @{
        period = @{
            interval = 5
            unit = "Minutes"
        }
    }
    window_delay = @{
        period = @{
            interval = 1
            unit = "Minutes"
        }
    }
    shingle_size = 8
}

$result = Invoke-OpenSearchAPI -Method POST -Path "/_plugins/_anomaly_detection/detectors" -Body $anomalyDetector
if ($result) {
    Write-Host "✓ Created anomaly detector: application-error-detector" -ForegroundColor Green
    
    # Start the detector
    $detectorId = $result._id
    $startResult = Invoke-OpenSearchAPI -Method POST -Path "/_plugins/_anomaly_detection/detectors/$detectorId/_start"
    if ($startResult) {
        Write-Host "✓ Started anomaly detector" -ForegroundColor Green
    }
}

# Create alerting monitors
Write-Host "`nSetting up alerting monitors..." -ForegroundColor Yellow

$highErrorRateMonitor = @{
    name = "high-error-rate-monitor"
    enabled = $true
    schedule = @{
        period = @{
            interval = 5
            unit = "MINUTES"
        }
    }
    inputs = @(
        @{
            search = @{
                indices = @("app-logs-*")
                query = @{
                    size = 0
                    query = @{
                        bool = @{
                            filter = @(
                                @{
                                    range = @{
                                        "@timestamp" = @{
                                            gte = "now-5m"
                                        }
                                    }
                                },
                                @{
                                    term = @{
                                        level = "error"
                                    }
                                }
                            )
                        }
                    }
                    aggs = @{
                        error_count = @{
                            value_count = @{
                                field = "_index"
                            }
                        }
                    }
                }
            }
        }
    )
    triggers = @(
        @{
            name = "error-rate-trigger"
            severity = "2"
            condition = @{
                script = @{
                    source = "ctx.results[0].aggregations.error_count.value > 100"
                    lang = "painless"
                }
            }
            actions = @()
        }
    )
}

$result = Invoke-OpenSearchAPI -Method POST -Path "/_plugins/_alerting/monitors" -Body $highErrorRateMonitor
if ($result) {
    Write-Host "✓ Created monitor: high-error-rate-monitor" -ForegroundColor Green
}

# Display summary
Write-Host "`n=== OpenSearch Configuration Complete ===" -ForegroundColor Green
Write-Host "✓ ISM Policies created:" -ForegroundColor White
Write-Host "  - app-logs-policy (hot-warm-delete lifecycle)" -ForegroundColor White
Write-Host "  - metrics-policy (7-day retention)" -ForegroundColor White
Write-Host "✓ Index templates created:" -ForegroundColor White
Write-Host "  - app-logs-template" -ForegroundColor White
Write-Host "  - metrics-template" -ForegroundColor White
Write-Host "✓ Initial indices created with aliases" -ForegroundColor White
Write-Host "✓ Anomaly detection configured" -ForegroundColor White
Write-Host "✓ Alerting monitor configured" -ForegroundColor White

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Configure log shipping from your applications"
Write-Host "2. Set up Logstash or Fluent Bit for log ingestion"
Write-Host "3. Create custom dashboards in OpenSearch Dashboards"
Write-Host "4. Configure alert destinations (SNS, Slack, etc.)"
Write-Host "5. Set up snapshot repository for backups"
