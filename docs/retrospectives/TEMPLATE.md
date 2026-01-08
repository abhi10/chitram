# Incident Retrospective Template

**Copy this template for each incident. Save as `YYYY-MM-DD-short-description.md`**

---

# Incident: [Short Title]

**Date:** YYYY-MM-DD
**Severity:** P1 (Critical) | P2 (Major) | P3 (Minor) | P4 (Low)
**Duration:** X hours (from detection to resolution)
**Author:** [Name]

---

## Summary

*One paragraph describing what happened and the user impact.*

---

## Timeline

| Time (UTC) | Event |
|------------|-------|
| HH:MM | First occurrence / deployment |
| HH:MM | Issue detected |
| HH:MM | Investigation started |
| HH:MM | Root cause identified |
| HH:MM | Fix deployed |
| HH:MM | Verified resolved |

---

## Impact

**Users Affected:** [Number or percentage]
**Functionality Impacted:** [What didn't work]
**Business Impact:** [Revenue, reputation, trust]

---

## Root Cause

*Detailed technical explanation of why the issue occurred.*

---

## Detection Gap

**How was it detected?** [User report / Monitoring / Manual testing]
**Why wasn't it caught earlier?**
- [ ] Missing test coverage
- [ ] Test environment differs from production
- [ ] No monitoring/alerting for this scenario
- [ ] Manual QA missed it
- [ ] Other: ___

---

## Resolution

**Immediate Fix:** [What was done to restore service]
**PR/Commit:** [Link to fix]

---

## Lessons Learned

### What Went Well
-

### What Went Wrong
-

### Where We Got Lucky
-

---

## Action Items

| Action | Owner | Priority | Due Date | Status |
|--------|-------|----------|----------|--------|
| [Action item] | [Name] | P1/P2/P3 | YYYY-MM-DD | [ ] |

---

## Prevention

**How do we prevent this class of issue?**

- [ ] Add automated test for this scenario
- [ ] Add monitoring/alerting
- [ ] Update deployment checklist
- [ ] Improve code review process
- [ ] Add integration test
- [ ] Other: ___

---

## References

- PR: [Link]
- Related Issues: [Links]
- Relevant Docs: [Links]
