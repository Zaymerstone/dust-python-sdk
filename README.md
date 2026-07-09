# dust-sdk (unofficial)

An unofficial Python client for the [Dust](https://dust.tt) API.

Dust ships an official [JavaScript/TypeScript SDK](https://docs.dust.tt/reference/javascript-sdk),
but has no official Python client - despite Python being the dominant
language for the data science, ML engineering, and automation teams
that make up a large part of Dust's target audience (their own
marketing highlights Data & Analytics as a core use case).

This project closes that gap.

## Installation

```bash
pip install dust-sdk
```

_(not yet published to PyPI — see [Status](#status) below)_

## Quickstart

```python
from dust_sdk.client import DustClient

client = DustClient(
    api_key="your-dust-api-key",
    workspace_id="your-workspace-id",
    base_url="https://eu.dust.tt",  # or https://dust.tt — see note below
)

# List agents available in your workspace
agents = client.list_agents()
for agent in agents:
    print(agent["sId"], "-", agent["name"])

# Talk to an agent
conversation = client.create_conversation(
    message_content="What can you help me with?",
    agent_sid="dust",
)
answer = client.get_last_agent_message_text(conversation)
print(answer)
```

### ⚠️ `base_url` is required, no default

Dust hosts separate regional infrastructure (`https://dust.tt` for US,
`https://eu.dust.tt` for EU). Using the wrong one doesn't 404 — it
returns a misleading `invalid_api_key_error`, making it look like your
key is wrong when it's actually a region mismatch. Check which region
your workspace lives in (visible in your workspace URL) before making
your first call.

## What's implemented

| Method                            | Operation             | Verified against         |
| --------------------------------- | --------------------- | ------------------------ |
| `list_agents()`                   | GET agent list        | ✅ Live API call         |
| `get_agent(sid)`                  | GET single agent      | ✅ Live API call         |
| `list_spaces()`                   | GET spaces            | ✅ Live API call         |
| `list_data_sources(space_id)`     | GET data sources      | ✅ Live API call         |
| `list_documents(space_id, ds_id)` | GET documents         | 📄 Official OpenAPI spec |
| `get_tables(space_id, ds_id)`     | GET tables            | 📄 Official OpenAPI spec |
| `create_conversation(...)`        | POST new conversation | ✅ Live API call         |
| `get_conversation(cid)`           | GET conversation      | ✅ Live API call         |
| `import_agent(...)`               | POST create agent     | ✅ Live API call         |
| `archive_agent(sid)`              | DELETE (soft) agent   | ✅ Live API call         |

_"Live API call" means the response schema was confirmed against a
real request during development, not just documentation. "Official
OpenAPI spec" means it's based on Dust's published spec but hasn't
been round-tripped against a live response yet (usually because
testing it live requires resources — like a connected data source —
that weren't available in the development workspace)._

## Known limitations

- **Message-sending is gated on Dust's Free plan.** Any endpoint that
  invokes a model (`create_conversation` with an agent mention) returns
  `429 rate_limit_error` on workspaces without a paid seat —
  `Programmatic usage` is entirely disabled (`No access`) on Free,
  independent of the regular in-app usage credits shown in the UI.
  Write operations that _don't_ invoke a model (`import_agent`,
  `archive_agent`) work fine on Free.
- **Some `Private` API endpoints aren't accessible via API key at all**,
  regardless of plan — e.g. `POST /spaces` (creating a space) returns
  `401 not_authenticated` even with a valid Bearer token, because it's
  a session-only, web-app-internal endpoint despite appearing in the
  public API reference.
- **The documentation contains at least one broken example URL.**
  `GET /spaces` is shown at `https://dust.tt/api/w/{wId}/spaces`
  (missing `/v1/`) — using that exact path returns a misleading
  `401 not_authenticated` instead of a 404, making it look like an
  auth problem. The correct path is `/api/v1/w/{wId}/spaces`.
- **Response shapes aren't consistent across endpoints.** Most list
  endpoints wrap results in an object (e.g. `{"data_sources": [...]}`),
  but `GET .../tables` returns a bare JSON array. This SDK normalizes
  both into consistent Python return types, but it's worth knowing if
  you're calling the raw API directly.
- **Dust's official OpenAPI spec has several inaccuracies**, found
  through live testing:
  - `agent.avatar_url` is required in practice, marked optional in the spec
  - `editors` must be an array of email strings, not objects as the spec shows
  - `generation_settings.reasoning_effort` is required but easy to miss
  - Message `type` example values in the spec show `"human"`, but the
    real API returns `"user_message"` / `"agent_message"`

## Development

```bash
git clone https://github.com/Zaymerstone/dust-python-sdk.git
cd dust-python-sdk
python -m venv venv
venv\Scripts\Activate.ps1   # Windows
pip install -e .
pip install pytest requests-mock
pytest -v
```

Tests run entirely against recorded fixtures (`tests/fixtures/`) —
no live API calls or credits are required to run the test suite.

## Status

This is an early-stage, unofficial project built to explore a gap in
Dust's SDK coverage. 10 methods are implemented and tested; the full
Dust API surface is 40+ endpoints. Contributions and feedback welcome.

## License

MIT
