# Host compatibility

Evolve's workflow is portable Markdown. Its executable helpers use Python 3.10+
and the standard library; repository evidence tools also require Git. A capable
host needs file/terminal access to implement changes. Browsing, UI automation,
subagents and GitHub access are optional environment capabilities, not bundled
services.

| Host | Bundled installation | Invocation |
| --- | --- | --- |
| Codex | Project `.agents/skills/`; global `~/.agents/skills/` | `$evolve` or a specialist name |
| Claude Code | Project `.claude/skills/`; global `~/.claude/skills/` | `/evolve` for a folder install |
| Shared Agent Skills host | `--host agents` uses `.agents/skills/` | Use the host's native skill loader |
| Another host | `--host portable --target /path/to/skills` | Load the installed `SKILL.md` explicitly |

Use the folder your installed host version actually discovers. The table describes
installation targets, not a certification of live behaviour. A text-only chat can
explain the method but cannot execute the tools or verify application changes.

## Installation behaviour

The coordinator owns shared references, templates and helpers. The bundled
installer includes it when you select any specialist. Specialists explain how to
find the sibling coordinator and contain a usable fallback procedure. When using
an external Skills CLI, select `evolve` with the specialists to retain shared tools.

The installer copies only the selected skills and their required resources/licence.
It does not configure models, connectors, permission settings, browsers or the host.
Restart/reload skills according to your agent if new files are not discovered.

Python commands may be `python3`, `python` or `py -3` depending on the environment.
Use an interpreter meeting the minimum version. Paths must be quoted. On Windows
use PowerShell variables (`$EvolveRoot`) or explicit quoted paths rather than POSIX
shell syntax; skill invocations are never terminal commands.

## Updates and removal

`.evolve-install.json` in the target skills directory records owned checksums.
Updates/removal refuse edited files, unsafe paths and symlinks. Updates also refuse
to silently restore a locally deleted managed file or adopt an unmanaged skill.
Preserve customisations explicitly before replacing an installation.

User-added files and unrelated skills are retained. Per-file replacement is atomic;
the entire pack update is not a transaction. An interrupted update may require
preserving the current folders and reinstalling into a clean target. Do not delete
customisations or forge checksums to conceal an interrupted/edited installation.
Install/update/remove operations are serialized by `.evolve-install.lock`; dry runs
make no writes and provide a point-in-time preview. After a crashed installation,
verify no writer remains before removing a leftover lock.

## Verification scope

Static checks validate metadata, links and syntax. Unit/integration tests exercise
helpers and installation behaviour. Behavioural evaluations test agent decisions
in a specific session. None of those alone establishes universal host compatibility.
Read [testing](testing.md) for the actual validation record and evaluation method.
