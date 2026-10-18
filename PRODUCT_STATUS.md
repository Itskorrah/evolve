# Product status

**19 October 2026 — development PR, not a published release.**

Evolve provides six Markdown engineering skills, a managed Python installer,
a source/evidence ledger and benchmark utilities. Separate implementation,
test evidence, actual host acceptance and released software.

| Capability | Implemented | Automated evidence | Real host acceptance | Released |
| --- | --- | --- | --- | --- |
| Six skills, installer, safe update/removal | Yes | Historical main matrix passed (Linux/macOS/Windows, Python 3.10/3.13) | Only prior small Python agent trial | Existing untagged main |
| Read-only installer verification, checksum validation | This PR | Targeted tests; verify final CI head | Not exercised in target agent hosts | No |
| Windows reparse-point rejection | This PR | New junction regression, may skip if Windows restricts creation | No physical Windows install check | No |
| Evidence ledger and benchmark scripts | Existing | Existing unit/integration tests | One small Python trial in [validation](docs/validation.md) | Existing untagged main |
| Four agent reference workloads and trial comparison | This PR | Fixture smoke tests and comparator tests | Matched live runs outstanding | No |
| Automated push/merge/publish | Not built into pack; agent-host delivery instructions only | Not certified as live workflow | Not established | No |

An older green check never certifies a changed PR head. Current acceptance
requires inspecting the **latest** PR revision's GitHub Actions results. No
production deployment, cross-host certification or measured model quality
improvement is claimed.

## Ranked next work

1. Resolve any latest-head CI failures; inspect Windows/macOS/Linux matrix results.
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
