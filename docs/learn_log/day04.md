# Day 04 — Flight Intent Parsing Prompt v1

## What Did I Do?

Today I created the first version of the Flight Intent Parsing Prompt.

The purpose of the prompt is to convert a user's natural-language flight request into structured data that follows the `FlightIntent` model.

I also created five test cases and used the real OpenAI API through `OpenAIClient.generate_text()` to verify the prompt behavior.

The test flow is:

```text
Test Case
    ↓
User Prompt
    ↓
OpenAIClient.generate_text()
    ↓
Flight Parser Prompt
    ↓
LLM Response
    ↓
JSON Parsing
    ↓
Expected Field Assertions
```

All five test cases eventually passed consistently.

---

# What I Learned

## 1. A Prompt Is an Application Contract

Before this exercise, it was easy to think of a prompt mainly as instructions given to an LLM.

After implementing and testing the Flight Parser prompt, I learned that a production prompt is closer to an **application contract**.

It defines how:

```text
Natural Language
        ↓
      Prompt
        ↓
Structured Application Data
```

should behave.

For every important output field, the prompt should clearly define:

* what information should be extracted;
* what values are allowed;
* what should happen when information is missing;
* what can be inferred;
* what must not be inferred;
* what the fallback value should be.

The clearer these rules are, the more predictable the LLM output becomes.

---

## 2. Prompt Rules Need to Be Precise

Natural language is inherently ambiguous.

A rule that appears clear to a human may still allow multiple reasonable interpretations by an LLM.

For example:

> I want to fly from Toronto to Chengdu around Christmas for three weeks.

Initially, I expected:

```json
{
  "trip_type": "round_trip"
}
```

because traveling "for three weeks" seems to imply that the traveler will return.

However, the model returned:

```json
{
  "trip_type": "unknown"
}
```

After reviewing the result, I realized that the model's answer was actually more conservative and consistent with another important rule:

> Do not invent information.

The user never explicitly said:

* round trip;
* return;
* come back;
* return to Toronto.

Therefore, inferring `round_trip` only from "for three weeks" introduces an assumption.

This led to a clearer rule:

```text
Use round_trip only when the user explicitly indicates a return trip,
provides a return date, or clearly expresses an intention to return.

Do not infer round_trip only from a travel duration.

Otherwise, use unknown.
```

This makes the expected behavior more deterministic.

---

## 3. Field Semantics Must Be Clearly Defined

Another issue appeared with:

```text
flexible_dates
```

For the query:

> I want to travel next month.

the model initially returned:

```json
{
  "flexible_dates": false
}
```

The model may have interpreted `flexible_dates` as:

> Did the user explicitly say that their dates are flexible?

But the intended application meaning was broader:

> Did the user provide a time window or approximate date rather than one specific calendar date?

Under this definition:

```text
next month              → true
around Christmas        → true
sometime in August      → true
any weekend next month  → true
September 15, 2026      → false
no date information     → false
```

This showed that choosing a field name is not enough.

The **semantic meaning of the field must also be explicitly defined** in the prompt.

---

## 4. Missing Data Is Different From Required Clarification

The tests also exposed an important question about:

```text
missing_fields
```

Consider again:

> I want to fly from Toronto to Chengdu around Christmas for three weeks.

The result contained:

```json
{
  "trip_type": "unknown",
  "departure_date": null,
  "return_date": null,
  "missing_fields": [
    "departure_date"
  ]
}
```

At first, it seemed reasonable to ask why `return_date` and `trip_type` were not also included.

This revealed that `missing_fields` can have two different meanings.

### Meaning A — Every field not provided by the user

Under this definition, many fields could be considered missing:

```text
departure_date
return_date
trip_type
cabin_class
...
```

### Meaning B — Information currently required to continue the business process

Under this definition, only fields that block the next step should be included.

The current implementation follows **Meaning B**.

For example, `return_date` should become required only after the system knows that:

```text
trip_type = round_trip
```

This also suggests that the name `missing_fields` may not be ideal in the long term.

A future model might use a clearer concept such as:

```text
required_clarifications
```

This should be revisited when clarification and conversation-state logic are implemented.

---

## 5. Do Not Over-Infer User Intent

One of the most important lessons from today's tests is:

> Extract what the user means, but do not silently complete missing business information.

For example:

```text
"I am traveling for three weeks."
```

does not necessarily mean:

```text
round_trip
```

and:

```text
"I want to travel."
```

does not mean:

```text
origin = Toronto
```

even if the application knows that the user lives in Toronto.

A parser should remain conservative.

A useful principle is:

> Extract, don't guess.

When important information cannot be determined reliably, representing it as `unknown` or `null` is safer than inventing a value.

---

## 6. Prompt Development Requires Testing and Iteration

This was the most important lesson from Day 4.

It is unrealistic to expect a production-quality prompt to be perfectly defined on the first attempt.

Human language is complex.

Even when a prompt appears clear, actual test cases can expose:

* ambiguous rules;
* conflicting rules;
* unclear field semantics;
* unexpected model interpretations;
* assumptions that were not explicitly defined.

The development process therefore looks more like:

```text
Define Prompt
     ↓
Create Test Cases
     ↓
Run Against LLM
     ↓
Compare Actual vs Expected
     ↓
Analyze Differences
     ↓
Clarify Prompt Rules
     ↓
Run Tests Again
```

This is very similar to normal software engineering:

```text
Requirement
    ↓
Implementation
    ↓
Testing
    ↓
Bug / Ambiguity
    ↓
Refinement
```

The difference is that the implementation being controlled is partly based on natural language and probabilistic model behavior.

Therefore:

> Prompt Engineering is not just writing good instructions. It is an iterative engineering process involving specification, testing, evaluation, and refinement.

---

## 7. Test Expected Behavior, Not Exact LLM Output

Because an LLM is not completely deterministic, testing the entire response with exact equality is often inappropriate.

For example:

```json
{
  "confidence": 0.87
}
```

and:

```json
{
  "confidence": 0.91
}
```

may both be valid.

Instead, the tests should focus on important deterministic business fields:

```python
assert result["origin"] == "Toronto"
assert result["destination"] == "Chengdu"
assert result["trip_type"] == "unknown"
assert result["passengers"] == 3
```

For non-deterministic values, validate constraints instead:

```python
assert 0 <= result["confidence"] <= 1
```

This is an important difference between testing traditional deterministic software and testing AI systems.

---

# Testing Strategy

For Day 4, I decided to test the prompt directly through:

```python
OpenAIClient.generate_text()
```

instead of testing through `main()`.

This keeps the test focused on the component being evaluated:

```text
Prompt + LLM
```

rather than:

```text
CLI + main() + Prompt + LLM
```

The tests use different user prompts as test data and verify the important fields returned by the model.

This makes the tests simple, readable, and directly related to the purpose of Day 4.

---

# Key Design Principles Learned

### Prompt Contract

A production prompt defines a contract between natural-language input and structured application data.

### Explicit Rules

Important fields should have explicit extraction, fallback, and inference rules.

### Extract, Don't Guess

The LLM should not invent missing business information.

### Clear Field Semantics

Field names alone are not enough. Their exact application meaning must be defined.

### Separation of Responsibilities

The Flight Parser extracts user intent.

It does not:

* search for flights;
* estimate flight prices;
* recommend airlines;
* make purchase decisions;
* execute business logic.

### Test and Iterate

A prompt should not be expected to work perfectly after the first version.

Real test cases are necessary to expose ambiguity and refine the specification.

### Test Semantics, Not Exact Text

AI tests should verify important semantic behavior and constraints instead of requiring every generated value to be identical.

---

# Day 4 Result

Five representative flight-intent test cases were implemented and tested against the real OpenAI API.

After refining ambiguous prompt rules, all five cases passed consistently.

The most valuable outcome of Day 4 was not simply producing a working prompt.

It was understanding that:

> **Prompt design is specification engineering for a probabilistic system.**

A good prompt becomes reliable through clear definitions, representative test cases, observed failures, and continuous refinement.

---

# Next Step

Day 5 will introduce the `FlightParser` service.

The goal will be to move from:

```text
User Query
    ↓
OpenAIClient.generate_text()
    ↓
JSON String
```

toward:

```text
User Query
    ↓
FlightParser
    ↓
OpenAI Structured Output
    ↓
Pydantic Validation
    ↓
FlightIntent
```

This will start connecting the Prompt developed today with the structured data model created on Day 3.
