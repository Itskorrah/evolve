# Product status

**19 October 2026 — improvements merged into main; no versioned release published.**

Evolve provides six Markdown engineering skills, a managed Python installer,
a source/evidence ledger and benchmark utilities. Separate implementation,
test evidence, actual host acceptance and released software.

| Capability | Implemented | Automated evidence | Real host acceptance | Released |
| --- | --- | --- | --- | --- |
| Six skills, installer, safe update/removal | Yes | Historical main matrix passed (Linux/macOS/Windows, Python 3.10/3.13) | Only prior small Python agent trial | Existing untagged main |
| Read-only installer verification, checksum validation | Merged in PR #1 | Direct local installer contract tests plus historical CI | Not exercised in target agent hosts | No tagged release |
| Windows reparse-point rejection (installer and ledger) | Merged in PRs #1 and #2 | Installer smoke tests and simulated ledger reparse-point regression | No live Windows device/host check for ledger change | No tagged release |
| Evidence ledger and benchmark scripts | Existing | Existing unit/integration tests | One small Python trial in [validation](docs/validation.md) | Existing untagged main |
| Four agent reference workloads and trial comparison | Merged in PR #1 | Four local fixture smoke tests and comparator positive/negative checks | Matched live runs outstanding | No tagged release |
| Automated push/merge/publish | Not built into pack; agent-host delivery instructions only | Not certified as live workflow | Not established | No |

Direct local verification is available through `python scripts/check.py` and
its two underlying commands; CI is not needed to execute these checks. Historical
cross-platform CI was successful for the original PR #1 head, but does not certify
the later ledger change or this offline runner. A passing local run verifies only
the current interpreter and platform. No production deployment, cross-host
certification or measured model quality improvement is claimed.

## Ranked next work

1. Run the complete offline pack suite from an actual clone on each available
   platform/interpreter, and resolve any failures; do not rely on GitHub Actions.
2. Run paired with/without agent trials for bug, UI, refactor and shipping; inspect
   diffs, live keyboard/browser behaviour and token overhead when metered.
3. Validate native skill loading and permissions on Codex, Claude Code, Cursor,
   OpenCode and Antigravity versions used by real users.
4. Review a release/versioning policy and tag only after approval and validation.
5. Consider whole-pack recovery/rollback if actual interruption evidence warrants it.

## Recovery, permissions and privacy

Install/uninstall manages selected skill directories and ownership state, not
application source. Local edits are not overwritten. On a damaged installation,
back up customisations, confirm no writer remains, and re-install from a reviewed
source. The pack cannot grant push/merge/billing/deployment rights. Keep raw
agent evidence and secrets private; publish only sanitised summaries.

### Further maintenance finding

Installer cleanup previously removed user-owned empty directories during repeat
installation and uninstall. It now prunes only parent folders of removed managed
files, with regression tests. Local reproduction and targeted Linux/Python 3.13
contract tests established the before/after behaviour; native Windows/macOS
verification of this increment remains unrun.

### Follow-up security hardening

The optional ledger's managed file guard now detects Windows junctions/reparse
points as well as ordinary symbolic links. A platform-independent regression
simulates the Windows attribute contract; native Windows verification remains
an external validation item, not a completed host certification.

### Offline validation improvement

A single standard-library command, `python scripts/check.py`, now executes
package validation and unittest discovery, including failure when discovery
finds zero tests. The runner's positive, failing and empty-suite cases were
verified in a synthetic local checkout with spaces in its path. Its execution
against the complete live pack is still a validation gap where network access
prevents retrieving the repository in this sandbox.
