# Thang implementation workflow

- [x] Read the poteto-mode Principles and applicable leaf skills.
- [x] Inspect clean git state; fetch origin; fast-forward main to b115719.
- [x] Read project instructions, ownership, contracts, all eight live issues and comments.
- [x] Capture starter baseline. Preserve framework files and original experiment artifacts.
- [x] T-01: create branch, 15 lesson pages plus isolated other-class page, >=12 assignments, reproducible data tests; verify, commit, push, open PR #7.
- [x] T-02: scoped leak checker plus behavioral tests and limitations; verify, commit, push, open PR #8.
- [x] T-03: proposed metric definitions in existing YAML schema, pending Khoa approval; verify, commit, push, open PR #9.
- [x] T-04: strict deterministic benchmark builder, malformed input tests, no fabricated member cases; verify, commit, push, open PR #16.
- [x] T-05: exactly B14-B21, mathematical verification, truthful synthetic provenance; verify, commit, push, open PR #17.
- [x] T-06: read-only draft grader with numerator/denominator, provenance checks, human review pending; verify, commit, push, open PR #18.
- [x] Prepare T-07 report skeleton and interview worksheet; no real results or participant IDs invented.
- [x] Record actual AI use; prepare reflection using official template, with personal observations pending.
- [x] Validate integrated state, independent review of trail, check git scopes and handoff ticket-by-ticket.

Definition of done: each feasible ticket has its own branch/commit/PR, relevant tests and CLI smoke pass, schema preserved, no foreign ownership or immutable artifact changes, blockers stated with receipts. Final benchmark remains untouched until all four real author files validate. PASS never substitutes for pending human judgments.

Rigor: strict checks for mathematical correctness, public/private answer separation, adversarial leak formats, byte-preserving benchmark construction and read-only grading. No redesign of agent, model, retrieval or framework.

Git strategy: independent branches from latest main where possible. T-05 depends on T-01. T-06 depends on T-01, T-02, T-03 and T-04. State dependencies in each PR. Never merge into main.

Final implementation verification: 108 tests passed at950815a; independent same-family reviewer rechecked fixes. PASS is implementation verification only. T03 approval, T04 complete benchmark, T06 real-run validation, T07 real results and interview remain pending. T07 reports stay local/uncommitted until evidence exists.
