"""Check Git history, Python source, and installed dependencies for security issues."""

import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    checks = [
        ('Scanning Git history for secrets...', ['gitleaks', 'git', '--redact']),
        (
            'Checking Python source for security issues...',
            [sys.executable, '-m', 'bandit', '-c', 'pyproject.toml', '-r', 'src'],
        ),
        (
            'Checking installed dependencies for known vulnerabilities...',
            [sys.executable, '-m', 'pip_audit', '--local', '--skip-editable'],
        ),
    ]
    for message, command in checks:
        print(message, flush=True)
        try:
            subprocess.run(command, cwd=root, check=True)
        except FileNotFoundError:
            raise SystemExit(f'{command[0]} is not installed or not on PATH') from None
        except subprocess.CalledProcessError as error:
            raise SystemExit(error.returncode) from None


if __name__ == '__main__':
    main()
