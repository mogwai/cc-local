# cc-local: Run Claude Code with local models

Use local models with [Claude Code](https://docs.anthropic.com/en/docs/claude-code) CLI and [Python SDK](https://github.com/anthropics/claude-agent-sdk-python) via Ollama or vLLM.

## What is Claude Code?

Claude Code is an AI coding agent that runs in your terminal. It can:

- **Read and edit files** in your project
- **Run shell commands** (git, tests, builds, etc.)
- **Search your codebase** (grep, glob, find patterns)
- **Create and review PRs**, write commits
- **Answer questions** about your code
- **Use custom tools** via MCP servers or CLI tools (CLIs are simpler - Claude can call any CLI via Bash)

It works by giving the model access to tools (Read, Write, Edit, Bash, Grep, etc.) and letting it decide which to use. With this repo, you can run it entirely locally using open-source models instead of the Anthropic API.

### Configuration

Claude Code uses `CLAUDE.md` files for project-specific instructions:

- **`~/.claude/CLAUDE.md`** - global instructions (applies to all projects)
- **`./CLAUDE.md`** - project-level instructions (checked into git)
- **`./CLAUDE.local.md`** - local overrides (gitignored)

Example `CLAUDE.md`:
```markdown
- Use pytest for testing
- Never modify files in src/generated/
- Run `make lint` before committing
```

Settings live in `~/.claude/settings.json` (global) and `.claude/settings.json` (project). See the [full docs](https://docs.anthropic.com/en/docs/claude-code).

## Ollama

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

### Verify

```sh
curl http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3.5:9b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 64}'
```

## vLLM (faster inference)

vLLM gives better GPU utilization and faster inference than Ollama, but requires Docker and NVIDIA GPUs.

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

## Models

| Model | Size | RAM/VRAM Needed | Notes |
|---|---|---|---|
| `qwen3.5:9b` | 6.6 GB | ~10 GB | Good balance of speed and quality |
| `qwen3.5:27b` | 18 GB | ~24 GB | Better quality, needs more memory |
| `qwen3.5:4b` | 3.0 GB | ~5 GB | Fastest, lower quality |

To switch models, pull it and update the model name in `claude-local.sh` or `docker-compose.yml`.

## Python SDK

```sh
pip install -r requirements.txt
```

Two SDKs:

- [`anthropic`](https://github.com/anthropics/anthropic-sdk-python) - direct API calls, simple, no CLI needed
- [`claude-agent-sdk`](https://github.com/anthropics/claude-agent-sdk-python) - wraps Claude Code CLI, gives access to tools (Read, Write, Bash, etc.)

See `example.py` for working examples of both.

### anthropic SDK

```python
import anthropic

client = anthropic.Anthropic(
    base_url="http://localhost:11434",  # or http://localhost:8000 for vLLM
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

Wraps the Claude Code CLI - has access to all tools (Read, Write, Bash, etc.):

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

### Custom Tools

You can give Claude new tools as Python functions using the `@tool` decorator. These run in-process as MCP servers:

```python
import anyio
from claude_agent_sdk import (
    tool, create_sdk_mcp_server, ClaudeAgentOptions,
    ClaudeSDKClient, AssistantMessage, TextBlock,
)

@tool("get_weather", "Get weather for a city", {"city": str})
async def get_weather(args):
    return {"content": [{"type": "text", "text": f"Sunny, 20C in {args['city']}"}]}

@tool("get_time", "Get current time in a timezone", {"timezone": str})
async def get_time(args):
    from datetime import datetime
    return {"content": [{"type": "text", "text": f"12:00 PM in {args['timezone']}"}]}

server = create_sdk_mcp_server(name="my-tools", tools=[get_weather, get_time])

async def main():
    options = ClaudeAgentOptions(
        max_turns=3,
        model="qwen3.5:9b",
        mcp_servers={"tools": server},
        allowed_tools=["mcp__tools__get_weather", "mcp__tools__get_time"],
    )
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's the weather in London?")
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

anyio.run(main)
```

Tool names follow the pattern `mcp__<server-name>__<tool-name>`. Adding them to `allowed_tools` lets Claude call them without a permission prompt.

See the [claude-agent-sdk docs](https://github.com/anthropics/claude-agent-sdk-python) for more details.
