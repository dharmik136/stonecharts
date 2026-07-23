param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("planner", "developer", "qa", "security", "compliance", "release")]
    [string]$Role,

    [Parameter(Mandatory = $false)]
    [string]$Branch = "",

    [Parameter(Mandatory = $true)]
    [string]$Worktree,

    [Parameter(Mandatory = $false)]
    [string]$Owner = ""
)

$repoRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot "bootstrap_agents.ps1") -Role $Role -Branch $Branch -Worktree $Worktree -Owner $Owner
Write-Host ""
Write-Host "Launch with:"
Write-Host "  tools\launch-$Role.ps1 -Branch $Branch -Worktree `"$Worktree`" -Owner $Owner"
