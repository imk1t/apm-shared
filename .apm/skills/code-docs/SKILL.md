---
name: code-docs
description: Write or update documentation comments for functions, types, constants, and modules (TSDoc/JSDoc, docstrings, etc.). Use when adding or changing exports, or when asked to improve code documentation.
argument-hint: '[file, directory, or symbol to document (defaults to the current diff)]'
---

# Writing Documentation Comments

Target: `$ARGUMENTS` (if omitted, declarations added or changed relative to the base branch)

Follow repository instructions (`AGENTS.md`, `CLAUDE.md`, CONTRIBUTING, lint configuration, etc.) if they specify the language, format, or tags for comments. Otherwise, match the style of nearby code (language, length, use of tags such as `@param`, and sentence punctuation). Existing code takes precedence over the examples in this Skill.

## Choose what to document

1. If no target is specified, use `git diff <base>...HEAD` and uncommitted changes to find declarations that were added, had their signatures changed, or had their behavior changed.
2. Write comments for these, in priority order:
   - Exports used from outside the module (functions, classes, types, constants)
   - Internal functions whose assumptions, units, or failure behavior are unclear from their names and types
   - Type fields with non-obvious semantics (units, defaults when omitted, or the meaning of `null`)
   - Modules whose responsibility is not apparent from their name (one line at the top of the file)
3. Do not document declarations whose names and types fully explain their meaning (such as `isEmpty`, simple getters, or type aliases), tests, generated files, or files with fixed hashes. Do not aim for a particular number of comments.

## What to write

Document what callers need to know, not a restatement of what the code does.

- State **what the declaration returns or does** in one sentence. Start with a verb or describe the return value as a noun (for example, “The largest multiple of `step` that is less than or equal to `ms`.”).
- **Preconditions and contract**: accepted input ranges, units (ms, yen, %), time basis (UTC, local), and side effects (writes, network access, changes to `process.exitCode`).
- **Failure behavior**: exceptions thrown, conditions that return `null`/`undefined`, and whether failures are propagated rather than swallowed.
- **Non-obvious rationale**: why this implementation is used, or why an alternative was not chosen (only when needed).
- If a parameter’s name and type are not enough, refer to it in the body as `` `name` ``. Follow the repository’s convention if it uses `@param`/`@returns`.
- Add an example with `@example` or a short inline example only when the signature alone could make usage easy to misunderstand.

Do not include:

- Type information already expressed by annotations (for example, `{string}` in TypeScript)
- Change history, authors, dates, ticket numbers, or phrases such as “newly added” (put that context in Git history and the PR)
- A line-by-line walkthrough of the implementation, or abandoned TODOs
- Behavior that does not exist or plans for the future. Comments must match the current code.

## Format

- For TypeScript/JavaScript, put `/** ... */` immediately before the declaration. Use one line when one sentence is enough; use multiple lines for multiple sentences.
- For other languages, follow the language standard (Python docstrings, Go `// Name ...`, Rust `///`).
- Wrap code snippets, identifiers, and values in backticks.
- Keep the language and style consistent within each file or module.

```ts
/** Returns the largest multiple of `step` not exceeding `ms`. Requires finite inputs and a positive `step`. */
export function floorTo(ms: number, step: number): number {
  return Math.floor(ms / step) * step;
}

export type Options = {
  /** Indentation for JSON written to stdout. Defaults to a single line. */
  indent?: number;
};
```

## Updating existing comments

1. When behavior changes, update the relevant comment in the same change. An outdated comment is worse than no comment.
2. If a comment conflicts with the implementation, check the implementation and tests before updating the comment to match. If the implementation appears wrong, leave the comment unchanged and report the discrepancy.
3. If a declaration is removed, remove its comment and references to it elsewhere (`{@link}`, README, etc.).

## Verification

1. Compare every comment with the implementation. Confirm that its stated assumptions, units, and failure behavior match the code.
2. Run the repository’s lint, type-check, and formatter. A formatter may produce changes even when only comments were edited.
3. In your report, list the declarations documented or updated, and explain any intentionally undocumented targets.
