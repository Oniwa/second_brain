#!/usr/bin/env bash
# Test the process-thought Edge Function with a curl call.
# Usage: ./scripts/test_capture.sh "Your thought here" [source]
# Example: ./scripts/test_capture.sh "Met Sarah about Q3 launch, she needs the deck by Friday" "cli"

set -euo pipefail

THOUGHT="${1:-"Test thought: the quick brown fox jumped over the lazy dog"}"
SOURCE="${2:-"cli"}"

if [[ -z "${SUPABASE_URL:-}" ]]; then
  # Try loading from .env if it exists
  if [[ -f ".env" ]]; then
    export $(grep -v '^#' .env | xargs)
  else
    echo "Error: SUPABASE_URL not set. Copy .env.example to .env and fill in values."
    exit 1
  fi
fi

FUNCTION_URL="${SUPABASE_URL}/functions/v1/process-thought"

echo "Sending thought to: ${FUNCTION_URL}"
echo "Text: ${THOUGHT}"
echo "Source: ${SOURCE}"
echo ""

curl -s -X POST "${FUNCTION_URL}" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
  -d "{\"text\": $(echo "${THOUGHT}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'), \"source\": \"${SOURCE}\"}" \
  | python3 -m json.tool
