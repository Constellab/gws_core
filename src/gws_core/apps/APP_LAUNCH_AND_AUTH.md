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
| **authorize grant** | single-use code (`UniqueCodeService`), app-bound, names the user | 10 min | `AppsManager.generate_authorize_grant` at gateway `start` | `AppsManager.consume_authorize_grant` at gateway `handoff` — carries identity across the two stateless gateway calls |
| **`gws_code`** (app grant) | single-use code (`UniqueCodeService`), app-bound | 60 s | `AppsManager.generate_app_access_code(user_id, app_id)` at `handoff` (post-RUNNING) | exchanged **once** for the app token — destructive |
| **app access token** | HS256 JWT `{sub, exp, typ:"app", app_id}` (`Bearer …`) | 2 days | `AppsManager.exchange_app_code` → `JWTService.create_app_jwt(user_id, app_id)` | validated repeatedly as an **app** credential → `AuthContextApp`; **rejected on user routes** |
| **dev sentinel** `dev_mode_token` | fixed string in app config | app lifetime | launch side (`_add_user`) | dev mode only |
| **system sentinel** `system_user_token` | fixed string in app config | app lifetime | launch side (`_add_user`) | `fallback_to_system_user` components |

The grants are short-lived and **single-use** (`UniqueCodeService.check_code` deletes on read). The
**app access token** is the durable credential; validating it is idempotent, so it is always safe to
re-check. **This asymmetry is load-bearing** — see §5.

> **App-scoped, not a session (this is the key security property).** The app access token carries
> `typ:"app"` + `app_id`. It authenticates the user **only** as an app credential
> (`AuthorizationMode.APP` → `AuthContextApp`) on the ~20 `_or_app` routes, and is **rejected** by
> the 344 user-only routes (`check_user_access_token` refuses `typ:"app"`). So a space-only /
> inactive user who opens an app never obtains a general lab session, and a leaked app token /
> cookie cannot roam the lab. Full design + rationale: [APP_AUTH_OAUTH_REDESIGN.md](APP_AUTH_OAUTH_REDESIGN.md).

Constant names: `gws_code`, `gws_app_jwt` (cookie), `gws-login` (nginx path), `nginx-login`
(core-api segment) — defined in the dependency-free
[app_gateway_constants.py](app_gateway_constants.py) (so low-level consumers can import them without
a cycle) and re-exported as class attributes on `AppGatewayService`. They are **also mirrored as
literals** in the gws_core-free app bases (`gws_streamlit_base` / `gws_reflex_base`), which cannot
import gws_core at all — keep those in sync.

### The relevant `core-api` routes ([app_controller.py](app_controller.py))

| Route | Auth | Purpose |
| --- | --- | --- |
| `POST /apps/gateway/start` | AUTHENTICATED app: one-time space `code` **or** lab session · PUBLIC app: none | resolve user **once** + (cold-)start app; return `status_token` + **`authorize_grant`** (None for PUBLIC) |
| `POST /apps/gateway/handoff` | AUTHENTICATED app: the **`authorize_grant`** from start · PUBLIC app: none | consume grant → mint `gws_code` (post-RUNNING) + return app URL · PUBLIC: **bare** app URL. No lab session needed. |
| `GET  /apps/process/{token}/status` | none (opaque process handle) | poll status until RUNNING — returns the **light DTO** `{id, status, status_text}` only (no user/config/env) |
| `POST /apps/exchange-code` | the `gws_code` itself | exchange `gws_code` → **app access token** (called **by the app**) |
| `POST /apps/validate-jwt` | the app token itself | validate an **app-scoped** token (bound to `app_id`) → user id (app reload) |
| `GET  /apps/{app_id}/nginx-login?gws_code=…` | the `gws_code` itself | exchange + `Set-Cookie gws_app_jwt` (app token) + 302 to `/` (Streamlit only) |

The two `gateway/*` routes are **thin controllers** — all logic (caller auth + cold-start + handoff
URL) lives in `AppGatewayService.start(...)` / `AppGatewayService.handoff(...)`
([app_gateway_service.py](app_gateway_service.py)). Whether a user is required is decided there by
`AppGatewayService.app_requires_authentication(app_resource)` (True for **AUTHENTICATED**, False for
**PUBLIC**).

**Why an authorize grant (start → handoff).** The two gateway calls are stateless, and a space user
has no lab session — so identity is resolved **once** at `start` and carried to `handoff` as a
single-use `authorize_grant` (the front replays it). The short-lived app grant (`gws_code`) is
minted at `handoff` **after** the app is RUNNING, so its 60 s lifetime can't expire during
cold-start. See [APP_AUTH_OAUTH_REDESIGN.md](APP_AUTH_OAUTH_REDESIGN.md).

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

## 1.5. Schemas — the auth workflow

### Standalone gateway + space (Mode B / Mode C), AUTHENTICATED app

Identity is resolved once at `start`; the **authorize grant** carries it to `handoff`; the app grant
(`gws_code`) is exchanged for the **app-scoped token** at the app host.

```
browser/front            lab (core-api)                         app host (nginx + app)
    |                        |                                          |
    | POST gateway/start     |                                          |
    |  {app_key, code?}      |                                          |
    |----------------------->| resolve user ONCE:                       |
    |                        |   space code (allow_inactive) OR session |
    |                        |   → mint AUTHORIZE GRANT (10m, app-bound) |
    |                        |   → cold-start app                        |
    |<-----------------------| {status_token, authorize_grant}          |
    |                        |                                          |
    | GET process/{tok}/status (poll, light DTO)                        |
    |----------------------->| {id,status,status_text}                  |
    |          ... until RUNNING ...                                    |
    |                        |                                          |
    | POST gateway/handoff   |                                          |
    |  {app_key, grant}      |                                          |
    |----------------------->| consume grant → user (no session needed) |
    |                        |   → mint gws_code NOW (60s, app-bound)    |
    |<-----------------------| {app_url = host + gws_code}              |
    |                        |                                          |
    | navigate to app_url ------------------------------------------->  |
    |                        |                        Streamlit: /gws-login?gws_code=…
    |                        |   nginx → core-api /apps/{id}/nginx-login |
    |                        |<---------- exchange gws_code ------------ |
    |                        | mint APP TOKEN (typ:app, app_id)          |
    |                        |----------- 302 "/" + Set-Cookie --------->| gws_app_jwt (HttpOnly)
    |                        |                        Reflex: /?gws_code=… → app POSTs exchange-code
    |                        |                                          |   → APP TOKEN in rx.Cookie
    |                        |                                          |
    | app API call: gws_app_id + gws_user_access_token = APP TOKEN      |
    |----------------------->| _auth_app → AuthContextApp (APP routes)  |
    |                        | (rejected on user-only routes)           |
```

### Reload (F5 / new tab), AUTHENTICATED app

```
browser --- GET / (cookie gws_app_jwt sent) ---> app
   app reads cookie → POST /apps/validate-jwt {app_id, token}
                          → check_app_access_token(token, app_id) → user id   (idempotent; no refresh)
```

### iframe (Mode A) — no gateway, fresh code each render

```
datalab (session) --- builds iframe src ---> app host
   AUTHENTICATED: src = host/?gws_code=<fresh code>   → app exchanges → APP TOKEN (session_state)
   PUBLIC:        src = host/                          → anonymous
   F5: datalab re-renders the iframe with a NEW gws_code (cookie is third-party here, not relied on)
```

### Credential hand-offs at a glance

```
 space code ──(start)──> authorize grant ──(handoff)──> gws_code ──(exchange)──> APP TOKEN
  (or lab session)         10m, 1-use            60m…              60s, 1-use      2d, app-scoped
  identifies user       carries identity      mints app grant    → app token    used for app API,
  at the gateway        across 2 calls         post-RUNNING        (HttpOnly /    rejected on user
                                                                   rx.Cookie)     routes
```

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
   - **AUTHENTICATED app:** the lab resolves the user **once** (lab session, or a space `code`). If
     none → `401` → the front redirects to login, then returns here. On success it mints an
     **`authorize_grant`** naming that user and returns it with `status_token`.
   - **PUBLIC app:** no user resolved/required; `authorize_grant` is None.
   - `start_app_and_get_status_token` (cold-)starts the app.
3. Front polls `GET /apps/process/{status_token}/status` until `RUNNING` (light DTO; shows progress).
4. Front `POST /apps/gateway/handoff {app_key, authorize_grant}` → `AppGatewayService.handoff`:
   - **AUTHENTICATED app:** consumes the `authorize_grant` (no lab session needed) → mints a fresh
     `gws_code` **now** (post-RUNNING, so it can't expire during cold-start) → `build_app_handoff_url`:
     - **Streamlit** → `http://{host}/gws-login?gws_code=<code>`  (note the `/gws-login` path)
     - **Reflex**    → `http://{host}/?gws_code=<code>`
   - **PUBLIC app** → the **bare** URL `http://{host}/` (no code; the app runs anonymously).
5. Front navigates the browser to that URL. From here the two app types diverge — see §5.

> **Front contract (Angular) changed with the redesign:** `start` now returns `authorize_grant`,
> and `handoff` must send it back in its body (`{app_key, authorize_grant}`). The status poll now
> returns only `{id, status, status_text}` — the front must not read user/config fields from it.

**Refresh (F5) / new tab of the app URL directly** is the case Mode A doesn't have (nobody
re-injects a code). For an AUTHENTICATED app that is what the cookie / `rx.Cookie` mechanism in §5
survives; a PUBLIC app has nothing to persist (it is always anonymous) so F5 just reloads.

### 3.1. Sharing the app URL — the nginx fallback

An app's nginx block only exists while the app runs (`AppProcess.stop` →
`AppNginxManager.unregister_services`). So a **shared app URL for a stopped app** matches no
`server` block. A persistent fallback block keeps it answering:

```
GET http://{resource_model_id}.localhost:8510/config   (app STOPPED)
  -> nginx `default_server` block (always present)
  -> 302 /gws-app-fallback?host=$host&target=$request_uri
  -> proxied to core-api GET /apps/fallback/resolve
  -> host -> app key (AppGatewayService.app_key_from_host, inverts _build_host_name)
  -> 302 {front}/open/app/{app_key}?redirect_to=/config
  -> the Mode B gateway takes over (auth guard -> start -> poll -> handoff)
```

- The fallback is `default_server`, so a **running** app's exact `server_name` always wins; it
  only catches hosts no specific block claims.
- It **starts nothing and authenticates nobody** — it maps a host to a key and redirects. The
  gateway still resolves identity before `start_app_and_get_status_token`, so a bare URL cannot
  become an unauthenticated app-start primitive.
- `redirect_to` carries the original path so a shared **deep link** survives the handoff. It is
  sanitised (single-slash-prefixed paths only) to avoid an open redirect, and the fallback path
  itself is dropped to avoid a loop.
- A host that maps to no app returns a real **404**, rather than bouncing into a gateway that
  would fail confusingly.
- Consequence: **nginx now stays up with zero registered apps** (it used to stop). Both the
  empty-services early return in `_build_nginx_config` and the `stop()` on empty in
  `unregister_services` were removed — either one would leave shared URLs dead.

### 3.2. Shared URL of a *running* app — the app re-enters the gateway

The fallback only covers a **stopped** app. A shared URL of a *running* app reaches the app itself
with either a **spent** `gws_code` (single-use, the first visitor consumed it) or **none** (the app
scrubs it from the URL after the first open). Neither is a dead end:

- `_exchange_code_if_present` treats a non-exchangeable code as "no credential" (it scrubs it and
  returns None) instead of raising. A spent code is what a shared link *normally* looks like.
- `_on_load` then calls `_redirect_to_gateway()`, which sends the browser to the core-api fallback
  resolver (`GWS_LAB_API_URL` + `/core-api/apps/fallback/resolve?host=…&target=…`) → gateway →
  fresh code. Transparent when the visitor holds a lab session.
- The resolver is reached **on the lab API, not the app host**: the nginx fallback `location` exists
  only on the catch-all block, so a running app's own block would serve that path from the app.
- **Loop guard:** the forwarded `target` carries `gws_gateway_retry=1`, **and** a short-lived
  `gws_gateway_retry` cookie (1 min) is set just before bouncing. Coming back still unauthenticated
  with *either* marker raises instead of bouncing again; the marker is cleared as soon as a
  credential is obtained. Two homes because neither alone is reliable: Reflex state is wiped by the
  reload so the flag cannot live in state, the query param only survives if the front carries the
  target's query over to the app URL it navigates to (the handoff URL it is built from carries only
  `gws_code`), and the cookie is gone once it expires.
- **Dev mode** keeps raising — a dev app failing auth is a config problem to see, not to bounce.

### 3.3. Session lifetime — sliding renewal

Two independent things used to cut sessions short, both fixed:

- **The cookie was a session cookie.** `rx.Cookie` had no `max_age`, so the browser dropped it when
  the tab closed — the app forgot the visitor long before the 2-day JWT expired. Both the Reflex
  `rx.Cookie` and the Streamlit nginx-login `Set-Cookie` now use
  `APP_JWT_COOKIE_MAX_AGE_SECONDS` (30 days). Outliving the JWT is deliberate: the JWT stays the
  authority, the cookie is only its persistent store.
- **The JWT never renewed.** `POST /apps/validate-jwt` now returns a `renewed_jwt` when the presented
  token is more than half-expired (`JWTService.app_token_needs_refresh`), and the app stores it. An
  app in active use renews on every page load; an idle one still expires on schedule. Reflex consumes
  this today — **Streamlit does not yet** (it reads only `user_id`; the field is additive, so it stays
  compatible and simply does not slide).

---

## 4. Mode C — space (share link)

A resource shared to the space with a `SPACE` share link. When the shared resource **is an app**,
the space link routes through the **same gateway** as Mode B, pre-seeded with a one-time code.

**Setup** (`ShareLinkService.generate_user_access_token_for_space_link`,
[share_link_service.py](../share/share_link_service.py)):

1. A `SPACE` `ShareLink` row exists for the resource ([share_link.py](../share/share_link.py)).
2. The `ShareLink` entity mints a **single-use space access code** bound to itself + the
   space-authenticated user: `share_link.generate_space_access_code(user.id)` (1-hour validity).
   Consumption lives on the same entity: `share_link.check_space_access_code(code)` → user id
   (used by `AuthorizationService.auth_share_link_from_token`).
3. `ShareLink.get_space_link(space_access_code)`:
   - if the resource **is an app** (`_resource_is_app()`) →
     `FrontService.get_app_gateway_url(entity_id, code=space_access_code)` = `{front}/open/app/{id}?code=<code>`
   - else (normal resource) → `{front}/open/resource/{token}?gws_user_access_token=<code>&hide_header=true`
     (the `gws_user_access_token` name is legacy wire; the value is a space access code).

**Flow (app case):**

1. User opens the space link → lands on the gateway page `{front}/open/app/{id}?code=<code>`.
2. Front `POST /apps/gateway/start {app_key, code}`.
   - Because a `code` is present, `_resolve_gateway_user` consumes it via
     `AuthorizationService.check_unique_code(code, allow_inactive=True)` → **no lab session
     required**, and the user **may be inactive** (a space visitor with no lab login). "Space
     decides, lab trusts": the space issued the code, the lab consumes it and issues an
     `authorize_grant`.
3. Steps 3–5 of Mode B follow identically (poll status → handoff **with the grant** → navigate).

> **Three single-use codes, one reader each** — do not confuse them: (1) the **space access code**
> authenticates the *gateway* at `start` (validated against `share_link.id` by
> `ShareLink.check_space_access_code`); (2) the **authorize grant** carries the resolved identity
> from `start` to `handoff`; (3) the app **`gws_code`** authenticates the *app* at exchange. The
> inactive user flows through all three and ends with an **app-scoped** token (never a lab session).

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
3. The core-api `app_nginx_login` handler exchanges the code for the **app-scoped token**, then
   returns `302 → "/"` with `Set-Cookie gws_app_jwt=<app token>; HttpOnly; Secure; SameSite=Lax`
   (host-only, no `domain=`).
4. Browser lands on `/` (clean URL, no code) with the cookie set.
5. On this and **every subsequent load (F5 / new tab)**, Streamlit `_authenticate_from_cookie_jwt()`
   reads `gws_app_jwt` via `st.context.cookies` and `POST /apps/validate-jwt` to re-authenticate —
   validated as an **app-scoped** token bound to this `app_id` (no refresh token; re-validate only).

Streamlit auth resolution order (`_check_authentication`): session_state → dev sentinel →
`gws_code` in URL (Mode A) → `gws_app_jwt` cookie (Mode B reload).

### Reflex — `rx.Cookie` (client-side)

Reflex's two-host split (front vs `-back`) and websocket transport make an HttpOnly nginx cookie
impractical (it would be third-party to the backend host and unreadable from the websocket
handshake). So Reflex uses its **native `rx.Cookie`** — a JS-readable cookie Reflex syncs into
state and rehydrates on load:

- `jwt_cookie: str = rx.Cookie(name="gws_app_jwt", same_site="lax")` on `ReflexMainStateBase`.
- On a successful `gws_code` exchange, the **app-scoped token** is written to both
  `user_access_token` (the API-call token) and `jwt_cookie` (the persistent store).
- On reload, Reflex rehydrates `jwt_cookie`; `_authenticate_from_jwt()` re-validates it via
  `POST /apps/validate-jwt` (bound to `app_id`).

Trade-off vs Streamlit: the Reflex cookie is **not HttpOnly** (JS-readable). But it holds an
**app-scoped** token (rejected on user routes, bound to this app), already validated server-side and
already in client state — so a stolen cookie cannot roam the lab. Deliberate, documented choice.

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
`user_access_token` — i.e. **the app-scoped token** (or the dev sentinel in dev mode). It is sent in
the `gws_user_access_token` header (legacy wire name) alongside `gws_app_id`.

Server side, `AuthorizationService._auth_app` ([authorization_service.py](../user/authorization_service.py)):

1. dev app + `dev_mode_token` → system user (dev connections only).
2. else look up the token in the app's in-memory `user_access_tokens` map
   (`AppsManager.user_has_access_to_app`) — this resolves the **dev / system sentinels**.
3. **else validate as an app-scoped token bound to this app** (`_user_id_from_app_token` →
   `JWTService.check_app_access_token(token, app_id)`) — resolves the **launching user**.

These routes admit `AuthorizationMode.APP` (the ~20 `check_user_access_token_or_app` endpoints);
the app token yields `AuthContextApp` and is **rejected** on the 344 user-only routes. That set of
`_or_app` routes *is* the app's scope. See [APP_AUTH_OAUTH_REDESIGN.md](APP_AUTH_OAUTH_REDESIGN.md).

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

**PUBLIC share link on an AUTHENTICATED app is refused** (both at creation in
`ShareLinkService.generate_share_link` and at open in `auth_share_link_from_token`) — a PUBLIC link
authenticates every visitor as the system user, which would bypass the app's auth. Such apps are
reachable only via a SPACE link or the gateway. See `ShareLinkService.resource_is_authenticated_app`.

---

## 9. Quick reference — file map

| Concern | File |
| --- | --- |
| App URL / launch / cold-start / env vars | [app_process.py](app_process.py) |
| Gateway/auth string constants (dependency-free) | [app_gateway_constants.py](app_gateway_constants.py) |
| Gateway service: `start` / `handoff`, auth, `app_requires_authentication` | [app_gateway_service.py](app_gateway_service.py) |
| Gateway (thin) + exchange + validate + nginx-login routes | [app_controller.py](app_controller.py) |
| nginx block generation (incl. `/gws-login`) | [app_nginx_service.py](app_nginx_service.py) |
| nginx template + persistent fallback `default_server` block | [app_nginx_manager.py](app_nginx_manager.py) |
| Host → app key mapping + fallback redirect target | [app_gateway_service.py](app_gateway_service.py) |
| Streamlit auth (URL code + cookie) | [streamlit/_gws_streamlit/gws_streamlit_base/streamlit_main_state_base.py](streamlit/_gws_streamlit/gws_streamlit_base/streamlit_main_state_base.py) |
| Streamlit code↔JWT HTTP helpers | [streamlit/_gws_streamlit/gws_streamlit_base/streamlit_code_exchange.py](streamlit/_gws_streamlit/gws_streamlit_base/streamlit_code_exchange.py) |
| Reflex auth (code + rx.Cookie, re-entrancy) | [reflex/_gws_reflex/gws_reflex_base/reflex_main_state_base.py](reflex/_gws_reflex/gws_reflex_base/reflex_main_state_base.py) |
| Reflex code↔JWT HTTP helpers | [reflex/_gws_reflex/gws_reflex_base/reflex_code_exchange.py](reflex/_gws_reflex/gws_reflex_base/reflex_code_exchange.py) |
| App-scoped JWT mint/verify (`create_app_jwt` / `check_app_access_token`) | [../user/jwt_service.py](../user/jwt_service.py) |
| App API-call auth (`_auth_app` → `AuthContextApp`); app token rejected on user routes | [../user/authorization_service.py](../user/authorization_service.py) |
| Authorize grant + app grant + app-token exchange | [apps_manager.py](apps_manager.py) |
| Space access code (mint + consume, on the entity) | [../share/share_link.py](../share/share_link.py) |
| PUBLIC-on-authenticated-app guard; space link → gateway URL | [../share/share_link_service.py](../share/share_link_service.py), [../share/share_link.py](../share/share_link.py) |
| Front gateway URL builder | [../core/service/front_service.py](../core/service/front_service.py) |
| OAuth-structured redesign (design + decisions) | [APP_AUTH_OAUTH_REDESIGN.md](APP_AUTH_OAUTH_REDESIGN.md) |
| Angular front integration (gateway request/response contract) | [APP_GATEWAY_FRONT_INTEGRATION.md](APP_GATEWAY_FRONT_INTEGRATION.md) |
