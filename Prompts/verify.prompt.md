---
name: verify
description: Entry prompt for the Verification phase of the Agentic SDLC.
---

# Verification Prompt

## Invoke Agent

Read and follow `Agents/verify.agent.md` in full — its Role, Objective, Responsibilities, Allowed/Forbidden Actions, and Human Approval/Gate Behavior govern this phase.

## Load Skill

Load and apply `Skills/verify/SKILL.md` for the verification methodology (requirement traceability check, coverage categories, actual test execution, acceptance-criteria check, reporting).

## Required Input

* `docs/code-review.md` — must show "Ready for Gate G4" with zero blocking findings.
* `requirements.md`
* Application source code and tests

## Expected Output

`docs/verification-report.md`, containing the requirement-to-test traceability table, actually-executed test results, acceptance-criteria results, and an overall verdict (PASS, PASS WITH DOCUMENTED LIMITATIONS, or FAIL).

## Human Approval / Gate

Gate G5's verification prerequisite is satisfied only once `docs/verification-report.md` shows a passing result, explicitly accepted by the human, with separate human authorization still required to open the PR.

## Scope Boundary

Do this phase only. Do not modify application source code or tests — report gaps rather than fixing them. Do not begin PR work in this pass.

## Stop Condition

STOP once `docs/verification-report.md` is produced and reported to the human. Do not proceed to Pull Request creation without a separate invocation of that phase and explicit human authorization.
