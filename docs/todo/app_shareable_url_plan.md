# Shareable app URLs — nginx fallback vhost

## Problem

A user copies the app URL from their address bar and shares it. Today that URL cannot
authenticate the recipient, in three distinct ways:

1. **Stale `gws_code`** — the code is single-use (60s). `_exchange_code_if_present`
   raises *"This app link has expired or was already used"*.
2. **No code** — the app scrubs `gws_code` from the URL after exchanging it
   (`_scrub_gws_code_from_url`), so the URL in the address bar never has one. A different
   user has no `gws_app_jwt` cookie, so `_authenticate_from_jwt` returns None → dead end.
3. **App stopped** — `unregister_services` removes the app's nginx block on stop, and when
   no services remain nginx stops entirely. The shared URL hits a dead port: no HTTP
   response at all, so no in-app code can run.

Root cause: **the app URL is not a self-sufficient entry point.** Only the Angular gateway
(`{front}/open/app/{app_key}`) can mint entry, and it sits upstream of the app. Case 3 is a
network-layer problem and bounds the whole feature — it must be fixed first, because the
in-app redirect (cases 1–2) has nowhere to go while the app is down.

## Approach

Keep a **persistent fallback server block** on the app port that survives individual app
stops. It resolves the requested hostname to an app key and `302`s to the existing gateway.
The fallback stays deliberately thin — no cold-start, no auth, no progress UI of its own.

```
bare/stale URL, app stopped
   -> nginx default_server (persistent)
   -> GET /core-api/apps/fallback/resolve?host=<host>&target=<path+query>
   -> 302 {front}/open/app/{app_key}?redirect_to=<target>
   -> existing Angular gateway: auth guard -> start -> poll -> handoff (fresh gws_code)
   -> app
```

Why redirect to the gateway rather than serve a page from nginx: resolving host→app_key,
checking identity, cold-starting and polling status is application logic. nginx can only
`proxy_pass` to something that does it — which is the gateway. Reusing it keeps one auth
guard and one progress UI, and keeps the fallback app-technology agnostic (pure HTTP host
mapping), which is what a future embedded-Angular app needs.

Security: the fallback **never starts an app**. It only maps a host to a key and redirects,
so a bare URL cannot become an unauthenticated app-start primitive. The gateway resolves
identity before `start_app_and_get_status_token`, exactly as today.

## Blockers found in the current code

Both must be fixed or the fallback never renders:

- `_build_nginx_config` returns `"# No services registered\n"` when `_services` is empty
  (app_nginx_manager.py:224-225) — the template, including `default_server`, is skipped.
- `unregister_services` calls `self.stop()` when no services remain
  (app_nginx_manager.py:109-111) — nginx exits, so nothing listens.

The existing `default_server` block (`return 444`) is the hook to replace.

## Changes

### 1. `app_nginx_manager.py` — keep nginx alive, redirect unmatched hosts

- `_build_nginx_config`: always render the template; drop the empty-services early return.
- `unregister_services`: never stop nginx on empty; keep the fallback listening.
- `NGINX_TEMPLATE` `default_server`: replace `return 444` with a redirect to the resolver,
  passing the original host and the original path+query so deep links survive.

Keep the `444` behaviour only when the resolver is unreachable, so a malformed request
still terminates rather than looping.

### 2. `app_controller.py` — the resolver route

`GET /apps/fallback/resolve` (no auth — it reveals only whether a host maps to an app):

- Parse the host into its middle segment, inverting `AppProcess._build_host_name`:
  - local: `{segment}.localhost`
  - prod: `{app_sub_domain}-{segment}.{virtual_host}`
  - strip a trailing `-back` (the Reflex backend host).
- `AppGatewayService.resolve_app_resource(segment)` — already handles both the resource
  model id and a custom subdomain.
- Unknown host / no matching app → real 404 page, **not** a redirect into a gateway that
  would then fail confusingly.
- Otherwise `302` to `FrontService().get_app_gateway_url(app_key)` carrying `redirect_to`.

### 3. `front_service.py` — carry the deep link

`get_app_gateway_url` gains an optional `redirect_to` so `/config`-style deep links are
preserved through the gateway handoff instead of dropping the user on the app root.

## Out of scope (deliberately deferred)

- **In-app redirect for cases 1–2.** Depends on this landing first. The stale-code raise
  should become "discard code, re-enter gateway" rather than an error, and the redirect
  needs the same `allow_code_exchange` gating as the code exchange or concurrent `@rx.var`
  evaluations will each fire a navigation (see APP_LAUNCH_AND_AUTH.md §6).
- **Cookie `max_age` + sliding JWT renewal.** Independent of the redirect; the `rx.Cookie`
  is currently a session cookie (dies on browser close) and the JWT never renews.
- **Space-origin re-auth.** An inactive space visitor bounced to lab login has no account;
  needs the origin recorded and a bounce back to the space instead.
- **Angular side of `redirect_to`.** The backend passes it; the front must honour it.

## Verification

- Unit: host parsing (local/prod/`-back`/custom subdomain/unknown), resolver 302 target
  and 404, template renders `default_server` with zero services.
- Manual: stop an app, open its URL → gateway → app starts → lands in app. Confirm nginx
  stays up with no apps registered, and that a running app is not shadowed by the fallback
  (specific `server_name` must win over `default_server`).
