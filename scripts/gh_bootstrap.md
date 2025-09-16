# GitHub bootstrap (using `gh` CLI)

```bash
# 1. Create a new private repo and push
gh repo create cassandra-project --private --source . --remote origin --push

# 2. Protect main branch (basic)
gh api -X PUT repos/:owner/cassandra-project/branches/main/protection -f required_status_checks.strict=true -f enforce_admins=true -F required_status_checks='{"checks":[{"context":"QA"}]}' -f required_pull_request_reviews.dismiss_stale_reviews=true

# 3. Enable Actions (default on for new repos)
# 4. Create a PR to test CI
git checkout -b setup-ci
git commit --allow-empty -m "test: trigger QA"
git push -u origin setup-ci
gh pr create --fill
```

If the protection endpoint errors, set branch rules via the GitHub UI:
- Require pull request reviews (1+), dismiss stale approvals when new commits land.
- Require status checks to pass (QA workflow).
- Restrict who can push to `main`.

Store any secrets as needed under Settings → Secrets and variables → Actions.
