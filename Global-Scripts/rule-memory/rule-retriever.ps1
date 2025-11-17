<#
.SYNOPSIS
    Rule Memory Retriever - Gets relevant rules based on semantic search

.DESCRIPTION
    Takes a query/prompt and returns the most relevant rules using semantic similarity search.
    Used to dynamically inject rules into context before sending to LLM.

.PARAMETER Query
    User query/prompt to find relevant rules for

.PARAMETER Limit
    Maximum number of rules to return (default: 10)

.PARAMETER MinSimilarity
    Minimum similarity threshold (0.0-1.0, default: 0.7)

.PARAMETER MandatoryOnly
    Return only mandatory rules

.PARAMETER Database
    PostgreSQL database name (default: ai_knowledge)

.PARAMETER Format
    Output format: 'json', 'text', 'context' (default: context - ready for injection)
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Query,
    
    [Parameter()]
    [int]$Limit = 10,
    
    [Parameter()]
    [double]$MinSimilarity = 0.7,
    
    [Parameter()]
    [switch]$MandatoryOnly,
    
    [Parameter()]
    [string]$Database = 'ai_knowledge',
    
    [Parameter()]
    [ValidateSet('json', 'text', 'context')]
    [string]$Format = 'context'
)

$ErrorActionPreference = 'Stop'

function Get-Embedding {
    param([string]$Text)
    
    $pythonScript = Join-Path $PSScriptRoot "embedding-generator.py"
    if (-not (Test-Path $pythonScript)) {
        throw "Embedding generator script not found: $pythonScript"
    }
    
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) {
        $python = Get-Command python3 -ErrorAction SilentlyContinue
    }
    if (-not $python) {
        throw "Python not found"
    }
    
    $embeddingJson = $Text | & $python.Path $pythonScript --text $Text 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python script failed: $embeddingJson"
    }
    return ($embeddingJson | ConvertFrom-Json)
}

function Format-RulesForContext {
    param(
        [array]$Rules,
        [string]$Query
    )
    
    $mandatoryRules = $Rules | Where-Object { $_.is_mandatory -eq $true }
    $contextualRules = $Rules | Where-Object { $_.is_mandatory -eq $false }
    
    $output = @"
[RULE CONTEXT - AUTOMATICALLY LOADED]
The following rules are active for this session:

"@
    
    if ($mandatoryRules) {
        $output += @"
[MANDATORY RULES - ALWAYS APPLIED]
"@
        $idx = 1
        foreach ($rule in $mandatoryRules) {
            $title = if ($rule.title) { " - $($rule.title)" } else { "" }
            $output += @"

$idx. Rule$title (Source: $($rule.source)):
$($rule.content)
"@
            $idx++
        }
        $output += "`n"
    }
    
    if ($contextualRules) {
        $output += @"
[CONTEXT-RELEVANT RULES - SEMANTIC MATCH]
"@
        $idx = 1
        foreach ($rule in $contextualRules) {
            $similarity = [math]::Round($rule.similarity * 100, 1)
            $title = if ($rule.title) { " - $($rule.title)" } else { "" }
            $output += @"

$idx. Rule$title (Similarity: ${similarity}%, Source: $($rule.source)):
$($rule.content)
"@
            $idx++
        }
        $output += "`n"
    }
    
    $output += @"
---
End of Rule Context
---

[USER QUERY]
$Query

"@
    
    return $output
}

# Generate query embedding
Write-Host "Generating embedding for query..." -NoNewline
try {
    $queryEmbedding = Get-Embedding -Text $Query
    Write-Host " [OK]"
} catch {
    Write-Error "Failed to generate embedding: $_"
    exit 1
}

# Prepare embedding array for PostgreSQL
$embeddingArray = "{" + ($queryEmbedding -join ',') + "}"

# Build SQL query
$mandatoryFlag = if ($MandatoryOnly) { "true" } else { "false" }
$query = @"
SELECT 
    rule_id::text,
    content,
    COALESCE(title, '') as title,
    source,
    priority,
    similarity,
    is_mandatory
FROM find_relevant_rules(
    '$embeddingArray'::vector,
    $mandatoryFlag,
    $Limit,
    $MinSimilarity,
    NULL
)
ORDER BY is_mandatory DESC, similarity DESC
"@

# Execute query
Write-Host "Searching for relevant rules..." -NoNewline
try {
    $results = & psql -h localhost -U postgres -d $Database -t -A -F "|" -c $query 2>&1
    
    if ($LASTEXITCODE -ne 0) {
        throw "Query failed: $results"
    }
    
    Write-Host " [OK]"
    
    # Parse results
    $rules = @()
    if ($results) {
        $results = $results | Where-Object { $_.Trim() }
        foreach ($line in $results) {
            if ($line.Trim()) {
                $parts = $line -split '\|'
                if ($parts.Count -ge 7) {
                    $rules += @{
                        rule_id = $parts[0]
                        content = $parts[1]
                        title = $parts[2]
                        source = $parts[3]
                        priority = [int]$parts[4]
                        similarity = [double]$parts[5]
                        is_mandatory = [bool]::Parse($parts[6])
                    }
                }
            }
        }
    }
    
    # Format output
    switch ($Format) {
        'json' {
            $rules | ConvertTo-Json -Depth 10
        }
        'text' {
            foreach ($rule in $rules) {
                $title = if ($rule.title) { " - $($rule.title)" } else { "" }
                $similarity = [math]::Round($rule.similarity * 100, 1)
                Write-Host "`n[$($rule.source)]$title (Similarity: ${similarity}%)"
                Write-Host $rule.content
                Write-Host "---"
            }
        }
        'context' {
            Format-RulesForContext -Rules $rules -Query $Query
        }
    }
    
} catch {
    Write-Error "Database query failed: $_"
    exit 1
}








