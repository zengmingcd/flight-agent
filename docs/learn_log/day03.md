# Learn log day 3

## What did I do
- Create flight intent model. This model will store the the user input llm result.
  - Added enum-like fields using Literal
  - Added validation constraints for passengers, price, and confidence 
- Create flight intent test cases.

## Design decisions

### Why allow origin and destination to be None?

The parser must be able to represent incomplete user requests.
The business layer will use missing_fields to decide whether clarification is required.

### Why is decision logic not included in the model?

The Pydantic model represents and validates data.
Business decisions belong in a separate service.

### Literal and default values

A field's default value should always be included in its Literal choices.
Otherwise, the Python model and generated JSON Schema may become inconsistent.
