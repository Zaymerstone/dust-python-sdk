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
pip install conversational-agent-client
```

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

21 methods, covering agents, spaces, data sources, apps, skills,
conversations, feedback, and analytics.

| Method                                | Operation             | Verified against                    |
| ------------------------------------- | --------------------- | ----------------------------------- |
| `list_agents()`                       | GET agent list        | ✅ Live API call                    |
| `get_agent(sid)`                      | GET single agent      | ✅ Live API call                    |
| `search_agents_by_name(query)`        | GET agent search      | ✅ Live API call ⚠️ see limitations |
| `export_agent_as_yaml(sid)`           | GET agent as YAML     | ✅ Live API call                    |
| `import_agent(...)`                   | POST create agent     | ✅ Live API call                    |
| `update_agent_configuration(...)`     | PATCH update agent    | 📄 Official docs ⚠️ admin-only      |
| `archive_agent(sid)`                  | DELETE (soft) agent   | ✅ Live API call                    |
| `list_spaces()`                       | GET spaces            | ✅ Live API call                    |
| `list_data_sources(space_id)`         | GET data sources      | ✅ Live API call                    |
| `list_documents(space_id, ds_id)`     | GET documents         | 📄 Official docs                    |
| `get_tables(space_id, ds_id)`         | GET tables            | ✅ Live API call                    |
| `search_data_source(...)`             | GET semantic search   | 📄 Official docs                    |
| `list_apps(space_id)`                 | GET apps in space     | ✅ Live API call                    |
| `create_app_run(...)`                 | POST run a Dust App   | 📄 Official docs                    |
| `list_skills()`                       | GET custom skills     | ✅ Live API call                    |
| `list_data_source_views(space_id)`    | GET data source views | ✅ Live API call                    |
| `create_conversation(...)`            | POST new conversation | ✅ Live API call                    |
| `get_conversation(cid)`               | GET conversation      | ✅ Live API call                    |
| `get_feedbacks_for_conversation(cid)` | GET feedback entries  | 📄 Official docs ⚠️ see limitations |
| `parse_mentions_in_markdown(text)`    | POST parse @mentions  | ✅ Live API call                    |
| `export_workspace_analytics(...)`     | GET analytics export  | 📄 Official docs ⚠️ admin-only      |

_"Live API call" means the response schema was confirmed against a
real request during development. "Official docs" means it's based on
Dust's published documentation but hasn't been round-tripped against
a live response, usually because that requires resources (an admin
role, a configured Dust App, a connected data source) that weren't
available in the development workspace._

## Known limitations

### Access restrictions (found through live testing, undocumented)

Four distinct categories of API restriction were found while building
this SDK:

1. **Programmatic credit gating.** Endpoints that invoke a model
   (`create_conversation` with an agent mention) return
   `429 rate_limit_error` on workspaces without programmatic credits —
   a separate pool from the regular in-app usage credits shown in the
   UI, disabled entirely on the Free plan regardless of plan tier.
2. **Public vs. private endpoints.** Some documented endpoints are
   session-only and return a misleading `401 not_authenticated` even
   with a valid API key, because they're internal to the web app
   rather than part of the public API.
3. **Role-based access** (confirmed on two separate endpoints:
   `update_agent_configuration` and `export_workspace_analytics`).
   These return `403 workspace_auth_error` ("Only admin users can
   perform this action") for "builder"-role accounts, even on
   harmless actions with no model invocation. Not mentioned in the
   official docs.
4. **User-session-only auth.** `get_feedbacks_for_conversation`
   returns `401 user_authentication_required` with a valid API key —
   a different error from the usual invalid-key response, suggesting
   the endpoint may not accept Bearer API key auth at all despite
   being documented that way.

### Known bugs in `search_agents_by_name`

- Global/system agents (e.g. `dust`, `helper`) are never returned by
  this endpoint, regardless of query — confirmed with exact
  first-letter matches that work for custom agents but not global
  ones.
- Matching behavior is inconsistent: a single-character query can
  match an agent's name correctly, but the agent's exact full name as
  the query returns zero results.

### Documentation inaccuracies found

- `GET /spaces` is shown at `/api/w/{wId}/spaces` (missing `/v1/`) on
  one reference page — using that exact path returns a misleading
  `401` instead of a 404. The correct path is `/api/v1/w/{wId}/spaces`.
- `agent.avatar_url` is required in practice for `import_agent`,
  marked optional in the spec.
- `editors` must be an array of email strings, not objects as shown
  in the import-agent spec.
- `generation_settings.reasoning_effort` is required but easy to miss.
- Response shapes aren't fully consistent across endpoints — most
  list endpoints wrap results in an object (e.g.
  `{"data_sources": [...]}`), while a few return bare arrays. This
  SDK normalizes both into consistent Python return types.

Several of these findings were reported to Dust directly; some
(like the `tables` response shape) have already been fixed
server-side and confirmed by their engineering team.

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

21 methods implemented and tested, covering agents, spaces, data
sources, apps, skills, conversations, feedback, and analytics. The
full Dust API surface is larger than this; some endpoints remain
out of reach due to the access restrictions noted above. Contributions
and feedback welcome.

## License

MIT
