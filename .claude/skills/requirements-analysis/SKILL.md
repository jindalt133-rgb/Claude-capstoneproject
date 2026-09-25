# Requirements Analysis Skill

## Purpose

Provide a consistent methodology for converting a User Story into clear, testable software requirements without fabricating missing information.

## Analysis Framework

Analyze the User Story for the following areas:

### 1. Business Objective

Identify the business problem and intended outcome.

### 2. Scope

Identify functionality explicitly inside the proposed solution's scope.

Also identify functionality explicitly outside scope when stated.

### 3. Actors and Stakeholders

Identify users, systems, teams, or other parties that interact with or are affected by the solution.

### 4. Functional Requirements

Extract observable system behaviors.

Assign identifiers:

* FR-001
* FR-002
* FR-003

Each requirement should be clear and independently understandable.

### 5. Non-Functional Requirements

Identify requirements involving qualities such as:

* Performance
* Security
* Reliability
* Maintainability
* Compatibility
* Usability

Assign identifiers:

* NFR-001
* NFR-002

Do not invent numeric targets that are absent from the User Story.

### 6. Constraints

Identify restrictions that limit implementation or operation.

### 7. Dependencies

Identify external systems, tools, services, files, workflows, or upstream decisions required by the solution.

### 8. Acceptance Criteria

Extract existing acceptance criteria and identify where additional criteria require clarification.

Acceptance criteria should eventually be objectively verifiable.

### 9. Assumptions

Record assumptions separately.

Never silently treat an assumption as an approved requirement.

### 10. Ambiguities

Identify statements that have multiple reasonable interpretations.

### 11. Missing Information

Identify information necessary for architecture, implementation, testing, or acceptance that has not been provided.

### 12. Conflicting or Unclear Statements

Identify requirements that contradict each other or whose relationship is unclear.

## Clarification Process

For each unresolved issue:

1. Explain what is unclear.
2. Explain why the answer matters.
3. Ask a concise question.
4. Where useful, present reasonable options.
5. Do not choose an option on behalf of the human.

Prioritize blocking questions over minor questions.

Do not generate a final requirements specification while blocking questions remain unanswered.

## Final Requirements Quality

Before finalizing requirements, verify that:

* Requirements are testable.
* Requirements do not contradict one another.
* Functional and non-functional requirements are separated.
* Assumptions are explicit.
* Acceptance criteria can be verified.
* Important unresolved issues are visible.
* No requirement has been fabricated.
