# App authentication — OAuth-structured redesign (design, not yet implemented)

> Status: **design proposal**. Nothing here is built. It supersedes the incremental auth work
> documented in [APP_LAUNCH_AND_AUTH.md](APP_LAUNCH_AND_AUTH.md); once implemented, that file
> should be rewritten to match. Read that file first for the *current* behavior and vocabulary.

## 1. Why redesign

The current app auth grew by patching. The recurring pain, in one sentence: **there is no
first-class "app access" credential — everything is expressed by reusing the general lab-session
JWT**, so the same token is stretched to mean "launch this app", "carry identity between two
gateway calls", and "call the lab API as the user". Every fix (dev buttons, cookie reload survival,
legacy `gws_user_access_token` removal, PUBLIC-link guard, inactive-user handling) patched one seam
and stressed another.

Concrete symptoms this design resolves:

1. **start→handoff loses identity.** The space one-time code is consumed at `start`; `handoff` is a
   separate stateless call with no way to recover who the user is, so it wrongly requires a lab
   session → a space-only user 401s at handoff.
2. **The app JWT is a full lab session.** `exchange_app_code` mints `JWTService.create_jwt(user_id)`
   — a general token that authenticates the user on **every** route guarded by
   `check_user_access_token`. A space-only user must not get a lab-wide session.
3. **Inactive users.** A user can reach an app from the space without lab access (exists in DB but
   `is_active = False`, cannot log in). The gateway code path rejects them
   (`_get_and_check_user(allow_inactive=False)`), yet the non-gateway space-open path allows them —
   inconsistent.
4. **System-user elevation on PUBLIC links** (already guarded, but it is the same root cause: a
   credential meaning more than intended).

## 2. The core idea (OAuth mapped onto our system)

OAuth's useful property here is **separating the authorization server from a resource-scoped access
token**, and separating **who issues identity** from **what a token may do**.

| OAuth concept | Our system |
| --- | --- |
| **Authorization server** | the **lab** (gws_core) — owns the JWT secret, decides who may open an app |
| **Identity providers** (who the user *is*) | **lab login** (active users, existing session) **and** the **space** (space-only / inactive users, via a one-time code) — two pluggable IdPs feeding one authorize step |
| **Authorization grant** (single-use, short-lived) | a one-time **launch code** (`UniqueCodeService`) — already exists as `gws_code` |
| **Access token** (scoped to a resource) | a **new app-scoped token** resolving to `AuthContextApp{app_id, user}`, valid **only** for that app's API calls — never a general session |
| **Resource server** | the **lab API**, which confines an app-token caller to app-scoped routes |

The seam already exists in the codebase: **`AuthContextApp{app_id, user}`** is a first-class
authorization context, distinct from `AuthContextUser`, and `_auth_app` already produces it. Today
the app JWT collapses into a *user* context (that is exactly why it grants normal routes). **The
redesign makes the app credential produce and stay an `AuthContextApp`.** That single structural
change delivers the scope restriction — not by claim-checking hacks on top of a session token, but
because the token was never a session token.

## 3. Credentials — three distinct things, named and typed

Today these are conflated. The design makes them separate, each with one job and one validator.

| Credential | Issued by | Lifetime | Carries | Accepted by | Analogy |
| --- | --- | --- | --- | --- | --- |
| **Launch grant** | lab `authorize` step | single-use, ~60 s | `{app_id, user_id}` | the `token` exchange endpoint **only** | OAuth authorization code |
| **App access token** | lab `token` exchange | short (e.g. 2 h) | `{app_id, user_id}`, **app-scope claim** | app-mode routes → `AuthContextApp`; **rejected** on user-only routes | OAuth access token |
| **App refresh token** *(optional)* | lab `token` exchange | longer (e.g. 2 days), per-app | `{app_id, user_id}` | the `token` refresh endpoint **only** | OAuth refresh token |

The **general lab-session JWT** (`create_jwt` → `AuthContextUser`) still exists for real logged-in
users on normal routes — untouched. It is simply **no longer** what an app hands around.

### App-scope enforcement (the restriction you asked for)

Routes already choose an allow-list of auth modes via
`AuthorizationService.check_authorization(request, [modes])`
([authorization_service.py](../user/authorization_service.py)):

- `AuthorizationMode.USER` — general session JWT → `AuthContextUser`
- `AuthorizationMode.APP` — app credential → `AuthContextApp`
- `AuthorizationMode.SHARE_LINK` — share link → `AuthContextShareLink`

The app access token is validated **only** under `AuthorizationMode.APP` (via `_auth_app`), yielding
`AuthContextApp`. It is **never** accepted by `check_user_access_token` (USER mode). Therefore:

- An app makes its API calls against routes that opt into `APP` mode (already the pattern for
  `check_user_access_token_or_app`), and the call runs as `AuthContextApp{app_id, user}`.
- The same token presented to a **user-only** route is rejected — it is not a session.
- "Confined to the app" = the set of routes that admit `APP` mode. Tightening/loosening that set is
  how you tune what a space-only user can reach, in one place, declaratively.

> This replaces the current `_auth_app` in-memory `user_access_tokens` map lookup for the launching
> user (which we already partly moved to a JWT fallback). The map remains only for the **dev** and
> **system-user** sentinels.

## 4. The unified flow (all modes)

One flow, parameterized by **which IdP** proves identity and **whether the app is PUBLIC**.

```
                         ┌─────────────────────────── lab (authorization server) ───────────────────────────┐
 front /open/app/{key}   │                                                                                   │
        │                │  authorize: identity via  (a) lab session  OR  (b) space one-time code            │
        ├─ POST authorize ┼─▶ resolve user (allow_inactive for space) ─▶ cold-start app ─▶ issue LAUNCH GRANT │
        │                │        (PUBLIC app: no user, no grant)                                             │
        │◀ status_token + launch grant (or none for PUBLIC) ────────────────────────────────────────────────┤
        │                │                                                                                    │
        ├─ poll status ──┼─▶ until RUNNING                                                                    │
        │                │                                                                                    │
        ├─ navigate ─────┼─▶ app URL carrying the LAUNCH GRANT (Streamlit: via /gws-login; Reflex: query)     │
        │                │                                                                                    │
   app  ├─ token exchange┼─▶ consume grant ─▶ issue APP ACCESS TOKEN (+ refresh)  → AuthContextApp{app_id,usr}│
        │                │                                                                                    │
   app  ├─ API calls ────┼─▶ APP-mode routes, run as AuthContextApp; rejected on USER-only routes             │
        │                │                                                                                    │
   app  └─ reload (F5) ──┴─▶ re-validate / refresh the APP token (cookie or rx.Cookie) — no new grant needed  │
```

### Identity providers at `authorize`

- **Lab IdP** — the browser has a lab session (Authorization cookie/header). Active users, normal
  datalab launch and standalone gateway. Resolved as today.
- **Space IdP** — the URL carries a one-time **space code** (minted by
  `ShareLinkService.generate_user_access_token_for_space_link`, bound to `{share_link_id, user_id}`).
  Consumed at `authorize`; the user may be **inactive** (`allow_inactive=True`) — legitimate, they
  have no lab login. This is the "space login" you intuited: the space vouches for identity, the lab
  trusts it for **app scope only** (never a lab session).

Both IdPs converge to the same next step: issue a **launch grant** bound to `{app_id, user_id}`.
The start→handoff identity-loss bug disappears because the browser now carries the **grant** into
the app (not a consumed code, not a required session).

### PUBLIC apps

No IdP required. `authorize` cold-starts for anyone and issues **no** grant; the app URL is bare;
the app runs anonymously. API calls use the existing `fallback_to_system_user` opt-in. (Unchanged
from current behavior — this flow degenerates cleanly.)

## 5. Reload survival (F5 / new tab)

Same split as today, but persisting the **app access token** (scoped), not a session JWT:

- **Streamlit** — the `token` exchange runs behind the app host `/gws-login` nginx location, which
  sets the app access token as the `gws_app_jwt` HttpOnly cookie; on reload the app reads it and
  re-validates (and, if a refresh token is used, refreshes when near expiry). See
  [APP_LAUNCH_AND_AUTH.md §5](APP_LAUNCH_AND_AUTH.md).
- **Reflex** — the app access token is held in an `rx.Cookie` (`jwt_cookie`), rehydrated on reload
  and re-validated; refresh if used.

Because the persisted token is **app-scoped**, a stolen app cookie still cannot roam the lab — a
strict improvement over persisting a general session JWT.

## 6. What maps to what (migration from today)

| Today | Redesign |
| --- | --- |
| `POST /apps/gateway/start` | `authorize` step (same route, richer contract): resolve IdP, cold-start, return `status_token` **+ launch grant** |
| `POST /apps/gateway/handoff` | folded into `authorize`'s grant, or a thin step that just formats the app URL from the grant — **no separate identity resolution**, so no lab-session requirement |
| `gws_code` (app handoff code) | the **launch grant** (same `UniqueCodeService` primitive, `{app_id, user_id}` payload) |
| `POST /apps/exchange-code` → `create_jwt` | the **`token` exchange**: consume grant → issue **app access token** (`AuthContextApp` claim), not a general session JWT |
| `POST /apps/validate-jwt` | validate/refresh the **app access token** |
| `_auth_app` map lookup for launching user | validate the app access token → `AuthContextApp`; map kept only for dev/system sentinels |
| `check_unique_code(allow_inactive=False)` | `authorize` resolves the space IdP with `allow_inactive=True`; login-style callers stay strict |

Note the start→handoff carrier question that started this becomes **moot**: identity is resolved
once at `authorize` and carried forward as the **grant** (single-use, app-scoped), then upgraded to
the app access token at the `token` step. No general JWT is ever handed to the front, and there is
no second stateless call that has to re-authenticate.

## 7. Security properties (the acceptance criteria)

1. A **space-only / inactive** user can open an AUTHENTICATED app end-to-end (authorize → grant →
   token → app), without a lab login.
2. The **app access token cannot call user-only lab routes** — presenting it to a USER-mode route is
   rejected. It resolves to `AuthContextApp`, confined to APP-mode routes.
3. **PUBLIC links / apps** never elevate a visitor to a real user or the system user beyond the
   explicit `fallback_to_system_user` opt-in.
4. A leaked **launch grant** is single-use and short-lived → one app open, then dead.
5. A leaked **app token / cookie** confines the attacker to that one app's API surface, not the lab.
6. The **general lab session JWT** is unchanged for real logged-in users on normal routes.

## 8. Design decisions (locked)

1. **App scope = the existing `check_user_access_token_or_app` allow-list.** Audit result: **344
   routes are USER-only (`check_user_access_token`); only 20 admit `APP` mode
   (`check_user_access_token_or_app`)**, across 7 controllers (user, typing, tag, space_folder,
   scenario, resource, brick). That small set is *already* the "routes an app may call". So there is
   **no new route audit and no re-annotation**: we make the app token resolve **only** via
   `_auth_app` (APP mode) and be **rejected** by `check_user_access_token` (USER mode). The token is
   thereby confined to those 20 routes; the leak today is only that a *general* JWT also passes the
   344 USER-only routes.
2. **Claim shape: `typ` + `app_id`, one secret.** The token is a JWT `{sub, exp, typ: "app",
   app_id}`, signed with the existing secret. `_auth_app` accepts `typ == "app"` → `AuthContextApp`;
   `check_user_access_token` (USER mode) **rejects** any token with `typ == "app"`. (Session JWTs
   have no `typ`/`typ == "user"` and are rejected by `_auth_app`.)
3. **Always issue an app token** at the `token` step — for an active lab user opening their own app
   **and** a space/inactive user. One code path; the app **never** holds the user's real lab session,
   so even an active user's app cannot roam the lab.
4. **No refresh token in v1.** The app access token lives ~2 days; reload just re-validates it
   (matches today's Streamlit cookie / Reflex `rx.Cookie` flow). Revisit only if a fixed lifetime
   becomes a problem.
5. **Grant binding to browser (PKCE-style): deferred.** Not in v1; optional hardening later. The
   launch grant is already single-use and short-lived.
6. **`authorize` returns the launch grant, NOT the access token.** The access token is long-lived
   (~2 days) and must never travel through the browser URL / history / Referer / access logs, and
   (for Streamlit) must be set HttpOnly by nginx. So `authorize` resolves identity **once** and
   returns a single-use **grant** (safe in a URL); the app exchanges it server-side for the access
   token. This is the OAuth *authorization-code* flow, deliberately not the deprecated *implicit*
   flow. Handoff's separate identity resolution is **merged into `authorize`** — `authorize` returns
   `status_token` + the app URL carrying the grant, so there is no second call that must
   re-authenticate (this was the start→handoff carrier bug).
7. **Status token = opaque process handle, outside the auth model (Option A).** The token guarding
   `GET /apps/process/{token}/status` identifies a *process*, carries no user, and is polled
   repeatedly — so it is NOT folded into `UniqueCodeService` (which is single-use and user-bound).
   It stays a random per-process handle. **But** the current status DTO leaks internals
   (`started_by`, `config_file_path`, `env_file_path`/`env_file_content`, `source_ids`, `name`), so
   the token-guarded polling route must return a **lighter DTO** = `{id, status, status_text}` only;
   the rich DTO stays on the authenticated `/apps/status` list route.

## 9. Suggested implementation order (when approved)

1. **App-scope the token + enforce it** (the safe, high-value core — decision 1/2/3):
   - In the app `token` exchange (currently `exchange_app_code`), mint the JWT with `typ: "app"` +
     `app_id` instead of a plain session JWT. Do this for **every** app open (active + space users).
   - `_auth_app`: accept a `typ == "app"` token (verify `app_id` matches the calling app) →
     `AuthContextApp`. This replaces the in-memory `user_access_tokens` map lookup for the launching
     user (map stays only for dev/system sentinels).
   - `check_user_access_token` (USER mode): **reject** `typ == "app"` tokens.
   - **No route changes** — the 20 `_or_app` routes already define the scope (decision 1). Add a
     regression test asserting an app token is rejected on a representative USER-only route and
     accepted on an `_or_app` route.
   This step alone fixes symptoms #2 (leak) and #3 (inactive-user session), and is independently
   shippable/verifiable before touching the flow.
2. **Unify authorize → grant → token**: fold handoff's identity resolution into `authorize`, carry
   the grant to the app, exchange for the app token. Fixes symptom #1; removes the carrier problem.
3. **Space IdP inactive support**: `authorize`'s space path uses `allow_inactive=True`.
4. **Reload survival** re-pointed at the app token (Streamlit cookie / Reflex `rx.Cookie`) —
   re-validate only, no refresh (decision 4).
5. **Rewrite [APP_LAUNCH_AND_AUTH.md](APP_LAUNCH_AND_AUTH.md)** to describe the new model and delete
   this proposal once it is the reality.

## 10. File map (integration points for the implementer)

| Concern | File |
| --- | --- |
| Auth contexts (`AuthContextApp` = the app-scope seam) | [../user/auth_context.py](../user/auth_context.py) |
| Mode-based authorization, `_auth_app`, USER-mode rejection of app tokens | [../user/authorization_service.py](../user/authorization_service.py) |
| JWT mint/verify (add `typ`/`app_id` claim) | [../user/jwt_service.py](../user/jwt_service.py) |
| One-time codes (launch grant) | [../user/unique_code_service.py](../user/unique_code_service.py) |
| Gateway service (`authorize`/`token`), current start/handoff | [app_gateway_service.py](app_gateway_service.py) |
| Gateway routes + exchange/validate | [app_controller.py](app_controller.py) |
| App code↔token exchange (currently `exchange_app_code`) | [apps_manager.py](apps_manager.py) |
| Space IdP: share link → launch, inactive users | [../share/share_link.py](../share/share_link.py), [../share/share_link_service.py](../share/share_link_service.py) |
| App-side token store/reload (Streamlit / Reflex) | streamlit & reflex `*_main_state_base.py` (see [APP_LAUNCH_AND_AUTH.md §9](APP_LAUNCH_AND_AUTH.md)) |
