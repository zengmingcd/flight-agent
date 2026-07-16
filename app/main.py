from app.services.llm_client import OpenAIClient


def main() -> None:
    client = OpenAIClient()
    generated_text = client.generate_text(
        system_prompt="You are a concise AI assistant.",
        user_prompt="Say hello in one sentence."
    )
    print(generated_text)


if __name__ == "__main__":
    main()
