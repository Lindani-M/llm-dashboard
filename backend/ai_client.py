import os
from pathlib import Path
from dotenv import load_dotenv
from anthropic import AnthropicFoundry

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

CLAUDE_ENDPOINT = os.getenv("CLAUDE_ENDPOINT", "").rstrip("/")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_DEPLOYMENT_NAME = os.getenv("CLAUDE_DEPLOYMENT_NAME", "claude-sonnet-4-6")


def generate_commentary(prompt: str) -> str:
    """Call Azure AI Foundry (Claude Sonnet 4.6) to generate commentary."""
    client = AnthropicFoundry(
        api_key=CLAUDE_API_KEY,
        base_url=CLAUDE_ENDPOINT,
    )
    message = client.messages.create(
        model=CLAUDE_DEPLOYMENT_NAME,
        max_tokens=8000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text

