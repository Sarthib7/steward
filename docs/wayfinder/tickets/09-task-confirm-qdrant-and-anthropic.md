# Task: confirm Qdrant Cloud cluster and Anthropic key

- Status: closed
- Labels: `wayfinder:task`
- Assignee: sarthib7
- Parent: [Steward HackNight design and plan](../maps/01-steward-hacknight-design-and-plan.md)
- Blocked-by: (none)

## Question

Confirm the operator has, for Monday, a Qdrant Cloud cluster (`VECTOR_DB_URL` + `VECTOR_DB_KEY`) and an Anthropic API key for Cognee's LLM. Record where those secrets live (path or password manager), not the secret values. Record whether local fastembed (`BAAI/bge-small-en-v1.5`) is acceptable on the demo machine.

This unblocks plan realism (the stack in Notes). It does not implement Steward.

HITL checklist for the operator. Do not read `.env` into chat.

## Comments

### Resolution (2026-08-14)

Operator confirmed **Qdrant Cloud** is available and an **OpenRouter API key** (not Anthropic). LLM provider for the Cognee path on this effort is OpenRouter. Vectors live on Qdrant Cloud.

Correction: the ticket asked for an Anthropic key. That language was wrong. Do not plan Anthropic as the Cognee LLM for this effort.

Not determined in this confirmation: where the secrets live (path or password manager), and whether local fastembed (`BAAI/bge-small-en-v1.5`) is acceptable on the demo machine.
