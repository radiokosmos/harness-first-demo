#!/usr/bin/env bash
# One-time setup for Codespaces / devcontainers: Python env, data, seeds, agent runtimes.
set -euo pipefail
pip install --quiet uv
uv sync --quiet
uv run python data/generate.py
DBT_PROFILES_DIR=. .venv/bin/dbt seed -q
DBT_PROFILES_DIR=. .venv/bin/dbt run -q -s staging
# Agent runtimes — bring your own login or API key (see README).
npm install -g --silent @earendil-works/pi-coding-agent @anthropic-ai/claude-code || echo "agent runtimes not installed — install one manually"
bin/doctor || true
