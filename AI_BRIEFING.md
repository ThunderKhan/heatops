# Evidence-grounded AI briefing

The language model is a narrator, not a decision-maker.

## Trust boundary

The deterministic pipeline calculates risk, runs maximum coverage, and constructs an evidence bundle containing only optimizer outputs. The bundle is canonically serialized and SHA-256 fingerprinted. Groq receives that bundle with an instruction to use no outside facts, and its JSON response is validated before display.

If Groq is unconfigured, rate-limited, unavailable, or returns invalid output, HeatOps generates the same action-brief schema with a deterministic template. Resource locations never change because of narration.

## Optional Groq configuration

Create a Groq key and add it only to `.env`:

```dotenv
GROQ_API_KEY=replace-locally
HEATOPS_GROQ_MODEL=qwen/qwen3.6-27b
```

The dashboard labels Groq output as `Groq-grounded AI` and fallback output as `Verified template`. Both include the evidence fingerprint and can be downloaded as Markdown.

## Claims policy

- Never claim illnesses or deaths prevented.
- Never invent site feasibility, accessibility, staffing, supplies, or weather.
- Describe coverage as modeled risk coverage.
- Preserve synthetic and mixed-provenance disclosures.
- Require human verification before operational deployment.
