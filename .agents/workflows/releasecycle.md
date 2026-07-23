# Release Cycle

## Description

Use this workflow to prepare a governed release candidate and final release
evidence.

## Steps

1. Confirm the release target with the `intake` skill.
2. Run the release self-checks and verify the required decisions, requirements, and evidence with the `compliance-review`
   skill.
3. Run the `test` skill across the required release checks.
4. Run the `security-review` skill if the release includes new code, workflows, or
   external dependencies.
5. Run the `release` skill to assemble the final release handoff.
