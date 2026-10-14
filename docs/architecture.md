# Package architecture

```text
skills/evolve/
  SKILL.md                 coordinator and shared rules
  agents/openai.yaml       Codex UI metadata
  references/              conditional engineering guidance
  templates/               task, PR and checkpoint formats
  scripts/                 optional inventory, ledger and benchmark helpers
skills/evolve-*/            five independently usable specialist entrypoints
scripts/                   managed installer and package validator
tests/                     executable helper/installation tests and evaluations
docs/                      usage, compatibility and validation documentation
```

The coordinator routes by task needs. It does not load every reference at once.
Specialists share the coordinator's reference vocabulary and provide fallback
procedures if shared resources are absent. Installation includes the coordinator
for every selected specialist to keep the normal package complete.

Application state lives at the target project's `.evolve/`, separate from skill
source and installation ownership. State writes are atomic and lock-protected.
Command checks record actual execution and source fingerprints. Observation evidence
records declared inspection with artifact hashes. Neither replaces engineering review.

The inventory does not run source or discovered scripts. The evidence runner and
benchmark runner execute only the argument vector explicitly supplied by the operator.
No helper provisions infrastructure, discovers credentials, calls a model or ships
code. GitHub delivery belongs to the authorised host workflow.

The installer owns only files listed in `.evolve-install.json`. Preflight detects
local edits, unmanaged collisions and unsafe paths before writing selected skills.
Per-file replacement is atomic; full-pack installation is not transactional.

The pack is deliberately stack-neutral. References describe decisions and evidence,
while the application supplies its architecture, conventions, tools and constraints.
