# Day 05 — FlightParser and Structured Output

## 1. What Did I Learn?

### 1.1 Built the `FlightParser` Service

Today I created the `FlightParser` service.

Its responsibility is to convert a natural-language flight request into a standard `FlightIntent` object.

The main processing flow is:

```text
User Query
    ↓
FlightParser.parse()
    ↓
OpenAIClient.generate_structured()
    ↓
OpenAI Responses API
    ↓
Structured Output
    ↓
FlightIntent
    ↓
Deterministic Business Processing
    ↓
Final FlightIntent
```

The caller no longer needs to understand JSON parsing or the details of the OpenAI API.

It can simply use:

```python
intent = flight_parser.parse(user_query)

print(intent.destination)
print(intent.trip_type)
```

This establishes a clean application boundary between natural-language input and typed application data.

---

## 1.2 Learned Python `TypeVar` and `type[T]`

To make `OpenAIClient.generate_structured()` reusable, I learned how Python generic types work.

The implementation uses:

```python
T = TypeVar("T", bound=BaseModel)
```

and:

```python
def generate_structured(
    self,
    system_prompt: str,
    user_prompt: str,
    response_model: type[T],
) -> T:
```

The important relationship is:

```text
type[T] → T

Class      Object
```

For example:

```python
response_model=FlightIntent
```

means:

```text
T = FlightIntent
```

so the return type is also:

```python
FlightIntent
```

This is similar to Java generics:

```java
<T extends BaseModel>
```

and:

```java
Class<T>
```

The benefit is that `OpenAIClient` does not need to know anything about the flight domain.

It can support:

```text
FlightIntent
KYCIntent
HotelIntent
Any other Pydantic BaseModel
```

without adding business-specific methods such as:

```text
generate_flight_intent()
generate_kyc_intent()
generate_hotel_intent()
```

This keeps the LLM client generic and reusable.

---

## 1.3 Learned OpenAI Structured Output

Before Day 5, the flow was:

```text
Prompt
    ↓
generate_text()
    ↓
LLM-generated JSON string
    ↓
json.loads()
    ↓
Application Data
```

The JSON structure was mainly enforced by instructions in the prompt.

For example:

```text
Return only one JSON object.
Do not include Markdown.
Use these fields...
```

The model was still generating normal text and trying to follow those instructions.

With Structured Output, the flow becomes:

```text
Pydantic Model
    ↓
Structured Output Schema
    ↓
OpenAI Responses API
    ↓
Schema-constrained output
    ↓
Pydantic Object
```

The implementation now uses the OpenAI SDK structured parsing capability:

```python
self.client.responses.parse(
    ...
    text_format=response_model,
)
```

and obtains:

```python
response.output_parsed
```

Therefore:

```python
generate_structured(..., FlightIntent)
```

directly returns a `FlightIntent` object instead of a raw JSON string.

---

## 1.4 Prompt and Schema Have Different Responsibilities

One of the most important architectural lessons from Day 5 is that Prompt and Structured Output should not be responsible for the same things.

### Prompt

The Prompt should primarily define **semantic rules**.

For example:

```text
"2 adults and 1 child"
    ↓
passengers = 3
```

or:

```text
"around Christmas"
    ↓
departure_date = null
flexible_dates = true
```

or:

```text
"for three weeks"
    ↓
Do not automatically infer round_trip
```

These require understanding natural language and user intent.

### Schema

The Pydantic / Structured Output Schema should primarily define **data structure and constraints**.

For example:

```text
origin → string or null

passengers → integer

trip_type →
    one_way
    round_trip
    unknown

confidence →
    number within the allowed range
```

Therefore, a useful principle is:

> **Prompt defines semantics; Schema defines structure.**

---

## 1.5 Pydantic Model Becomes the Structural Source of Truth

In Day 4, the Prompt contained an explicit output-schema description.

Now that Structured Output uses `FlightIntent` directly, this creates some duplication:

```text
FlightIntent
    ↓
defines structure

Prompt
    ↓
also describes structure
```

This creates two possible sources of truth.

For example, if the Python model changes but the Prompt is not updated, the two definitions may become inconsistent.

A better long-term design is:

```text
Pydantic
    ↓
Structure + Constraints

Prompt
    ↓
Semantic Extraction Rules

Python
    ↓
Deterministic Business Rules
```

Therefore, the duplicated output-schema description in the Prompt should eventually be reviewed and simplified.

This is primarily a maintainability and Single Source of Truth issue, not merely a token-cost optimization.

---

# 2. What Did We Discover During Implementation?

## 2.1 Structured Output Does Not Guarantee Semantic Correctness

During testing, the following request exposed an important problem:

```text
I want to fly from Toronto to Chengdu around Christmas for three weeks.
Two adults and one child, under 5000 CAD.
```

The expected result included:

```json
{
  "trip_type": "unknown",
  "missing_fields": [
    "departure_date"
  ]
}
```

However, one Structured Output result returned:

```json
{
  "missing_fields": [
    "departure_date",
    "return_date",
    "trip_type"
  ]
}
```

This output was structurally valid.

`missing_fields` was still:

```text
list[str]
```

so Structured Output had done its job correctly.

The problem was semantic.

This demonstrated an important distinction:

> **Structured Output guarantees structure, not business correctness.**

A valid JSON Schema does not guarantee that the values inside the structure correctly represent our business rules.

We still need:

- good Prompt rules;
- tests;
- deterministic validation;
- business logic;
- evaluations.

---

## 2.2 `missing_fields` Is a Derived Field

The `missing_fields` failure led to a more important design discovery.

We originally allowed the LLM to calculate:

```python
missing_fields
```

However, this field can be calculated deterministically from other parsed fields.

For example:

```python
if intent.origin is None:
    missing_fields.append("origin")

if intent.destination is None:
    missing_fields.append("destination")

if intent.departure_date is None:
    missing_fields.append("departure_date")

if (
    intent.trip_type == "round_trip"
    and intent.return_date is None
):
    missing_fields.append("return_date")
```

For the Chengdu example:

```text
origin = Toronto
destination = Chengdu
departure_date = None
return_date = None
trip_type = unknown
```

Python can deterministically calculate:

```python
["departure_date"]
```

There is no reason to ask the LLM to make the same business decision again.

Therefore, `FlightParser` now recalculates `missing_fields` after receiving the Structured Output.

This led to an important engineering principle:

> **If a value can be derived deterministically from already extracted data, prefer normal code instead of asking the LLM to reason about it.**

---

## 2.3 LLM and Python Should Do Different Types of Work

The `missing_fields` problem helped clarify the responsibility boundary.

### LLM is good at:

```text
Natural-language understanding
Semantic extraction
Ambiguous-language interpretation
Intent recognition
```

For example:

```text
"Two adults and one child"
        ↓
passengers = 3
```

### Python is good at:

```text
Deterministic rules
Validation
Calculation
State transitions
Business constraints
```

For example:

```text
trip_type == round_trip
AND
return_date is None

        ↓

missing_fields += ["return_date"]
```

Therefore:

```text
LLM → understand

Code → enforce
```

This separation can improve:

- predictability;
- testability;
- maintainability;
- reliability.

---

## 2.4 The Current `missing_fields` Design Still Has Duplication

Although `FlightParser` now recalculates `missing_fields`, the current `FlightIntent` still contains:

```python
missing_fields: list[str]
```

Therefore Structured Output still asks the LLM to generate this field.

Then Python immediately overwrites it:

```text
LLM generates missing_fields
          ↓
FlightParser receives it
          ↓
Python recalculates it
          ↓
Original LLM value is discarded
```

This is not ideal.

It means the current Structured Output model contains a field that is not actually trusted as LLM output.

Possible future designs include:

```text
LLMFlightIntent
      ↓
semantic extraction
      ↓
FlightIntent
      ↓
derived missing_fields
```

or making `missing_fields` a computed/derived property.

This should be revisited later when the domain model becomes more mature.

For Day 5, the current implementation is intentionally kept simple.

---

## 2.5 Generic Infrastructure Should Not Know Business Concepts

Initially, one possible method design was:

```python
generate_flight_intent(...)
```

However, this would make `OpenAIClient` depend on the Flight domain.

Later it could lead to:

```python
generate_flight_intent()
generate_kyc_intent()
generate_hotel_intent()
generate_test_case()
```

This would mix infrastructure and business responsibilities.

Instead, the generic method:

```python
generate_structured(
    ...,
    response_model: type[T],
) -> T
```

keeps the client domain-independent.

The architecture becomes:

```text
OpenAIClient
    ↓
Generic LLM Infrastructure

FlightParser
    ↓
Flight Domain

FlightIntent
    ↓
Flight Domain Model
```

This is a cleaner separation of concerns.

---

## 2.6 Exception Handling Is Intentionally Simple for Now

`FlightParser` currently catches broad exceptions and wraps them as:

```python
FlightParsingError
```

This is acceptable for the current learning stage, but we identified that it is too broad for a mature system.

In the future, different failures should probably be distinguished, such as:

```text
OpenAI API / Network Error
        ↓
LLMServiceError

Structured Parsing Error
        ↓
FlightParsingError

Business Validation Error
        ↓
FlightValidationError
```

They may also have different retry policies.

For example:

```text
Timeout
→ potentially retryable

Rate limit
→ potentially retryable

Invalid business input
→ not retryable; clarification may be required
```

We intentionally postponed this design because Day 5 is focused on Structured Output rather than production-grade error handling.

---

## 2.7 Real LLM Tests Consume Tokens, but Token Optimization Is Not the Current Priority

Now that integration tests call a real model, repeated testing consumes API tokens.

In a mature project, tests should eventually be separated into layers such as:

```text
Unit Tests
    ↓
No LLM calls

Mock/Fake LLM Tests
    ↓
No LLM calls

Real LLM Integration / Eval Tests
    ↓
Real API calls
```

However, token cost is currently not an optimization priority for this learning project.

Running real LLM tests is useful because it exposes:

- non-deterministic behavior;
- Prompt ambiguity;
- semantic errors;
- model interpretation differences.

The more important optimization discovered today is removing duplicated Prompt/Schema responsibilities because that is an engineering maintainability issue even when token cost is irrelevant.

---

## 2.8 AI Engineering Knowledge Requires Regular Freshness Reviews

The project currently uses OpenAI Python SDK 2.45.

A newer major SDK version exists, but the concepts currently being learned remain relevant:

```text
Responses API
Structured Output
Pydantic
JSON Schema
Typed model output
Prompt / Schema separation
```

Therefore, upgrading the SDK is not currently necessary just for the sake of using a newer version.

However, AI technology changes significantly faster than many traditional backend technologies.

This led to a new learning-plan principle:

> At the end of every learning stage, perform a Freshness Review.

The review should check:

- whether APIs used in the project are deprecated;
- whether SDK best practices have changed;
- whether newer recommended model patterns exist;
- whether Structured Output / Agent / RAG / Eval practices have changed;
- whether learning materials remain current;
- whether project implementations need updating;
- whether the learned capabilities still align with current North American AI Engineer job requirements.

Each item can be classified as:

```text
CURRENT
UPDATE RECOMMENDED
OBSOLETE
```

A broader Technology + Job Market Review should also be performed at the end of each month.

The six-month learning plan should therefore remain dynamic rather than being executed mechanically when the AI ecosystem changes.

---

# 3. Day 5 Architecture

After Day 5, the main architecture is:

```text
                 flight_parser_v1.md
                        │
                        ↓
User Query → FlightParser.parse()
                        │
                        ↓
             OpenAIClient.generate_structured()
                        │
                        ↓
               OpenAI Responses API
                        │
                        ↓
                Structured Output
                        │
                        ↓
                  FlightIntent
                        │
                        ↓
          Deterministic Business Logic
                        │
                        ↓
              Final FlightIntent
```

Responsibilities are becoming clearer:

```text
Prompt
→ semantic extraction rules

FlightIntent / Pydantic
→ structure and validation

OpenAIClient
→ generic OpenAI communication

FlightParser
→ flight-specific parsing workflow

Python business logic
→ deterministic derived values
```

---

# 4. Key Takeaways

The most important lessons from Day 5 are:

1. **Structured Output is stronger than asking the LLM to return JSON through Prompt instructions.**

2. **Structured Output guarantees structure, but it does not guarantee semantic or business correctness.**

3. **Prompt should primarily define semantic interpretation rules.**

4. **Pydantic should be the source of truth for output structure and constraints.**

5. **Deterministic business rules should be implemented in normal code rather than delegated to the LLM.**

6. **Derived fields such as `missing_fields` should ideally not require LLM reasoning.**

7. **Generic infrastructure such as `OpenAIClient` should remain independent of business domains.**

8. **Python generics (`TypeVar`, `type[T]`) allow reusable infrastructure without losing concrete return-type information.**

9. **AI application testing needs to verify semantic correctness in addition to Schema validity.**

10. **Prompt, Schema, LLM reasoning, validation, and deterministic business logic are different layers and should have clearly defined responsibilities.**

11. **AI engineering knowledge and dependencies need periodic freshness reviews because the ecosystem evolves quickly.**

---

# 5. Day 5 Result

Day 5 successfully moved the application from:

```text
LLM
 ↓
JSON String
 ↓
Manual Parsing
```

to:

```text
LLM
 ↓
Structured Output
 ↓
Typed Pydantic Object
 ↓
Deterministic Application Logic
```

The most important learning was not simply how to call `responses.parse()`.

The deeper lesson was understanding where the LLM should stop and where deterministic software engineering should begin:

> **Use the LLM for language understanding and probabilistic reasoning. Use schemas and normal code to constrain, validate, and enforce deterministic application behavior.**