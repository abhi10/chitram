---
allowed-tools: Bash(git:*), Bash(gh:*), Bash(uv run pytest:*)
description: Run tests, commit, push, and create PR with validation
---

## Context
- Branch: !`git branch --show-current`
- Base comparison: !`git log --oneline main..HEAD 2>/dev/null | head -10 || echo "No commits ahead of main"`
- Changes: !`git status --short`
- Diff stats: !`git diff --stat`
- Recent commits: !`git log --oneline -5`

## Task

### 1. Run Tests First
Run `uv run pytest` in the backend directory. If any tests fail, **stop immediately** and report the failures. Do not proceed with git operations if tests fail.

### 2. Review Changes
Show a summary of what will be committed:
- Files added/modified/deleted
- Brief description of the changes

### 3. Generate Commit Message
Create a commit message following project conventions:
- Use conventional commit format: `type: description`
- Types: feat, fix, docs, refactor, test, chore
- Reference phase from branch name if applicable (e.g., Phase 2B from `feature2/phase-2-redis-minio`)
- End with the Claude Code footer

### 4. Stage and Commit
- Stage all relevant changes (`git add .`)
- Create the commit with the generated message
- Use HEREDOC format for multi-line messages

### 5. Push to Remote
- Push to current branch
- Use `-u` flag if branch doesn't have upstream tracking

### 6. Create Pull Request
Create a PR using `gh pr create` with:

```
## Summary
- [Bullet points summarizing the changes based on ALL commits in the branch]

## Test Results
- X tests passing
- [Any notable test coverage changes]

## Related
- [Phase reference if applicable]
- [Any related issues from branch name]

---
Generated with [Claude Code](https://claude.com/claude-code)
```

### Important
- If `$ARGUMENTS` is provided, use it as the commit message instead of generating one
- If PR already exists for this branch, skip PR creation and just push
- Never force push or amend commits that have been pushed
