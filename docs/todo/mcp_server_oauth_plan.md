# Remote MCP server with Constellab OAuth authentication

## Goal

Expose the `gws` CLI functionality as an **MCP server** hosted by the lab, consumable from a
**local Claude Code** over the network, authenticated with the user's **Constellab credentials**
(the same identity used by the lab).

**v1 scope**: only the `gws db` commands (`query`, `list`) are exposed, as a proving ground for
the transport + auth. Other CLI groups (`resource`, `scenario`, `community`) follow the same
pattern once v1 is validated.

## Why this is not just "port rag_mcp.py to HTTP"

The existing MCP servers (`gws_cli/mcp/rag_mcp.py`, `mcp/rich_text_mcp.py`) run
`mcp.run(transport="stdio")` as a **local, already-authenticated lab process**. They call
`DbQueryService` / `CommunityService` directly with no auth because the process *is* the user.

A remote MCP breaks both assumptions:

1. **Transport**: stdio only works for a subprocess on the same machine. A remote server needs
   `streamable-http`.
2. **Identity**: every request now arrives from an untrusted network and must carry proof of who
   the caller is, then run as that user.

> **Superseded (identity step).** The flow below originally used the Constellab
> `/cli-auth` device flow for identity, which redirected the user to
> `constellab.community`. It now authorizes **entirely within the lab**: `/authorize`
> redirects to a lab front-end consent page, which proves identity with a
> single-use `UniqueCodeService` code. No Space, no Community, no password. See
> "Consent flow" below and `mcp_consent_frontend_spec.md`. Everything about the
> token model (the lab mints its own JWT) is unchanged, and is *why* this works.

## Key architectural fact (drove the auth design)

The lab **already is** an OAuth-style resource server:

- `JWTService.create_jwt(user_id)` signs a token with the **lab's own** `secret_key`
  (`src/gws_core/user/jwt_service.py`).
- Every lab route validates it via `Depends(AuthorizationService.check_user_access_token)`, which
  reads `Authorization` from header or cookie and resolves it to an `AuthContextUser`
  (`src/gws_core/user/authorization_service.py:248-267`).

Crucially: **the community backend's token is NOT a lab JWT.** `gws community login`
(`gws_cli/utils/community_cli_service.py`) obtains a token from `/cli-auth/token` on
`api.constellab.community` and uses it only against the community API. `JWTService._decode` would
reject it (different issuer/secret).

Since the `db_query` tool runs **inside the lab** against the lab DB, it needs a **lab JWT**.
Therefore the lab must mint the MCP's token itself. The community `/cli-auth` flow is reused for
the **identity** step (browser login proving who you are); the lab mints the resource token.

This is the standard OAuth shape: *the resource server's authorization server issues
resource-scoped tokens.* We implement that authorization server **inside gws_core**, backed by the
existing `/cli-auth` device flow.

## Architecture

```
LOCAL (developer machine)               REMOTE (lab server, `gws server run`)
┌────────────────┐                      ┌───────────────────────────────────────┐
│  Claude Code   │  1. connect          │  gws_core FastAPI app                 │
│  .mcp.json     │─────────────────────▶│  /mcp/   FastMCP streamable-http      │
│                │  401 + WWW-Auth      │          tools: db_query, db_list     │
│                │◀─────────────────────│                                       │
│                │  2. discovery        │  /.well-known/oauth-protected-resource│
│                │─────────────────────▶│  /.well-known/oauth-authorization-... │
│                │                      │                                       │
│                │  3. browser login    │  /mcp-auth/authorize  ──▶ /cli-auth   │
│  opens browser │─────────────────────▶│      (Constellab identity)            │
│                │  4. token            │  /mcp-auth/token  ──▶ JWTService       │
│  stores +      │◀─────────────────────│      .create_jwt(user_id)  [LAB JWT]  │
│  auto-refresh  │                      │                                       │
│                │  5. tool calls       │  LabJwtTokenVerifier                  │
│                │────Bearer lab JWT───▶│   → AuthorizationService              │
│                │                      │       .authenticate_from_token()      │
│                │                      │   → DbQueryService (runs as the user) │
└────────────────┘                      └───────────────────────────────────────┘
```

## Implementation steps

### 1. Dependency

Add `mcp` (Python SDK, version with OAuth `TokenVerifier` + `streamable_http_app` support) to the
pip packages in `gws_core/settings.json`. It is currently **not** a gws_core dependency — only the
CLI's env has it.

### 2. `db_mcp.py` — the tool layer

New file, `src/gws_core/mcp/db_mcp.py` (moves into the brick src, not `gws_cli`, because it is now
served by the lab app rather than run as a CLI subprocess).

- `FastMCP("gws-lab", ...)` with instructions mirroring the `gws db` help text.
- `db_list()` → `DbQueryService.list_db_names()`
- `db_query(sql, db="gws_core", limit=20)` → `DbQueryService.assert_read_only(sql)` then
  `DbQueryService.execute_read_only_query(db, sql)`, returning the JSON shape already produced by
  `db_cli._print_json` (columns / row_count / truncated / rows).
- Reuse `DbQueryError` handling: return the actionable message as tool output so the agent
  self-corrects (same rationale as the CLI's docstring).
- **No `mcp.run(...)` call** at import time (unlike the stdio servers) — the app is mounted.

### 3. `LabJwtTokenVerifier` — the auth bridge

New file, `src/gws_core/mcp/mcp_token_verifier.py`.

Implements the MCP SDK's `TokenVerifier` protocol. Body is essentially:

- take the bearer token from the request,
- `AuthorizationService.authenticate_from_token(token)` → `AuthContextUser`
  (this both validates the JWT *and* sets the current user in the context, exactly as HTTP routes
  do),
- return the verified token/identity to the MCP layer; raise → 401.

This is why the tools need no auth code of their own: by the time `db_query` runs,
`CurrentUserService` already resolves to the calling user.

### 4. Mount the MCP app

In the module that registers lab APIs (alongside the other `ApiRegistry` calls):

```python
mcp_api = ApiRegistry.register_api("/mcp/", with_security_headers=False)
mcp_api.mount("/", mcp.streamable_http_app())
```

- `with_security_headers=False`: machine-to-machine API, no browser renders it (the flag is
  documented for exactly this case in `api_registry.py`).
- Served by the existing `gws server run` process → reuses the lab's TLS, domain and JWT secret.
- Consider `silent_access_log=True` if MCP polling proves chatty.

### 5. OAuth: implement the provider, let the SDK serve the endpoints

**Revised after inspecting mcp 1.28.1** — the SDK does much more than originally assumed. We do
**not** hand-write the OAuth endpoints. `FastMCP.streamable_http_app()` calls
`create_auth_routes(...)` which generates the full surface from a single provider object:

| Endpoint | Who writes it |
|---|---|
| `/.well-known/oauth-authorization-server` | **SDK** (from `AuthSettings`) |
| `/.well-known/oauth-protected-resource` | **SDK** (from `auth.resource_server_url`) |
| `POST /register` (DCR) | **SDK** (gated by `ClientRegistrationOptions`) |
| `GET /authorize`, `POST /token` | **SDK** handlers |
| `401` + `WWW-Authenticate: ... resource_metadata=...` | **SDK** (`RequireAuthMiddleware`) |
| **PKCE verification** (S256 challenge/verifier) | **SDK** (`TokenHandler`) |
| redirect_uri match validation | **SDK** (`TokenHandler`) |

What **we** implement is `ConstellabOAuthProvider(OAuthAuthorizationServerProvider)` in
`src/gws_core/mcp/mcp_oauth_provider.py`, i.e. the Constellab-specific bridge:

- `register_client` / `get_client` — store DCR clients (in-memory for v1).
- `authorize(client, params)` → return the Constellab login URL (drives `/cli-auth/code`),
  stashing `params` (state, PKCE `code_challenge`, `redirect_uri`) against the device code. This is
  exactly the SDK's documented **"3rd Party OAuth"** shape: Claude ↔ lab ↔ Constellab.
- A **callback route** completing the 3rd-party leg: poll/receive the Constellab token, resolve the
  Constellab identity → lab `User` (via `UserService.get_user_by_email`), mint an
  `AuthorizationCode`, redirect back to Claude's `redirect_uri`.
- `load_authorization_code` / `exchange_authorization_code` → mint the **lab JWT** with
  `JWTService.create_jwt(user_id)` and return it as the OAuth access token.
- `load_refresh_token` / `exchange_refresh_token` → refresh handling (see open questions).

Set `subject=<lab user id>` on `AuthorizationCode`/`AccessToken` so the identity propagates.

`AuthSettings` wiring:

```python
AuthSettings(
    issuer_url=<lab url>/mcp,          # the lab is its own authorization server
    resource_server_url=<lab url>/mcp, # and the resource server
    client_registration_options=ClientRegistrationOptions(enabled=True),
)
```

**Identity mapping**: the `/cli-auth` flow proves the Constellab identity; map that to the lab
`User` (the existing `AuthenticationService.get_and_refresh_user_from_space` /
`UserService.get_user_by_email` path) before minting the lab JWT. A Constellab user with no active
lab account must be rejected (`_get_and_check_user` already enforces `is_active`).

### 6. Local Claude configuration

```json
{
  "mcpServers": {
    "gws-lab": { "type": "http", "url": "https://<your-lab-domain>/mcp/" }
  }
}
```

Claude hits the 401, runs discovery, opens the browser for Constellab login, stores and
auto-refreshes the token. No manual token pasting.

## Verification

1. `gws server run` on the lab; confirm `/mcp/` returns `401` with the `WWW-Authenticate` header.
2. `curl` the two `.well-known` docs; validate JSON shape against the MCP auth spec.
3. From local Claude: add `.mcp.json`, connect → browser opens → log in with Constellab creds.
4. Ask Claude: *"list the lab databases"* → `db_list`; then *"SHOW TABLES on gws_invest"* →
   `db_query`.
5. Negative tests:
   - no token → 401
   - expired/tampered JWT → 401
   - a **community** token (not a lab JWT) → 401 (proves the resource-token separation)
   - write statement (`UPDATE ...`) → blocked by `assert_read_only`
   - token of an inactive user → rejected

## Consent flow (current design)

```
Claude -> GET /mcp/authorize            (lab stashes PKCE/state, mints login_state)
       -> 302 <FRONT_URL>/mcp-consent?login_state=...        [front-end page]
             user is already logged into the lab front-end
             on "Allow": GET /core-api/user/mcp-consent-code -> {"code": ...}  (60s, single-use)
       -> GET /mcp-auth/consent?login_state=...&code=...     [lab API]
             check_unique_code(code) -> User -> complete_authorization()
       -> 302 back to the client with the OAuth code
Claude -> POST /mcp/token -> lab JWT
```

**Why the one-time code:** the front-end (`dev-lab.*`) and the API (`glab-dev.*`) are
different sub-domains and the lab session cookie is `samesite=strict`, so the cookie is
never sent to the API and cannot identify the user there. `UniqueCodeService` is the
bridge the lab already uses for `login-temp-access`.

This removed the whole `mcp_constellab_login` module and, with it, the `email`-claim
risk: identity is now a lab `User` object, never a parsed foreign token.

## Discovery paths: two SDK gaps to know about

Both were found by running the flow, not by reading the SDK, and both 404 the login
before the browser ever opens:

1. **Metadata must be served from the domain root.** RFC 9728 / 8414 put the
   well-known documents at the *host root*, but the SDK's routes live inside the
   MCP app, which the lab mounts at ``/mcp/``. They are therefore re-registered on
   the root app (``_add_well_known_routes``).
2. **Our issuer has a path (``https://<lab>/mcp``).** RFC 8414 §3.1 then requires the
   client to insert the well-known segment *between host and path* and fetch
   ``/.well-known/oauth-authorization-server/mcp`` -- which Claude does. The SDK
   hardcodes the bare ``/.well-known/oauth-authorization-server`` regardless of the
   issuer, so the two disagree. (Note the SDK *is* path-aware for the
   protected-resource URL via ``build_resource_metadata_url`` -- the asymmetry is
   the trap.) Both paths are now served; see
   ``_authorization_server_metadata_paths``.

## Open questions / risks

- **DCR support**: if implementing full Dynamic Client Registration proves heavy, a pre-registered
  static client id for Claude Code is an acceptable v1 narrowing — discovery still works.
- **Token lifetime**: lab JWT is 2 days (`ACCESS_TOKEN_EXPIRE_SECONDS`). OAuth clients expect a
  refresh token; decide whether to issue refresh tokens or let Claude re-run the browser flow
  every 2 days.
- **Exposure**: `/mcp/` must be reachable from outside the lab network — confirm the reverse
  proxy/ingress exposes it, and that CORS (lab default = lab sub-domains only) doesn't block a
  non-browser client (it shouldn't; MCP clients don't send Origin).
- **`AuthContext` lifetime**: `DefaultAuthContextLoader` falls back to a *process-global* when not
  in an HTTP context (`auth_context_loader.py:56-68`). The MCP requests *are* HTTP, so
  `starlette_context` request scoping should apply — but this must be verified under concurrent
  requests, since a leak would cross-authenticate users. **Requires the `ContextMiddleware` to be
  active on the mounted sub-app.**

## Follow-ups (post-v1)

- Expose `resource` / `scenario` / `community` tool groups (same verifier, more tools).
- Consider whether the stdio servers (`rag_mcp.py`, `rich_text_mcp.py`) should be refactored onto
  the same tool definitions to avoid divergence.
