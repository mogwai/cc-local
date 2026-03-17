#!/bin/bash
# Run Claude Code against local vLLM instance
# Start vLLM first: docker compose up -d

ANTHROPIC_BASE_URL=http://localhost:8000 \
ANTHROPIC_API_KEY=dummy \
ANTHROPIC_AUTH_TOKEN=dummy \
ANTHROPIC_DEFAULT_OPUS_MODEL=local-model \
ANTHROPIC_DEFAULT_SONNET_MODEL=local-model \
ANTHROPIC_DEFAULT_HAIKU_MODEL=local-model \
claude "$@"
