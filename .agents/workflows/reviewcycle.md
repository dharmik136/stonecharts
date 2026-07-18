# Review Cycle

## Description

Use this workflow when the main task is to evaluate an existing change set.

## Steps

1. Run the `intake` skill to identify scope and governing docs.
2. Run the `test` skill to reproduce the current result.
3. Run the `compliance-review` skill if the change touches docs, decisions, or
   release controls.
4. Run the `security-review` skill if the change touches code execution, auth,
   dependencies, or workflows.
5. Summarize findings with file references and recommended next steps.
