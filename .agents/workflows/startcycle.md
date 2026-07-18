# Start Cycle

## Description

Use this workflow to take a request from intake through implementation and
verification.

## Steps

1. Run the `intake` skill.
2. Check `.agents/coordination.md` and the active lock before editing.
3. Run the Socratic self-checks for the active role.
4. Convert the request into a bounded plan with the `plan` skill.
5. Assign a single owner and a narrow file set.
6. Execute the approved work with the `implement` skill.
7. Verify the result with the `test` skill.
8. If the change affects controls, run the `compliance-review` skill.
9. If the change affects attack surface or automation, run the `security-review`
   skill.
10. Record the handoff state before the next agent begins.
