# Evolve

**Turn existing codebases into better software. Keep the evidence.**

Evolve is a portable skill pack for coding agents. It gives the agent a repeatable
workflow for investigating an application, choosing worthwhile improvements,
implementing them, verifying the result, and continuing with the next task.

Use it to improve an open-source fork, repair a neglected project, strengthen a
production application, or modernise an existing product. It works with the
architecture you have and requires a reason for a rewrite.

```text
Understand → Baseline → Investigate → Prioritise
    → Implement → Verify → Measure → Deliver → Repeat
```

The aim is completed, trustworthy engineering work: working features, repaired
bugs, simpler code, better interfaces, and measured improvements.

## Start here

Clone the pack and install it into the application you want to improve. The
installer needs **Python 3.10+** and uses only the standard library.

```sh
git clone https://github.com/Itskorrah/evolve.git
cd evolve
python3 scripts/install.py install --host codex --project "/path/to/your-app"
```

Then open **your application project** in the agent and invoke:

```text
Use $evolve to improve this application. Investigate correctness, performance,
maintainability, usability, and missing functionality. Prioritise substantial
improvements, implement and verify them, and continue through the next useful
tasks within this run. Keep changes local.
```

`$evolve` is a Codex skill invocation, not a terminal command. In Claude Code use
`/evolve`. In another capable agent, ask it to load the `evolve/SKILL.md` file and
follow it. See [host compatibility](docs/compatibility.md).

Already using the [Vercel Skills CLI](https://github.com/vercel-labs/skills)?

```sh
npx skills add Itskorrah/evolve
```

Select `evolve` and the specialist skills you want. The coordinator includes the
shared references and tools. The bundled installer installs all six by default
and keeps that dependency intact.

## What it improves

| Area | What the agent looks for |
| --- | --- |
| Correctness and reliability | Reproducible bugs, crashes, data loss, broken workflows, recovery failures |
| Security | Trust boundaries, authentication, authorisation, unsafe input, secrets, dependency risks |
| Performance | Measured bottlenecks, responsiveness, memory, expensive work and unnecessary rendering |
| Architecture and maintenance | Change friction, coupling, duplication, dead code, brittle interfaces |
| Product and design | Incomplete features, confusing interactions, accessibility, consistency, customisation |
| Tests and delivery | Missing regression coverage, unreliable checks, broken builds and release gaps |

It distinguishes documented claims from working implementations. Findings need
evidence. Feature suggestions need a concrete user benefit. Performance claims
need comparable measurements.

## Six skills, one workflow

| Skill | Purpose |
| --- | --- |
| **evolve** | Own the improvement loop, priorities, shared state and integration |
| **evolve-audit** | Establish coverage, investigate problems and verify findings |
| **evolve-build** | Complete a selected improvement through its real execution path |
| **evolve-design** | Improve actual product flows and implement coherent interfaces |
| **evolve-verify** | Independently challenge changes and verify their acceptance criteria |
| **evolve-ship** | Deliver verified changes according to the user's GitHub authorisation |

The coordinator loads specialist guidance when it is useful. You can also invoke
one specialist for a focused task. Missing tools or sibling skills are reported;
the portable workflow still applies.

## Choose how far it can go

State delivery permission in your request. Evolve preserves that permission
through the run; it does not ask again for routine steps already authorised.

| Delivery | Example instruction |
| --- | --- |
| Local | "Implement improvements and keep changes local." |
| Commit | "Commit verified improvements on this branch." |
| Pull request | "Push a branch and create a PR in owner/repo." |
| Merge | "Create PRs and merge verified improvements into main in owner/repo." |

Installing the pack does not authorise external changes. Permission belongs to
the user's task. Merge delivery requires current checks and respects branch
protections. Production deployment is a separate action.

For an audit without implementation:

```text
Use $evolve-audit for a deep audit of this repository. Verify findings, show the
highest-value opportunities, and make no application changes.
```

For sustained engineering:

```text
Use $evolve on this repository. Focus on reliability, speed and user experience.
Implement complete improvements, use independent review when available, and
keep choosing the next highest-value task. You may commit, push branches, create
PRs and merge into main in owner/repo after the required checks pass. Preserve
existing user changes. Record unfinished work so the next run can resume.
```

For resuming:

```text
Use $evolve to resume this project. Reconcile .evolve/state.json with the current
code and continue the next eligible task using the same scope and delivery
permission I have authorised in this conversation.
```

See [more examples](docs/examples.md) for focused performance and design work.

## Evidence and continuity

Working records live in `.evolve/` in the **application repository**, separate
from the installed skill files. Keep this directory out of version control; it
can contain internal findings and command output. Commit deliberately sanitised
reports only when they are useful to the project.

The coordinator records scope, the verified baseline, findings, task dependencies,
acceptance criteria, checks, measurements and delivery status. The helper CLI
supports task tracking, bounded command execution, evidence freshness checks and
resumption. An old passing check cannot finish a task after source changes.

```sh
# From the application project; replace EVOLVE_ROOT with the installed evolve folder.
python3 "$EVOLVE_ROOT/scripts/evolve.py" init --goal "Improve reliability and usability"
python3 "$EVOLVE_ROOT/scripts/evolve.py" status
```

`EVOLVE_ROOT` is the folder containing the coordinator's `SKILL.md`. For the
Codex project installation above it is `/path/to/your-app/.agents/skills/evolve`.
The [tool guide](docs/tools.md) documents commands, formats and evidence limits.

## Built for useful autonomy

- Establish a baseline and preserve existing work before making changes.
- Rank verified opportunities by impact, confidence, effort and risk.
- Complete a small set of meaningful changes before expanding the queue.
- Investigate with parallel agents when available; isolate implementation work.
- Verify functionality, failure paths and the user's acceptance criteria.
- Change approach when repeated attempts stop producing useful evidence.
- Reserve time to validate, deliver and write a compact continuation record.

Evolve adapts to the project's language, framework, build system and deployment
model. It does not mandate a stack, a rewrite, a coverage percentage, or new
infrastructure for every application.

## What this pack provides

Portable Markdown skills, detailed engineering references, templates, a managed
installer, an inventory tool, a persistent task/evidence CLI, a benchmark tool,
and tests. The Python tools require Git for repository snapshots; GitHub delivery
uses the host's available connector or authenticated tooling.

It is **not a background service**. Execution, models, browsing, UI access,
subagents, credentials and time limits come from your agent environment. It can
resume progress across runs; it cannot extend the host's limits or certify an
application as production-ready from passing tests alone.

Instructions are portable. Live behaviour across every agent host is not claimed
as tested. [Validation and evaluation](docs/testing.md) separates automated tool
checks from behavioural evaluation and host-specific verification.

## Install, update and remove

```sh
python3 scripts/install.py install --host codex --scope global
python3 scripts/install.py install --host claude --project "/path/to/your-app"
python3 scripts/install.py install --target "/path/to/agent/skills" --dry-run
```

To update, pull this checkout and repeat the install command. To remove:

```sh
python3 scripts/install.py uninstall --host codex --project "/path/to/your-app"
```

The installer tracks owned files and refuses to overwrite locally edited or
unmanaged installations. It preserves unrelated skills and user-added files.
Installation does not alter agent configuration, permissions or model settings.

## Check installation integrity

```sh
python3 scripts/install.py verify --host codex --project "/path/to/your-app"
```

`verify` is read-only: it hashes installed files against the ownership manifest
and reports source drift as `outdated` without overwriting user edits. It does
**not** execute a skill in the target host. The development branch records
`0.2.0-dev` as an informational pack version, **not** a published release.
After updating the checkout, repeat `install` to upgrade (edited files are
refused rather than silently overwritten). The installer blocks Windows
junction/reparse-point paths as well as symbolic links.

See [product status](PRODUCT_STATUS.md) for implemented versus verified versus
released capabilities and [reference evaluations](tests/evaluations/README.md)
for four checkable workloads and paired model comparisons.

## Develop the pack

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

Read [CONTRIBUTING.md](CONTRIBUTING.md) for changes and behavioural evaluation.
The [architecture guide](docs/architecture.md) explains the package structure.

## License

[MIT](LICENSE). Built and maintained by [Itskorrah](https://github.com/Itskorrah).
Applications improved with Evolve retain their own licences and attribution.
