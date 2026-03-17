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

## Alternative: vLLM (faster inference)

vLLM gives better GPU utilization and faster inference than Ollama, but requires Docker and NVIDIA GPUs.

```
Claude Code  --[Anthropic API]-->  vLLM (:8000)  -->  Qwen3.5
```

### 1. Start vLLM

```sh
docker compose up -d
docker compose logs -f vllm  # wait for "Uvicorn running on http://0.0.0.0:8000"
```

First run downloads the model from HuggingFace (~18GB).

### 2. Run Claude Code

```sh
bash claude-local-vllm.sh
```

### Configuration

Edit `docker-compose.yml` to change the model or GPU settings. Key flags:

- `--model` - HuggingFace model ID
- `--max-model-len` - context length (default 65536, needs ~24GB VRAM for 9B)
- `--enforce-eager` - required for Qwen3.5 due to a [vLLM bug](https://github.com/vllm-project/vllm/pull/35347) with CUDA graph capture on hybrid Mamba/transformer architectures. Can be removed once fixed upstream
- `--tool-call-parser=qwen3_coder` - enables tool calling
- `--reasoning-parser=qwen3` - separates thinking from content

Stop with `docker compose down`.

## Python

```sh
pip install -r requirements.txt
```

Two SDKs:

- [`anthropic`](https://github.com/anthropics/anthropic-sdk-python) - direct API calls, simple, no CLI needed
- [`claude-agent-sdk`](https://github.com/anthropics/claude-agent-sdk-python) - wraps Claude Code CLI, gives access to tools (Read, Write, Bash, etc.)

See `example.py` for working examples of both.

### anthropic SDK

Use the standard `anthropic` package pointed at Ollama:

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:11434",
    auth_token="ollama",
    api_key="ollama",
)

response = client.messages.create(
    model="qwen3.5:9b",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is 2+2?"}],
)

for block in response.content:
    if block.type == "text":
        print(block.text)
```

The model returns `thinking` blocks (reasoning) followed by `text` blocks (answer). Filter by `block.type == "text"` to get just the answer.

### Streaming

```python
with client.messages.stream(
    model="qwen3.5:9b",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a hello world in Python"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### claude-agent-sdk

Wraps the Claude Code CLI, so it has access to all tools. Set the env vars before running:

```sh
ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_API_KEY="" python example.py
```

```python
import anyio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

async def main():
    options = ClaudeAgentOptions(max_turns=1, model="qwen3.5:9b")
    async for message in query(prompt="What files are here?", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)

anyio.run(main)
```

## Verify Ollama is running

```sh
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3.5:9b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 64}'
```
