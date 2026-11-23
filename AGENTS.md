# Project instructions

## Workflow

- Before starting any fix or non-trivial change, create a GitHub issue first. Use `gh issue create` when available.
- Reference the issue number in commit messages and in the pull request body, for example `Closes #123`.
- Never commit directly to `main`. Create a branch from the latest `main` for every change.
- Use conventional branch names:
  - `feature/<short-slug>` for new features
  - `fix/<short-slug>` for bug fixes
  - `docs/<short-slug>` for documentation
  - `chore/<short-slug>` for maintenance
- Use Conventional Commits for every commit:
  - `feat:` new feature
  - `fix:` bug fix
  - `docs:` documentation only
  - `chore:` maintenance
  - `refactor:` code change that neither fixes a bug nor adds a feature
  - `test:` adding or updating tests
  - `style:` formatting or visual changes without behavior change
  - `perf:` performance improvement
  - `ci:` CI configuration
  - `build:` build system or dependency changes
  - `revert:` revert a previous commit
  - Add a scope when useful, for example `feat(lessons): add hint text`.
- Keep one logical change per commit and one focused change per pull request.
- Push the branch and open a pull request against the branch this work is based on, usually `main`. Use `gh pr create` when available.
- Run `python manage.py test --settings=sqlplayground.settings_test` before opening or updating a pull request.

## Scope

- Preserve authentication, roles, profile management, and administrator behavior unless the issue explicitly asks for changes there.
- Do not use em dashes in project documentation or UI copy. Use commas, periods, or parentheses instead.
