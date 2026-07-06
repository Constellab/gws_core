# App launch & authentication

How a Streamlit / Reflex app is started and how the launching user is authenticated, across the
three ways an app is opened: **iframe (datalab)**, **standalone gateway (bookmarkable link)**, and
**space (share link)**.

This is the source of truth for a future agent touching app launch/auth. Keep it in sync with the
code it references.

> **Note on terminology.** "lab" = the gws_core backend (FastAPI, `core-api` routes, the JWT
> secret). "app" = the spawned Streamlit/Reflex process running behind nginx on its own host. The
> app process **cannot import gws_core** (it may run in a virtual env without it) — it reaches the
> lab over HTTP with `requests` + env vars only. That constraint drives most of the design.

---

## 1. The moving pieces

### Hosts (one nginx, routed by `server_name`)

Apps are served behind a single nginx on the app port (`Settings.get_app_external_port()`, `8510`
locally). Each app gets one or more `server` blocks distinguished by host name. Host names are built
by `AppProcess._build_host_name` (see [app_process.py](app_process.py)):

| Env | Front host | Reflex backend host |
| --- | --- | --- |
| local / desktop | `{resource_model_id}.localhost:8510` | `{resource_model_id}-back.localhost:8510` |
| prod | `{app_sub_domain}-{resource_model_id}.{virtual_host}` | `…-{resource_model_id}-back.{virtual_host}` |

- **Streamlit** = one host (the app server reads its own request → can read cookies directly).
- **Reflex** = **two hosts**: a static front bundle (`…`) and a separate state/websocket backend
  (`…-back`). The front's JS connects to the backend host. This split is why Reflex can't use the
  same cookie mechanism as Streamlit (see §5).
- The `resource_model_id` is used as the stable host segment so a Reflex build's baked-in backend
  URL survives restarts. A custom subdomain, if set, is added as an **alias** on the front block —
  never a replacement.

### The credentials

| Credential | Type | Lifetime | Minted by | Consumed by |
| --- | --- | --- | --- | --- |
| **`gws_code`** | single-use opaque code (`UniqueCodeService`, in-memory) | 60 s | `AppsManager.generate_app_access_code(user_id, app_id)` | exchanged **once** for a JWT — destructive |
| **app session JWT** | HS256 JWT (`Bearer …`), signed by the lab | 2 days | `AppsManager.exchange_app_code` → `JWTService.create_jwt(user_id)` | validated repeatedly (idempotent) |
| **dev sentinel** `dev_mode_token` | fixed string in app config | app lifetime | launch side (`_add_user`) | dev mode only |
| **system sentinel** `system_user_token` | fixed string in app config | app lifetime | launch side (`_add_user`) | `fallback_to_system_user` components |

The `gws_code` is short-lived and **single-use** (`UniqueCodeService.check_code` deletes it on
read). The JWT is the durable credential; validating it is idempotent, so it is always safe to
re-check. **This asymmetry is load-bearing** — see §5 and §6.

Constant names: `gws_code`, `gws_app_jwt` (cookie), `gws-login` (nginx path), `nginx-login`
(core-api segment) — defined in the dependency-free
[app_gateway_constants.py](app_gateway_constants.py) (so low-level consumers can import them without
a cycle) and re-exported as class attributes on `AppGatewayService`. They are **also mirrored as
literals** in the gws_core-free app bases (`gws_streamlit_base` / `gws_reflex_base`), which cannot
import gws_core at all — keep those in sync.

### The relevant `core-api` routes ([app_controller.py](app_controller.py))

| Route | Auth | Purpose |
| --- | --- | --- |
| `POST /apps/gateway/start` | AUTHENTICATED app: one-time `code` **or** lab session · PUBLIC app: none | resolve user (if required) + (cold-)start app, return status token |
| `POST /apps/gateway/handoff` | AUTHENTICATED app: lab session · PUBLIC app: none | AUTHENTICATED: mint `gws_code` + return app URL · PUBLIC: return **bare** app URL |
| `GET  /apps/process/{token}/status` | none (opaque token) | poll app status until RUNNING |
| `POST /apps/exchange-code` | the `gws_code` itself | exchange `gws_code` → JWT (called **by the app**) |
| `POST /apps/validate-jwt` | the JWT itself | validate a JWT → user id (called **by the app** on reload) |
| `GET  /apps/{app_id}/nginx-login?gws_code=…` | the `gws_code` itself | exchange + `Set-Cookie gws_app_jwt` + 302 to `/` (Streamlit only) |

The two `gateway/*` routes are **thin controllers** — all logic (caller auth + cold-start + handoff
URL) lives in `AppGatewayService.start(...)` / `AppGatewayService.handoff(...)`
([app_gateway_service.py](app_gateway_service.py)). Whether a user is required is decided there by
`AppGatewayService.app_requires_authentication(app_resource)` (True for **AUTHENTICATED**, False for
**PUBLIC**).

`exchange-code` / `validate-jwt` / `nginx-login` have **no user-auth dependency** — the code / JWT
in the body/query *is* the credential. That is deliberate: the app has no lab session to present.

### The front gateway route (Angular)

`{front}/open/app/{app_key}` — built by `FrontService.get_app_gateway_url`
([front_service.py](../core/service/front_service.py)). `app_key` = resource model id or custom
subdomain. This page owns the auth-guard (redirect to login), the progress UI, and drives
`gateway/start` → poll `status` → `gateway/handoff`. Optional `?code=` carries a one-time code
(used by the space flow, §4). For a **PUBLIC** app the gateway never blocks on auth — `start` and
`handoff` succeed for anyone and the app is entered anonymously.

---

## 2. Mode A — iframe (datalab resource page)

The datalab embeds the app in an `<iframe>` whose `src` is the app host URL built by
`AppProcess.get_app_full_url` ([app_process.py](app_process.py)). For an AUTHENTICATED app the URL is:

```
http://{resource_model_id}.localhost:8510/?gws_code=<single-use code>
```

Only `gws_code` is on the URL (the legacy `gws_token` / `gws_user_access_token` params were
**removed** — see §6).

**Flow:**

1. Datalab (already an authenticated lab session) requests the app URL; the launch side mints a
   `gws_code` for the current user and puts it on the iframe `src`.
2. The app boots and reads `gws_code` from its URL:
   - **Streamlit**: `_authenticate_from_url_code()` in
     [streamlit_main_state_base.py](streamlit/_gws_streamlit/gws_streamlit_base/streamlit_main_state_base.py)
   - **Reflex**: `_exchange_code_if_present()` in
     [reflex_main_state_base.py](reflex/_gws_reflex/gws_reflex_base/reflex_main_state_base.py)
3. The app `POST /apps/exchange-code {app_id, code}` → receives the JWT + user id, stores them in
   its session state, and **scrubs `gws_code` from the URL** (single-use).
4. The app is now authenticated; API calls carry the JWT (§7).

**Refresh (F5) inside the iframe:** the datalab re-renders the iframe with a **fresh `gws_code`**
each time, so step 2–3 simply repeat. No cookie is needed or used here. (A cookie set on the app
host would be a *third-party* cookie relative to the datalab origin, and modern browsers block/
partition those — so relying on the fresh code is both simpler and more robust.)

**PUBLIC app:** the iframe `src` is **bare** (`http://{resource_model_id}.localhost:8510/`, no
`gws_code`). This is decided in `AppProcess.get_app_full_url` via `token_in_url()` — PUBLIC returns
early with no params. The app boots, `authentication_is_required()` is False, so it runs
**anonymously** (no user, no exchange). Front components that still need the data lab API can opt
into the system-user fallback (§7).

---

## 3. Mode B — standalone gateway (bookmarkable link)

The stable, iframe-free way to open an app: `{front}/open/app/{app_key}`. Solves "app is stopped"
(cold-start) and "no bookmarkable URL" and "client blocks iframes".

**Flow:**

1. Browser opens `{front}/open/app/{app_key}` (an Angular page).
2. Front `POST /apps/gateway/start {app_key}` → `AppGatewayService.start`.
   - **AUTHENTICATED app:** the lab resolves the user from the **lab session** (Authorization
     cookie/header). If none → `401` → the front redirects to login, then returns here.
   - **PUBLIC app:** no user is resolved or required — start proceeds for anyone.
   - `start_app_and_get_status_token` (cold-)starts the app and returns a `status_token`.
3. Front polls `GET /apps/process/{status_token}/status` until `RUNNING` (shows progress).
4. Front `POST /apps/gateway/handoff {app_key}` → `AppGatewayService.handoff` → `build_app_handoff_url`:
   - **AUTHENTICATED app** (mints a `gws_code` for the session user):
     - **Streamlit** → `http://{host}/gws-login?gws_code=<code>`  (note the `/gws-login` path)
     - **Reflex**    → `http://{host}/?gws_code=<code>`
   - **PUBLIC app** → the **bare** URL `http://{host}/` (no code; the app runs anonymously).
5. Front navigates the browser to that URL. From here the two app types diverge — see §5.

**Refresh (F5) / new tab of the app URL directly** is the case Mode A doesn't have (nobody
re-injects a code). For an AUTHENTICATED app that is what the cookie / `rx.Cookie` mechanism in §5
survives; a PUBLIC app has nothing to persist (it is always anonymous) so F5 just reloads.

---

## 4. Mode C — space (share link)

A resource shared to the space with a `SPACE` share link. When the shared resource **is an app**,
the space link routes through the **same gateway** as Mode B, pre-seeded with a one-time code.

**Setup** (`ShareLinkService.generate_user_access_token_for_space_link`,
[share_link_service.py](../share/share_link_service.py)):

1. A `SPACE` `ShareLink` row exists for the resource ([share_link.py](../share/share_link.py)).
2. `generate_user_access_token_for_space_link(user, share_link)` mints a **single-use code** bound
   to the share link:
   `UniqueCodeService.generate_code(user.id, {SPACE_ACCESS_SHARE_LINK_ID_KEY: share_link.id}, 3600)`
   (1-hour validity).
3. `ShareLink.get_space_link(code)`:
   - if the resource **is an app** (`_resource_is_app()`) →
     `FrontService.get_app_gateway_url(entity_id, code=code)` = `{front}/open/app/{id}?code=<code>`
   - else (normal resource) → `{front}/open/resource/{token}?gws_user_access_token=<code>&hide_header=true`

**Flow (app case):**

1. User opens the space link → lands on the gateway page `{front}/open/app/{id}?code=<code>`.
2. Front `POST /apps/gateway/start {app_key, code}`.
   - Because a `code` is present, `_resolve_gateway_user` consumes it via
     `AuthorizationService.check_unique_code(code)` → **no lab session required**. This is the
     "space decides, lab trusts" model: the space issued the code, the lab consumes it.
3. Steps 3–5 of Mode B follow identically (poll status → handoff → navigate into the app).

> The space code in step 1 and the app `gws_code` in the handoff are **two different codes**, each
> with a single reader: the space code authenticates the *gateway*; the handoff code authenticates
> the *app*. (The space code is validated against `share_link.id` in
> `AuthorizationService.auth_share_link_from_token`, SPACE branch.)

---

## 5. Into the app: how auth survives a reload (the divergence)

Once handed off (§3/§4), the two app types establish and persist auth differently. **This section
applies to AUTHENTICATED apps only** — a PUBLIC app never has a user/JWT/cookie: it runs
anonymously (`authentication_is_required()` is False) and there is nothing to persist across a
reload.

### Streamlit — nginx-set HttpOnly cookie

Streamlit **can read** request cookies (`st.context.cookies`) but **cannot set** them (its JS runs
in a sandboxed iframe; `st.html`/`st.markdown` strip `<script>`). So the cookie is set at the nginx
layer:

1. Handoff sends the browser to `http://{host}/gws-login?gws_code=<code>`.
2. nginx `location = /gws-login` (built by `AppNginxRedirectServiceInfo._build_login_location` in
   [app_nginx_service.py](app_nginx_service.py)) proxies to
   `GET {lab}/core-api/apps/{app_id}/nginx-login?gws_code=<code>`.
   - **Important nginx detail:** the `proxy_pass` uses a **literal `127.0.0.1` host and no
     variables** (`_to_loopback_upstream`). A hostname or any `$var` in `proxy_pass` forces
     runtime DNS resolution, which needs a `resolver` directive we don't configure → `502 no
     resolver defined`. The original query string is appended automatically.
3. The core-api `app_nginx_login` handler exchanges the code, then returns `302 → "/"` with
   `Set-Cookie gws_app_jwt=<JWT>; HttpOnly; Secure; SameSite=Lax` (host-only, no `domain=`).
4. Browser lands on `/` (clean URL, no code) with the cookie set.
5. On this and **every subsequent load (F5 / new tab)**, Streamlit `_authenticate_from_cookie_jwt()`
   reads `gws_app_jwt` via `st.context.cookies` and `POST /apps/validate-jwt` to re-authenticate.

Streamlit auth resolution order (`_check_authentication`): session_state → dev sentinel →
`gws_code` in URL (Mode A) → `gws_app_jwt` cookie (Mode B reload).

### Reflex — `rx.Cookie` (client-side)

Reflex's two-host split (front vs `-back`) and websocket transport make an HttpOnly nginx cookie
impractical (it would be third-party to the backend host and unreadable from the websocket
handshake). So Reflex uses its **native `rx.Cookie`** — a JS-readable cookie Reflex syncs into
state and rehydrates on load:

- `jwt_cookie: str = rx.Cookie(name="gws_app_jwt", same_site="lax")` on `ReflexMainStateBase`.
- On a successful `gws_code` exchange, the JWT is written to both `user_access_token` (the API-call
  token) and `jwt_cookie` (the persistent store).
- On reload, Reflex rehydrates `jwt_cookie`; `_authenticate_from_jwt()` re-validates it via
  `POST /apps/validate-jwt`.

Trade-off vs Streamlit: the Reflex cookie is **not HttpOnly** (JS-readable). It holds the same JWT
already validated server-side and already in client state, so the exposure delta is small. This is
a deliberate, documented choice, not an oversight.

---

## 6. Reflex re-entrancy — why the JWT is checked *before* the code

Reflex evaluates **every bound `@rx.var` on load, often concurrently**, and each computed var can
call the auth check (`_load_and_check_user_authentication` → `_check_user_token`). Naively exchanging
`gws_code` from each call caused a **race**: several calls read "no JWT yet" simultaneously and all
tried to exchange the *same single-use code* → the first succeeded, the rest got `403 Invalid url`
("This app link has expired or was already used").

The fix (in [reflex_main_state_base.py](reflex/_gws_reflex/gws_reflex_base/reflex_main_state_base.py)):

1. **JWT first, code second.** `_check_user_token` validates any existing JWT (state or rehydrated
   cookie) *before* attempting a code exchange. Validation is idempotent; a spent code is not.
2. **Code exchange is gated to the init path only.** `_load_and_check_user_authentication` passes
   `allow_code_exchange=store_in_state`. Only `_on_load` runs with `store_in_state=True`; the
   concurrent `@rx.var` / read-only contexts (`store_in_state=False`) may **validate** a JWT but
   never **consume** the code.
3. **`jwt_cookie` is the sole JWT source of truth**, kept separate from `user_access_token` (which,
   in the past, could hold a non-JWT opaque token and fail validation — the collision that produced
   `403 Invalid token`).

Streamlit does not have this problem (it does not re-enter auth from concurrent computed vars).

---

## 7. API calls from inside an app (app → lab)

Front components call the data lab API with the user's identity. The token used is
`user_access_token` — i.e. **the session JWT** (or the dev sentinel in dev mode). It is sent in the
`gws_user_access_token` header alongside `gws_app_id`.

Server side, `AuthorizationService._auth_app` ([authorization_service.py](../user/authorization_service.py)):

1. dev app + `dev_mode_token` → system user (dev connections only).
2. else look up the token in the app's in-memory `user_access_tokens` map
   (`AppsManager.user_has_access_to_app`) — this resolves the **dev / system sentinels**.
3. **else validate the token as a JWT** (`_user_id_from_app_jwt`) — this resolves the **launching
   user** (whose token is the session JWT, no longer stored in the map).

Step 3 is what makes the launching-user API auth JWT-based end-to-end after the legacy removal (§6).

**PUBLIC app:** there is no authenticated user, so no `user_access_token` is sent — API calls are
unauthenticated. A component that must still reach the API can opt into `fallback_to_system_user`,
which sends the `system_user_token` sentinel (resolved by step 2 above) and runs the request as the
system user. ⚠️ That lets any visitor read/write data lab objects as the system user — use with care.

---

## 8. Legacy that was removed (do not reintroduce)

The pre-`gws_code` scheme put two things on the app URL and in an in-memory map:

- `gws_token` (a per-process token gated against `GWS_APP_TOKEN`) — **removed** as a URL param /
  gate. `GWS_APP_TOKEN` still exists as the process-identity env var (status/health), just not as a
  URL auth gate.
- `gws_user_access_token` (an opaque per-user token, added to the in-memory map via `_add_user`) —
  **removed** as a URL param. The launching user is no longer added to the map; their API calls
  authenticate via the JWT (§7).

Still present (NOT legacy): the `user_access_tokens` map itself, used only for the **dev sentinel**
and the **system-user fallback** (`fallback_to_system_user`).

---

## 9. Quick reference — file map

| Concern | File |
| --- | --- |
| App URL / launch / cold-start / env vars | [app_process.py](app_process.py) |
| Gateway/auth string constants (dependency-free) | [app_gateway_constants.py](app_gateway_constants.py) |
| Gateway service: `start` / `handoff`, auth, `app_requires_authentication` | [app_gateway_service.py](app_gateway_service.py) |
| Gateway (thin) + exchange + validate + nginx-login routes | [app_controller.py](app_controller.py) |
| nginx block generation (incl. `/gws-login`) | [app_nginx_service.py](app_nginx_service.py) |
| Streamlit auth (URL code + cookie) | [streamlit/_gws_streamlit/gws_streamlit_base/streamlit_main_state_base.py](streamlit/_gws_streamlit/gws_streamlit_base/streamlit_main_state_base.py) |
| Streamlit code↔JWT HTTP helpers | [streamlit/_gws_streamlit/gws_streamlit_base/streamlit_code_exchange.py](streamlit/_gws_streamlit/gws_streamlit_base/streamlit_code_exchange.py) |
| Reflex auth (code + rx.Cookie, re-entrancy) | [reflex/_gws_reflex/gws_reflex_base/reflex_main_state_base.py](reflex/_gws_reflex/gws_reflex_base/reflex_main_state_base.py) |
| Reflex code↔JWT HTTP helpers | [reflex/_gws_reflex/gws_reflex_base/reflex_code_exchange.py](reflex/_gws_reflex/gws_reflex_base/reflex_code_exchange.py) |
| App API-call auth (JWT fallback) | [../user/authorization_service.py](../user/authorization_service.py) |
| Space share link → gateway URL | [../share/share_link.py](../share/share_link.py), [../share/share_link_service.py](../share/share_link_service.py) |
| Front gateway URL builder | [../core/service/front_service.py](../core/service/front_service.py) |
