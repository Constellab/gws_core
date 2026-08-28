# DC Dashboard Component Builder

Create (or extend) a shared UI component in the `dc-dashboard-components` Angular
app so it can be embedded from both Reflex and Streamlit apps, and handle its
release through GitHub tags. Use this skill whenever the user wants a new
"dc component" (e.g. a resource picker, a rich editor, a menu, a tree) that
needs to run inside a Reflex or Streamlit app built with `gws_core`.

## Why this exists

Reflex and Streamlit can't directly host a full Angular component. Instead, one
Angular component is built once in the monorepo and consumed through two
different bridges:

- **Reflex**: the component is compiled to a **custom element** (web component,
  via `@angular/elements`) and wrapped in a small JSX file so it behaves like a
  native Reflex component.
- **Streamlit**: Streamlit components must live in an iframe, so a tiny
  `streamlit-iframe-message` app runs inside that iframe and only forwards
  postMessage events to a "loader" component (`dc-root`) that runs in the
  *main* Streamlit page and creates the real Angular component there,
  side-by-side with the rest of the page.

Both bridges are built from the exact same Angular component living under
`dc-components/`. You write it once.

## Repos involved

- `/lab/user/other-bricks/monorepo-front` — the Angular monorepo. This is
  where the actual component logic lives (`apps/dc-dashboard-components`).
- `/lab/user/bricks/gws_core` — the Python brick. This is where the Reflex and
  Streamlit Python wrappers live, plus the downloader that fetches the built
  Angular bundles from GitHub releases (`AppPluginDownloader`).

A new component almost always touches both repos.

## Step 1 — Understand the request

Ask (if not already clear from the request):

- **Name** of the component (kebab-case, e.g. `dc-date-picker`) and what it
  does (inputs, outputs).
- **Targets**: does it need to work in Reflex, Streamlit, or both? Not every
  existing component supports both — e.g. `dc-menu`, `dc-tree-menu` and
  `dc-process-config` are only wired into the Streamlit path today, while
  `dc-select-resource`, `dc-text-editor` and `dc-input-search` support both.
- Whether there's an existing Angular building block to reuse (a `li-*`
  component from `lab-lib`, an `fl-*` from `front-core-lib`), the way
  `dc-select-resource` just wraps `li-select-resource`.

## Step 2 — Build the Angular component

Location:
`monorepo-front/apps/dc-dashboard-components/src/dashboard-components/dc-components/<name>/`

Create the standard Angular component file set (mirror an existing one, e.g.
`dc-select-resource/`):

- `dc-<name>.component.ts`
- `dc-<name>.component.html`
- `dc-<name>.component.scss`

Rules specific to dc components (on top of the repo's general Angular rules —
see `docs/concepts` and the root `CLAUDE.md` in `monorepo-front`):

- The component class **must implement**
  `DcDynamicComponent<Input, Output>` from
  `../../../core/model/dc-dynamic-component.class.ts`:
  - `inputData = input<Input, any>(null, { transform: dcParseJsonInput })`
  - `authenticationInfo = input<DcAuthenticationInfo, any>(null, { transform: dcParseJsonInput })`
    — only needed if the component calls the lab API.
  - `outputEvent = output<Output>()` — only if the component emits values back.
- Add `hostDirectives: [DcCoreMainDirective]` in the `@Component` decorator and
  call `this.mainDirective.init(this.authenticationInfo())` in `ngOnInit`
  (`mainDirective = inject(DcCoreMainDirective)`) — this wires the auth token
  into the HTTP interceptor so the component's API calls are authenticated as
  the embedding user (or the system user, if the host app opted into that
  fallback).
- Use `computed()` signals to derive whatever the template needs from
  `inputData()`, exactly like `dc-select-resource.component.ts` does for
  `placeholder`, `defaultFilters`, `resource`, etc.
- Keep styling minimal (see the monorepo's general SCSS rules: no hardcoded
  colors/font-sizes, use the theme CSS variables and `g-text-*` classes).

Reference implementation to read before writing:
`monorepo-front/apps/dc-dashboard-components/src/dashboard-components/dc-components/dc-select-resource/dc-select-resource.component.ts`

## Step 3 — Register the component

Three registration points, all in
`monorepo-front/apps/dc-dashboard-components/src/dashboard-components/`:

1. **`core/model/dc-dynamic-component.class.ts`** — add a new member to
   `DcDynamicComponentEnum`, kebab-case value, e.g.
   `DATE_PICKER = 'date-picker'`. This string is the `component_name` the
   Python side will pass.
2. **`dc-core/service/dc-component-loader.service.ts`** — add a `case` in
   `getComponentType()`'s switch, dynamically importing the new component
   class. This is what makes it loadable from the Streamlit main-page loader
   (`dc-root` / `DcComponentLoaderProdComponent`). **Required for the
   Streamlit path**, not needed for Reflex-only components.
3. **`dc-main-reflex-prod.ts`** — only if the component must work in Reflex:
   import the component class and add a
   `createCustomElements(DcNewComponent, 'dc-<name>', app);` line inside
   `dcInitComponents()`. The tag name registered here
   (`dc-<name>`) is what the Reflex JSX will render.

If the component is Streamlit-only, skip step 3. If it's Reflex-only (rare —
most components want Streamlit support too since it's cheap), you can skip
step 2, but there's little reason to.

## Step 4 — Python wrapper for Reflex (if targeting Reflex)

Location:
`gws_core/src/gws_core/apps/reflex/_gws_reflex/gws_reflex_main/gws_components/reflex_<name>_component/`

Two files, mirroring `reflex_select_resource_2_component/`:

- **`reflex_<name>_component.py`**:
  - A DTO (`BaseModelDTO`) mirroring the Angular `Dc<Name>Input` interface
    field-for-field.
  - An `rx.Component` subclass: `library = rx.asset("reflex_<name>_component.jsx", shared=True)`
    wrapped as `"$/public/" + asset_path`, `tag = "<PascalName>Component"`
    (must match the JSX export name), a `Var[DTO | None]` for the input, a
    `Var[ReflexUserAuthInfo | None]` for `authentication_info`, and an
    `rx.EventHandler[rx.event.passthrough_event_spec(dict)]` if there's an
    output event.
  - A factory function `<name>_component(input_data, output_event=None,
    fallback_to_system_user=False, **kwargs)` that resolves
    `ReflexMainState.get_reflex_user_auth_info` (or
    `..._with_system_fallback` when `fallback_to_system_user=True`) and calls
    `.create(...)`.
- **`reflex_<name>_component.jsx`**:
  - Import the plugin's CSS/JS once:
    `import '/public/external/gws_plugin/styles.css';` and
    `import { dcInitComponents } from '/public/external/gws_plugin/dc-reflex.js'; await dcInitComponents();`
  - A React function component matching the `tag` above, taking `inputData`,
    `authenticationInfo`, `outputEvent` as props.
  - On `inputData` change, `JSON.stringify` it onto the DOM element (the
    custom element expects string props, parsed with `dcParseJsonInput` on
    the Angular side) — include an incrementing `__count__` field so
    re-sending an identical value still triggers a re-parse.
  - Attach/detach a native `outputEvent` DOM event listener that calls the
    `outputEvent` prop with `event.detail`.
  - Render the custom element tag registered in Step 3
    (`<dc-<name> ref={...} authenticationInfo={...} ...></dc-<name>>`).

Reference: read both files of `reflex_select_resource_2_component/` in full
before writing the new pair — the pattern is very mechanical.

## Step 5 — Python wrapper for Streamlit (if targeting Streamlit)

Location:
`gws_core/src/gws_core/apps/streamlit/_gws_streamlit/gws_streamlit_main/gws_components/streamlit_<name>.py`

- A class (or set of helper classes/DTOs, if the component's input is
  structured — see `StreamlitMenuButton` / `StreamlitMenuButtonItem` for a
  richer example) holding:
  `_streamlit_component_loader = StreamlitComponentLoader("<enum-value-from-step-3>")`
  — the string **must** match the `DcDynamicComponentEnum` value exactly.
- A public method (e.g. `select_resource(...)`, `render(...)`) that:
  1. Builds the `data` dict matching the Angular `Dc<Name>Input` interface
     (snake_case keys — they're `jsonable_encoder`'d, not camelCased).
  2. Calls
     `self._streamlit_component_loader.call_component(data, key=key, authentication_info=StreamlitMainState.get_user_auth_info(fallback_to_system_user=...))`.
  3. Interprets the returned `component_value` and (if the component holds
     state across reruns, like a selection) stashes/reads it from
     `st.session_state`.

Reference: `streamlit_resource_select.py` (simple, stateful selection) and
`streamlit_menu_button.py` (structured input tree, click-dedup via a
timestamp in the returned value — copy that pattern for anything with
discrete "action" outputs instead of continuous state).

## Step 6 — Dev loop (test before releasing)

From `monorepo-front` root (bun workspace, never `npm`/`yarn`/`pnpm`):

- **Standalone** (fastest, no Python app needed):
  `bun run dc-components:serve` → open `http://localhost:4201`.
- **Inside a Streamlit app**: `bun run dc-streamlit-components:serve-iframe`
  (serves on `:4201`, no HMR), then in the Python app set
  `StreamlitComponentLoader.IS_RELEASED = False` (or the specific
  `_streamlit_component_loader` instance) so it points at the dev server
  instead of a downloaded release. Must be tested via
  `http://localhost:8511` (not a `*.localhost` subdomain — cross-origin
  breaks the iframe otherwise), and only one app can run this dev iframe at
  a time (others must use the production-built `streamlit-components`).
- **Inside a Reflex app**:
  1. `bun run dc-reflex-components:build-dev`
  2. Copy `dist/apps/dc-dashboard-components/reflex-components/gws_plugin`
     into the Reflex app's `assets/external/` folder.
  3. Set `AppPluginDownloader.IS_RELEASE = False` (or on the specific
     `ReflexPlugin`/downloader subclass) — combined with
     `Settings.is_local_dev_env()`, this makes `install_package()` copy from
     `AppPluginDownloader.LOCAL_PLUGIN_PATH` instead of downloading, or here
     effectively use the manually-copied local build.
  4. Run the Reflex app normally (`gws reflex run` / `gws reflex compile` to
     just check it builds).

## Step 7 — Release

Nothing is usable in `IS_RELEASE=True` mode until it's published as a GitHub
release under `Constellab/dashboard-components`. The CI/CD pipeline
(`monorepo-front/.github/workflows/build_dashboard_components.yml`) does this
automatically on tag push:

1. Commit the Angular + Python changes normally (in their respective repos —
   they're independent git histories).
2. In `monorepo-front`, create and push a tag matching `dc_*`, e.g.:
   ```bash
   git tag dc_1.0.13
   git push origin dc_1.0.13
   ```
   This builds and releases **all three** packages in one shot —
   `streamlit-iframe-message`, `streamlit-components`, `reflex-components` —
   each zipped and attached to a GitHub release tagged `dc_1.0.13` in
   `Constellab/dashboard-components`, with a generated `version.json`
   (`{"version": "dc_1.0.13"}`) baked into each package.
3. In `gws_core`, bump
   `AppPluginDownloader.DASHBOARD_COMPONENTS_VERSION` in
   `src/gws_core/apps/app_plugin_downloader.py` to the new tag
   (`"dc_1.0.13"`). This single constant governs the version downloaded for
   **all** components across both Reflex and Streamlit — it is not
   per-component.
4. Bump the `gws_core` brick version (`settings.json`) and publish it
   (`gws brick version push`) so labs actually pick up the new downloader
   constant — see the brick version/publish commands in the root
   `CLAUDE.md`.

Until step 3–4 are done, released labs keep using the previously pinned
version even though the new GitHub release already exists — the version bump
is what flips them over.

## Checklist for a new dc component

- [ ] Angular component under `dc-components/<name>/`, implements
      `DcDynamicComponent`, uses `dcParseJsonInput` + `DcCoreMainDirective`
- [ ] New value in `DcDynamicComponentEnum`
- [ ] Switch case in `DcComponentLoaderService.getComponentType()` (Streamlit path)
- [ ] `createCustomElements(...)` call in `dc-main-reflex-prod.ts` (Reflex path, if needed)
- [ ] `reflex_<name>_component/` (`.py` + `.jsx`) under `gws_components/` (if Reflex)
- [ ] `streamlit_<name>.py` under `gws_components/` (if Streamlit)
- [ ] Tested via the standalone/dev-iframe/dev-reflex loop
- [ ] Tag `dc_x.y.z` pushed on `monorepo-front`
- [ ] `DASHBOARD_COMPONENTS_VERSION` bumped in `app_plugin_downloader.py`
- [ ] `gws_core` brick version bumped and published
