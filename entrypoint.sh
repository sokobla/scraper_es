#!/bin/bash
# 🔥 Entrypoint script for scrapper_spain container
# Handles database connection startup, retries, and app launch

set -e  # Exit on error

# Enable error messages
trap 'echo "❌ Entrypoint failed"; exit 1' ERR

echo "Starting scrapper_spain..."
echo "DATABASE_URL: ${DATABASE_URL:0:40}..." # Show first 40 chars (hide password)
echo "LOG_LEVEL: ${LOG_LEVEL:-INFO}"

# 🔥 Wait for PostgreSQL to be ready (with retries)
# This is a fallback if docker healthcheck isn't available
echo "⏳ Checking PostgreSQL connection..."

python3 << 'PYTHON_SCRIPT'
import asyncio
import sys
from database.session import wait_for_db

try:
    # Wait up to 60 seconds for PostgreSQL
    asyncio.run(wait_for_db(max_retries=30, retry_delay=2.0))
    print("✅ PostgreSQL is ready!")
except RuntimeError as e:
    print(f"❌ PostgreSQL startup failed: {e}", file=sys.stderr)
    sys.exit(1)
PYTHON_SCRIPT

# 🔥 Run the actual scraper
echo ""
echo "🚀 Starting scraper application..."
echo "---"
exec python3 run_scrapper.py
