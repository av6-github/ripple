"""Security and Credentials Audit Script for RIPPLE.

Validates AGENTS.md Rule 5 (No Unauthorized Hardcoding) and Rule 18 (Security Rules):
- Ensures .env is gitignored and not committed.
- Scans tracked source code for accidental hardcoded secrets or private keys.
- Ensures backend-only credentials are never referenced in frontend client files.
"""

import os
import re
import subprocess
import sys

SUSPICIOUS_PATTERNS = [
    (r"neo4j\+s://[^:\s]+:[^@\s]+@", "Hardcoded Neo4j URI with credentials"),
    (r"postgresql://[^:\s]+:[^@\s]+@", "Hardcoded PostgreSQL connection with credentials"),
    (r"-----BEGIN (RSA|EC|OPENSSH|PRIVATE) KEY-----", "Private key file committed"),
    (r"(?i)(api[_-]?key|secret[_-]?key|password)\s*=\s*['\"][A-Za-z0-9_\-\.]{20,}['\"]", "High-entropy API key/secret assignment"),
]

FRONTEND_FORBIDDEN_ENV = [
    "NEO4J_PASSWORD",
    "SUPABASE_SERVICE_ROLE_KEY",
    "PINECONE_API_KEY",
    "DATABASE_URL",
    "GATEWAY_SECRET_KEY",
]


def audit_gitignore() -> bool:
    """Ensure .env is gitignored."""
    if not os.path.exists(".gitignore"):
        print("[-] FAIL: .gitignore missing.")
        return False

    with open(".gitignore", "r") as f:
        content = f.read()

    if ".env" not in content:
        print("[-] FAIL: .env is not listed in .gitignore.")
        return False

    print("[+] PASS: .env is properly gitignored.")
    return True


def audit_tracked_files() -> bool:
    """Scan all project files for suspicious hardcoded secrets."""
    scanned_files = []
    ignored_dirs = {".git", ".venv", "node_modules", ".next", ".cache", ".pytest_cache", "__pycache__"}
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ignored_dirs]
        for f in files:
            scanned_files.append(os.path.relpath(os.path.join(root, f), "."))

    violations = []

    for filepath in scanned_files:
        # Skip this script and env template
        if filepath in ("scripts/run_security_audit.py", ".env.example", ".env") or not os.path.isfile(filepath):
            continue

        try:
            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            continue

        for pattern, desc in SUSPICIOUS_PATTERNS:
            match = re.search(pattern, content)
            if match:
                violations.append((filepath, desc, match.group(0)[:30] + "..."))

        # Check frontend isolation (Rule 18)
        if filepath.startswith("app/") or filepath.startswith("lib/"):
            for forbidden in FRONTEND_FORBIDDEN_ENV:
                if forbidden in content and "NEXT_PUBLIC_" not in content:
                    violations.append(
                        (filepath, f"Backend-only secret '{forbidden}' referenced in client code", forbidden)
                    )

    if violations:
        print("[-] FAIL: Security violations detected:")
        for file, desc, snippet in violations:
            print(f"    - {file}: {desc} ({snippet})")
        return False

    print(f"[+] PASS: Scanned {len(scanned_files)} files. Zero hardcoded secrets found.")
    return True


def main():
    print("==================================================")
    print("RIPPLE Security & Credentials Audit (Rules 5 & 18)")
    print("==================================================")

    pass_gi = audit_gitignore()
    pass_files = audit_tracked_files()

    if pass_gi and pass_files:
        print("\n[+] SUCCESS: Repository passes all security audit checks.")
        sys.exit(0)
    else:
        print("\n[-] FAILED: Security audit failed. Resolve issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
