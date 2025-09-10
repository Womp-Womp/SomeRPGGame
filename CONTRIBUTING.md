# Contributing to AstraRPG

Thank you for your interest in improving AstraRPG. This project aims for a deterministic, testable core engine with thin adapters (CLI and Discord). Contributions should keep that separation clear and be accompanied by strong tests.

## Principles

- Add tests with every change. Do not remove existing tests unless replacing them with stronger coverage that preserves intended behavior.
- Keep numeric logic deterministic and covered by tests. Use seeded RNG via `astrarpg.engine.generation`.
- Use AI assistance responsibly. If AI helps produce code, include tests that lock in behavior, edge cases, and failure modes.
- Prefer small, focused PRs with clear scope and rationale.

## Getting Started

1. Fork the repo and create a feature branch from `main` (e.g., `feat/...` or `fix/...`).
2. Create a virtual environment and install dependencies:
   - Runtime (if needed): `pip install -r requirements.txt`
   - Dev/test: `pip install -r requirements-dev.txt`
3. Run tests locally: `pytest -q`

## Tests

- New features and bugfixes must include tests in `tests/`.
- Cover deterministic engine behavior first (combat, economy, farming, etc.).
- Adapters (CLI/Discord) should stay thin; prefer testing the shared dispatcher and underlying engine.

## Commit Style

- Use concise, descriptive messages (conventional-ish):
  - `feat: ...`, `fix: ...`, `docs: ...`, `test: ...`, `refactor: ...`.
- Keep diffs minimal and focused on the task.

## PR Checklist

- [ ] Added/updated tests for all changes.
- [ ] No tests removed (or replaced with stronger coverage and rationale).
- [ ] Ran `pytest` locally and it passed.
- [ ] Description explains why and how, with any relevant context.
- [ ] If AI-assisted, clearly note it in the PR and ensure tests demonstrate behavior.

## Code of Conduct

Be respectful, constructive, and collaborative. Disagreements should focus on the code and product goals. Harassment or abusive behavior is not tolerated.
