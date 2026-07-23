param(
    [string]$Branch = "",
    [string]$Worktree = "",
    [string]$Owner = ""
)

& (Join-Path $PSScriptRoot "launch-agent.ps1") -Role notetaker -Branch $Branch -Worktree $Worktree -Owner $Owner
