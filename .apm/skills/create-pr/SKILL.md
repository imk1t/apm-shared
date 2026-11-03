---
name: create-pr
description: Create a pull request. Use after committing the changes.
disable-model-invocation: true
argument-hint: '[base branch (defaults to main)]'
---

# Creating a Pull Request

Base branch: `$ARGUMENTS` (defaults to `main` if omitted)

Follow repository instructions (`AGENTS.md`, `CLAUDE.md`, CONTRIBUTING, etc.) if they define branch naming, title, body, or review procedures.

## Procedure

### 0. Check for a review agent

1. Check repository instructions and Review Agent definitions. If an agent covering the changes exists, run it before creating the PR.
2. If no Review Agent exists, note why in the creation report.
3. Resolve findings before creating the PR, or document them in the PR body.

### 1. Check the branch

1. Run `git branch --show-current` and check that the current branch matches the requested scope.
2. If the existing session provides enough context to determine the branch and scope, use it and continue. Do not ask again about already-approved information.
3. Only if the branch does not exist, conflicts with the scope, or the target is ambiguous, propose a name following the repository’s naming convention (or `<type>/<scope>/<description>` if none is specified) and ask for confirmation.

### 2. Preflight checks

Run these in parallel:

- Check uncommitted changes with `git status` and inspect both staged and unstaged diffs to identify changes within the requested scope.
- Review all commits since the base branch with `git log --oneline <base-branch>...HEAD`.
- Review all changes since the base branch with `git diff <base-branch>...HEAD`.

Then complete these steps in order:

1. If intended PR changes are uncommitted, stage only those changes, review the staged diff, and commit them following repository conventions. Preserve unrelated changes; ask only if it is unclear whether a change belongs in the PR.
2. Recheck `git status`, the commits, and the diff against the base branch after committing. Confirm that all intended PR changes are committed before generating the final title and body.

### 3. Generate the PR title and body

Use the repository’s PR template if one exists. Include `Closes #<id>` in a related-issue section only when there is a matching, existing issue.

Analyze all commits and the full diff to generate the following:

**Title**:

- 70 characters or fewer
- Use Conventional Commits format: `<type>(<scope>): <description>`; follow repository conventions for the description language.
- Infer the type and scope from the branch name and commits.

**Body** (when there is no template):

```markdown
## Summary

<!-- Describe 1–3 key changes in bullets. -->

## Test plan

<!-- List checks that were run and checks that were not run. -->
```

### 4. Create the PR

Run these steps in order:

1. Push the branch to the remote (`git push -u origin <current-branch>`).
2. Create the PR with `gh pr create`, explicitly passing the selected base branch with `--base`. Pass the body through a temporary file using `--body-file`. If `gh` is unavailable, use an equivalent method such as GitHub MCP with the same base branch:

```bash
gh pr create --base "<base-branch>" --title "<title>" --body-file <body-file>
```

3. Show the created PR’s URL.
