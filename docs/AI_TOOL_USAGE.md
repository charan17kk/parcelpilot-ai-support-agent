# AI Tool Usage

Codex was used as the implementation assistant for repository scaffolding, architecture translation, source-pack inspection, backend/frontend development, Docker and deployment troubleshooting, and verification. The implementation was checked with Python compilation, TypeScript type checking, deterministic unit tests, live API calls, database-backed access-control checks, ingestion/retrieval checks, production Docker builds, and hosted end-to-end smoke tests.

The application itself uses free OpenRouter-hosted models for natural-language interpretation and explanation. It prefers Liquid LFM2.5, falls back to inclusionAI Ling and OpenRouter's free tool-capable router, and deterministically routes obvious ID-based requests to the relevant safe tool. Local FastEmbed embeddings support document retrieval. AI is not used for authentication, authorisation, deterministic policy calculations, source precedence, or action execution.

No LangSmith tracing or paid observability platform is used.
