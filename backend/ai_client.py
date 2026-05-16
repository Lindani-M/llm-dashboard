import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

CLAUDE_ENDPOINT = os.getenv("CLAUDE_ENDPOINT", "").rstrip("/")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
CLAUDE_DEPLOYMENT_NAME = os.getenv("CLAUDE_DEPLOYMENT_NAME", "claude-sonnet-4-6")


def generate_commentary(prompt: str) -> str:
    """Call Azure AI Foundry (Claude Sonnet 4.6) to generate commentary."""
    url = f"{CLAUDE_ENDPOINT}/v1/messages"
    headers = {
        "api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": CLAUDE_DEPLOYMENT_NAME,
        "max_tokens": 500,
        "messages": [{"role": "user", "content": prompt}],
    }
    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, json=payload, headers=headers)
        response.raise_for_status()
    return response.json()["content"][0]["text"]
