# Shareable app URLs — status

**Status: implemented.** Backend in gws_core (uncommitted at time of writing), front committed in
monorepo-front as `0ddb9d8a1`. Remaining work is listed under [To do](#to-do).

Design reference: `src/gws_core/apps/APP_LAUNCH_AND_AUTH.md` §3.1 (fallback), §3.2 (in-app
re-entry), §3.3 (session lifetime).

---

## Problem

A user copies the app URL from their address bar and shares it. That URL could not authenticate the
recipient, in three distinct ways:

1. **Stale `gws_code`** — the code is single-use (60s). `_exchange_code_if_present` raised
   *"This app link has expired or was already used"*.
2. **No code** — the app scrubs `gws_code` from the URL after exchanging it, so the address bar copy
   never has one. A different user has no `gws_app_jwt` cookie → dead end.
3. **App stopped** — `unregister_services` removes the app's nginx block on stop, and when no
   services remained nginx stopped entirely. The shared URL hit a dead port: no HTTP response at
   all, so no in-app code could run.

Root cause: **the app URL was not a self-sufficient entry point.** Only the Angular gateway
(`{front}/open/app/{app_key}`) could mint entry, and it sits upstream of the app. Case 3 was a
network-layer problem and bounded the whole feature — it had to be fixed first, because the in-app
redirect (cases 1–2) has nowhere to go while the app is down.

---

## Done

### 1. Persistent nginx fallback (case 3)

A `default_server` block that survives individual app stops, maps the requested host back to an app
key and `302`s to the existing gateway.

```
bare/stale URL, app stopped
   -> nginx default_server (persistent)
   -> GET /core-api/apps/fallback/resolve?host=<host>&target=<path+query>
   -> 302 {front}/open/app/{app_key}?redirect_to=<target>
   -> Angular gateway: auth guard -> start -> poll -> handoff (fresh gws_code)
   -> app
```

- `app_nginx_manager.py` — `_build_nginx_config` always renders the template (it used to
  short-circuit to a bare comment with zero services, skipping `default_server`);
  `unregister_services` no longer stops nginx when empty; `NGINX_TEMPLATE`'s `default_server`
  replaces `return 444` with the resolver redirect, forwarding host + original path/query.
- `app_gateway_service.py` — `app_key_from_host` inverts `AppProcess._build_host_name`
  (local / prod shapes, strips the Reflex `-back` suffix, case-insensitive, ignores the port);
  `build_fallback_redirect_url` maps host → app → gateway URL.
- `app_controller.py` — `GET /apps/fallback/resolve`, unauthenticated and side-effect free.
- `front_service.py` — `get_app_gateway_url` gained `redirect_to`; switched to `urlencode`, which
  also fixed latent under-encoding of the existing `code` param.

**Security:** the fallback never starts an app — it maps a host and redirects, so a bare URL cannot
become an unauthenticated app-start primitive. The gateway still resolves identity before
`start_app_and_get_status_token`.

### 2. nginx starts at lab boot

`AppNginxManager.init()` used to **stop** nginx at boot, and nothing restarted it until the first app
launched — so a shared URL of a stopped app hit a dead port for the whole idle period. It now starts
nginx (fallback-only config), wrapped in a try/except that logs instead of raising: another process
may already hold the app port, and that must not take lab boot down.

### 3. Unknown app → styled error, not raw JSON

The resolver is reached by a top-level browser navigation, so raising an API exception rendered the
raw JSON error envelope to a human. It now **always redirects**, to a gateway error URL carrying no
app key (so the page cannot try to start anything):

- `invalid_host` — not shaped like an app host (mistyped/foreign URL)
- `app_not_found` — well-formed key, app deleted or never existed

Front: keyless route `path: 'app'`, a terminal error state that never calls `start`, Retry hidden,
FR/EN translations. The `error` value is attacker-controlled, so it is mapped through an allowlist to
a translation key and never interpolated into the UI.

### 4. Deep links + login hop (front)

- `redirect_to` is merged into `app_url` at the final navigation, preserving `gws_code` (which always
  wins a key collision, so a deep link cannot forge it).
- **Pre-existing bug fixed:** `onStartError` rebuilt the return URL from `appKey` alone, dropping
  every query param — so a logged-out visitor lost `redirect_to` across the 401 → login → return hop.
  It now preserves the query while stripping the single-use `code`.

### 5. Spent/missing code on a *running* app (cases 1–2)

- `_exchange_code_if_present` treats a non-exchangeable code as "no credential" (scrubs it, returns
  None) instead of raising. A spent code is what a shared link normally looks like.
- `_on_load` calls `_redirect_to_gateway()` → core-api fallback resolver → gateway → fresh code.
  Transparent when the visitor holds a lab session.
- Reached on the **lab API**, not the app host: the nginx fallback `location` exists only on the
  catch-all block, so a running app's own block would serve that path from the app itself.
- **Loop guard** rides in the URL (`gws_gateway_retry=1`), because Reflex state is wiped by the
  reload the bounce causes. Returning still-unauthenticated with the marker raises instead of
  bouncing again.
- The spent `gws_code` is stripped from the forwarded `target` — the scrub is a client-side history
  rewrite, so the server-side router still sees it, and carrying it would put a stale code beside the
  fresh one.
- Dev mode still raises: a dev app failing auth is a config problem to see, not to bounce.

### 6. Session lifetime

- **Cookie was a session cookie.** `rx.Cookie` had no `max_age`, so the browser dropped it on
  close — long before the 2-day JWT expired, which reads as "the app logs me out constantly". Both
  the Reflex `rx.Cookie` and the Streamlit nginx-login `Set-Cookie` now use
  `APP_JWT_COOKIE_MAX_AGE_SECONDS` (30 days). Outliving the JWT is deliberate: the JWT stays the
  authority, the cookie is only its persistent store.
- **JWT never renewed.** `POST /apps/validate-jwt` returns a `renewed_jwt` when the presented token
  is more than half-expired (`JWTService.app_token_needs_refresh`), and the Reflex app stores it. An
  app in active use renews on every page load; an idle one still expires on schedule.

---

## To do

- **Streamlit sliding renewal.** `validate-jwt` returns `renewed_jwt`, but the Streamlit client reads
  only `user_id`, so its session still ends at the fixed JWT expiry. The field is additive, so
  nothing breaks — it just does not slide yet.
- **Streamlit in-app gateway re-entry.** Only Reflex re-enters the gateway on a spent/missing code;
  Streamlit still dead-ends.
- **Space-origin re-auth.** An inactive space visitor bounced to lab login has no account. Needs the
  entry origin recorded and a bounce back to the *space* (the only party that can mint a fresh space
  code) instead of to lab login.
- **Commit the gws_core side.** The front is committed (`0ddb9d8a1`); the backend is not.

---

## Verification

**Done:**

- Unit: host parsing (local / port / `-back` / case / non-app hosts), resolver error URLs for both
  reasons, `redirect_to` sanitising, nginx boot behaviour (starts, and survives a failed start),
  template renders `default_server` with zero services, `ReflexURL` exposes `netloc` (not `host`),
  JWT renewal (fresh token not renewed, half-expired token re-minted).
  → `tests/test_gws_core/apps/test_app_fallback_resolve.py` (14),
  `test_app_gateway_auth.py` (15), `test_orphan_app_reaper.py` (4) — all passing.
- `nginx -t` validates the generated config both with zero services and with an app registered.
- Live check: with **zero apps registered**, `curl -H "Host: abc123.localhost" …/config?tab=1`
  returns `302 …/gws-app-fallback?host=abc123.localhost&target=/config?tab=1`.
- A running app's exact `server_name` still wins over `default_server` (apps are not shadowed).

**Environment note:** `test_reflex_app` / `test_streamlit_app` fail with `Failed to start nginx`
(port 8510 held by a running lab server). Confirmed by stashing that they fail **identically on
unmodified code** — not caused by this work.

The stopped-app fallback, the in-app gateway re-entry and the cookie lifetime were all also confirmed
by hand against a running lab.
