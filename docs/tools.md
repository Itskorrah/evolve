# Optional tools

Tools live in `skills/evolve/scripts/` and are copied into the coordinator's folder.
Run from the application repository root or pass the documented project argument.
No third-party Python packages are needed. Exit codes: **0** successful operation,
**1** failed check/gate/regression threshold, **2** invalid input or unavailable
precondition. Output is JSON; stderr carries actionable errors.

## Inventory

```sh
python3 "$EVOLVE_ROOT/scripts/inventory.py" --project "/path/to/app"
python3 "$EVOLVE_ROOT/scripts/inventory.py" --project "/path/to/app" --output .evolve/inventory-001.json
```

Lists Git-visible files, likely stack manifests, instructions, CI files and language
counts without reading source contents or running discovered scripts. Generated,
dependency, state, credential-like and symlink files are explicitly excluded.
Ignored untracked files are absent. `--max-files` bounds the included inventory and
records remaining paths as omitted. File inventory does not establish audit coverage.
Output refuses existing files and project traversal.

## Tasks and evidence

```sh
python3 "$EVOLVE_ROOT/scripts/evolve.py" init --goal "Improve reliability"
python3 "$EVOLVE_ROOT/scripts/evolve.py" add --title "Repair save cancellation" --evidence "Observed interrupted-save failure" --category correctness --criterion regression --criterion review --file src/save.py
python3 "$EVOLVE_ROOT/scripts/evolve.py" start --task E001
python3 "$EVOLVE_ROOT/scripts/evolve.py" run --task E001 --criterion regression --timeout 120 -- python3 -m unittest
python3 "$EVOLVE_ROOT/scripts/evolve.py" observe --task E001 --criterion review --artifact .evolve/review.md --detail "Inspected changed contracts and recovery" --outcome pass
python3 "$EVOLVE_ROOT/scripts/evolve.py" gate --task E001
python3 "$EVOLVE_ROOT/scripts/evolve.py" finish --task E001 --summary "Save cancellation preserves state"
python3 "$EVOLVE_ROOT/scripts/evolve.py" next
python3 "$EVOLVE_ROOT/scripts/evolve.py" reconcile
```

Replace example files/commands with actual project paths and checks. Create and
inspect the review artifact before recording it. Put `--project /path/to/app`
**before the subcommand** when needed.

`add` supports `--impact`, `--effort`, `--risk` (1–5), `--confidence`, repeated
`--criterion`, `--file` and `--depends-on`. The score assists prioritisation; it is
not an automatic decision policy. Criteria are lowercase named labels. The task
brief defines their behavioural meaning.

`move --status queued|blocked|deferred|rejected --reason "..."` records a decision.
`delivery --status local|committed|pr|merged --ref "..."` records a separately
verified result; it performs no Git or GitHub actions. `init --delivery` likewise
records, rather than grants, the permission in the user's task.

Checks run an explicit argument vector with no shell expansion. Timeout is bounded
to 1 hour per command; choose a shorter limit appropriate to the run. Output capture
is bounded to 512 KiB and best-effort redacted. Processes that time out or leave
incomplete output cannot supply passing evidence. Truncated large output is marked;
inspect the relevant signal separately if it is missing.

Snapshots cover tracked and Git-visible untracked files, not ignored untracked
runtime inputs. New source changes or modified inspected artifacts invalidate
evidence. `finish` requires every registered criterion to have a current pass.
Adequate tests and honest observations remain the operator's responsibility.
See [the state reference](../skills/evolve/references/state.md) for lock/recovery.

## Benchmarks

```sh
python3 "$EVOLVE_ROOT/scripts/bench.py" run --name cli-load --workload sample-1000 --machine "runner-id" --runtime "actual-version" --mode release --samples 7 --warmups 1 --output .evolve/load-before.json -- your-app load sample-file
python3 "$EVOLVE_ROOT/scripts/bench.py" compare .evolve/load-before.json .evolve/load-after.json --max-regression 5
```

`run` requires an explicit `--machine` runner/hardware identity and also records OS
and architecture. Do not reuse an identity for distinct hardware. It captures
process wall-clock samples, including process startup and output
capture overhead. It requires a stable source snapshot and refuses failed commands
and existing output files. Use a profiler or instrumented workload for internal
latency, allocations, frame time or memory. Export actual samples in this format:

```json
{
  "name": "typing-latency",
  "unit": "ms",
  "direction": "lower",
  "workload": "synthetic-document-1000-paragraphs",
  "environment": {"machine": "runner-id", "runtime": "actual-version", "mode": "release"},
  "samples": [12.1, 12.4, 12.2]
}
```

The numbers above illustrate the format, not Evolve performance. Both records need
matching name, unit, direction, workload and environment, plus at least three
positive finite samples. `higher` supports throughput-like metrics. Median change
and relative median absolute deviation are descriptive; no significance or causal
proof is claimed. The example 5% regression threshold is a configurable choice.
