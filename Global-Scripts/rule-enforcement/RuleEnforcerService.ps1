#Requires -Version 7.0
#Requires -Modules BurntToast

<#
.SYNOPSIS
    Windows Service that enforces ALL rules from /all-rules command
    
.DESCRIPTION
    This service continuously monitors AI coding sessions and enforces all rules
    defined in Global-Commands/all-rules.md. It reads the rules file on startup
    and watches for changes to reload rules dynamically.
    
    The service monitors:
    - File system changes (detects AI session activity)
    - Session events (start/stop, pair confirmation, tests, milestones)
    - Timer service status
    - Memory consolidation
    - Work visibility
    
.NOTES
    Service Name: RuleEnforcerService
    Installation: Use Global-Scripts/rule-enforcement/Install-RuleEnforcerService.ps1
#>

param(
    [string]$ProjectRoot = $PWD.Path,
    [string]$RulesPath = "",
    [int]$Port = 5757,
    [string]$StatePath = "$env:ProgramData\RuleEnforcer\state",
    [string]$LogPath = "$env:ProgramData\RuleEnforcer\logs"
)

using namespace System.Net
using namespace System.IO

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# --- CONFIGURATION ---
if ([string]::IsNullOrWhiteSpace($RulesPath)) {
    # Try to find Global-Commands/all-rules.md relative to project root
    $possiblePaths = @(
        (Join-Path $ProjectRoot "Global-Commands\all-rules.md"),
        (Join-Path $ProjectRoot ".cursor\rules\all-rules.md"),
        "$env:USERPROFILE\Documents\PowerShell\Global-Commands\all-rules.md",
        "$env:ProgramData\RuleEnforcer\all-rules.md"
    )
    
    foreach ($path in $possiblePaths) {
        if (Test-Path $path) {
            $RulesPath = $path
            break
        }
    }
}

if ([string]::IsNullOrWhiteSpace($RulesPath) -or -not (Test-Path $RulesPath)) {
    Write-Error "Rules file not found. Searched: $($possiblePaths -join ', ')"
    exit 1
}

# Ensure directories exist
New-Item -ItemType Directory -Path $StatePath -Force | Out-Null
New-Item -ItemType Directory -Path $LogPath -Force | Out-Null

$logFile = Join-Path $LogPath "RuleEnforcer-$(Get-Date -Format 'yyyy-MM-dd').log"
Start-Transcript -Path $logFile -Append

Write-Output "=========================================="
Write-Output "RuleEnforcerService Starting"
Write-Output "Rules Path: $RulesPath"
Write-Output "Project Root: $ProjectRoot"
Write-Output "State Path: $StatePath"
Write-Output "Log Path: $LogPath"
Write-Output "Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Output "=========================================="

# --- GLOBAL STATE ---
$Global:Rules = @()
$Global:Sessions = @{}
$Global:Violations = @{}
$Global:Timers = @{}
$Global:LastRulesLoad = Get-Date
$Global:RulesFileWatcher = $null
$Global:HttpListener = $null
$Global:ServiceRunning = $true

# --- FUNCTIONS ---

function Parse-AllRulesMarkdown {
    param([string]$FilePath)
    
    Write-Output "INFO: Parsing rules from '$FilePath'"
    
    if (-not (Test-Path $FilePath)) {
        Write-Warning "WARN: Rules file not found: $FilePath"
        return @()
    }
    
    try {
        $content = Get-Content $FilePath -Raw -Encoding UTF8
        $rules = @()
        
        # Extract rule definitions from markdown
        # Look for sections marked as MANDATORY rules
        $rulePatterns = @(
            # Peer-based coding
            @{
                Name = "Peer-Based Coding"
                Pattern = "(?s)## Peer Based Coding.*?## "
                Triggers = @("SessionStarted", "GitPreCommit", "FileSaved")
                Condition = { param($Context, $Event) 
                    -not $Context.Session.PairConfirmed 
                }
                Enforcement = @{
                    Severity = "blocking"
                    Actions = @("Warn", "RequireAck", "BlockCommit", "PromptForPair")
                }
            },
            # Pairwise testing
            @{
                Name = "Pairwise Testing"
                Pattern = "(?s)## Pairwise Testing.*?## "
                Triggers = @("GitPreCommit", "FileSaved")
                Condition = { param($Context, $Event)
                    $timeSinceTest = (Get-Date) - $Context.Session.LastTestRunTime
                    $timeSinceTest.TotalMinutes -gt 30 -or -not $Context.Session.PairConfirmed
                }
                Enforcement = @{
                    Severity = "blocking"
                    Actions = @("RequireTestRun", "BlockCommit", "Warn")
                }
            },
            # Memory consolidation
            @{
                Name = "Memory Consolidation"
                Pattern = "(?s)## MEMORY CONSOLIDATION.*?## "
                Triggers = @("TimerTick", "TaskStart")
                Condition = { param($Context, $Event)
                    $timeSinceMemory = (Get-Date) - $Context.Session.LastMemoryUpdateTime
                    $timeSinceMemory.TotalMinutes -gt 30
                }
                Enforcement = @{
                    Severity = "high"
                    Actions = @("Warn", "OpenMemoryFile", "RequireAck")
                }
            },
            # Comprehensive testing
            @{
                Name = "Comprehensive Testing"
                Pattern = "(?s)## COMPREHENSIVE TESTING.*?## "
                Triggers = @("TaskComplete", "GitPreCommit")
                Condition = { param($Context, $Event)
                    $timeSinceTest = (Get-Date) - $Context.Session.LastTestRunTime
                    $timeSinceTest.TotalMinutes -gt 60
                }
                Enforcement = @{
                    Severity = "blocking"
                    Actions = @("RequireTestRun", "BlockCommit")
                }
            },
            # 45-minute milestone
            @{
                Name = "45-Minute Milestone"
                Pattern = "(?s)## 45-MINUTE MILESTONE.*?## "
                Triggers = @("TimerTick")
                Condition = { param($Context, $Event)
                    if ($Context.Session.Milestones.Count -eq 0) { return $false }
                    $lastMilestone = $Context.Session.Milestones[-1]
                    $timeSinceMilestone = (Get-Date) - $lastMilestone.Time
                    $timeSinceMilestone.TotalMinutes -gt 45
                }
                Enforcement = @{
                    Severity = "high"
                    Actions = @("Warn", "CreateMilestoneTask", "RequireAck", "AutoStartTimer")
                }
            },
            # Timer service
            @{
                Name = "Timer Service"
                Pattern = "(?s)## TIMER SERVICE.*?## "
                Triggers = @("TimerTick", "SessionStarted")
                Condition = { param($Context, $Event)
                    -not $Context.Session.TimerActive
                }
                Enforcement = @{
                    Severity = "high"
                    Actions = @("Warn", "AutoStartTimer", "RequireAck")
                }
            },
            # Work visibility
            @{
                Name = "Work Visibility"
                Pattern = "(?s)## WORK VISIBILITY.*?## "
                Triggers = @("TimerTick", "GitPreCommit")
                Condition = { param($Context, $Event)
                    $timeSincePush = (Get-Date) - $Context.Session.LastPushTime
                    $timeSincePush.TotalMinutes -gt 60
                }
                Enforcement = @{
                    Severity = "medium"
                    Actions = @("Warn", "RequireAck")
                }
            },
            # Automatic continuation
            @{
                Name = "Automatic Continuation"
                Pattern = "(?s)## AUTOMATIC CONTINUATION.*?## "
                Triggers = @("TaskComplete")
                Condition = { param($Context, $Event)
                    $Context.Session.LastTaskComplete -and 
                    ((Get-Date) - $Context.Session.LastTaskComplete).TotalMinutes -gt 5
                }
                Enforcement = @{
                    Severity = "medium"
                    Actions = @("Warn", "RequireAck")
                }
            }
        )
        
        # Check if content contains mandatory rule sections
        foreach ($ruleDef in $rulePatterns) {
            if ($content -match $ruleDef.Pattern) {
                $rule = [PSCustomObject]@{
                    Id = "R-$($rules.Count + 1)"
                    Name = $ruleDef.Name
                    Enabled = $true
                    Triggers = $ruleDef.Triggers
                    ConditionScript = $ruleDef.Condition
                    Enforcement = $ruleDef.Enforcement
                }
                $rules += $rule
                Write-Output "INFO: Loaded rule '$($rule.Name)'"
            }
        }
        
        # Also parse YAML rules if embedded in markdown
        $yamlPattern = '(?ms)```(?:rules-yaml|yaml)\s+(?<yaml>.+?)\s+```'
        $yamlMatches = [regex]::Matches($content, $yamlPattern)
        
        foreach ($match in $yamlMatches) {
            try {
                $yaml = $match.Groups['yaml'].Value
                # If ConvertFrom-Yaml is available, use it
                if (Get-Command ConvertFrom-Yaml -ErrorAction SilentlyContinue) {
                    $yamlRules = $yaml | ConvertFrom-Yaml
                    if ($yamlRules -is [array]) {
                        foreach ($yr in $yamlRules) {
                            if ($yr.enabled -ne $false) {
                                $rule = [PSCustomObject]@{
                                    Id = $yr.id
                                    Name = $yr.name
                                    Enabled = $true
                                    Triggers = $yr.trigger
                                    ConditionScript = if ($yr.condition) { [ScriptBlock]::Create($yr.condition) } else { $null }
                                    Enforcement = $yr.enforcement
                                }
                                $rules += $rule
                                Write-Output "INFO: Loaded YAML rule '$($rule.Name)'"
                            }
                        }
                    }
                }
            } catch {
                Write-Warning "WARN: Failed to parse YAML rule block: $_"
            }
        }
        
        Write-Output "INFO: Loaded $($rules.Count) rules"
        return $rules
        
    } catch {
        Write-Error "ERROR: Failed to parse rules file: $_"
        return @()
    }
}

function Load-State {
    Write-Output "INFO: Loading state from $StatePath"
    
    $stateFiles = @{
        Sessions = "sessions.json"
        Violations = "violations.json"
        Timers = "timers.json"
    }
    
    foreach ($name in $stateFiles.Keys) {
        $file = Join-Path $StatePath $stateFiles[$name]
        if (Test-Path $file) {
            try {
                $data = Get-Content $file -Raw | ConvertFrom-Json -AsHashtable
                if ($data) {
                    $Global:Sessions = $data
                    Write-Output "INFO: Loaded $($data.Count) $name"
                }
            } catch {
                Write-Warning "WARN: Failed to load $name state: $_"
            }
        }
    }
}

function Save-State {
    Write-Output "INFO: Saving state to $StatePath"
    
    try {
        $Global:Sessions | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $StatePath "sessions.json") -Encoding UTF8
        $Global:Violations | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $StatePath "violations.json") -Encoding UTF8
        $Global:Timers | ConvertTo-Json -Depth 10 | Set-Content (Join-Path $StatePath "timers.json") -Encoding UTF8
    } catch {
        Write-Warning "WARN: Failed to save state: $_"
    }
}

function Get-SessionContext {
    param(
        [string]$User = $env:USERNAME,
        [string]$Repo = "",
        [string]$Branch = ""
    )
    
    if ([string]::IsNullOrWhiteSpace($Repo)) {
        $Repo = $ProjectRoot
    }
    
    $key = "$User|$Repo|$Branch"
    $session = $Global:Sessions[$key]
    
    if (-not $session) {
        $session = @{
            SessionId = [guid]::NewGuid().ToString()
            User = $User
            Repo = $Repo
            Branch = $Branch
            StartTime = Get-Date
            PairConfirmed = $false
            TimerActive = $false
            LastTestRunTime = (Get-Date).AddDays(-1)
            LastPushTime = (Get-Date).AddDays(-1)
            LastMemoryUpdateTime = (Get-Date).AddDays(-1)
            LastTaskComplete = $null
            Milestones = @()
            Flags = @{}
        }
        $Global:Sessions[$key] = $session
        Write-Output "INFO: Created new session: $($session.SessionId)"
    }
    
    return @{
        Session = $session
        Now = Get-Date
    }
}

function Evaluate-Rules {
    param(
        [hashtable]$Context,
        [hashtable]$Event
    )
    
    foreach ($rule in $Global:Rules) {
        if (-not $rule.Enabled) { continue }
        if ($rule.Triggers -and -not ($rule.Triggers -contains $Event.Type)) { continue }
        
        $violated = $false
        try {
            if ($rule.ConditionScript) {
                $ExecutionContext.SessionState.PSVariable.Set('Context', $Context)
                $ExecutionContext.SessionState.PSVariable.Set('Event', $Event)
                $result = & $rule.ConditionScript -Context $Context -Event $Event
                $violated = -not [bool]$result
            }
        } catch {
            Write-Warning "WARN: Error evaluating rule $($rule.Id): $_"
            continue
        }
        
        if ($violated) {
            Invoke-Enforcement -Rule $rule -Context $Context -Event $Event
        }
    }
}

function Invoke-Enforcement {
    param(
        [PSCustomObject]$Rule,
        [hashtable]$Context,
        [hashtable]$Event
    )
    
    $violationId = "$($Rule.Id)|$($Context.Session.SessionId)"
    $violation = $Global:Violations[$violationId]
    
    if (-not $violation) {
        $violation = @{
            ViolationId = $violationId
            RuleId = $Rule.Id
            RuleName = $Rule.Name
            SessionId = $Context.Session.SessionId
            FirstDetected = Get-Date
            LastDetected = Get-Date
            Count = 1
            State = "Open"
            ActionsTaken = @()
        }
        $Global:Violations[$violationId] = $violation
        Write-Output "VIOLATION: $($Rule.Name) - Rule $($Rule.Id)"
    } else {
        $violation.LastDetected = Get-Date
        $violation.Count++
    }
    
    foreach ($action in $Rule.Enforcement.Actions) {
        try {
            switch ($action) {
                "Warn" {
                    Send-AgentNotification -Title "Rule Violation: $($Rule.Name)" -Text "Violation detected: $($Rule.Name)" -Severity $Rule.Enforcement.Severity
                }
                "RequireAck" {
                    Send-AgentNotification -Title "Acknowledgment Required: $($Rule.Name)" -Text "Please acknowledge this violation to continue" -RequireAck $true -ViolationId $violationId
                }
                "BlockCommit" {
                    $Context.Session.Flags["BlockCommit"] = @{
                        Value = $true
                        Reason = $Rule.Id
                        Updated = Get-Date
                    }
                }
                "PromptForPair" {
                    Send-AgentNotification -Title "Pair Required" -Text "Please confirm your pair partner to continue" -Command "pair:prompt" -Severity "high"
                }
                "RequireTestRun" {
                    Send-AgentNotification -Title "Tests Required" -Text "Please run tests before committing" -Command "tests:run" -Severity "high"
                }
                "OpenMemoryFile" {
                    Send-AgentNotification -Title "Memory Consolidation Required" -Text "Please update memory files" -Command "open:memory" -Severity "medium"
                }
                "CreateMilestoneTask" {
                    Send-AgentNotification -Title "Milestone Due" -Text "Please record your 45-minute milestone checkpoint" -Command "milestone:prompt" -Severity "high"
                }
                "AutoStartTimer" {
                    Start-SessionTimer -Session $Context.Session -Name "Milestone45" -Due (Get-Date).AddMinutes(45)
                }
            }
            $violation.ActionsTaken += $action
        } catch {
            Write-Warning "WARN: Failed to execute action '$action': $_"
        }
    }
}

function Send-AgentNotification {
    param(
        [string]$Title,
        [string]$Text,
        [string]$Severity = "medium",
        [bool]$RequireAck = $false,
        [string]$ViolationId = "",
        [string]$Command = ""
    )
    
    try {
        # Send to agent via HTTP API
        $body = @{
            user = $env:USERNAME
            title = $Title
            text = $Text
            severity = $Severity
            requireAck = $RequireAck
            violationId = $ViolationId
            command = $Command
            timestamp = (Get-Date).ToString("o")
        } | ConvertTo-Json
        
        Invoke-RestMethod -UseBasicParsing -Method Post -Uri "http://localhost:$Port/agent/notify" -Body $body -ContentType "application/json" -ErrorAction SilentlyContinue | Out-Null
    } catch {
        # Fallback: Use BurntToast directly
        try {
            Import-Module BurntToast -ErrorAction SilentlyContinue
            New-BurntToastNotification -Text $Title, $Text -AppLogo "C:\Windows\System32\WindowsPowerShell\v1.0\powershell_ise.exe" | Out-Null
        } catch {
            Write-Warning "WARN: Failed to send notification: $_"
        }
    }
}

function Start-SessionTimer {
    param(
        [hashtable]$Session,
        [string]$Name,
        [datetime]$Due
    )
    
    $timerId = "$($Session.SessionId)|$Name"
    $Global:Timers[$timerId] = @{
        SessionId = $Session.SessionId
        Name = $Name
        Due = $Due
        Created = Get-Date
    }
    $Session.TimerActive = $true
    Write-Output "INFO: Started timer '$Name' for session $($Session.SessionId)"
}

function Ensure-HttpListener {
    param([int]$Port)
    
    $prefix = "http://+:$Port/"
    $listener = [HttpListener]::new()
    $listener.Prefixes.Add($prefix)
    
    try {
        $listener.Start()
        Write-Output "INFO: HTTP listener started on port $Port"
        return $listener
    } catch {
        Write-Warning "WARN: Failed to start HTTP listener. You may need to run: netsh http add urlacl url=http://+:$Port/ user=Everyone"
        throw
    }
}

function Handle-HttpRequest {
    param([System.Net.HttpListenerContext]$Context)
    
    $req = $Context.Request
    $res = $Context.Response
    
    $path = $req.Url.AbsolutePath.ToLowerInvariant()
    $body = ""
    
    if ($req.HasEntityBody) {
        $reader = New-Object IO.StreamReader($req.InputStream, $req.ContentEncoding)
        $body = $reader.ReadToEnd()
        $reader.Close()
    }
    
    $payload = if ($body) { $body | ConvertFrom-Json -AsHashtable } else { @{} }
    
    try {
        switch ($path) {
            "/event" {
                $event = @{
                    Type = $payload.type
                    Time = Get-Date
                    User = if ($payload.user) { $payload.user } else { $env:USERNAME }
                    Repo = $payload.repo
                    Branch = $payload.branch
                    Payload = $payload.payload
                }
                
                $sessionContext = Get-SessionContext -User $event.User -Repo $event.Repo -Branch $event.Branch
                Evaluate-Rules -Context $sessionContext -Event $event
                
                Write-JsonResponse -Response $res -Object @{ ok = $true }
            }
            "/policy/commit" {
                $repo = $req.QueryString["repo"]
                $branch = $req.QueryString["branch"]
                $user = $req.QueryString["user"]
                
                $sessionContext = Get-SessionContext -User $user -Repo $repo -Branch $branch
                $violations = $Global:Violations.Values | Where-Object { $_.SessionId -eq $sessionContext.Session.SessionId -and $_.State -eq "Open" }
                $blocked = $sessionContext.Session.Flags["BlockCommit"]?.Value -eq $true
                
                Write-JsonResponse -Response $res -Object @{
                    allowed = (-not $blocked -and $violations.Count -eq 0)
                    violations = $violations
                    reasons = @($violations | ForEach-Object { $_.RuleName })
                }
            }
            "/acknowledge" {
                $vid = $payload.violationId
                if ($Global:Violations[$vid]) {
                    $Global:Violations[$vid].State = "Resolved"
                    Write-Output "INFO: Violation acknowledged: $vid"
                }
                Write-JsonResponse -Response $res -Object @{ ok = $true }
            }
            "/agent/notify" {
                # Notification endpoint for agent
                Write-JsonResponse -Response $res -Object @{ ok = $true }
            }
            "/status" {
                Write-JsonResponse -Response $res -Object @{
                    service = "RuleEnforcerService"
                    status = "running"
                    rulesLoaded = $Global:Rules.Count
                    activeSessions = $Global:Sessions.Count
                    openViolations = ($Global:Violations.Values | Where-Object { $_.State -eq "Open" }).Count
                    lastRulesLoad = $Global:LastRulesLoad.ToString("o")
                }
            }
            default {
                $res.StatusCode = 404
                $res.Close()
            }
        }
    } catch {
        Write-Error "ERROR handling request to $path : $_"
        $res.StatusCode = 500
        $res.Close()
    }
}

function Write-JsonResponse {
    param(
        [System.Net.HttpListenerResponse]$Response,
        [object]$Object
    )
    
    $json = $Object | ConvertTo-Json -Depth 10
    $buffer = [Text.Encoding]::UTF8.GetBytes($json)
    $Response.ContentType = "application/json"
    $Response.ContentLength64 = $buffer.Length
    $Response.OutputStream.Write($buffer, 0, $buffer.Length)
    $Response.Close()
}

# --- MAIN EXECUTION ---

# Load rules
$Global:Rules = Parse-AllRulesMarkdown -FilePath $RulesPath
if ($Global:Rules.Count -eq 0) {
    Write-Warning "WARN: No rules loaded. Service will monitor but not enforce."
}

# Watch rules file for changes
$rulesDir = Split-Path $RulesPath -Parent
$rulesFile = Split-Path $RulesPath -Leaf
$Global:RulesFileWatcher = New-Object FileSystemWatcher $rulesDir, $rulesFile
$Global:RulesFileWatcher.EnableRaisingEvents = $true

Register-ObjectEvent $Global:RulesFileWatcher Changed -Action {
    Start-Sleep -Milliseconds 500
    Write-Output "INFO: Rules file changed, reloading..."
    $Global:Rules = Parse-AllRulesMarkdown -FilePath $RulesPath
    $Global:LastRulesLoad = Get-Date
    Write-Output "INFO: Reloaded $($Global:Rules.Count) rules"
} | Out-Null

# Load state
Load-State

# Start HTTP listener
$Global:HttpListener = Ensure-HttpListener -Port $Port

# Start periodic timer evaluation
$timer = New-Object Timers.Timer
$timer.Interval = 300000  # 5 minutes
$timer.AutoReset = $true
Register-ObjectEvent $timer Elapsed -Action {
    foreach ($session in $Global:Sessions.Values) {
        $context = @{
            Session = $session
            Now = Get-Date
        }
        $event = @{
            Type = "TimerTick"
            Time = Get-Date
            User = $session.User
            Repo = $session.Repo
            Branch = $session.Branch
            Payload = @{}
        }
        Evaluate-Rules -Context $context -Event $event
    }
    
    # Save state periodically
    Save-State
} | Out-Null
$timer.Start()

Write-Output "INFO: Service is now active and monitoring"
Write-Output "INFO: Listening on http://localhost:$Port/"

# Main request loop
while ($Global:ServiceRunning -and $Global:HttpListener.IsListening) {
    try {
        $context = $Global:HttpListener.GetContextAsync()
        $context.Wait(1000)  # 1 second timeout
        
        if ($context.IsCompleted) {
            Handle-HttpRequest -Context $context.Result
        }
    } catch {
        if ($Global:ServiceRunning) {
            Write-Warning "WARN: Error in request loop: $_"
        }
    }
}

# Cleanup
Write-Output "INFO: Service stopping..."
Save-State
$timer.Stop()
if ($Global:RulesFileWatcher) { $Global:RulesFileWatcher.Dispose() }
if ($Global:HttpListener) { $Global:HttpListener.Stop(); $Global:HttpListener.Close() }
Stop-Transcript

Write-Output "INFO: RuleEnforcerService stopped at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"


