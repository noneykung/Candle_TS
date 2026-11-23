#!/usr/bin/env bash
# Pull the latest code on the server and rebuild the bot.
# Usage: ./deploy.sh ubuntu@<vm-ip>
# Env:   DEPLOY_DIR (default candle_ts), DEPLOY_BRANCH (default main)
set -euo pipefail

host="${1:?usage: ./deploy.sh user@host}"
dir="${DEPLOY_DIR:-candle_ts}"
branch="${DEPLOY_BRANCH:-main}"

ssh "$host" bash -s -- "$dir" "$branch" <<'REMOTE'
set -euo pipefail
cd "$1"
git fetch --prune origin
git checkout "$2"
git pull --ff-only origin "$2"
docker compose up -d --build
docker image prune -f >/dev/null
docker compose ps
docker compose logs --tail 20
REMOTE
