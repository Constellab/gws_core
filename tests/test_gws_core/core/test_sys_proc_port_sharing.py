import os
import socket
from unittest import TestCase

import psutil
from gws_core.core.model.sys_proc import SysProc


# test_sys_proc_port_sharing
class TestSysProcPortSharing(TestCase):
    """Grouping of the processes that hold a listening socket on the same port.

    An app port held by several *unrelated* processes means a duplicate app start: the app server
    sets SO_REUSEPORT, so the second start binds instead of failing, and the two processes then
    split users between them (each keeps its own in-memory auth state). A forked worker is not a
    duplicate, so pids of one process tree must collapse into a single group.
    """

    def _with_fake_ancestry(self, ancestors_by_pid: dict[int, set[int]], pids: list[int]):
        """Run the grouping against a synthetic process tree.

        Real ancestry cannot express the interesting cases: every process on the machine descends
        from init, so any two real pids are either in the same lineage or plain siblings.
        """
        original = SysProc._ancestors_of
        SysProc._ancestors_of = staticmethod(lambda pid: ancestors_by_pid[pid])
        try:
            return [sorted(group) for group in SysProc.group_pids_by_process_tree(pids)]
        finally:
            SysProc._ancestors_of = original

    def test_a_process_and_its_parent_are_one_group(self):
        """The real ancestry case: a listener plus the supervisor that forked it is one app."""
        pid = os.getpid()
        parent_pid = psutil.Process(pid).ppid()

        groups = SysProc.group_pids_by_process_tree([pid, parent_pid])

        # the order inside a group is not meaningful (it follows the discovery order)
        self.assertEqual([sorted(group) for group in groups], [sorted([pid, parent_pid])])

    def test_grouping_does_not_depend_on_the_pid_order(self):
        """Same tree, parent listed first: still one group.

        `psutil.process_iter` yields pids in whatever order the OS reports, and a forked worker may
        well have a lower pid than its parent, so the result must not depend on it.
        """
        pid = os.getpid()
        parent_pid = psutil.Process(pid).ppid()

        groups = SysProc.group_pids_by_process_tree([parent_pid, pid])

        self.assertEqual([sorted(group) for group in groups], [sorted([pid, parent_pid])])

    def test_children_listed_before_their_parent_merge_into_one_group(self):
        """Two workers seen before the parent that binds the socket are still one app.

        Each worker opens its own group (they are siblings, unrelated to each other), so the parent
        has to merge *both* of them — joining only the first match would report a duplicate start
        that does not exist.
        """
        # 10 and 11 are children of 9; 9 is a child of 1
        tree = {9: {9, 1}, 10: {10, 9, 1}, 11: {11, 9, 1}}

        self.assertEqual(self._with_fake_ancestry(tree, [10, 11, 9]), [[9, 10, 11]])

    def test_two_independent_starts_are_two_groups(self):
        """Neither pid descends from the other: this is the duplicate start worth reporting."""
        tree = {20: {20, 1}, 30: {30, 1}}

        self.assertEqual(self._with_fake_ancestry(tree, [20, 30]), [[20], [30]])

    def test_no_pid_is_no_group(self):
        """Nothing listening on the port yields no group (the caller must not report anything)."""
        self.assertEqual(SysProc.group_pids_by_process_tree([]), [])

    def test_get_listening_pids_finds_the_current_python_process_port(self):
        """The listener lookup must attribute a real listening socket to its owner process."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            port = server.getsockname()[1]

            self.assertIn(os.getpid(), SysProc.get_listening_pids_on_port(port))

    def test_get_listening_pids_on_a_free_port_is_empty(self):
        self.assertEqual(SysProc.get_listening_pids_on_port(1), [])
