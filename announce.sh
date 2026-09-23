#!/bin/bash
# Sunday 18:00 Europe/Berlin cron entry. uv loads .env from this directory.
set -euo pipefail
cd "$(dirname "$0")"
export PATH="$HOME/.local/bin:$PATH"
echo "$(date -Iseconds) announcing"
exec uv run --env-file .env python announce.py
