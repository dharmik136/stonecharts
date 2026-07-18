param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("planner", "stakeholder", "developer", "qa", "security", "compliance", "release", "notetaker")]
    [string]$Role,

    [Parameter(Mandatory = $false)]
    [string]$Branch = "",

    [Parameter(Mandatory = $false)]
    [string]$Worktree = "",

    [Parameter(Mandatory = $false)]
    [string]$Owner = ""
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$stateDir = Join-Path $repoRoot ".agents\state"
$launchFile = Join-Path $repoRoot ".agents\launch\$Role.md"
$inventoryPath = Join-Path $stateDir "inventory.md"
$operatingModelNote = "Runtime model: private local CLI workers only; no GitHub collaborator role."

if (-not (Test-Path $launchFile)) {
    throw "Unknown role launch file: $launchFile"
}

New-Item -ItemType Directory -Force -Path $stateDir | Out-Null

if (-not (Test-Path $inventoryPath)) {
    $inventoryHeader = @"
# Agent Inventory

This log records local CLI agent launches, their intended scope, and the verification
they reported back.

| Time | Role | Branch or worktree | Owner | Launch note |
|---|---|---|---|---|
"@
    [System.IO.File]::WriteAllText($inventoryPath, $inventoryHeader, [System.Text.Encoding]::UTF8)
}

function Write-AtomicTextFile {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [string]$Content
    )

    $directory = Split-Path -Parent $Path
    $tempPath = Join-Path $directory ([System.IO.Path]::GetRandomFileName())
    [System.IO.File]::WriteAllText($tempPath, $Content, [System.Text.Encoding]::UTF8)
    Move-Item -Force -LiteralPath $tempPath -Destination $Path
}

function Test-GitBranchExists {
    param([Parameter(Mandatory = $true)][string]$Name)

    git rev-parse --verify --quiet "refs/heads/$Name" *> $null
    return $LASTEXITCODE -eq 0
}

if ($Worktree) {
    if (-not $Branch) {
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $Branch = "agent/$Role-$stamp"
    }

    $worktreeRoot = Split-Path -Parent $Worktree
    if ($worktreeRoot) {
        New-Item -ItemType Directory -Force -Path $worktreeRoot | Out-Null
    }

    if (Test-Path $Worktree) {
        throw "Worktree path already exists: $Worktree"
    }

    if (Test-GitBranchExists -Name $Branch) {
        git worktree add $Worktree $Branch | Out-Null
    } else {
        git worktree add -b $Branch $Worktree | Out-Null
    }
}

$lockPath = Join-Path $stateDir "branch-lock.md"
$handoffPath = Join-Path $stateDir "handoff.md"

$now = Get-Date -Format "yyyy-MM-dd HH:mm:ss zzz"

$lock = @"
# Branch Lock

- Owner: $Owner
- Branch or worktree: $Branch
- Claim time: $now
- Files in scope:
- Stop point:
- Required checks before handoff:
- Handoff target:
"@

$handoff = @"
# Handoff

- From: 
- To: $Role
- Branch or worktree: $Branch
- Commit or state:
- Files changed:
- Verification completed:
- Remaining checks:
- Risks or blockers:
"@

Write-AtomicTextFile -Path $lockPath -Content $lock
Write-AtomicTextFile -Path $handoffPath -Content $handoff

$location = $Branch
if (-not $location) {
    $location = $Worktree
}
if (-not $location) {
    $location = "-"
}
$inventoryEntry = "| $now | $Role | $location | $Owner | Private local CLI worker; no GitHub collaborator role. |"
[System.IO.File]::AppendAllText($inventoryPath, "$inventoryEntry`r`n", [System.Text.Encoding]::UTF8)

Write-Host "Prepared agent state for role '$Role'."
Write-Host $operatingModelNote
Write-Host "Launch note: $launchFile"
Write-Host "Lock file: $lockPath"
Write-Host "Handoff file: $handoffPath"
Write-Host "Inventory log: $inventoryPath"
if ($Worktree) {
    Write-Host "Worktree created: $Worktree"
}
