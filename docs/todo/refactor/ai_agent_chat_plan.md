# AI Agent Chat — implementation plan

> ⚠ **Amended by [traceability_plan.md](traceability_plan.md)** once MCP tools stop being read-only:
> agent-initiated mutations are audited like any other caller (intent is declared at service level,
> so capture is automatic), but they need an action context and their intent rows must record that
> the actor was an **agent acting on behalf of a user**. In compliance mode, agent-initiated
> mutations are a likely candidate for either exclusion or mandatory human confirmation — to settle
> in this plan.

## Goal

Add an AI agent to the lab that the user chats with from the Angular front. The
agent acts on the lab by calling the lab's **existing MCP server** as tools
(read-only DB access today, more tools later). The LLM **provider is
configurable and switchable** (Anthropic / OpenAI / Gemini / local …) without
touching agent logic.

## What already exists (reused as-is, not rebuilt)

- **MCP server** — `src/gws_core/mcp/db_mcp.py` exposes `db_list` + `db_query`
  (read-only, guarded, capped) as MCP tools. Written explicitly for an AI agent.
- **MCP mount + OAuth** — `src/gws_core/mcp/mcp_controller.py` mounts it under
  `/mcp/` (Streamable HTTP) with a full OAuth flow (`LabOAuthProvider`, RFC
  8414/9728 discovery, DCR). The minted JWT is the token `JWTService` already
  validates → **"agent acts with the connected user's rights" is already solved**.
- **Controller pattern** — `ApiRegistry.register_api(path, ...)` (see
  `mcp_controller.py`, `apps/app_controller.py`).
- **Credentials store** — `credentials/` with typed `CredentialsData*`
  (`CredentialsDataOther` = arbitrary key/value) for storing provider API keys.
- **Deps** — `pydantic` and `openai` are already in `settings.json`.

So the "MCP surtout" capability layer is **done**. Only the agent, its HTTP
endpoint, and the Angular chat are new.

## Architecture

```
Angular front  ──POST /ai-agent/chat (SSE stream)──►  Agent backend (Pydantic AI)
  chat component                                          model = <provider:model>  (configurable)
                                                          toolset = MCPServerStreamableHTTP(/mcp/, Bearer <user JWT>)
                                                                        │
                                                                        ▼
                                                          Existing lab MCP server (db_mcp.py)
```

Key decision (confirmed): the agent consumes lab tools **through the HTTP+OAuth
MCP server**, as a normal MCP client — no in-process duplication of
`DbQueryService`. Any tool added to `db_mcp.py` is then usable by this agent
**and** by external MCP clients (Claude Desktop, Claude Code) for free.

## Provider ↔ MCP compatibility (why the switch is safe)

MCP does **not** depend on the LLM provider. Two independent layers:

- **Provider layer** — `model = 'openai:…' / 'anthropic:…' / 'mistral:…'`,
  interchangeable.
- **MCP layer** — `toolsets=[MCPServerStreamableHTTP(...)]`, identical for every
  provider.

Pydantic AI (server-side, on our host) is the MCP client. The LLM never speaks
MCP: Pydantic AI fetches the MCP tool list, **translates it into each provider's
native function-calling format** (OpenAI/Anthropic/Mistral all have `tools`),
executes the requested call over MCP, and feeds the result back. So MCP works
with **OpenAI, Claude, and Mistral** — the tools in `db_mcp.py` are written once
and run under any of them with no rewrite. Switching provider never breaks tool
access.

What *does* vary between providers is the **quality of tool use**, not the MCP
mechanics: picking the right tool, passing valid arguments (e.g. correct
read-only SQL for `db_query`), chaining calls and self-correcting on errors.

| Provider | MCP works | Agentic / tool-calling quality |
|---|---|---|
| **Claude** (recent Opus/Sonnet) | yes | Excellent — best at chaining tools + self-correcting |
| **OpenAI** (GPT-4o / recent) | yes | Very good |
| **Mistral** (Large / recent) | yes | Good; weaker on complex multi-tool chains |

Requirements / caveats:
- The chosen model **must support function/tool calling**. Small/old/pre-tool
  models may do it poorly or not at all — this is the one case where a switch
  can fail *in practice* (MCP is fine; the model just can't drive the tools).
- Argument-format quirks per provider (strict JSON, etc.) are absorbed by
  Pydantic AI.

**Design implication:** keep the provider configurable (as planned), but default
to **Claude** for agentic quality, with OpenAI and Mistral as selectable
alternatives. `list_available_providers()` should only offer tool-calling-capable
models.

## New components

### 1. Provider config + credentials — `src/gws_core/impl/ai_agent/ai_agent_config.py`
- A small `AiAgentConfig` resolving `(provider, model, api_key)`.
- `provider:model` string drives Pydantic AI's model selection (its native
  switch mechanism). Default read from env/settings; overridable per request.
- API keys resolved from the **credentials store** (`CredentialsDataOther`),
  falling back to env (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, …) to match how
  `Settings.get_open_ai_api_key()` works today.
- `list_available_providers()` → drives a front dropdown.

### 2. Agent backend — `src/gws_core/impl/ai_agent/ai_agent_service.py`
- Builds a Pydantic AI `Agent(model, toolsets=[mcp_server], system_prompt=...)`.
- `mcp_server = MCPServerStreamableHTTP(url=<lab>/mcp/, headers={Authorization:
  Bearer <user JWT>})` — the user's own JWT, so tool calls run with the user's
  rights. The MCP server URL comes from `Settings.get_lab_api_url()` + `/mcp/`
  (same helper `mcp_controller._get_mcp_url()` already builds).
- System prompt: what the lab is, that DB access is read-only, to prefer MCP
  tools, to self-correct on tool errors (the MCP tools already return
  agent-readable errors).
- `run_stream(message, history, provider, model)` → async generator yielding
  text deltas **and** tool-call events (name / args / result) for the UI.

### 3. REST controller — `src/gws_core/impl/ai_agent/ai_agent_controller.py`
- `ApiRegistry.register_api("/ai-agent/")` — same pattern as `mcp_controller`.
  Keep `with_security_headers=True` (unlike `/mcp/`, this **is** called from the
  Angular page).
- `POST /ai-agent/chat` — standard lab auth (connected user); streams the
  agent output as **SSE**. The user's JWT is forwarded to the MCP client.
- `GET /ai-agent/providers` — returns configured providers/models for the front.
- Register it where `mount_mcp_app` / brick controllers are wired at startup.

### 4. Angular chat component (lab front repo — separate)
- Chat panel: input + message list.
- Consumes the SSE stream: render streaming tokens, and one **tool-call card**
  per MCP tool invocation (name + args + result) so the agent's actions are
  visible and auditable.
- Provider/model selector fed by `GET /ai-agent/providers`.
- Talks to `/ai-agent/chat` with the session's auth (localhost:4200 in dev).

## Dependencies to add (`settings.json` pip section)
- `pydantic-ai` (agent loop + MCP client + provider switch).
- Provider SDKs as needed — `anthropic` (OpenAI already present). `pydantic-ai`
  can pull provider extras; pin explicitly to match the brick convention.

## Security
- **Read before write.** Today the only tools are read-only (`db_*`). When write
  tools are added to the MCP server, gate them behind explicit UI confirmation.
- **User rights.** Agent uses the connected user's JWT for MCP calls — no root,
  no shared service identity.
- **Prompt injection.** DB rows / future resources may carry adversarial text;
  keep human confirmation on any future write/outbound tool. The finite MCP tool
  set (vs. a raw shell) is itself the main mitigation.
- **Keys.** Provider API keys from the credentials store, never hardcoded, never
  sent to the front.

## Build sequence
1. Add deps to `settings.json`; `pydantic-ai` + `anthropic` importable.
2. `ai_agent_config.py` — provider/model/key resolution + `list_available_providers`.
3. `ai_agent_service.py` — build agent, wire MCP-over-HTTP client with user JWT,
   `run_stream`. **Test in CLI / a test first** (no front needed) — confirms the
   agent reaches the real `/mcp/` and answers a DB question end to end.
4. `ai_agent_controller.py` — SSE `/ai-agent/chat` + `/ai-agent/providers`; wire
   at startup.
5. Angular chat component (front repo) against the endpoints.
6. `ruff check --fix` on changed files; add a test under `tests/test_gws_core/`.

## Related: RAG + Datasets/Chats management (gws_ai_toolkit)
The RAG knowledge layer and the Datasets/Chats management product live in
`gws_ai_toolkit` — see `gws_ai_toolkit/docs/todo/rag_migration_ragflow_to_llamaindex_plan.md`.
Consequences for this plan:
- **Conversation persistence is owned there** (Chat + ChatMessage in DB), so the
  agent here is the stateless *engine* called by that brick's Chat service, which
  supplies history and the retrieval scope (bound datasets → metadata filter).
- Retrieval is exposed to this agent as a **tool** (RAG search), alongside the MCP
  tools.

## Open questions
- Which providers to enable at launch (drives which SDK deps to pin).
- Streaming contract detail (SSE event shapes for text-delta vs tool-call vs done).

## UI ownership (decided)
The RAG config app **and** the chat product are **Reflex**, in gws_ai_toolkit. A
separate Angular chat may come later but is handled externally — **out of scope**.
The gws_core agent stays a UI-agnostic engine (SSE endpoint) that the Reflex Chat
service calls.
