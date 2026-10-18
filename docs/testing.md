# Validation and evaluation

See the [initial validation record](validation.md) for actual checks and the live
workflow trial, including its limitations.

## Automated checks

```sh
python3 scripts/validate.py
python3 -m unittest discover -s tests -v
```

The validator checks six entrypoints, names/descriptions, UI invocation metadata,
relative links, JSON and Python syntax. It does not judge agent decisions.

The executable suite exercises task dependencies and completion, evidence freshness,
latest failures, source-changing checks, artifact changes, resumption, concurrent
state writes, bounded output, timeouts, redaction, literal argv execution, benchmark
comparability/regressions, inventory exclusions and safe installation/update/removal.
Tests use temporary Git repositories and synthetic data. They do not modify accounts
or call model APIs.

CI runs the validator and suite on Linux, macOS and Windows with supported Python
versions. A configured matrix is not evidence that it has run; inspect the actual
GitHub Actions results. Symlink-specific tests skip when the host cannot create links.

## Behavioural evaluation

Use [the evaluation scenarios](../tests/evaluations/README.md) for meaningful skill
changes. Give a fresh agent the skill, a realistic user request and raw fixture
artifacts. Do not include the expected solution in its task prompt. Evaluate actual
diffs, checks and reports with the rubric.

The scenarios are deliberately not an automatic paid model runner. The evaluator
chooses an available authorised host and records model/host, starting revision,
tools, request, outcome and remaining limits. Do not extrapolate one successful
session into universal compatibility or guaranteed autonomous performance.

## Reporting evidence

Distinguish package validation, helper tests, actual agent trial outcomes and
host-specific live sessions. If a tool test passes but a workflow trial fails,
repair the demonstrated behaviour and repeat the relevant evaluation. Prefer
targeted corrections over accumulating generic instructions.

## Installer integrity command

```sh
python scripts/install.py install --target "/tmp/evolve skills"
python scripts/install.py verify --target "/tmp/evolve skills"
python scripts/install.py uninstall --target "/tmp/evolve skills"
```

The standalone `verify` checks managed bytes and compares source payloads; it
does not certify native skill discovery. Run real agent-host and device/browser
checks separately. Workload comparison instructions are under
[tests/evaluations](../tests/evaluations/README.md).

## Offline one-command checks

Run `python3 scripts/check.py` directly from a trusted checkout to run
`scripts/validate.py` and the unittest suite without relying on GitHub
Actions. It fails if either command fails or discovery runs no tests, and does
not install dependencies, call model providers or modify other repositories.
This verifies only the current environment; compatibility with other Python
versions and operating systems requires separate executions.
