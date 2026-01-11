# Git Branch Workflow Rule

Guidelines for AI assistants working on git branches in this project.

---

## Branch Workflow Protocol

### When Starting New Work

**ALWAYS follow this workflow before starting a new phase or feature:**

```bash
# 1. Check current status
git status

# 2. Stash any uncommitted changes (including untracked files)
git stash push -u -m "WIP: [description of changes]"

# 3. Switch to main and sync with remote
git checkout main
git pull origin main

# 4. Create new contextual branch
git checkout -b <branch-name>

# 5. Pop stashed changes
git stash pop
```

---

## Branch Naming Convention

Follow this pattern for branch names:

### Feature Branches
```
feat/<phase-name>-<short-description>
```

Examples:
- `feat/phase5-ai-vision-provider`
- `feat/phase6-automatic-tagging`
- `feat/phase7-distributed-cache`

### Documentation Branches
```
docs/<phase>-<description>
```

Examples:
- `docs/phase5-comprehensive-analysis`
- `docs/phase6-planning`

### Bug Fix Branches
```
fix/<issue-description>
```

Examples:
- `fix/auth-token-expiry`
- `fix/ai-provider-error-handling`

### Other Branches
| Prefix | Use Case | Example |
|--------|----------|---------|
| `feat/` | New features | `feat/phase6-automatic-tagging` |
| `fix/` | Bug fixes | `fix/auth-token-expiry` |
| `docs/` | Documentation | `docs/phase5-retrospective` |
| `refactor/` | Code refactoring | `refactor/ai-provider-cleanup` |
| `test/` | Test additions | `test/integration-openai` |
| `chore/` | Maintenance | `chore/update-dependencies` |

---

## Claude's Automated Workflow

**When user says:** "Let's start Phase X" or "Let's work on feature Y"

**Claude should automatically:**

1. Check current branch with `git status`
2. Stash any uncommitted changes: `git stash push -u -m "WIP: <description>"`
3. Pull latest from `main`: `git pull origin main`
4. Create contextual branch: `git checkout -b <branch-name>`
5. Pop stashed changes: `git stash pop`
6. Confirm branch creation and show status

### Example Execution

```bash
# User: "Let's start Phase 6"

# Claude automatically runs:
git stash push -u -m "docs: Phase 5 documentation updates"
git checkout main
git pull origin main
git checkout -b feat/phase6-automatic-tagging
git stash pop
git status

# Confirms: "Created feat/phase6-automatic-tagging branch with your changes preserved"
```

---

## When to Use This Workflow

### Use Cases

✅ **Always use before:**
- Starting a new phase
- Beginning a new feature
- Creating substantial documentation
- Making significant refactoring

✅ **Examples:**
```
User: "Let's start Phase 6"
User: "Save these docs on a new branch"
User: "Let's implement automatic AI tagging"
User: "Create a branch for this feature"
```

❌ **Don't use for:**
- Emergency hotfixes that need immediate deployment
- Simple typo fixes (commit directly to main)
- Emergency production issues

---

## Standard Workflow Commands

### Full Workflow

```bash
# 1. Stash current changes (including untracked files)
git stash push -u -m "Stashing changes before creating new branch"

# 2. Switch to main and sync
git checkout main
git pull origin main

# 3. Create and switch to new contextual branch
git checkout -b <branch-name>

# 4. Pop stashed changes
git stash pop

# 5. Verify changes applied
git status
```

### Quick One-Liner

```bash
# Stash, sync, create branch, pop - all in one command
git stash push -u -m "WIP" && \
git checkout main && \
git pull origin main && \
git checkout -b feat/phase6-automatic-tagging && \
git stash pop
```

---

## Stash Management

### Listing Stashes
```bash
git stash list
# Shows: stash@{0}: On main: Phase 5 docs complete
```

### Applying Specific Stash
```bash
git stash apply stash@{0}  # Apply but keep in stash
git stash pop stash@{0}    # Apply and remove from stash
```

### Viewing Stash Contents
```bash
git stash show -p stash@{0}  # Show diff of stashed changes
```

### Clearing Stashes
```bash
git stash drop stash@{0}  # Remove specific stash
git stash clear           # Remove all stashes (use with caution)
```

---

## Troubleshooting

### Problem: Stash pop has conflicts

```bash
# Solution 1: Resolve conflicts manually
# Edit conflicting files
git add <resolved-files>
git stash drop  # Remove stash after resolving

# Solution 2: Keep stash for later
git stash apply  # Try applying without removing
git stash show   # See what was stashed
```

### Problem: Forgot to stash before pulling

```bash
# Solution: Stash now (if no conflicts)
git stash push -u -m "Late stash"
git pull origin main
git stash pop
```

### Problem: Need to switch branches mid-work

```bash
# Solution: Stash, switch, work, switch back, pop
git stash push -u -m "WIP: feature X"
git checkout other-branch
# Do work...
git checkout original-branch
git stash pop
```

---

## Best Practices

1. **Always stash with descriptive messages**
   - ❌ Bad: `git stash`
   - ✅ Good: `git stash push -u -m "Phase 5 docs before phase 6 branch"`

2. **Pull before creating branches**
   - Ensures branch starts from latest main
   - Avoids merge conflicts later

3. **Use `-u` flag for untracked files**
   - Stashes new files too (like new docs)
   - Prevents loss of work

4. **Verify after pop**
   - Check `git status` to confirm all changes applied
   - Look for conflict markers `<<<<<<<`

5. **Clean up stashes**
   - Don't accumulate old stashes
   - Drop after successful pop: `git stash drop`
   - Clear periodically: `git stash list`

---

## Integration with Existing Rules

This workflow complements:
- `.claude/rules/commit-checklist.md` - Pre-commit verification
- `.claude/commands/ship.md` - Full CI/CD workflow
- `.claude/rules/python.md` - Code quality standards

**Development Flow:**
```
1. Branch Creation (this rule)
   ↓
2. Development (make changes)
   ↓
3. Commit Checklist (verify quality)
   ↓
4. Ship Command (push, PR, deploy)
```

---

## Examples

### Example 1: Starting Phase 6

```bash
# Current: On main with Phase 5 documentation updates
git stash push -u -m "Phase 5 docs complete"
git checkout main
git pull origin main
git checkout -b feat/phase6-automatic-tagging
git stash pop

# Result: On feat/phase6-automatic-tagging with docs preserved
```

### Example 2: Documentation Branch

```bash
# Current: Working on comprehensive analysis docs
git stash push -u -m "Phase 5 comprehensive analysis"
git checkout main
git pull origin main
git checkout -b docs/phase5-comprehensive-analysis
git stash pop

# Result: Docs committed separately from feature work
```

### Example 3: Bug Fix Branch

```bash
# Current: Found bug in AI provider
git stash push -u -m "WIP: provider refactor"
git checkout main
git pull origin main
git checkout -b fix/ai-provider-error-handling
git stash pop

# Result: Bug fix isolated in dedicated branch
```

---

## Related Rules

- [Commit Checklist](.claude/rules/commit-checklist.md) - Pre-commit verification
- [Ship Command](.claude/commands/ship.md) - Full deployment workflow
- [Python Guidelines](.claude/rules/python.md) - Code quality standards

---

**Created:** 2026-01-11
**Purpose:** Ensure consistent git branch management for phase-based development
