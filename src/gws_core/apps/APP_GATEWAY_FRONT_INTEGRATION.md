# App launcher gateway — Angular front integration

Exact request/response contract for the Angular gateway page `{front}/open/app/:appKey`, after the
OAuth-structured auth redesign. Read alongside [APP_LAUNCH_AND_AUTH.md](APP_LAUNCH_AND_AUTH.md)
(§1.5 has the flow schema) and [APP_AUTH_OAUTH_REDESIGN.md](APP_AUTH_OAUTH_REDESIGN.md) (rationale).

All routes are under the core-api prefix (`{labApiUrl}/core-api/...`). JSON bodies. The lab session
(`Authorization` cookie/header) is sent automatically by the browser for a logged-in user.

## What changed (⚠️ breaking for the front)

1. **`start` response now returns `authorize_grant`** — the front MUST keep it in page state.
2. **`handoff` request MUST send `authorize_grant`** in its body (it no longer relies on the lab
   session — a space visitor has none).
3. **The status poll response is trimmed** to `{ id, status, status_text }`. Any code reading
   `app`, `started_by`, `config_file_path`, `nb_of_connections`, `custom_subdomain_url`, or
   `started_at` from the *poll* response must stop — those fields are gone from this route.

## The page: `{front}/open/app/:appKey`

`appKey` = the app's resource model id **or** its custom subdomain. Optional query param `?code=`
carries a one-time **space access code** (present when arriving from a space share link; absent for
a normal standalone/bookmarked open).

### Sequence

```
1. read appKey (route param) and code (optional ?code= query param)
2. POST /core-api/apps/gateway/start   { app_key, code? }
      → { status_token, authorize_grant }         // keep BOTH in component state
      → on 401: redirect to login, then return to this page
3. poll GET /core-api/apps/process/{status_token}/status  until status === "RUNNING"
      → { id, status, status_text }               // show status_text as progress label
4. POST /core-api/apps/gateway/handoff { app_key, authorize_grant }
      → { app_url }
5. window.location.assign(app_url)                 // full navigation, NOT an iframe, NOT router
```

## Endpoint reference

### 1) POST `/core-api/apps/gateway/start`

Request body:
```json
{ "app_key": "string", "code": "string | null" }
```
- `app_key` — from the route.
- `code` — the `?code=` query param if present (space open), else omit / null.

Response `200`:
```json
{ "status_token": "string", "authorize_grant": "string | null" }
```
- `authorize_grant` is `null` for a **PUBLIC** app (no auth); a string for an **AUTHENTICATED** app.
- Keep **both** values; `status_token` for step 3, `authorize_grant` for step 4.

Errors:
- `401 Unauthorized` — AUTHENTICATED app and the caller could not be identified (no valid `code`,
  no lab session). **Action:** redirect to login, then retry this page. (PUBLIC apps never 401.)

### 2) GET `/core-api/apps/process/{status_token}/status`

No body. No auth header needed (the token is an opaque process handle).

Response `200`:
```json
{ "id": "string", "status": "STOPPED | STARTING | RUNNING", "status_text": "string | null" }
```
- Poll until `status === "RUNNING"`. Suggested interval ~1s; show `status_text` as the progress
  label. `status` is one of `STOPPED`, `STARTING`, `RUNNING`.

### 3) POST `/core-api/apps/gateway/handoff`

Call **only after** the app is `RUNNING`.

Request body:
```json
{ "app_key": "string", "authorize_grant": "string | null" }
```
- `authorize_grant` — the value from the `start` response (send it back verbatim). For a PUBLIC app
  it is `null`; send `null`.

Response `200`:
```json
{ "app_url": "string" }
```
- `app_url` is the app host URL to navigate to. For AUTHENTICATED apps it embeds a one-time code;
  for PUBLIC apps it is the bare app URL.

Errors:
- `401 Unauthorized` — missing/invalid/expired `authorize_grant` (AUTHENTICATED app). This should
  not happen in the normal flow; if it does, the grant expired (>10 min between start and handoff)
  or start was skipped — restart the page from step 2.

### 4) Navigate

```ts
window.location.assign(response.app_url);
```
Use a **full browser navigation**, not the Angular router and not an iframe. The URL points at a
different origin (the app host), and (for Streamlit) it passes through a `/gws-login` redirect that
sets an HttpOnly cookie — both require a real navigation.

## Timing / lifetime notes

- `authorize_grant` lives **10 minutes** and is **single-use** — comfortably covers cold-start +
  polling. Do not call `handoff` twice with the same grant (the second call 401s).
- The app grant embedded in `app_url` lives **60 s**, but it is minted at `handoff` time (post-
  RUNNING), so navigating immediately after handoff is safe. Navigate promptly; don't sit on the
  `app_url`.
- On a page reload of the gateway page itself, start over from step 2 (grants are single-use).

## PUBLIC vs AUTHENTICATED — front behaviour is identical

The front does **not** need to know the app's access mode. It always: start → poll → handoff →
navigate. The difference is server-side and reflected in the payloads:

| | AUTHENTICATED | PUBLIC |
| --- | --- | --- |
| `start` 401 possible? | yes (→ login) | no |
| `authorize_grant` from start | string | `null` |
| `authorize_grant` sent to handoff | that string | `null` |
| `app_url` from handoff | carries a one-time code | bare URL |

So: pass `authorize_grant` through from start to handoff **as-is** (string or null) and the same
code path works for both.

## TypeScript shapes (for reference)

```ts
interface GatewayStartRequest  { app_key: string; code?: string | null; }
interface GatewayStartResponse { status_token: string; authorize_grant: string | null; }

type AppProcessStatus = 'STOPPED' | 'STARTING' | 'RUNNING';
interface ProcessStatusResponse { id: string; status: AppProcessStatus; status_text: string | null; }

interface GatewayHandoffRequest  { app_key: string; authorize_grant: string | null; }
interface GatewayHandoffResponse { app_url: string; }
```

## Migration checklist for the Angular repo

- [ ] Capture `authorize_grant` from the `start` response into the gateway page state.
- [ ] Send `authorize_grant` in the `handoff` request body (add the field).
- [ ] Remove any reads of `app` / `started_by` / `config_file_path` / `nb_of_connections` /
      `custom_subdomain_url` / `started_at` from the **status poll** response (fields removed).
- [ ] Keep the existing start(401)→login→retry guard.
- [ ] Confirm handoff is called only once per open (grant is single-use).
