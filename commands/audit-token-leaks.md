---
description: Full token-leak audit of this workspace (icm-token-discipline)
---
Run a token-leak audit of the workspace at $ARGUMENTS (if no path given: the current directory), using the icm-token-discipline skill.

1. Load ~/.claude/skills/icm-token-discipline/SKILL.md (or the project-level copy under .claude/skills/) and follow its Audit mode.
2. If this conversation already carries significant history, say so first and recommend running /clear and re-issuing this command in the fresh session — an audit should not ride on a fat context.
3. Run scripts/icm_audit.sh from the workspace root; follow references/audit.md in order; propose any file moves for approval before executing them.
4. Deliver TOKEN_LEAK_AUDIT.md in the workspace root per references/report-template.md, and close with a load report.
