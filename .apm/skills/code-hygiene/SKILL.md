---
name: code-hygiene
description: Remove obsolete implementations, references, dependencies, and duplicate logic after replacing, moving, renaming, or deleting a module, CLI, screen, component, or dependency, or before completing a refactor. Also use when asked to investigate dead code.
---

# Cleaning Up Obsolete Code After Changes

Prioritize repository instructions, public API and compatibility policies, code ownership boundaries, and existing static analysis and verification. Clean up what became obsolete because of the current change; do not expand the task into unrelated refactoring.

## What to clean up

1. **Replaced paths**: Identify old modules, symbols, and entry points from the target diff. Use `rg`, language reference search, and existing unused-code checks to find consumers. Check references in tests, scripts, CI, configuration, and documentation as well as implementation code.
2. **Consumers not visible to static search**: Check package exports, public APIs, plugin registration, dynamic imports, string-based registration, framework-convention entry points, generation steps, and external consumers. Do not delete something only because a search returns no results. Report public artifacts with unknown external usage as candidates.
3. **Remaining compatibility layers and re-exports**: Remove obsolete old paths and forwarding code when no longer needed. Retain compatibility layers and barrel exports when required by a public API or staged migration, according to the consumers’ contracts.
4. **Duplicate logic**: Before adding a helper, look for equivalent existing logic and its source of truth. When sharing is needed, use an existing shared module that fits the responsibility instead of redeclaring the same type or logic for convenience. Do not merge business logic just because the expressions look similar.
5. **Dependencies and settings made obsolete in turn**: When removing the last consumer of a component, script, or dependency, check manifests, lockfiles, configuration, startup registration, and related generation steps. Update dependencies and lockfiles with the package manager used by the consumer.

## How to make changes

- Once the basis for removal or consolidation is clear, clean up obsolete implementations and references within scope as part of the same task. Preserve the user’s changes and work outside the task scope.
- When moving or deduplicating code, preserve existing behavior such as return values, exceptions, exit codes, persisted formats, times, and units. If the contract needs to change, do not present that as routine cleanup; check it against the requested scope.
- Do not hand-edit generated artifacts or assets with fixed hashes; use the consumer’s update process. Check that rejection handling, permission checks, and regression tests are not still needed to uphold the current contract.
- If names in documents or commands are affected, update the related README, specifications, and references. Use `project-docs-sync` if available.

## Verification and reporting

1. After cleanup, search again for references to old symbols, paths, and dependencies. Confirm that required consumers have not been disconnected.
2. Run the consumer’s unused-code and dependency checks, plus type checks, tests, and lint relevant to the changed areas. If a public export or startup entry point changed, include checks of its consumers or launchers.
3. Report what was removed or consolidated and why, what was retained for compatibility, verification results, and any consumers that remain unconfirmed.

For investigation-only requests, do not edit files. For each candidate, provide the supporting path and symbol, usage status, and behavior or compatibility impact. Removing external resources is outside code cleanup.
