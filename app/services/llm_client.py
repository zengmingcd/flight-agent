import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class OpenAIClient:
    """Provide centralized access to the OpenAI Response API."""
    def __init__(self) -> None:
        load_dotenv(ENV_FILE)

        api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL")

        if not api_key:
            raise ValueError(f"OPENAI_API_KEY is not set in {ENV_FILE}")
        if not self.model:
            raise ValueError(f"OPENAI_MODEL is not set in {ENV_FILE}")

        self.client = OpenAI(api_key=api_key)

    def generate_text(
            self, 
            system_prompt: str,
            user_prompt: str,
            ) -> str:
        """Generate text from system instructions and user input."""
        response = self.client.responses.create(
            model=self.model,
            instructions=system_prompt,
            input=user_prompt,
        )

        return response.output_text
