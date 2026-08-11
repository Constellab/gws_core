import contextlib
import os
import signal
import time

import psutil
from psutil import Popen, Process

from ..exception.exceptions import BadRequestException
from ..utils.logger import Logger


class SysProc:
    """
    SysProc class.

    Wrapper of `psutil.Process` class.
    This class that only exposes necessary functionalities to easily manage shell processes.
    """

    _process: Process | None = None
    _use_process_group: bool = False

    def __init__(self, process: Process | None = None, use_process_group: bool = False):
        self._process = process
        self._use_process_group = use_process_group

    def get_process(self) -> Process:
        return self._process

    def is_alive(self) -> bool:
        return self._process.is_running()

    def is_zombie(self) -> bool:
        return self._process.status() == "zombie"

    def kill(self):
        self._process.kill()

    def kill_with_children(self):
        """Kill the process and all its children.

        If the process was started with a process group (start_new_session=True),
        sends SIGTERM to the entire process group first for graceful shutdown,
        waits briefly, then sends SIGKILL to any survivors.
        Otherwise, falls back to killing each child individually.
        """
        if self._use_process_group:
            self._kill_process_group()
        else:
            for child in self.get_all_children():
                child.kill()
            self.kill()

    def _kill_process_group(self):
        """Kill the entire process group: SIGTERM first, then SIGKILL after a short wait."""
        try:
            pgid = os.getpgid(self._process.pid)
        except (ProcessLookupError, OSError):
            # Process already gone
            return

        # Send SIGTERM to the entire process group for graceful shutdown
        try:
            os.killpg(pgid, signal.SIGTERM)
        except (ProcessLookupError, OSError):
            return

        # Wait up to 5 seconds for processes to terminate gracefully
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if not self._process.is_running():
                return
            time.sleep(0.2)

        # Force kill any survivors
        with contextlib.suppress(ProcessLookupError, OSError):
            os.killpg(pgid, signal.SIGKILL)

    def get_all_children(self) -> list[Process]:
        """Return all the chlidren of process recursively.

        :return: _description_
        :rtype: List[Process]
        """
        return self._process.children(recursive=True)

    def stats(self) -> dict:
        """
        Get process statistics
        """
        return self._process.as_dict()

    def wait(self, timeout=None):
        """
        Wait for a process PID to terminate
        """
        self._process.wait(timeout=timeout)

    @property
    def pid(self) -> int:
        if self._process is None:
            return 0
        return self._process.pid

    @classmethod
    def popen(cls, cmd, *args, **kwargs) -> "SysProc":
        try:
            use_process_group = kwargs.get("start_new_session", False)
            return SysProc(Popen(cmd, *args, **kwargs), use_process_group=use_process_group)
        except Exception as err:
            raise BadRequestException(
                f"An error occured when calling command {cmd}. Error: {err}"
            ) from err

    @staticmethod
    def from_pid(pid) -> "SysProc":
        return SysProc(Process(pid))

    @staticmethod
    def get_listening_pids_on_port(port: int) -> list[int]:
        """Return the PIDs of every process holding a LISTEN socket on `port`.

        More than one PID is not normal for an app port: it means several processes share the
        socket via SO_REUSEPORT (which the app server sets), so the kernel load-balances
        connections between them. For a stateful app that silently splits users across processes.

        Iterates per process rather than using ``psutil.net_connections()``: with SO_REUSEPORT
        the global call reports both sockets but attributes them to the *same* pid, which hides
        the very duplication this method exists to detect. Walking processes attributes each
        socket to its real owner.

        Processes the OS refuses to inspect are skipped. That is the norm rather than an anomaly on
        Linux (a non-root process cannot read another user's sockets), so the count is only logged at
        debug level -- but it is logged, because an empty result may mean "port is free" or "the
        holder was invisible to us".
        """
        pids: list[int] = []
        inaccessible = 0
        for proc in psutil.process_iter(["pid"]):
            try:
                connections = proc.net_connections(kind="inet")
            except psutil.AccessDenied:
                inaccessible += 1
                continue
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue

            for conn in connections:
                if (
                    conn.status == psutil.CONN_LISTEN
                    and conn.laddr
                    and conn.laddr.port == port
                    and proc.pid not in pids
                ):
                    pids.append(proc.pid)

        if not pids and inaccessible:
            Logger.debug(
                f"No process found listening on port {port}, but the sockets of {inaccessible} "
                "process(es) could not be enumerated (permission denied)"
            )
        return pids

    @staticmethod
    def group_pids_by_process_tree(pids: list[int]) -> list[list[int]]:
        """Group the given pids by process tree, so related processes count as one.

        A forked child inherits its parent's file descriptors, so a server that binds then forks a
        worker shows up as several pids holding the same listening socket. Those are one app, not a
        duplicate. Grouping them makes "how many independent processes are here" answerable: one
        group means one app, several groups means several independent starts.

        Two pids are related when one descends from the other. Full ancestry is deliberately *not*
        intersected: every process on the machine shares init (and two duplicate starts share the
        lab server that spawned both), so shared ancestry would collapse everything into one group
        and never detect anything. The flip side is that two sibling workers whose listening parent
        is missing from `pids` -- it exited, or the OS refused to inspect it -- land in separate
        groups and read as a duplicate. Acceptable for a diagnostic: over-reporting is safer than
        hiding a real duplicate.

        :param pids: the pids to group
        :return: one list of pids per independent process tree
        """
        ancestors_by_pid = {pid: SysProc._ancestors_of(pid) for pid in pids}

        groups: list[list[int]] = []
        for pid in pids:
            ancestors = ancestors_by_pid[pid]
            # every group holding a relative of this pid: they are all one tree, so merge them all
            # rather than joining the first match (the pids may arrive child-before-parent)
            related = [
                group
                for group in groups
                if any(
                    other in ancestors or pid in ancestors_by_pid[other] for other in group
                )
            ]
            if not related:
                groups.append([pid])
                continue

            merged = [pid]
            for group in related:
                merged.extend(group)
            groups = [group for group in groups if group not in related]
            groups.append(merged)

        return groups

    @staticmethod
    def _ancestors_of(pid: int) -> set[int]:
        """Return `pid` plus the pids of all its ancestors (empty-safe)."""
        ancestors: set[int] = {pid}
        with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            ancestors.update(parent.pid for parent in psutil.Process(pid).parents())
        return ancestors

    @staticmethod
    def kill_process_on_port(port: int) -> list[int]:
        """Find any process with a LISTEN socket on `port` and kill its entire process group.

        Killing the process group (SIGKILL via killpg) takes down the listener
        plus its supervisor and siblings atomically — necessary for runners like
        Reflex where the listener's parent would otherwise respawn a replacement
        between our kill and the next bind attempt.

        Listeners are looked up with `get_listening_pids_on_port`, which walks processes one by one:
        `psutil.net_connections()` attributes every socket sharing a port via SO_REUSEPORT to the
        same pid, so it would leave the other holder alive and the new app would end up sharing the
        port with it.

        Returns the list of PIDs that were targeted (may be empty).
        """
        offender_pids = SysProc.get_listening_pids_on_port(port)

        killed_pgids: set[int] = set()
        killed_pids: list[int] = []
        for pid in offender_pids:
            with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                if SysProc._killpg_of_pid(
                    pid, killed_pgids, reason=f"Port {port} is held by orphan process"
                ):
                    killed_pids.append(pid)
                    Logger.info(f"Freed port {port} (killed pid={pid})")

        return killed_pids

    @staticmethod
    def _killpg_of_pid(pid: int, killed_pgids: set[int], reason: str) -> bool:
        """SIGKILL the whole process group of `pid`, deduplicating by pgid.

        SIGKILLing the group atomically takes down the listener plus any supervisor
        (e.g. `reflex run`) and siblings, leaving no window for a respawn. `killed_pgids`
        is mutated in place so a caller iterating several pids of the same group only
        kills it once.

        :param pid: the pid whose process group to kill
        :param killed_pgids: set of already-killed pgids (updated in place)
        :param reason: prefix for the warning log line, for context
        :return: True if this pid's group was targeted, False if the process was gone
        """
        proc = Process(pid)
        try:
            proc_name = proc.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            proc_name = "<unknown>"
        try:
            proc_cmdline = proc.cmdline()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            proc_cmdline = []

        try:
            pgid = os.getpgid(pid)
        except (ProcessLookupError, OSError):
            return False

        Logger.warning(
            f"{reason} pid={pid} pgid={pgid} name={proc_name} "
            f"cmdline={proc_cmdline!r} — killing process group"
        )

        if pgid not in killed_pgids:
            with contextlib.suppress(ProcessLookupError, OSError):
                os.killpg(pgid, signal.SIGKILL)
            killed_pgids.add(pgid)

        return True

    @staticmethod
    def find_marked_processes(marker_env_var: str) -> tuple[dict[int, str], bool]:
        """Find all processes carrying `marker_env_var` in their environment.

        The app layer sets `marker_env_var` on every app child (and thus its whole inherited
        tree), so this locates app processes regardless of which port they ended up on.

        :param marker_env_var: env var name that identifies an app process (e.g. GWS_APP_ID)
        :return: a tuple of (mapping pid -> marker value, whether any environ read was denied).
            The denied flag lets callers fall back to a coarser detection (e.g. a port sweep)
            when process environments cannot be read under stricter permissions.
        """
        found: dict[int, str] = {}
        environ_denied = False

        for proc in psutil.process_iter(["pid"]):
            try:
                environ = proc.environ()
            except (psutil.NoSuchProcess, psutil.ZombieProcess):
                continue
            except (psutil.AccessDenied, OSError):
                # Cannot read this process's env — remember so the caller can fall back.
                environ_denied = True
                continue

            value = environ.get(marker_env_var)
            if value is not None:
                found[proc.pid] = value

        return found, environ_denied

    @staticmethod
    def killpg_of_pids(pids: list[int], reason: str) -> list[int]:
        """SIGKILL the process groups of the given pids, deduplicating groups.

        :param pids: the pids whose process groups to kill
        :param reason: prefix for the per-process warning log line, for context
        :return: the pids that were targeted (a process already gone is skipped)
        """
        killed_pgids: set[int] = set()
        killed_pids: list[int] = []
        for pid in pids:
            with contextlib.suppress(psutil.NoSuchProcess, psutil.AccessDenied):
                if SysProc._killpg_of_pid(pid, killed_pgids, reason=reason):
                    killed_pids.append(pid)
        return killed_pids

    @staticmethod
    def kill_orphan_app_processes(marker_env_var: str, port_band: range) -> list[int]:
        """Kill app child processes left over from a previous, uncleanly-stopped server run.

        Apps are spawned in their own process group (start_new_session=True), so a hard
        server stop (SIGKILL, crash, OOM, closing the terminal) leaves them running with no
        one tracking them. On the next boot they must be reaped explicitly, before any port
        allocation, or their RAM accumulates run after run (see issue #97).

        Detection is by the `marker_env_var` environment variable. This catches orphans
        regardless of which port they ended up on. When reading process environments is denied
        (`AccessDenied`), falls back to a port-band sweep so the reaper still works under
        stricter permissions.

        This kills EVERY marked process, so it is only safe at boot, when no app is tracked
        yet. For mid-session use, find the marked processes and kill only the untracked ones.

        :param marker_env_var: env var name that identifies an app process (e.g. GWS_APP_ID)
        :param port_band: the range of local ports apps may bind to, used for the fallback sweep
        :return: the list of orphan pids that were targeted (may be empty)
        """
        marked, environ_denied = SysProc.find_marked_processes(marker_env_var)

        killed_pids = SysProc.killpg_of_pids(
            list(marked.keys()), reason="Orphan app process from a previous run"
        )

        if environ_denied and not killed_pids:
            Logger.warning(
                "Could not read process environments to find orphan apps (permission denied) — "
                "falling back to a port-band sweep"
            )
            for port in port_band:
                killed_pids.extend(SysProc.kill_process_on_port(port))

        if killed_pids:
            Logger.info(f"Reaped {len(killed_pids)} orphan app process(es): {killed_pids}")

        return killed_pids
