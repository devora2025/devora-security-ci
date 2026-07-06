#!/usr/bin/env bash
# One-time setup: stamp your GitHub org/user name into every file.
# Usage: ./setup.sh <your-github-org-or-username>
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Usage: ./setup.sh <your-github-org-or-username>"
  echo "Example: ./setup.sh devora-agency"
  exit 1
fi

ORG="$1"
echo "Stamping org '$ORG' into workflow references..."
grep -rl "YOUR_GITHUB_ORG" --exclude-dir=.git --exclude=setup.sh . | while read -r f; do
  perl -pi -e "s/YOUR_GITHUB_ORG/\Q$ORG\E/g" "$f"
  echo "  updated: $f"
done
echo "Done. Now push this repo to github.com/$ORG/devora-security-ci"
