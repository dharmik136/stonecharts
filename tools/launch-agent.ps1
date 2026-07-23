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
$launchFile = Join-Path $repoRoot ".agents\launch\$Role.md"
$bootstrap = Join-Path $PSScriptRoot "bootstrap_agents.ps1"

& $bootstrap -Role $Role -Branch $Branch -Worktree $Worktree -Owner $Owner
Write-Host ""
Get-Content $launchFile
