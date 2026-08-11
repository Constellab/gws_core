# Front spec — honour `redirect_to` on the app gateway page

**Target:** `monorepo-front` / `lab-front`
**Component:** `apps/lab-front/src/app/lab-public-route/lab-open-app-page/lab-open-app-page.component.ts`
**Backend status:** already implemented (`docs/todo/app_shareable_url_plan.md`). The backend *sends*
`redirect_to`; nothing reads it yet, so shared **deep links** silently land on the app root.

---

## 1. Why this exists

An app's nginx block only exists while the app runs, so a shared URL for a **stopped** app used to
hit a dead port. A persistent nginx fallback now catches those hosts and routes them here:

```
user opens  http://{resource_model_id}.localhost:8510/config     (app STOPPED)
  -> nginx default_server
  -> 302 /gws-app-fallback?host=$host&target=$request_uri
  -> core-api GET /apps/fallback/resolve
  -> 302 /open/app/{app_key}?redirect_to=%2Fconfig                <-- LabOpenAppPageComponent
  -> existing flow: start -> poll -> handoff -> navigate to app_url
```

The user asked for `/config`; today they get the app root. Two changes close that gap — and one of
them is a **pre-existing bug** the fallback makes reachable.

---

## 2. Change 1 — carry `redirect_to` into the app URL

### 2.1 Read the param (`ngOnInit`)

Alongside the existing `code` read:

```ts
private redirectTo?: string;

ngOnInit(): void {
  this.appKey = this.activatedRoute.snapshot.paramMap.get('appKey');
  this.code = this.activatedRoute.snapshot.queryParamMap.get('code') ?? undefined;
  this.redirectTo = this.activatedRoute.snapshot.queryParamMap.get('redirect_to') ?? undefined;

  this.start();
}
```

`queryParamMap.get()` already URL-decodes — do **not** decode again (`%2F` decoded twice turns
`/a%2Fb` into a wrong path).

### 2.2 Apply it at the final navigation (`handoff`)

`app_url` carries the single-use `gws_code`, so the merge must preserve the existing query string
and only replace the path.

```ts
private handoff(): void {
  this.appService.gatewayHandoff(this.appKey, this.authorizeGrant).subscribe({
    next: (result) => {
      window.location.href = LabOpenAppPageComponent.applyRedirectTo(result.app_url, this.redirectTo);
    },
    error: () => this.onError(),
  });
}

/**
 * Merge a requested in-app path into the handoff URL.
 * The handoff URL's own query (gws_code) must survive: the app exchanges it for a JWT.
 */
private static applyRedirectTo(appUrl: string, redirectTo?: string): string {
  if (!redirectTo) return appUrl;
  // Only same-origin, path-only targets (defence in depth; the backend also sanitises).
  if (!redirectTo.startsWith('/') || redirectTo.startsWith('//') || redirectTo.includes('\\')) {
    return appUrl;
  }

  const target = new URL(appUrl);
  const requested = new URL(redirectTo, target.origin);

  target.pathname = requested.pathname;
  // keep gws_code; add the deep link's own params without ever clobbering it
  requested.searchParams.forEach((value, key) => {
    if (!target.searchParams.has(key)) target.searchParams.set(key, value);
  });
  return target.toString();
}
```

### Rules

| # | Rule | Why |
| --- | --- | --- |
| 1 | Never drop `gws_code` from `app_url` | It is the app's only credential; losing it breaks auth |
| 2 | Accept only single-slash-prefixed paths | Open-redirect guard (`//evil.com`, `https://…`, `\`) |
| 3 | Absent `redirect_to` → `app_url` verbatim | The common case must not regress |
| 4 | Apply at final navigation only | Not in the `start` / `handoff` request bodies |
| 5 | `gws_code` wins on key collision | A deep link must not be able to forge it |

---

## 3. Change 2 — preserve `redirect_to` across the login hop (**pre-existing bug**)

`onStartError` rebuilds the return URL from `appKey` only, dropping every query param:

```ts
// lab-open-app-page.component.ts:105 — current
const redirectUri = `/${LI_CONST_OPEN_ROUTE}/app/${this.appKey}`;
```

So a **logged-out** visitor loses `redirect_to` (and already loses `code`) on the 401 → login →
return hop. Fix by preserving the current URL's query:

```ts
const redirectUri = `/${LI_CONST_OPEN_ROUTE}/app/${this.appKey}${window.location.search}`;
```

> **Note on `code`:** the existing comment at lab-open-app-page.component.ts:103-104 says the code
> is intentionally not resent (single-use, and a session exists after login). Preserving the whole
> query string means `code` now *does* come back. That is harmless — the backend prefers the code
> path and a spent code raises, so **if you want to keep the current behaviour**, strip `code` and
> keep only `redirect_to`:
>
> ```ts
> const params = new URLSearchParams(window.location.search);
> params.delete('code');
> const query = params.toString();
> const redirectUri = `/${LI_CONST_OPEN_ROUTE}/app/${this.appKey}${query ? `?${query}` : ''}`;
> ```
>
> **Recommended:** this second form — it fixes the deep link without changing the code semantics.

### Login-side guard: already compatible, verify only

`LabLoginPageComponent.isSafeRedirectUri` (lab-login-page.component.ts:41-44) tests
`/^\/open\/app\//` and rejects `//` and `\`. A query string does not affect that regex, so
`/open/app/abc123?redirect_to=%2Fconfig` passes unchanged. **No login-side change needed** — but
add a spec case, since this guard is the security boundary for the whole hop.

---

## 4. Contract reference (verified against the backend)

Real values from `FrontService.get_app_gateway_url`:

```
root         /open/app/abc123
deep link    /open/app/abc123?redirect_to=%2Fconfig%3Ftab%3D1
space + deep /open/app/abc123?code=XYZ&redirect_to=%2Fconfig
```

`redirect_to` is optional, URL-encoded, and may coexist with `code`. Unchanged shapes:

| Call | Body | Response |
| --- | --- | --- |
| `POST /apps/gateway/start` | `{app_key, code?}` | `{status_token, authorize_grant?}` |
| `GET /apps/process/{status_token}/status` | — | `{id, status, status_text}` |
| `POST /apps/gateway/handoff` | `{app_key, authorize_grant?}` | `{app_url}` |

No `LiAppService` change: `redirect_to` never reaches the backend, it only shapes the final
client-side navigation.

---

## 5. Test cases

`applyRedirectTo` — all rows below are **verified actual output** of the implementation above:

| `redirect_to` | `app_url` | Expected navigation |
| --- | --- | --- |
| *(absent)* | `http://a.localhost:8510/?gws_code=C` | `http://a.localhost:8510/?gws_code=C` |
| `/config` | `http://a.localhost:8510/?gws_code=C` | `http://a.localhost:8510/config?gws_code=C` |
| `/config?tab=1` | `http://a.localhost:8510/?gws_code=C` | `…/config?gws_code=C&tab=1` |
| `//evil.com` | `http://a.localhost:8510/?gws_code=C` | unchanged (rejected) |
| `https://evil.com` | `http://a.localhost:8510/?gws_code=C` | unchanged (rejected) |
| `/x?gws_code=FORGED` | `http://a.localhost:8510/?gws_code=C` | `…/x?gws_code=C` (real code wins) |

Also cover:
- `onStartError` builds a `redirectUri` that still carries `redirect_to` (Change 2).
- `isSafeRedirectUri('/open/app/abc123?redirect_to=%2Fconfig')` is `true`.

**Manual end-to-end:** stop an app, open `http://{resource_model_id}.localhost:8510/config`,
confirm the browser ends on `/config` inside the started app and the app authenticates (no
"expired or already used" toast). Repeat **logged out** — that path only works with Change 2.

Run with `bunx nx test lab-front`.

---

## 6. Not in scope

- **Host maps to no app** → the resolver returns 404 and never redirects here; do not add handling.
- **App fails to start** → existing `onError` / Retry UI is unchanged.
- Backend follow-ups in `docs/todo/app_shareable_url_plan.md`: stale-`gws_code` recovery for a
  *running* app, cookie `max_age` + sliding JWT renewal, space-origin re-auth.
