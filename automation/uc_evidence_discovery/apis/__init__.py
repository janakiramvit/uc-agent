"""Public-API clients. Every request goes through :class:`.http.Http`, which enforces the
host allowlist, timeouts, bounded retries with exponential backoff, per-host rate limiting
and a response-size ceiling. No Reddit, no paywalled/login hosts, no paid model or research
APIs, no OpenAI / Anthropic.
"""
