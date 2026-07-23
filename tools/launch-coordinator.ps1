param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("implementation", "review", "release", "full")]
    [string]$Mode = "full",

    [Parameter(Mandatory = $false)]
    [string]$Branch = "",

    [Parameter(Mandatory = $false)]
    [string]$WorktreeRoot = "",

    [Parameter(Mandatory = $false)]
    [string]$Owner = "coordinator"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$stateDir = Join-Path $repoRoot ".agents\state"
New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
$operatingModelNote = "Runtime model: private local CLI workers only; no GitHub collaborator role."

$sequences = @{
    implementation = @("planner", "stakeholder", "developer", "qa", "notetaker")
    review = @("qa", "compliance", "security", "stakeholder", "notetaker")
    release = @("planner", "stakeholder", "developer", "qa", "compliance", "security", "release", "notetaker")
    full = @("planner", "stakeholder", "developer", "qa", "compliance", "security", "release", "notetaker")
}

$sequence = $sequences[$Mode]
$queuePath = Join-Path $stateDir "queue.md"

$content = @"
# Agent Queue

- Mode: $Mode
- Branch: $Branch
- Worktree root: $WorktreeRoot
- Owner: $Owner

## Execution order

"@

foreach ($role in $sequence) {
    $content += "- $role`n"
}

$content += @"

## Rules

- Only one role writes at a time if the queue shares a branch.
- The next role starts only after handoff and self-check completion.
"@

[System.IO.File]::WriteAllText($queuePath, $content, [System.Text.Encoding]::UTF8)

Write-Host "Coordinator queue written to $queuePath"
Write-Host $operatingModelNote
Write-Host ""
Write-Host "Role order:"
foreach ($role in $sequence) {
    Write-Host " - $role"
}

if ($Branch -or $WorktreeRoot) {
    Write-Host ""
    Write-Host "Recommended start sequence:"
    foreach ($role in $sequence) {
        $worktree = ""
        if ($WorktreeRoot) {
            $worktree = Join-Path $WorktreeRoot $role
        }
        $cmd = if ($worktree) {
            "tools\launch-$role.ps1 -Branch $Branch -Worktree `"$worktree`" -Owner $Owner"
        } else {
            "tools\launch-$role.ps1 -Branch $Branch -Owner $Owner"
        }
        Write-Host $cmd
    }
}
