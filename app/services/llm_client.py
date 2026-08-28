import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from typing import TypeVar
from pydantic import BaseModel


ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

T = TypeVar("T", bound=BaseModel)
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
    
    def generate_structured(self, 
                            system_prompt: str, 
                            user_prompt: str, 
                            response_model: type[T]) -> T:
        response = self.client.responses.parse(
            model=self.model,
            instructions=system_prompt,
            input=user_prompt,
            text_format=response_model
        )

        parsed = response.output_parsed

        if parsed is None:
            raise ValueError("OpenAI response could not be parsed!")
        
        return parsed
