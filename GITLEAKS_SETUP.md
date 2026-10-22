# Secret scanning for contributors

Install Gitleaks from its official release/package source, then enable the repository hook path:

```powershell
git config core.hooksPath .githooks
gitleaks version
```

On Windows, run this in Git Bash or use Git for Windows, which provides the `sh` runtime for `.githooks/pre-commit`. In Git Bash, also run `chmod +x .githooks/pre-commit`. The hook scans staged changes and blocks commits when Gitleaks reports a finding. Do not bypass it to commit credentials. If it flags a real key, rotate/revoke it at its issuer, remove it from the current files, and assess Git history separately.

The hook is a safeguard, not a substitute for scanning every branch and the complete history. After installing it, stage a harmless change and confirm the hook runs before relying on it.
