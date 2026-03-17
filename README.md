# cc-local: Run Claude Code with local models

Run open-source models locally and use them as a backend for Claude Code. Ollama supports the Anthropic API natively, so no proxy or translation layer is needed.

```
Claude Code  --[Anthropic API]-->  Ollama (:11434)  -->  Qwen3.5
```

## Quick Start

### 1. Install Ollama

```sh
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Pull a model

```sh
ollama pull qwen3.5:9b
```

First run downloads the model (~6.6GB). It stays cached after that.

### 3. Run Claude Code

```sh
bash claude-local.sh
```

Or manually:

```sh
ANTHROPIC_BASE_URL=http://localhost:11434 \
ANTHROPIC_AUTH_TOKEN=ollama \
ANTHROPIC_API_KEY="" \
claude --model qwen3.5:9b
```

## Model Recommendations

| Model | Size | RAM/VRAM Needed | Notes |
|---|---|---|---|
| `qwen3.5:9b` | 6.6 GB | ~10 GB | Good balance of speed and quality |
| `qwen3.5:27b` | 18 GB | ~24 GB | Better quality, needs more memory |
| `qwen3.5:4b` | 3.0 GB | ~5 GB | Fastest, lower quality |

To switch models, pull it and edit `claude-local.sh`:

```sh
ollama pull qwen3.5:27b
# then change --model qwen3.5:9b to --model qwen3.5:27b in claude-local.sh
```

## Verify Ollama is running

```sh
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3.5:9b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 64}'
```
