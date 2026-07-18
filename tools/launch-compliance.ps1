param(
    [string]$Branch = "",
    [string]$Worktree = "",
    [string]$Owner = ""
)

& (Join-Path $PSScriptRoot "launch-agent.ps1") -Role compliance -Branch $Branch -Worktree $Worktree -Owner $Owner
