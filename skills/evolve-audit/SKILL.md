---
name: evolve-audit
description: Investigate an existing codebase and product, establish audit coverage, reproduce faults and rank evidence-backed improvements. Use for deep repository audits or the investigation stage of Evolve; audit-only requests do not authorise application changes.
---

# Evolve Audit

Find problems that matter and prove the findings. Match the user's audit scope
and depth. An audit alone does not authorise fixes or external publication.

## Shared resources

Resolve the sibling `evolve` skill using the host loader or the parent of this
skill folder. Read its [audit reference](../evolve/references/audit.md),
[intake](../evolve/references/intake.md) and
[prioritisation](../evolve/references/prioritisation.md). If absent, use the
procedure below without claiming the shared tools were used. Work in the target
application, not the skill directory.

## Procedure

1. Read user scope, applicable project instructions, architecture and CI. Record
   the current revision, pre-existing changes and relevant baseline failures.
2. Map core workflows, trust boundaries, data ownership and important contracts.
   Inspect code together with how it is reached and used.
3. Investigate correctness, integrity/recovery, security, performance, maintenance,
   tests, dependencies, tooling, product/UI and docs. Weight effort by actual risk;
   record packages investigated, methods used and exclusions.
4. Use bounded parallel read-only investigations when supported. Re-read cited
   code before accepting reports. Differentiate a documented intentional tradeoff
   from a problem whose observed consequences warrant changing it.
5. Reproduce bugs where possible. Trace data from user input to outcome. For
   vulnerabilities establish reachability and impact; for performance establish a
   workload and measurements. Mark unresolved candidates as investigations.
6. Rank verified findings by impact, confidence, effort and fix risk. Give each a
   trigger, source references, observed/expected result, proposed scope and an
   acceptance test. Keep feature opportunities separate from defects.
7. Return a small ready-to-implement queue plus coverage and material limits. In
   an Evolve implementation run, hand the best eligible task to the coordinator.
   For audit-only requests, report without modifying application source.

Never infer working behaviour from a README or a command identifier. Do not pad
the report with style preferences, generic coverage targets or theoretical
infrastructure. Do not expose live credentials or publish sensitive findings.
