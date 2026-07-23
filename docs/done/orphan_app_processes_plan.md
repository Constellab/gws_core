# Plan — Reap orphaned app processes (issue #97)

## Problem

Each `gws server run` layers a fresh set of app child processes (streamlit / reflex)
on top of the previous run's survivors, so RAM climbs until the lab OOMs.

Root cause is a combination of three facts:

1. App children are spawned with `start_new_session=True` (`shell_proxy.py`), so they
   live in **their own process group**, detached from the server's group. Killing the
   server's group (terminal close, container stop) does not kill them.
2. `AppsManager.running_processes` is an **in-memory dict**. On an unclean stop
   (SIGKILL, crash, OOM, closing the VSCode terminal → SIGHUP) the graceful shutdown
   path never runs, the dict evaporates, and the detached app groups keep running.
3. On the next boot nothing reclaims them, and `_get_next_available_port` actively
   **skips bound ports**, so the new instance picks a *different* port and the orphan
   lingers forever.

Reproduced in dev: a lab run from the VSCode terminal via `gws server run`, restarted
repeatedly, accumulated orphan app processes.

## Fix — two complementary parts

### Part A — Boot-time marker reaping (safety net for unclean stops)

In `AppsManager.init()` (runs on every server start, before any port allocation),
find and kill leftover app processes from previous runs.

- Detect by the `GWS_APP_ID` env var, which is already set on every app child via
  `AppProcess._get_common_env_variables`. Enumerate `psutil` processes and read
  `Process.environ()`; a process is an orphan app if `GWS_APP_ID` is present.
- Kill each orphan's **process group** (`os.killpg`, SIGKILL) — mirrors
  `SysProc.kill_process_on_port`, so the whole reflex/streamlit tree dies atomically.
- **Fallback**: `Process.environ()` can raise `AccessDenied` under stricter
  permissions. When environ reading is denied, fall back to a **port-band sweep**
  (kill any listener from `get_app_external_port()+1` up to
  `+ MAX_RUNNING_APPS*2`, reusing `SysProc.kill_process_on_port`).
- Must run **before** the auto-start listener starts new apps, and before port
  allocation, so ports are freed and reused rather than leaked.

New method: `SysProc.kill_orphan_app_processes(marker_env_var, port_band)` (static),
called from `AppsManager.init()`.

### Part C — Continuous mid-session reaping of untracked orphans

The boot reaper (Part A) only runs once, in `init()`. An app can also be orphaned
*while the same server keeps running* (a crashed check-running loop, a runner that
respawns a stray listener). Those would accumulate until the next restart.

`AppsManager._refresh_processes()` — already called on every create/status pass —
now also calls `_reap_untracked_orphans()`:

- `SysProc.find_marked_processes(marker)` returns `{pid: marker_value}` (the marker
  value is the app id / `resource_model_id`).
- Kill only the pids whose marker value is **not** a key in `running_processes`.
- An app is tracked from the moment it is registered — before its child is even
  spawned — so a starting-but-not-yet-running app is never mistaken for an orphan,
  and a still-tracked (possibly-live) app's tree is left alone until it goes STOPPED.
- Best-effort: failures are logged and swallowed. The environ-denied port-sweep
  fallback is intentionally NOT used here (a port sweep cannot distinguish a live
  app's port from a stray one).

Refactor: `SysProc` gains `find_marked_processes` and `killpg_of_pids`; the boot
reaper `kill_orphan_app_processes` is rebuilt on top of them (it kills ALL marked
processes — safe only at boot, when nothing is tracked yet).

### Part B — Harden clean-kill-on-stop (prevent orphans in the graceful case)

1. Register a **SIGHUP** handler in addition to SIGINT/SIGTERM
   (`AppsManager._register_signal_handlers`). Closing a terminal sends SIGHUP — the
   exact Vilnius case.
2. Make `stop_all_processes()` reap in **parallel**: SIGTERM every process group,
   then a single bounded wait, then SIGKILL survivors — so a multi-app shutdown
   completes inside uvicorn's shutdown window instead of being cut off by the
   sequential 5s-per-app wait.

## Files touched

- `core/model/sys_proc.py` — `kill_orphan_app_processes` (+ helper).
- `apps/apps_manager.py` — call reaper in `init()`; SIGHUP handler; parallel
  `stop_all_processes`.
- Tests in `tests/`.

## Notes

- The marker env var name lives in `AppProcess` (`GWS_APP_ID`); expose it as a
  constant to avoid duplicating the literal.
- Reaping by marker is safe: the server never sets `GWS_APP_ID` in its own
  `os.environ`, only in the per-app env dict, so only real app children match.
