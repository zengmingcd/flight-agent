from services.llm_client import OpenAIClient


def main() -> None:
    client = OpenAIClient()
    generated_text = client.generate_text("Hello")
    print("Hello")
    print(generated_text)


if __name__ == "__main__":
    main()
