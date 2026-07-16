# Learn log day 2

## What did I do:
- Create .env and store the api_key, default model value.
- Create services/llm_client.py to create a reusable `OpenAIClient` that centralizes OpenAI API access.
- Create main.py to invoke the openai function.

## Tips

### Why wrap the SDK?

The application should not call the OpenAI SDK directly from business services.
Centralizing access makes model configuration, error handling, retries, logging,
testing, and future provider replacement easier.

## Problems:
- N/A
