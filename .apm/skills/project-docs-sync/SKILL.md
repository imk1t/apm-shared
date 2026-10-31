---
name: project-docs-sync
description: Keep the README and related documentation in sync with changes to structure, development commands, configuration, responsibilities, or verification methods, and with moved or deleted code or settings. Also use when asked to update documentation. Use code-docs for declaration-level documentation comments.
---

# Keeping Project Documentation in Sync

Follow repository instructions (`AGENTS.md`, `CLAUDE.md`, CONTRIBUTING, etc.) and documentation ownership policies. Make routine updates required by structural changes as part of the task.

## Determine what to update

1. Read `git status --short`, the target diff, tracked files, and changed implementation and configuration. Distinguish the user’s uncommitted work from changes within the current task.
2. Identify changes to structure, startup, environment variables, configuration, public APIs, ownership, or verification methods. If no target is specified, update only documents affected by the current changes.
3. Find the source of truth for each piece of information in the README, agent instructions, specifications, and directory-level READMEs. Use the repository’s existing documentation locations; do not require a fixed directory structure or filenames.

## Keep documentation aligned with implementation

- Compare commands, arguments, defaults, environment variables, and required tools with the actual scripts, manifests, Makefiles, CI, and configuration. Do not reimplement behavior in documentation or IDE settings.
- When a development entry point changes, also check consumer-managed IDE task/launch settings and CI invocations. Do not add new settings when none currently exist just to satisfy this check.
- Search with `rg` or a similar tool for names, paths, commands, and anchors that were added, moved, renamed, or removed. Update references, links, and structure tables. For generated documentation, update the source of truth and use the existing generation process.
- Do not duplicate the same contract across multiple documents; link to the authoritative detailed source. Before deleting an old document, move any still-needed contract to its source of truth. Follow existing retention policies for archival copies.
- Distinguish what is implemented in the current worktree, what was verified locally, and what is planned but not implemented. Do not describe work from another branch or a past check as merged implementation or current external state.
- Do not change specifications or permissions as part of documentation sync. If it is unclear whether the implementation or specification is correct, report the discrepancy with its supporting evidence.

## Verification and reporting

1. Compare changed statements with the actual files and command definitions. Confirm that local relative links and anchors exist.
2. Run `git diff --check` and any documentation lint, formatter, or generation checks required by the consumer. Do not add a full application test run for documentation-only edits; run relevant checks if execution scripts or configuration also changed.
3. If an APM Skill or configuration changes, update generated artifacts and lockfiles using the consumer’s pinned version and update process, then run the existing APM checks. Do not directly edit deployed copies or lock hashes.
4. Report the documents updated, checks run, checks not run and why, and any remaining inconsistencies.

Do not add external state lookups or updates, deployments, publishing, or monitor registrations based on an assumption that documentation sync requires them. If external verification is part of the request, follow its authorization and the repository’s operational procedures.
