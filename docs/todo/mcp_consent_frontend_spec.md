# Frontend spec — MCP OAuth consent page

## Context

We are exposing the lab's tools to external MCP clients (Claude Code running on a
developer's machine). Before such a client can call the lab, the user must
authorize it — the standard OAuth "consent screen".

The lab handles the whole OAuth flow itself: no Space, no Community, no password,
and the browser never leaves our infrastructure. Your page is the **only** UI in
that flow, and the single point where a human decides whether an external agent
may act as them against lab data.

You are implementing **one route**. Its whole contract is: *two query params in,
one redirect out.*

## Where this page sits in the flow

```
Claude Code
    │  1. wants access, opens the browser at:
    │     https://<API_URL>/mcp/authorize?...
    ▼
Lab API  ── 2. 302 redirect ──▶  https://<FRONT_URL>/mcp-consent?login_state=<opaque>
                                          │
                                          │   ★ YOUR PAGE ★
                                          │   3. user must be logged into the lab
                                          │   4. GET /core-api/user/mcp-consent-code
                                          │      -> { "code": "<one-time code>" }
                                          │   5. "Allow Claude Code to access this lab?"
                                          │              [Allow]      [Deny]
                                          ▼
                    Allow: navigate to
                    https://<API_URL>/mcp-auth/consent?login_state=<opaque>&code=<code>
                                          │
                                          ▼
                    Lab API validates, 302s back to Claude Code. Done.
```

Your page's job ends at step 5. Everything after the redirect is backend + Claude.

## The route

**Path:** `/mcp-consent`
**Query params (both provided by the backend's redirect — never invent them):**

| Param | Type | Notes |
|---|---|---|
| `login_state` | string | Opaque. Pass through **verbatim**. Do not parse, decode, or alter it. |

## What the page must do

### 1. Require a lab session

The page must only render the consent UI for a logged-in user.

- If the user is **not logged in** → send them through the normal lab login, then
  return to `/mcp-consent?login_state=<original>` with the param intact. Losing
  `login_state` across the login bounce breaks the flow and the user has to
  restart from Claude.
- If logged in → render the consent UI.

### 2. Render the consent UI

Show, at minimum:

- **Which client** is asking: "Claude Code"
- **Which lab** it will access (the current lab's name/URL — the user may have several)
- **What it will be able to do**: *"Run read-only SQL queries against this lab's
  databases."*
- **As whom**: the signed-in user's email — it will act as them.
- Two actions: **Allow** and **Deny**.

Please make this read as a real decision rather than a formality: this is the only
gate before an external agent can read lab data as the user. No dark patterns —
Deny must be as reachable as Allow.

### 3. On **Allow**

**Fetch the code inside the click handler — not on page load.**

```
GET /core-api/user/mcp-consent-code
  (authenticated exactly like every other core-api call the front-end makes)

200 -> { "code": "3f9a…" }
```

Then navigate (full page navigation, **not** fetch/XHR — the backend answers with a
302 that must be followed by the browser):

```
window.location.href =
  `${API_URL}/mcp-auth/consent?login_state=${encodeURIComponent(login_state)}&code=${encodeURIComponent(code)}`
```

> **Why fetch on click:** the code is **single-use and expires in 60 seconds**. Fetching
> it when the page loads means a user who pauses to read will send an expired code
> and see a failure. Fetch it at the moment of the click and redirect immediately.

### 4. On **Deny**

Do **not** call the backend. Navigate away (lab home) or close the tab. The pending
authorization expires on its own; Claude reports that the login did not complete.

## Error handling

| Situation | What to show |
|---|---|
| `login_state` missing/empty from the URL | "This authorization link is invalid. Please start again from Claude Code." Do not call the API. |
| `/core-api/user/mcp-consent-code` returns 401 | Session expired → route through login, return to `/mcp-consent?login_state=…`. |
| That call returns any other error | "Could not authorize Claude Code right now. Please try again." Offer a retry that re-runs the Allow handler. |

After the redirect in step 3, failures are rendered by the **backend** (expired
login session, reused code, inactive account). You do not need to handle those —
but do not treat leaving your page as success. Your page cannot know the outcome.

## Security requirements

- **Never** send `login_state` anywhere except the `/mcp-auth/consent` URL above.
  It is not a credential, but it identifies a pending authorization.
- **Never** log, store, or persist the one-time `code` — no localStorage, no
  sessionStorage, no analytics. It is a bearer credential for 60 seconds. Fetch,
  redirect, forget.
- **Never** auto-submit. Consent requires a real click. Do not "remember" a previous
  choice and skip the screen.
- Do not follow a `redirect_uri` or any other URL supplied in the query string. The
  only URL you navigate to is the `API_URL`-based one constructed above.

## Configuration

- `API_URL` — the lab API base URL the front-end already uses for `core-api` calls.
  Reuse the existing config; do not hardcode. (e.g. `https://glab-dev.rio.gencovery.io`)

## Acceptance criteria

- [ ] `/mcp-consent?login_state=abc` while logged out → login → returns to the page with `login_state=abc` intact.
- [ ] While logged in → consent UI naming the client, the lab, the access, and the user's email.
- [ ] No network call to `mcp-consent-code` happens on page load.
- [ ] Allow → fetches the code, then full-page-navigates to `<API_URL>/mcp-auth/consent?login_state=…&code=…`.
- [ ] Deny → no API call, user leaves the page.
- [ ] Missing `login_state` → error message, no API call.
- [ ] The one-time code appears in no storage and no logs.

## Backend endpoints you depend on (already provided)

| Endpoint | Auth | Returns |
|---|---|---|
| `GET /core-api/user/mcp-consent-code` | lab session (as usual) | `{ "code": "<single-use, 60s>" }` |
| `GET /mcp-auth/consent?login_state=…&code=…` | none (the code *is* the proof) | 302 back to Claude Code |

## Out of scope

- The OAuth protocol itself (discovery, PKCE, tokens) — entirely backend.
- The MCP tools.
- Any Space/Community interaction — deliberately none in this flow.
