# Contributing

Improve a demonstrated failure or useful workflow. Prefer a focused change that
affects agent decisions over more instructions saying to be thorough.

1. Explain the problem and the observable outcome the change should produce.
2. Update the relevant skill or reference, keeping instructions in one place.
3. Add or adjust meaningful tests for executable behaviour.
4. Run the validator and unit suite from the repository root.
5. For workflow changes, exercise an applicable behavioural evaluation and report
   its outcome, environment, limitations and remaining uncertainty.
6. Submit a focused pull request with the change and validation evidence.

Use Python 3.10+ without third-party packages. Test cross-platform path handling,
failed commands, interrupted state, stale evidence and existing user content.
Installer operations must not discard local edits. Error messages should explain
the condition and the next useful action without exposing credentials.

The evaluation suite is a set of reproducible scenarios and scoring rubrics. It
does not silently call models or incur provider charges. Host compatibility
claims require a real session on that host; static package validation is not
equivalent evidence.
