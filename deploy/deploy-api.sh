#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "==> Pulling latest code..."
# Generate GitHub token using existing App credentials
source ~/.bashrc

HEADER=$(echo -n '{"alg":"RS256","typ":"JWT"}' | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')
NOW=$(date +%s)
IAT=$((NOW - 60))
EXP=$((NOW + 600))
PAYLOAD=$(echo -n "{\"iat\":${IAT},\"exp\":${EXP},\"iss\":\"${GITHUB_APP_ID}\"}" | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')
SIGNATURE=$(echo -n "${HEADER}.${PAYLOAD}" | openssl dgst -sha256 -sign "${GITHUB_APP_KEY}" | openssl base64 -e -A | tr '+/' '-_' | tr -d '=')
JWT="${HEADER}.${PAYLOAD}.${SIGNATURE}"

TOKEN=$(curl -s -X POST \
  -H "Authorization: Bearer ${JWT}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/app/installations/${GITHUB_INSTALLATION_ID}/access_tokens" | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

git remote set-url origin "https://x-access-token:${TOKEN}@github.com/{your-github-org}/pump-lifecycle-api.git"
git pull origin main
git remote set-url origin "https://github.com/{your-github-org}/pump-lifecycle-api.git"

echo "==> Building and deploying API..."
docker compose -f docker-compose.api.yml build --no-cache
docker compose -f docker-compose.api.yml up -d --force-recreate

echo "==> Waiting for health check..."
sleep 10
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool

echo "==> Deploy complete!"
