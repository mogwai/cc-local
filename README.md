# cc-local: Run Qwen3.5 with vLLM for Claude Code

Run Qwen3.5 models locally on 4090s and use them as a backend for Claude Code via an OpenAI-compatible API + litellm translation layer.

## Architecture

```
Claude Code  --[Anthropic API]-->  litellm (:4000)  --[OpenAI API]-->  vLLM (:8000)  -->  Qwen3.5
```

Claude Code speaks the Anthropic API. LiteLLM translates that to the OpenAI-compatible format that vLLM serves.

## Model Recommendations for 4090 (24GB)

| Model | Active Params | GPUs Needed | Notes |
|---|---|---|---|
| `Qwen/Qwen3.5-35B-A3B` | 3B (MoE) | 1 | **Default.** Best quality-per-VRAM via MoE |
| `Qwen/Qwen3.5-9B` | 9B | 1 | Dense model, solid quality |
| `Qwen/Qwen3.5-4B` | 4B | 1 | Fastest, lower quality |
| `Qwen/Qwen3.5-27B` | 27B | 2+ | Dense, needs multi-GPU or quantization |

## Quick Start

### 1. Configure

```sh
cp .env.example .env
# Edit .env - at minimum set MODEL and GPU_COUNT
```

### 2. Start services

```sh
docker compose up -d
```

First run downloads the model to your HuggingFace cache (~20-70GB depending on model). Monitor progress:

```sh
docker compose logs -f vllm
```

Wait for vLLM to show `Uvicorn running on http://0.0.0.0:8000` before proceeding.

### 3. Verify

```sh
# Check vLLM health
curl http://localhost:8000/health

# Test completion directly
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "Qwen/Qwen3.5-35B-A3B", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 64}'

# Test via litellm (Anthropic API format)
curl http://localhost:4000/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: sk-1234" \
  -H "anthropic-version: 2023-06-01" \
  -d '{"model": "claude-sonnet-4-20250514", "max_tokens": 64, "messages": [{"role": "user", "content": "Hello"}]}'
```

### 4. Configure Claude Code

```sh
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_API_KEY=sk-1234
claude
```

Or add to your shell profile for persistence:

```sh
echo 'export ANTHROPIC_BASE_URL=http://localhost:4000' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY=sk-1234' >> ~/.bashrc
```

## Configuration

All config is via `.env` (copy from `.env.example`):

- **`MODEL`** - HuggingFace model ID (default: `Qwen/Qwen3.5-35B-A3B`)
- **`GPU_COUNT`** - Number of GPUs for tensor parallelism (default: `1`)
- **`MAX_MODEL_LEN`** - Max context length in tokens (default: `65536`). Reduce to `32768` or `16384` if you hit OOM
- **`GPU_MEM_UTIL`** - Fraction of GPU memory vLLM pre-allocates (default: `0.92`)
- **`HF_TOKEN`** - HuggingFace token, only needed for gated models
- **`HF_CACHE`** - Where models are cached on the host (default: `~/.cache/huggingface`)

### Model Mapping

The `litellm-config.yml` maps Claude model names to your local model. By default all Claude model names (opus, sonnet, haiku) route to the same local model. Edit this file if you're running multiple models.

## Multi-GPU Setup

For `Qwen3.5-27B` on 2x 4090:

```sh
# .env
MODEL=Qwen/Qwen3.5-27B
GPU_COUNT=2
MAX_MODEL_LEN=32768
```

## Troubleshooting

**OOM on startup** - Reduce `MAX_MODEL_LEN` or `GPU_MEM_UTIL`. The 35B-A3B MoE model needs ~20GB for weights despite only 3B active params.

**Slow first request** - vLLM compiles CUDA graphs on the first request. Subsequent requests are fast.

**Model download slow** - Set `HF_TOKEN` and make sure you've accepted any model license agreements on huggingface.co.

**litellm errors** - Check that vLLM is healthy first (`curl localhost:8000/health`). litellm won't start until vLLM's healthcheck passes.

## Stopping

```sh
docker compose down
```

Models stay cached in `HF_CACHE` and won't re-download on next start.
