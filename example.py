# pip install -r requirements.txt
# Run: ANTHROPIC_BASE_URL=http://localhost:11434 ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_API_KEY="" python example.py
import os
import anyio
from anthropic import Anthropic
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, TextBlock

MODEL = os.environ.get("MODEL", "qwen3.5:9b")


def anthropic_sdk_example():
    """Direct API calls via the anthropic SDK."""
    client = Anthropic(
        base_url="http://localhost:11434",
        auth_token="ollama",
        api_key="ollama",
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": "What is 2+2?"}],
    )

    for block in response.content:
        if block.type == "text":
            print(block.text)


def anthropic_sdk_streaming():
    """Streaming via the anthropic SDK."""
    client = Anthropic(
        base_url="http://localhost:11434",
        auth_token="ollama",
        api_key="ollama",
    )

    with client.messages.stream(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": "Write a hello world in Python"}],
    ) as stream:
        for text in stream.text_stream:
            print(text, end="", flush=True)
    print()


async def agent_sdk_example():
    """Uses Claude Code CLI under the hood - has access to tools."""
    options = ClaudeAgentOptions(
        max_turns=1,
        model=MODEL,
    )
    async for message in query(
        prompt="What files are in the current directory?",
        options=options,
    ):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text)


if __name__ == "__main__":
    print("=== anthropic SDK ===")
    anthropic_sdk_example()

    print("\n=== anthropic SDK (streaming) ===")
    anthropic_sdk_streaming()

    print("\n=== claude-agent-sdk ===")
    anyio.run(agent_sdk_example)
